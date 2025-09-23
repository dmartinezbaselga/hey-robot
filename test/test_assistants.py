import pickle
from openai import OpenAI

from ..assistants.code_generation_assistant import CostGenerationAssistant
# from assistants import CapabilityAssistant, EnablerAssistant, WeightAssistant
# from explain_weights_from_code import WeightExplanationAssistant
# from code_capability_assistant import CodeCapabilityAssistant
from ..assistants.behavior_or_task_assistant import BehaviorOrTaskAssistant
from ..assistants.weight_retrieval_assistant import WeightRetrievalAssistant

# from prompts import EnvironmentPrompt, UserInputPrompt, get_instruction_prompt
from navigation_settings import NavigationSettings

from util.logging import print_value, print_success
from util.timer import Timer

generate_solver = True

verbose = False

settings = NavigationSettings() # Initializes the planner's settings
# Initialize the OpenAI client with your API key
client = OpenAI(api_key='') # Opens the client

country = "the Netherlands"
# domain = "busy narrow corridor in a hospital"
domain = "a large open square in a city"
env_description = f"{domain} in {country}."


def generate_solver_with_query(query):

    if generate_solver:
        CostGenerationAssistant(client, settings, verbose=verbose, save_full_conversation=False).query_cost(query)

def test_capability_assistant(yes_queries, no_queries):
    timer = Timer()
    settings.load_weights_from_file()

    capability_assistant = CodeCapabilityAssistant(client, settings, verbose=verbose)
    for query in yes_queries:
        capability_assistant.query(query)
        if not verbose:
            capability_assistant.print_status()
        assert capability_assistant.capable, f"The task \"{query}\" should be possible"

    capability_assistant = CodeCapabilityAssistant(client, settings, verbose=verbose)
    for query in no_queries:
        capability_assistant.query(query)
        if not verbose:
            capability_assistant.print_status()
        assert not capability_assistant.capable, f"The task \"{query}\" should NOT be possible"

    total_time = timer.get_elapsed_time()
    print(f"Avg time per query: {total_time / (len(yes_queries) + len(no_queries)):.1f}s")

def test_behavior_or_task_assistant(behavior_queryies, task_queries):

    for query in behavior_queryies:
        a = BehaviorOrTaskAssistant(client, settings, verbose=verbose)
        a.query(query)
        if not verbose:
            a.print_status()
        assert a.is_behavior, f"The task \"{query}\" should be a behavior"

    for query in task_queries:
        a = BehaviorOrTaskAssistant(client, settings, verbose=verbose)
        a.query(query)
        if not verbose:
            a.print_status()
        assert a.is_task, f"The task \"{query}\" should be a task"

def test_weight_retrieval_assistant(queries):

    queries = [
        # "Ignore the path"
        "Slow down"
    ]
    for query in queries:
        a = WeightRetrievalAssistant(client, settings, verbose=verbose)
        a.query(query)


yes_goal_queries = [
    "Go to the goal",
    "Slow down",
    "Speed up",
]

no_goal_queries = [
    "Follow the path",
    "follow the road",
    "Follow the nearest pedestrian",
    "Stay 1.5m from pedestrians",
    "Go to the goal and keep a distance of 1.0m from pedestrians",
    "Fly to the goal position",
]

yes_path_queries = [
    "Follow the path",
    "Speed up"
]

no_path_queries = [
    "Go to the goal",
    "Go to the living room"
]


behavior_queryies = [
    "Speed up",
    "Stand still",
    "Stop moving",
    "You are in a restaurant",
    "Drive carefully",
    "You are in a hospital, drive carefully",
    "Move faster",
    "Move much faster",
    "Drive more smoothly"
]

task_queries = [
    "Follow the path",
    "Go to the goal",
    "Go to the front door",
    "Follow the hallway",
    "Follow the nearest pedestrian",
    "Keep a distance from pedestrians",
    "Keep a distance of 1.5m from pedestrians"
]

generate_solver_with_query("Go to the goal")
test_capability_assistant(yes_goal_queries, no_goal_queries)
print_success("Tests for goal queries succeeded")


generate_solver_with_query("Follow the path")
test_capability_assistant(yes_path_queries, no_path_queries)
print_success("Tests for path queries succeeded")

test_behavior_or_task_assistant(behavior_queryies, task_queries)
print_success("Tests for behavior or task assistant succeeded")

test_weight_retrieval_assistant(no_goal_queries)