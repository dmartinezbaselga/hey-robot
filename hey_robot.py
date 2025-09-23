import pickle
from openai import OpenAI

from assistant_system import AssistantSystem

from util.logging import print_value
from util.timer import Timer

continuous_mode = False
pickle_path = "intermediate"

# Save prompts to txt
save_prompts = True
file_path = "prompts"

verbose = True

# Settings of chatGPT
temperature = 0.2 # Higher is more random

def pickle_settings(settings, path):
  pickle_file = open(f'{path}.pkl', 'wb')
  pickle.dump(settings, pickle_file)
  
def load_pickled_settings(path):
  pickle_file = open(f'{path}.pkl', 'rb')
  return pickle.load(pickle_file)

# Write your API key here
client = OpenAI(api_key='') # Opens the client

country = "the Netherlands"
# domain = "busy narrow corridor in a hospital"
domain = "a large open square in a city"
env_description = f"{domain} in {country}."


timer = Timer()
# initial_task = "Follow the reference path"
initial_task = "Go to the goal"
# initial_task = "Keep a minimum distance of 1.5m from pedestrians and go to the goal"

assistants = AssistantSystem(client, verbose=verbose)
assistants.query_environment(env_description, "Go to the goal", reload_solver_func=lambda: print("reload solver"))


if continuous_mode:
  finish = False
  while True:
      try:
        user_input = input("User Input: ") # Listen to user input
      except KeyboardInterrupt:
          print("Interrupted")
          exit(0)
      # print_value("User Input", user_input)
      if user_input == "exit":
        exit(0)
      assistants.query_user_input(user_input, reload_solver_func=lambda: print("reload solver"))
else:
  assistants.query_user_input("Drive faster!", reload_solver_func=lambda: print("reload solver"))
  assistants.query_user_input("Follow the path", reload_solver_func=lambda: print("reload solver"))
  assistants.query_user_input("Stick less to the path", reload_solver_func=lambda: print("reload solver"))