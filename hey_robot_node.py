import rospy
import os, sys

import pickle
from openai import OpenAI

from mpc_planner_msgs.msg import WeightArray, Weight
from std_msgs.msg import Empty

from assistant_system import AssistantSystem
from speech_to_text import SpeechToText

from util.logging import print_value


country = "the Netherlands"
domain = "a large open square in a city"
env_description = f"{domain} in {country}."

# initial_task = "Follow the path while following the reference velocity. Drive smoothly. Your maximum velocity is 2.5 m/s."
# initial_task = "Follow the closest obstacle."
# initial_task = "Go to the goal."
initial_task = "Follow the path."
use_speech_to_text = False
enable_input = True
use_environment_from_camera = True

verbose = False

# Settings of chatGPT
# temperature = 0.05 # Higher is more random

class HeyRobotNode:
    def __init__(self, initial_prompt=initial_task):
        self._initial_prompt = initial_prompt
        rospy.init_node('hey_robot_node', anonymous=True)
        # Initialize the OpenAI client with your API key
        self.client = OpenAI(api_key='') # Opens the client

        if use_speech_to_text:
          self.stt = SpeechToText()

        self._reload_solver_pub = rospy.Publisher('/mpc/reload_solver', Empty, queue_size=1)

        self.assistants = AssistantSystem(self.client, verbose=verbose, use_environment_from_camera=use_environment_from_camera)

        # Define a publisher
        self.pub = rospy.Publisher('/hey_robot/weights', WeightArray, queue_size=10)

        self.rate = rospy.Rate(1)

        self.env_description = env_description

        self.initialize_environment()
    
    def reload_solver(self):
      #  print("Reload solver")
       empty_msg = Empty()
       self._reload_solver_pub.publish(empty_msg)

    def initialize_environment(self):
      print("Initializing settings based on the environment and task")
      self.assistants.query(f"The robot's task is: {self._initial_prompt}", self.reload_solver)

    def publish_weights(self) -> None:
      weights, names = self.assistants.get_weights()
     
      if verbose:
        for idx, weight in enumerate(weights):
          print_value(f"{names[idx]} weight", weight)

      weight_msg = WeightArray()

      for idx, weight in enumerate(weights):
        new_weight = Weight()

        new_weight.name = names[idx]
        new_weight.value = weight
        if new_weight.value is None:
           print("Warning: Setting ", new_weight.name, "value to 1 because the return value was None")
           new_weight.value = 1.0
        weight_msg.weights.append(new_weight)

      self.pub.publish(weight_msg)

    def run(self):
        self.rate.sleep()

        while not rospy.is_shutdown():

            # First publish the weights
            self.publish_weights()

            if use_speech_to_text:
              success = False
              while success == False:
                user_input = input("Press Enter to start recording")
                self.stt.button_press()
                user_input = input("Press Enter to stop recording")
                success, user_input = self.stt.button_release()
            else:
              if enable_input:
                try:
                  user_input = input("User Input: ") # Listen to user input
                except KeyboardInterrupt:
                  print("Interrupted")
                  exit(0)

                # print_value("User Input", user_input)
                if user_input == "exit":
                  exit(0)

                if use_speech_to_text:
                  user_input += " (transcribed from speech)"
                self.assistants.query_user_input(user_input, self.reload_solver)
                # self.assistants.query_environment(self.env_description, user_input, self.reload_solver)

            self.rate.sleep()

if __name__ == '__main__':
    
    try:
        if len(sys.argv) > 1:
          node = HeyRobotNode(sys.argv[1]) # Supply the initial prompt
        else:
           node = HeyRobotNode()
        node.run()
    except rospy.ROSInterruptException:
        pass