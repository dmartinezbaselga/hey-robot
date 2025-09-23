from util.logging import print_warning, print_success, print_value
from pathlib import Path

from navigation_settings import NavigationSettings

from assistants.code_generation_assistant import CostGenerationAssistant
from assistants.code_capability_assistant import CodeCapabilityAssistant
from assistants.weight_retrieval_assistant import WeightRetrievalAssistant
# from assistants.behavior_or_task_assistant import BehaviorOrTaskAssistant
from camera_to_environment_description import CameraToEnvironmentDescriptionOnDemand

from util.timer import Timer

class AssistantSystem:

    def __init__(self, client, verbose=False, use_environment_from_camera=False) -> None:

        self.client = client
        self.verbose = verbose

        if not Path("../mpc_planner/mpc_planner_modules/scripts/llm_generated.py").exists():
            print_warning("No generated cost function found. Generating an initial cost function")
            CostGenerationAssistant.generate_solver("Go to the goal")

        self.capability_assistant = CodeCapabilityAssistant(client, verbose=verbose)
        self.cost_generation_assistant = CostGenerationAssistant(client, verbose=verbose)
        
        self.weight_retrieval_assistant = WeightRetrievalAssistant(client, verbose=verbose)

        self.first_query = True

        self.use_environment_from_camera = use_environment_from_camera
        if self.use_environment_from_camera:
            self.camera_assistant = CameraToEnvironmentDescriptionOnDemand()

    def query(self, query, reload_solver_func):
        print_value("Query", query)
        query_timer = Timer("Full query", self.verbose) 
                            
        generate_code = True
        if self.first_query:
            self.first_query = False
        else:
            self.capability_assistant.query(query)
            self.capability_assistant.print_status()
            if self.capability_assistant.environment and not self.use_environment_from_camera:
                # self.behavior_assistant.is_environment = False
                # self.behavior_assistant.is_behavior = True
                print_warning("Using the environment from the camera is disabled!")
                generate_code = False
            elif self.capability_assistant.environment:
                # if self.camera_assistant.analyze_environment():
                self.camera_assistant.analyze_environment()
                print_value("New environment detected", self.camera_assistant.environment_description)
                # query = f"The robot is driving in {self.camera_assistant.environment_description}. How should it adapt its behavior?"
                query = "Adapt to an environment with the following features:\n" + self.camera_assistant.environment_description
                generate_code = False
            elif self.capability_assistant.capable: 
                generate_code = False

        if generate_code:
            # self.cost_generation_assistant.clear_conversation()
            self.capability_assistant.clear_conversation()
            self._generate_code(query, reload_solver_func)
            
        self.weight_retrieval_assistant.query(query)
        self.weight_retrieval_assistant.print_status()
    
    def _generate_code(self, query, reload_solver_func):
        cost_generation_timer = Timer("Cost generation", self.verbose)
        self.cost_generation_assistant.query_cost(query)

        if not self.cost_generation_assistant.success:
            print_warning("Failure in cost generation")
            return
        else:
            print_value("Assisant System", "Reloading solver ...", end ="")
            reload_solver_func()
            print_success('-> Done')

        self.weight_retrieval_assistant.enabled_weights = None

    def query_environment(self, env_description, reload_solver_func):
        query = f"The robot is driving in {env_description}. How should it adapt its behavior?"
        self.query(query, reload_solver_func)
    
    def query_user_input(self, user_input, reload_solver_func):
        query = f"User input: {user_input}."
        self.query(query, reload_solver_func)
    
    def get_weights(self):
        return self.weight_retrieval_assistant.get_weights()