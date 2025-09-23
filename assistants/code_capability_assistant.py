from assistant_base import Assistant

from util.logging import print_value, print_header, print_path, print_success, print_warning
from util.reading import read_boolean_tag, read_tag, read_list_tag, has_tag

from util.timer import TimerCollection

class CodeCapabilityAssistant(Assistant):

    """
    Determines if a user task can be achieved informed by the generated code that implements the cost function
    """

    def __init__(self, client, verbose=False, generated_code_file = "llm_generated.py") -> None:

        self.generated_code_file = generated_code_file
        system_prompt = ""
        self.timing = TimerCollection("Capability")

        super().__init__(client, verbose, system_prompt=system_prompt)

    def get_instructions(self) -> str:

        instruction = '''You are an expert in designing MPC cost functions for mobile robot navigation in 2D environments. 
        You will be given a cost function written in Python that will be minimized by an MPC and you will be given a task or behavior adaptation specified by a user. Your task is to decide if the cost is sufficient to achieve the query or not. 
        ### Query type
        First, the query may be one of two types. If the user asks the robot to adapt and perceive the environment WITHOUT any other information that helps the robot, answer with a sentence of motivation and \"Perceive environment\", and don't do the next tasks. In any other case, skip this and go to the next task. 
        ### Components
        '''

        # instruction+= "Second, state in words the components that MUST appear in the cost function. Use words like minimize or maximize. Then, do the same for the components that currently are in the cost function.\n"
        instruction += "Second, state in words the components that MUST appear in the cost function. Use words like minimize or maximize.\n"
        instruction += '''
        ### Decision
        Then, you must make the decision. Ignore prioritization of the cost function. Consider the values of the parameters, specified in the code with`params.get(\"<param_name\">)`. If changing the parameters can achieve the task (e.g., reducing or increasing the reference velocity or reducing/increasing a weight), then respond with \"Update the parameters\". If a new cost must be generated, respond with \"New cost must be generated\".
        Please consider that generating a new cost function will take time and is not desirable.
        It is very important to understand the different parts of user query and check that the cost can fulfill all of them.'''

        instruction += "The goal position and path are unrelated. The robot can't achieve tasks like reaching the goal or path tracking if the cost is not in the function.\n"

        # instruction += "Motivate your decision on a new line in one brief sentence formatted as \"M: <motivation>\"."
        # instruction += "Motivate your decision saying the parameters to use and all the tasks and behaviors sepcified by the user formatted as \"M: <motivation>\"."

        return instruction
    
    def query(self, task):
        self.task = task
        prompt = ""
        file_name = self.generated_code_file
        func_name = "get_value"

        if self.verbose:
            print_value("CodeCapabilityAssistant", f": Loading generated code from {file_name}")
            
        with open("../mpc_planner/mpc_planner_modules/scripts/" + file_name, 'r') as file:
            writing = False
            for line in file:
                if func_name in line:
                    writing = True
                if writing:
                    prompt += line
                    if "return" in line:
                        break

        prompt += f"\nUser task: {task}"
        self.timing.start()
        self.query_base(prompt)
        self.timing.stop()

    def read_response(self, response):
        self.capable = False
        self.environment = False
        self.motivation = ""
        for line in response.splitlines():
            # if line.strip().split(".")[0] == "Cost is sufficient":
            #     self.capable = True
            # elif line.strip().split(".")[0] == "Update the parameters":
            #     self.capable = True
            # elif line.strip().split(".")[0] == "New cost must be generated":
            #     self.capable = False
            if "Perceive environment" in line:
                self.environment = True
            elif "Update the parameters" in line:
                self.capable = True
            elif "New cost must be generated" in line:
                self.capable = False

            if has_tag(line, "M: "):
                self.motivation = read_tag(line, "M: ")

        return True

    def print_status(self):
        # print_value("Task", self.task.strip(), end=" ")
        if self.environment:
            print_warning("-> The robot has to perceive the environment")
        elif self.capable:
            print_success("-> The planner can do this task")
        else:
            print_warning("-> The planner cannot do this task", no_tab=True)
        
        if self.motivation != "":
            print_value("Motivation", self.motivation)