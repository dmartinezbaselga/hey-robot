from random import shuffle
import pickle

from util.logging import print_warning, print_header, print_success, print_value, print_path

load_weights_from_file = True
# weight_file = "weights_explanations.txt"
weight_file = "weights_explanations.pkl"
tasks_file = "tasks_explanations.pkl"

enable_motivation_prompts = False

class CostComponentSetting():

    def __init__(self, name, purpose) -> None:
        self.name = name
        self.purpose = purpose
        self.enabled = False
        self.weights = []

    def to_prompt(self) -> str:
        return f"({self.name}) {self.purpose.strip().split('.')[0]}?\n" # Must the robot ...

    def is_line_an_answer(line) -> bool:
        return "Cost" in line
    
    def from_response_line(self, response_line):
        self.enabled = "enable" in response_line.lower()
        if not self.enabled:
            for weight in self.weights:
                weight.importance = 0.

    def add_weight(self, weight):
        self.weights.append(weight)
    
    def __str__(self) -> str:
        return f"{self.name}: " + ("Enabled" if self.enabled else "Disabled")

class BooleanSetting():
    """
    A boolean setting is a setting that can be either True or False.
    """

    def __init__(self, description, prompt) -> None:
        self.description = description
        self.value = None
        self.prompt = prompt

    @staticmethod
    def format_prompt() -> str:
        prompt = ""
        prompt += "Please answer the following questions with \"<nr>. Answer: <Yes/No> "
        if enable_motivation_prompts:
            prompt += "- Motivation: <motivation>\".\n"
        else:
            prompt += "\". Do not provide any motivation. Do not repeat the question.\n"

        return prompt
    
    @staticmethod
    def is_line_an_answer(line) -> bool:
        return "Answer: " in line and ". " in line and (not "Cost" in line) and not "<nr>" in line

    def to_prompt(self) -> str:
        return self.prompt
    
    def from_response_line(self, response_line):
        answer = response_line.split("Answer:")[-1].split(" - ")[0]
        self.value = "yes" in answer.lower()

    def __str__(self) -> str:
        if self.value:
            return f"{self.description.lower().capitalize()} is allowed"
        else:
            return f"{self.description.lower().capitalize()} is NOT allowed"



class DoubleSetting():
    """
    A double setting is a setting that ranges between min and max
    """

    def __init__(self, description, prompt, min, max) -> None:
        self.description = description
        self.value = None
        self.prompt = prompt
        self.min = min
        self.max = max

    @staticmethod
    def format_prompt() -> str:
        prompt = ""
        prompt += "Please answer the following questions with a numerical value up to one digit "
        prompt += "in the indicated range \"<nr>. Value: <value (e.g., 1.3)> "
        if enable_motivation_prompts:
            prompt += "- Motivation: <motivation>\".\n"
        else:
            prompt += "\". Do not provide any motivation. Do not repeat the question.\n"
        return prompt
    
    @staticmethod
    def is_line_an_answer(line) -> bool:
        return "Value: " in line

    def to_prompt(self) -> str:
        return self.prompt
    
    def from_response_line(self, response_line):
        self.value = float(response_line.split("Value:")[-1].split(" - ")[0])

    def __str__(self) -> str:
        return f"{self.description}: {self.value}."

class RelativeSetting():
    
    """
    A relative setting is a setting that is ranked in importance.
    """

    def __init__(self, name, description, weight_name, min=0., max=1.) -> None:
        self.name = name
        self.description = description
        self.weight_name = weight_name
        self.importance = 0
        self.order = None

    @staticmethod
    def format_prompt(relative_settings) -> str:
        prompt = ""

        example_setting_list = [x for x in range(1, len(relative_settings) + 1)]
        shuffle(example_setting_list)

        prompt += "The following lists a set of aspects that are important for the robot's navigation behavior. "
        prompt += "Please order the aspect in a list from most to least important (formatted as "
        prompt += "\"Order: " + str(example_setting_list) + "\"). If a term belongs to a cost that is deactivated, you can skip it. "
        prompt += "Below this order, please provide for each aspect an absolute importance between 0 and 10"
        prompt += ", e.g., Aspect: <aspect>. Importance: <importance> "
        if enable_motivation_prompts:
            prompt += "- Motivation: <motivation>\".\n"
        else:
            prompt += "\". Do not provide any motivation.\n"
        prompt += "\n"
        return prompt

    @staticmethod
    def is_line_an_answer(line) -> bool:
        return "Aspect" in line and "Importance" in line

    def from_response_line(self, response_line):
        self.importance = int(response_line.split("Importance: ")[1].split(" - ")[0])

    def to_prompt(self) -> str:
        return f"{self.name}. Description: {self.description}"
        # return f"{self.name} Order: {self.order}. Importance: {self.importance}."

    def __str__(self) -> str:
        return f"{self.name}: {self.importance}."

class NavigationSettings:

    """
    The navigation settings class contains the settings of the robot navigation system.
    """
 
    def __init__(self, cost_component_settings=None, boolean_settings=None, relative_settings=None, double_settings=None) -> None:
        # if cost_component_settings is not None and boolean_settings is not None and relative_settings is not None and double_settings is not None:
        #     self.cost_component_settings = cost_component_settings
        #     self.boolean_settings = boolean_settings
        #     self.relative_settings = relative_settings
        #     self.double_settings = double_settings
        # else:
        #     self.cost_component_settings = []
        #     self.cost_component_settings.append(CostComponentSetting("Contouring", "follow the reference path"))
        #     self.cost_component_settings.append(CostComponentSetting("Goal", "go to a specific 2-D goal"))

            

            # self.relative_settings = []

            # # Retrieve the weights from the MPC itself!
        if load_weights_from_file:
            self.load_weights_from_file()
            for c in self.cost_component_settings:
                c.enabled = True

            # else:
            #     self.relative_settings.append(RelativeSetting(
            #         "Velocity Weight",
            #         "The velocity weight determines how important it is to track the given reference velocity.",
            #         "velocity"
            #     ))

            #     self.relative_settings.append(RelativeSetting(
            #         "Acceleration Weight",
            #         "The acceleration weight penalizes the robot's acceleration. Increasing the weight leads to lower accelerations that lead to smoother, but slower motion.",
            #         "acceleration"
            #     ))

            #     self.relative_settings.append(RelativeSetting(
            #         "Rotational Velocity Weight",
            #         "The rotational velocity weight penalizes the robot's rotational velocity. Increasing the weight lead to smoother, but slower rotation.",
            #         "rotational_velocity"
            #     ))

            #     self.relative_settings.append(RelativeSetting(
            #         "Contouring Weight",
            #         "The contouring weight determines how accurately the robot should follow the reference path.",
            #         "contour"
            #     ))

            # Settings not yet from file
            self.double_settings = []
            self.double_settings.append(DoubleSetting(
                "reference_velocity", 
                "How fast should the robot drive in m/s?",
                0.0, 2.0))
            self.boolean_settings = []
            self.boolean_settings.append(BooleanSetting(\
                "Left Overtaking", 
                "Should the robot overtake humans walking in the same direction as the robot on the left in this environment?"))
            self.boolean_settings.append(BooleanSetting(\
                "Right Overtaking", 
                "Should the robot overtake humans walking in the same direction as the robot on the right in this environment?"))
            self.available_tasks.append("- Decide if overtaking humans in the same direction as the robot is forbidden or not.")
            self.last_change = ""

    def load_achievable_tasks(self):
        pickle_file = open(tasks_file, 'rb')
        self.available_tasks = pickle.load(pickle_file)
    
    def load_weights_from_file(self):
        self.available_tasks = []
        # self.load_achievable_tasks()
        self.relative_settings = []
        self.cost_component_settings = []

        # pickle_file = open(weight_file, 'rb')
        # self.cost_component_settings = pickle.load(pickle_file)

        # for component in self.cost_component_settings:
        #     for weight in component.weights:
        #         self.relative_settings.append(weight)
    # def to_prompt(self) -> str:
    #     prompt = ""
    #     prompt += "Settings:\n"

    #     prompt += "\tRules:\n"
    #     for s in self.boolean_settings:
    #         prompt += "\t - " + str(s) + "\n"
        
    #     prompt += "\n\tNavigation Objectives:\n"
    #     for s in self.relative_settings:
    #         prompt += "\t - " + s.to_prompt() + "\n"

    #     prompt += "\n\tNumerical Settings:\n"
    #     for s in self.double_settings:
    #         prompt += "\t - " + s.to_prompt() + "\n"

    #     return prompt

    def print(self) -> None:
        print_header("Settings")
        print(self)

    def __str__(self) -> str:
        result = ""
        result += "Boolean Settings: "
        for s in self.boolean_settings:
            result += str(s) + " | "

        result += "\nRelative Settings: "
        ordered_settings = sorted(self.relative_settings, key=lambda x: x.importance, reverse=True)
        for s in ordered_settings:
           result += str(s) + " | "

        result += "\nNumerical Settings: "
        for s in self.double_settings:
           result += str(s) + " | "

        return result
    
    def to_weights(self):
        settings = []
        for component in self.cost_component_settings:
            for weight in component.weights:
                if not component.enabled and weight != 0.:
                    weight.importance = 0.
                settings.append(weight)

        # Normalize the importance of the factors
        total = sum([s.importance for s in settings])
        nr = float(len([s for s in settings if s != 0]))
        if nr == 0:
            weights = [s.importance for s in settings]
        else:
            mean = total/nr
            if total == 0.:
                mean = 1.
            weights = [s.importance/mean for s in settings]

        names = [s.weight_name for s in settings]

        weights.append(self.double_settings[0].value)
        names.append(self.double_settings[0].description.lower())
        return weights, names
