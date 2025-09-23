import pickle 
import copy

from assistant_base import Assistant

from navigation_settings import CostComponentSetting, RelativeSetting
from util.logging import print_value, print_header, print_path, print_divider, print_success
from util.reading import read_list_tag, read_tag
from util.timer import TimerCollection

class WeightRetrievalAssistant(Assistant):

    """
    Determine the weight values directly from the cost and the user input
    """

    def __init__(self, client, verbose=False) -> None:
        super().__init__(client, verbose, system_prompt="")
        self.enabled_weights = None
        self.disabled_weights = None
        self.timing = TimerCollection("Tuning")
        self.file_name = "llm_generated.py"

    def __del__(self):
        self.timing.report()
    # def initialize_from_cost(self):
    #     code = ""
    #     with open("../mpc_planner/mpc_planner_modules/scripts/llm_generated.py", 'r') as file:
    #         writing = False
    #         for line in file:
    #             if "get_value" in line:
    #                 writing = True
    #             if writing:
    #                 code += line
    #                 if "return" in line:
    #                     break
        
    #     if "params.get(" in line:
    #         param

    def get_instructions(self) -> str:
        instruction = "You will be given python code from a file that implements a cost function for an MPC. "
        instruction += "The MPC is used to plan a trajectory for a mobile robot in a 2D space. "
        
        # Robot information
        instruction += "The robot can achieve speeds between 0-3 m/s.\n"
        # instruction += "The robot can achieve speeds between 0-0.65 m/s.\n"
        
        instruction += "The code contains several parameters that are represented as `params.get(\"<param_name>\")`. "
        instruction += "These parameters represent weights for tuning or floating point input parameters. Some parameters specify real-world data and should be ignored. These are:\n"

        instruction += '''`goal_x`, `goal_y`, `ellipsoid_obst_<nr>_<anything>`.\n'''

        instruction += "You will additionally be given a user task. Your task is to specify new values of these parameters to achieve the user's task. If the user gives information about the environment, makes sure your parameters are suitable for that environment. Consider for example if humans are generally present in this environment and how the robot parameters should be adjusted. Please do so in 3 steps.\n"

        # instruction += "1. For weights, determine if they should be enabled or disabled based on the user input and their current value. Only disable a weight if you are sure that it is not needed and if it is not sufficient to reduce the weight. Please do so by listing enabled weights followed by all weights as: \"1.\nEnabled: [<enabled_weight_1>, ..., <enabled_weight_n>]\nAll: [<weight_1>, ..., <weight_n>]\".\n\n"
        # instruction += "1. For weights, determine if they should be enabled or disabled based on the user input and their current value. It is almost always enough to keep the weight enabled and to reduce its weight rather than disabling them. Therefore, only disable components if the user input requires that the component has no influence. If you want to influence a behavior, you will need to keep the weight enabled. You should almost never disable weights that penalize input commands. Respond by listing all weights under \"A: [<w1>, ..., <wn>]\" and disabled weights as: \"1.\nD: [<disabled_weight_1>, ..., <disabled_weight_n>]\".\n\n"
        # instruction += "1. For all parameters, specify the parameters that need to be changed as a list \"1.\nP: [<p1>, ..., <pn>]\nD: []\"."
        instruction += "1. First, write the user intention with different words from the ones in the query. Then determine the parameters related to the request. Format your response as \"M: <completion>\"."
        instruction += "2. Write the new value of all the weight parameters (both the unchanged and changed ones) on a new line as \"<param_name>: <value>\". The value must be an integer between 0 and 10. Only set a weight to 0 if you want its component to have no effect. Start your answer with \"2.\n\".\n\n" #Try to prioritize tasks if necessary. 
        instruction += "3. For all floating point parameters specify their new value on a new line as \"<param_name>: <value>\". If there are no floating point parameters, do not put anything. Start your answer with \"3.\n\n"

        # instruction += "At the end, complete the following brief sentence: \"The main change is to ...\". Format your response as \"M: <completion>\". Do not provide any additional output"
        # instruction += "Explain how your weights are affected by the environment in one final sentence."

        return instruction
    
    def query(self, query):
        print_value("Weight Assistant", "Retrieving and tuning weights", end="")
        func_name = "get_value"

        prompt = ""
        prompt += "The code is described below:\n"
        prompt += "```python\n"
        
        if self.verbose:
            print(f"WeightExplanationAssistant: reading function {func_name} of {self.file_name}")
        with open("../mpc_planner/mpc_planner_modules/scripts/" + self.file_name, 'r') as file:
            writing = False
            for line in file:
                if func_name in line:
                    writing = True
                if writing:
                    prompt += line
                    if "return" in line:
                        break

        prompt += "```\n\n"
        if self.enabled_weights is None:
            prompt += "All weights are currently enabled. They do not yet have an intitial value so you need to decide their initial value to fit the user's task and environment.\n"
        else:
            prompt += "Enabled weights are currently:\nEnabled: " + str(self.enabled_weights) + ".\n\n"
            prompt += "The current values of the weights are:\n"
            for weight, value in self.weights.items():
                prompt += f"{weight}: {int(value)}"

            prompt += "The current values of the double valued parameters are:\n"
            for double, value in self.doubles.items():
                prompt += f"{double}: {value:.1f}"
            prompt += "\n"

        prompt += f"{query}"
        self.timing.start()
        self.query_base(prompt)
        self.timing.stop()
        print(f" (took {self.timing.get_last():.1f}s) ", end="")
        print_success("-> Done")

    def read_response(self, response):
        # print(response)
        # self.read_parameters(response)
        weight_mode = False
        double_mode = False
        self.motivation = ""
        self.disabled_weights = []

        self.weights = dict()
        self.doubles = dict()
        for line in response.splitlines():
            # if "Enabled:" in line:
                # self.enabled_weights = read_list_tag(line, "Enabled: ")
            # if "All:" in line:
                # self.all_weights = read_list_tag(line, "All: ")
            if "D:" in line:
                self.disabled_weights = read_list_tag(line, "D: ")

            if "M: " in line:
                self.motivation = read_tag(line, "M: ")
                if "The main change is to" in self.motivation:
                    self.motivation = self.motivation.split("The main change is to ")[1].capitalize()
                continue

            if weight_mode and ":" in line:
                weight_name = line.split(":")[0].strip()
                weight_value = int(line.split(":")[1].strip())
                self.weights[weight_name] = weight_value

            if double_mode and ":" in line:
                double_name = line.split(":")[0].strip()
                double_value = float(line.split(":")[1].strip())
                self.doubles[double_name] = double_value

            if line.strip() == "2.":
                weight_mode = True
            
            if line.strip() == "3.":
                double_mode = True
                weight_mode = False

        self.enabled_weights = [v for v in self.weights.keys() if v not in self.disabled_weights]
        return True

    def save_cost_components(self):
        pickle_file = open(f'{self.output_file}', 'wb')
        pickle.dump(self.cost_component_settings, pickle_file)
    
    def save_tasks_components(self):
        pickle_file = open(f'{self.output_tasks_file}', 'wb')
        pickle.dump(self.available_tasks, pickle_file)

    def print_status(self):
        print_divider()
        if self.motivation != "":
            print_value("Main Change", self.motivation)

        sorted_weights = sorted(self.weights.items(), key=lambda x:x[1], reverse=True)

        for weight, value in sorted_weights:
            print_value(weight, "", end=" ")  
            for i in range(35 - len(weight)):
                print(" ", end="")
            for i in range(value):
                print("===", end="")
            for i in range(10 - value):
                print("   ", end="")
            print(f" ({value}/10)")
        # print("\b\b  ", flush=True)

        for double, value in self.doubles.items():
            print_value(double, value, end=", ")  
        print("\b\b  ", flush=True)
        print_divider()

    def get_weights(self):
        # Normalize the importance of the factors
        total = sum([v for v in self.weights.values()])
        nr = float(len([v for v in self.weights.keys() if v in self.enabled_weights]))

        if nr != 0:
            mean = total/nr
            if total == 0.:
                mean = 1.
            weights = [v / mean for v in list(self.weights.values())]
        else:
            weights = list(self.weights.values())
        names = list(self.weights.keys())

        # Add disabled weights
        for w in self.disabled_weights:
            if w not in self.weights.keys() and w not in self.doubles.keys():
                weights.append(0.)
                names.append(w)

        weights += list(self.doubles.values())
        names += list(self.doubles.keys())
        
        return weights, names