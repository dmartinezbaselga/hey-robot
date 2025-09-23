from openai import OpenAI
import subprocess

from util.logging import print_warning, print_success, print_path, print_value
from util.timer import TimerCollection

from assistant_base import Assistant

use_poetry = True
compile_planner = False

known_components = dict()
known_components["goal_cost"] = '''
    # Goal cost. Shortcut name: <goal_cost>
    goal_weight = params.get("reach_goal_weight")
    goal_x = params.get("goal_x")
    goal_y = params.get("goal_y")
    dist_to_goal = cd.sqrt((x - goal_x)**2 + (y - goal_y)**2) # Get distance to goal
    normalized_dist_to_goal = dist_to_goal / 20
    cost_goal = normalized_dist_to_goal**2 # Try to minimize the distance
    cost += goal_weight * cost_goal
'''

known_components["contour_cost"] = '''
    # Contour cost. Shortcut name: <contour_cost>
    # The path is given with this function
    path = Spline2D(params, settings["contouring"]["num_segments"], s)
    contour_weight = params.get("contour_weight")
    lag_weight = params.get("lag_weight")
    path_x, path_y = path.at(s)
    path_dx_normalized, path_dy_normalized = path.deriv_normalized(s)
    error_contour = path_dy_normalized * (x - path_x) - path_dx_normalized * (y - path_y)
    cost_contour = contour_weight / 5. * (error_contour / 4.)**2
    error_lag = path_dx_normalized * (x - path_x) + path_dy_normalized * (y - path_y)
    cost_lag = lag_weight / 5. * (error_lag / 4.)**2
    cost += cost_lag
    cost += cost_contour
'''

known_components["input_cost"] = '''
    # Penalize the inputs. Shortcut name: <input_cost>
    # Lower weight = less penalty, more acceleration capability
    acceleration_resistance_weight = params.get("acceleration_resistance_weight")
    cost_acceleration = model.get_cost("a")
    cost += acceleration_resistance_weight * cost_acceleration
    rotation_resistance_weight = params.get("rotation_resistance_weight")
    # Lower weight = less penalty, more rotation capability
    rotation_value = model.get_cost("w")
    cost += rotation_resistance_weight * rotation_value
'''

known_components["velocity_tracking_cost"] = '''
    # Track a reference velocity. Shortcut name: <velocity_tracking_cost>
    velocity_tracking_weight = params.get("velocity_tracking_weight")
    velocity_reference = params.get("reference_velocity")
    cost_velocity_tracking = ((v - velocity_reference) / 3.0)**2
    cost += velocity_tracking_weight * cost_velocity_tracking
'''

def snake_to_camel(snake_str):
    components = snake_str.split('_')
    # Capitalize the first letter of each component and join them together
    camel_str = ''.join(x.title() for x in components)
    return camel_str

class CostGenerationAssistant(Assistant):

    def __init__(self, client, verbose=False) -> None:
        # Settings of chatGPT
        self.generated_python_path = '../mpc_planner/mpc_planner_modules/scripts/llm_generated.py'
        self.generated_cpp_path = '../mpc_planner/mpc_planner_modules/include/mpc_planner_modules/llm_generated.h'

        self.timing = TimerCollection("Cost Generation")

        system_prompt = ""

        super().__init__(client, verbose, system_prompt=system_prompt)

    def __del__(self):
        self.timing.report()

    def get_instructions(self) -> str:
        instructions = '''
Your task is to specify the cost function of an MPC for a differential drive mobile robot moving in a 2D space. Your output must contain a python function that implements the cost requested by the user. Do it as fine grained as possible and do not include unrequested aspects. 

### Components
First, state in words the components that should appear in the cost function. Use words like minimize or maximize.

### Function structure
Second, provide the code. You must only provide <your_code> in the code snippet below. Do not output any of the other code given below. Indent your code with \"    \". You cannot import python functions. You cannot use numpy.
        
```python
def get_value(model, params, settings, stage_idx):

    cost = 0.

    # Retrieve states
    x = model.get("x")
    y = model.get("y")
    psi = model.get("psi")
    v = model.get("v")
    a = model.get("a")
    w = model.get("w")
    s = model.get("spline")

    <your_code_here>
    
    return cost
```

### Available variables
States and inputs of the robot can be retrieved via `model.get("<state_name>")`. The robot has the following states: `x` (x position), `y` (y position), `psi` (robot orientation), `v` (linear velocity), `spline` (distance along a reference path). The robot has the following inputs: `a` (acceleration), `w` (angular velocity). To use a state, first retrieve it at the start of the function.
Also, there are up to 4 obstacles (dynamic objects or humans). Their positions can be retrieved to a list doing:
"obstacles = []
for i in range(4)
    obstacles[i] = [params.get(f"ellipsoid_obst_{i}_x"), params.get(f"ellipsoid_obst_{i}_y")]"
You can't access any more variables.
    
Parameters can be retrieved via `params.get("<parameter_name>")`. All weights must be specified with params.get("<weight_name>"). You must use a different weight for each of the states or inputs involved.
You must use floating point parameters to parametrize any input value you can, retrieved via `params.get("<parameter_name>").

The cost function as a whole should return a scalar value.

You have access to the following functions:
    - model.get_cost("<variable_name>"): Penalizes the variable with a quadratic weight and normalization. Note that "<variable_name>" must be a string part of the state or input.
    - model.get_tracking_cost("<variable_name>", <tracking_value>)): Penalizes the difference between the variable and the tracking value with a quadratic weight and normalization. Note that the tracking value should be a value, e.g., retrieved with `params.get("reference_velocity")` and the <variable_name> a string part of the state or input.
    - path = Spline2D(params, settings["contouring"]["num_segments"], s)
    You should use these functions anytime you can. The values returned by get_cost and get_tracking_cost functions must be multiplied by weights to tune it as fine grained as possible.
    - cd.sqrt(value): takes the square root of the argument.
    

### Known cost cost components
The following components are cost components that you already know. To add these to your cost function specify ONLY their shortcut name. Do not add the related code. These components are:
'''

# You can use a quadratic cost:
#     - To minimize d: d**2
#     - To maximize d: 1/(d**2 + 1e-3)
#     - To apply a cost only if a condition is fulfilled: if_else(<condition>, <cost>, 0)
        for _, c in known_components.items():
            instructions += "```python"
            instructions += c
            instructions += "```\n\n"

        instructions += '''### Example
You should decide what cost components are required based on the user input. Tracking path and goal costs are ONLY to follow a specified path or goal, so if you are requiered to fulfill other task, you have to design a new cost. 
If you track a path, you must use contour and lag costs and not the goal cost. You can't use goal and contour costs at the same time. You must always put <input_cost> and <velocity_tracking_cost>. Write brief comments explaining all cost terms and parameters.

The following provides an example of your code. 
```python

    # Contouring and lag costs for tracking a path
    <contour_cost>

    # Costs that you should always add!
    # Penalize the robot input commands
    <input_cost>

    # Track a velocity reference
    <velocity_tracking_cost>
```
Remember that you are using casadi variables, so you must use if_else casadi function anytime you can. It is the only casadi function you can use (you must not use min or max, for example). Also make sure that your cost function cannot divide by zero by adding a small constant, otherwise the optimization will fail.

### Parameter explanation
At the end, write the weight and floating point parameter names in lower_case and an initial value that you think is reasonable in the following format (ONLY the parameters you use):
\"### Params: [<param_1>: <initial_value>, ..., <param_n>: <initial_value>]\"        
''' 
        return instructions

    def query_cost(self, cost_prompt):
        print_value("Code Generation Assistant", "Generating new cost function... ", end = "", flush=True)
        self.timing.start()
        self.query_base(cost_prompt)
        self.timing.stop()
        print(f" (took {self.timing.get_last():.1f}s) ", end="")
        print_success(" -> Done")
        # answer = response.choices[0].message.content

    def read_response(self, response):
        # print(response)
        self.read_python_code(response)

        if compile_planner:
            self.read_cpp_code()

        # In principle we can check if the solver is any good later
        self.success = True
        self.status = 0
        return True

        max_trials = 2
        self.status = -1
        for _ in range(max_trials):
            success = CostGenerationAssistant.generate_solver()
            if not success:
                print_warning("Failed to generate a solver")
                self.status = 1
                continue
            else:
                print_success("-> Done")
                print_path("Generated python code", self.generated_python_path, tab=True)

                if compile_planner:
                    print_path("Generated cpp code", self.generated_cpp_path, tab=True)

            if compile_planner:
                success = CostGenerationAssistant.compile_planner()
                if not success:
                    print_warning("Failed to compile the generated solver")
                    self.status = 2
                    continue
                else:
                    print_success("-> Done!")
                    self.status = 0
                    self.success = True
                    return True
            else:
                self.success = True
                return True

        self.success = False
        return False
    
    def print_status(self):
        if self.status == 0:
            print_success("New solver generated and compiled")
        elif self.status == 1:
            print_warning("Failed to generate a solver")
        elif self.status == 2:
            print_warning("Failed to compile the generated solver")

    @staticmethod
    def generate_solver():
        print("Code Generation Assistant: Generating solver...", end="", flush=True)
    
        cmd = ""
        if use_poetry:
            cmd = "poetry run "
        cmd += "python ../mpc_planner/mpc_planner_jackalsimulator/scripts/generate_jackalsimulator_solver.py &>/dev/null"
        result = subprocess.run(cmd, shell=True, executable="/bin/bash")
        return result.returncode == 0

    @staticmethod
    def compile_planner():
        # return True
        print("Code Generation Assistant: Compiling planner...", end="", flush=True)
        cmd = "source /workspace/devel/setup.bash && catkin build mpc_planner_jackalsimulator &>/dev/null"
        result = subprocess.run(cmd, shell=True, executable="/bin/bash")
        return result.returncode == 0

    def read_python_code(self, response):
        # print(response)
        # Write the content to the file
        with open(self.generated_python_path, 'w') as file:
            file.write("from util.math import huber_loss\n\n")
            file.write("import casadi as cd\n\n")
            file.write("from spline import Spline, Spline2D\n")
            file.write("from casadi import if_else\n\n")
            file.write('def get_value(model, params, settings, stage_idx):\n')

            file.write("    cost = 0.\n")

            file.write("    # Retrieve states\n")
            file.write("    x = model.get(\"x\")\n")
            file.write("    y = model.get(\"y\")\n")
            file.write("    psi = model.get(\"psi\")\n")
            file.write("    v = model.get(\"v\")\n")
            file.write("    a = model.get(\"a\")\n")
            file.write("    w = model.get(\"w\")\n")
            file.write("    s = model.get(\"spline\")\n")

            is_code = False
            for line in response.splitlines():
                if "```python" in line:
                    is_code = True
                    continue

                if "```" in line and is_code:
                    is_code = False
                    file.write("    return cost")
                    file.write("\n\n")
                    continue
                
                if is_code:
                    if "<" in line and ">" in line:
                        shortcut_name = line.split("<")[1].split(">")[0]
                        if shortcut_name in known_components.keys():
                            file.write(known_components[shortcut_name])
                            continue

                    file.write(line + "\n")

                if "### Params:" in line:
                    file.write("def define_parameters(params):\n")
                    self.weights = [(w.split(": ")[0], float(w.split(": ")[1])) for w in line.split("[")[1][:-1].split(", ")]
                    for weight in self.weights:
                        if weight[0] not in ["goal_x", "goal_y", "reference_velocity"] and weight[1] != 0.:
                            file.write(f"\tparams.add(\"{weight[0]}\", add_to_rqt_reconfigure=True)\n")
                    file.write("\treturn params")

                    file.write("\n\n")
                    file.write("def get_weights():\n")
                    file.write("\tweights = dict()\n")
                    for weight in self.weights:
                        if weight[0] not in ["goal_x", "goal_y", "reference_velocity"] and weight[1] != 0.:
                            file.write(f"\tweights[\"{weight[0]}\"] = {weight[1]}\n")
                    file.write("\treturn weights\n")
                    

    def read_cpp_code(self):
        print("Generated cpp: ", self.generated_cpp_path)
        with open(self.generated_cpp_path, 'w') as file:
            file.write("#pragma once\n")
            file.write("namespace MPCPlanner{\n")
            file.write("inline void setGeneratedParameters(const RealTimeData &data, std::shared_ptr<Solver> solver, const ModuleData &module_data, int k){")
            for weight in self.weights:
                print(weight)
                if weight[0] not in ["goal_x", "goal_y", "reference_velocity"] or weight[1] == 0.:
                    file.write("if (!CONFIG[\"weights\"][\"" + weight[0] + "\"])\n\tCONFIG[\"weights\"][\"" + weight[0] +"\"] = " + str(weight[1]) + ";\n")
            for weight in self.weights:  
                if weight[0] not in ["goal_x", "goal_y", "reference_velocity"] or weight[1] == 0.:   
                    file.write("setSolverParameter" + snake_to_camel(weight[0]) + "(k, solver->_params, CONFIG[\"weights\"][\"" + str(weight[0]) + "\"].as<double>());\n")
            file.write("}} // namespace MPCPlanner")
