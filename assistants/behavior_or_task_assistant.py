from assistant_base import Assistant

from util.logging import print_value, print_header, print_path, print_success, print_warning
from util.reading import read_boolean_tag, read_tag, read_list_tag, has_tag

class BehaviorOrTaskAssistant(Assistant):

    """
    Determines if a user input constitutes a behavior change or a task assignment
    """

    # NOTE: The problem with deciding between tasks and behaviors is that it depends on the code if something should change behavior or the task

    def __init__(self, client, verbose=False) -> None:
        super().__init__(client, verbose, system_prompt="")

    def get_instructions(self) -> str:

        instruction = "You will be given a user input. Your task is to determine if the user is requesting a change in behavior (respond with \"B\"), is assigning a task (respond with \"T\") or perceiving a new environment (respond with \"E\"). Do not motivate your choice. "
        instruction += "Tasks ask the robot to do something (e.g., go to ...) or place restrictions on the robot (e.g., stay away from ...). Behaviors indicate tweaking changes in the way the robot is already moving (e.g., drive more ...). Perceiving a new environment means sensing the sourroundings with a camera to adapt to it (e.g., you are in a new scenario)."
        

        instruction += "Motivate your decision on a new line in one sentence."

        return instruction

    def get_internal_examples(self) -> str:
        query = [
            "Follow the path",
            "Go to the kitchen",
            "Stand still",
            "You are in a hospital",
            "Keep a distance of 1.0m from pedestrians"
        ]

        responses = [
            "T",
            "T",
            "B",
            "B",
            "T"
        ]

        for i in range(len(query)):
            self.conversation.append({"role": "user", "content": f"User input: {query[i]}"})
            self.conversation.append({"role": "assistant", "content": responses[i]})

    def query(self, task):
        self.task = task
        prompt = f"User input: {task}"
        self.query_base(prompt)

    def read_response(self, response):
        # print(response)
        for line in response.splitlines():
            if line.strip() == "B":
                self.is_behavior = True
                self.is_task = False
                self.is_environment = False
            elif line.strip() == "T":
                self.is_behavior = False
                self.is_task = True
                self.is_environment = False
            elif line.strip() == "E":   
                self.is_behavior = False
                self.is_task = False
                self.is_environment = True       

        return True

    def print_status(self):
        if self.is_task:
            print_value("Task", self.task.strip(), end=" ")
        elif self.is_behavior:
            print_value("Behavior", self.task.strip())
        elif self.is_environment:
            print_value("Environment", self.task.strip())