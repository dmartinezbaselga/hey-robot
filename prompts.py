def call_openai_api(client, conversation, model="gpt-4o-mini", **kwargs):

        response = client.chat.completions.create(
            model = model,
            messages=conversation,
            **kwargs)

        return response.choices[0].message.content

# class Prompt:

#     prompt = ""
#     response = ""

#     conversation = []

#     def __init__(self) -> None:
#         pass

#     def get_prompt(inputs) -> str:
#         pass

#     def call(self, client, conversation, env_description, settings, 
#              input="", verbose=True, save=False, file_path=None, **kwargs):

#         prompt = self.get_prompt(env_description, settings, input)

#         if verbose:
#             print_header("Prompt")
#             print(prompt)

#         ### === This calls chatGPT to determine the initial behavior in a particular environment === ###
#         response = self.call_openai_api(client, conversation, prompt, **kwargs)
#         response_text = response.choices[0].message.content

#         if verbose:
#             print_header("Response")
#             print(response_text)

#         self.handle_response(response_text, settings)

#         if (save) and (file_path is not None):
#             if input != "":
#                 self.save(file_path, input)
#             else:
#                 self.save(file_path, env_description)

#     def call_openai_api(self, client, conversation, prompt, model="gpt-4o-mini", **kwargs):
#         conversation.append({"role": "user", "content": prompt})

#         response = client.chat.completions.create(
#             # model="gpt-3.5-turbo",
#             model = model, #"gpt-4o-mini",
#             messages=conversation,
#             **kwargs)
        
#         # Append the response to the conversation
#         conversation.append({"role": "assistant", "content": response.choices[0].message.content})

#         return response

#     def handle_response(response : str):
#         pass

#     def save(self, file_path, file_name):
#         file_name = file_name.split(".")[0]
#         with open(f"{file_path}/{file_name}.txt", "w") as text_file:
#             text_file.write("=== Prompt ===\n %s\n\n" % self.prompt)
#             text_file.write("=== Response ===\n %s" % self.response)


# def get_instruction_prompt(settings):
#     prompt = ""

#     prompt += "For all queries you should always provide new settings in the following format:\n\n"

#     prompt += "Please answer the following questions with \"Cost Component <nr>. <question>? Answer: <Enable/Disable> - Motivation: <motivation>\".\n"
#     prompt += "Cost Component 1. Must the robot " + "track a path" + "? (answer with enable/disable)\n"
#     prompt += "Cost Component 2. Must the robot " + "go to a goal" + "? (answer with enable/disable)\n"
#     prompt += "Cost Component 3. Must the robot " + "track the desired path velocity" + "? (answer with enable/disable)\n"
#     prompt += "\n\n"

#     prompt += BooleanSetting.format_prompt()
#     for idx, boolean_setting in enumerate(settings.boolean_settings):
#         prompt += f"{idx+1}. {boolean_setting.prompt}\n"
#     prompt += "\n\n"

#     # Relative settings
#     prompt += RelativeSetting.format_prompt(settings.relative_settings)
#     for idx, relative_setting in enumerate(settings.relative_settings):
#         prompt += f"{idx + 1}. {relative_setting.to_prompt()}\n"
#     prompt += "\n\n"

#     # Double settings
#     prompt += DoubleSetting.format_prompt()
#     for idx, double_setting in enumerate(settings.double_settings):
#         prompt += f"{idx+1}. {double_setting.prompt}\n"

#     prompt += "\n\n"
#     prompt += "You must never skip any of the settings of enabled components!"
#     return prompt

# class EnvironmentPrompt(Prompt):

#     """
#     The environment prompt is the first prompt that is given to the model. It describes the environment in which the robot will navigate
#     """

#     def get_prompt(self, env_description, settings, input) -> str:

#         print_header("Setting environment as: " + env_description)

#         # Permanent instructions first
#         prompt = ""
#         prompt += f"Our robot will navigate in {env_description} "
#         prompt += f"Its task is to go to a goal position. "
#         prompt += "Please provide initial settings that are appropriate in this environment."

#         self.prompt = prompt
#         return prompt

#     def handle_response(self, response : str, settings):
#         self.response = response

#         # Create an order for the settings
#         for line in response.splitlines():

#             if BooleanSetting.is_line_an_answer(line):
#                 nr = line.split(".")[0]
#                 settings.boolean_settings[int(nr) - 1].from_response_line(line)
#                 continue

#             if RelativeSetting.is_line_an_answer(line):
#                 for idx, setting in enumerate(settings.relative_settings):
#                     if line.split(":")[1].split(".")[0].strip() == setting.name:
#                         setting.from_response_line(line)
#                         break
#                 continue

#             if DoubleSetting.is_line_an_answer(line):
#                 nr = line.split(".")[0]
#                 settings.double_settings[int(nr) - 1].from_response_line(line)
#                 continue

#         # Sort settings
#         ordered_settings = sorted(settings.relative_settings, key=lambda x: x.importance, reverse=True)
#         for idx, setting in enumerate(ordered_settings):
#             setting.order = idx

# class UserInputPrompt(Prompt):

#     """
#     The user input prompt updates the settings with the user input that is given to the robot
#     """

#     def get_prompt(self, env_description, settings, user_input) -> str:

#         if user_input[-1] == ".":
#             user_input = user_input[:-1]

#         if env_description[-1] == ".":
#             env_description = env_description[:-1]

#         # print_header("User input: \"" + user_input + "\"")

#         example_setting_list = [x for x in range(1, len(settings.relative_settings) + 1)]
#         shuffle(example_setting_list)

#         # Make an overview of the current situtation
#         prompt = ""
#         prompt += f"For the same robot, the main user has given the following instructions: \"{user_input}\". "
#         prompt += "How should these settings be changed to fulfill the user's instructions? "
#         prompt += "Please try to follow the user input as accurately as possible "
#         prompt += "but also try to stick to previous user inputs if they are not mutually exclusive.\n\n"
#         prompt += "\n"

#         prompt += "Explain the main change in one brief sentence at the end of your response, formatted as \"**Main Change:** <main_change>\". "
#         prompt += "If you have changed the order of the navigation objectives then you must also modify their importance."

#         self.prompt = prompt
#         return prompt

#     def handle_response(self, response : str, settings):
#         self.response = response

#         # Create an order for the settings
#         for line in response.splitlines():

#             if BooleanSetting.is_line_an_answer(line):
#                 nr = line.split(".")[0]
#                 settings.boolean_settings[int(nr) - 1].from_response_line(line)
#                 continue

#             if RelativeSetting.is_line_an_answer(line):
#                 for idx, setting in enumerate(settings.relative_settings):
#                     if line.split(":")[1].split(".")[0].strip() == setting.name:
#                         setting.from_response_line(line)
#                         break
#                 continue

#             if DoubleSetting.is_line_an_answer(line):
#                 nr = line.split(".")[0]
#                 settings.double_settings[int(nr) - 1].from_response_line(line)
#                 continue


#             if "Main Change" in line:
#                 settings.last_change = line.split(":**")[-1].strip()

#         # Sort settings
#         ordered_settings = sorted(settings.relative_settings, key=lambda x: x.importance, reverse=True)
#         for idx, setting in enumerate(ordered_settings):
#             setting.order = idx

#         print_value("Main Change", settings.last_change)






























# class TestEnvironmentPrompt(Prompt):

#     prompt = ""
#     response = ""

#     def get_prompt(self, env_description, settings) -> str:

#         prompt = "To determine the navigation behavior of the robot you should take into account the environment " + \
#                 "and how it influences social behavior.\n\n"

#         # Permanent instructions first
#         prompt += f"The robot will navigate in {env_description}"
#         prompt += "\n\n"

#         # Testing prompts
#         use_relative_importance = False
#         use_ordinal = True
#         if use_relative_importance:
#             use_ordinal = False

#         if not use_relative_importance and not use_ordinal:
#             prompt += "Please answer the following questions with \"very low\", \"low\", \"medium\", \"high\", or \"very high\".\n"
#             prompt += "C1. How important is it that the robot follows a predefined path at the center of the space?\n"
#             prompt += "C2. How important is it that the robot keeps an extra distance from humans?\n"
#             prompt += "\n"

#             prompt += "Please answer the following questions with \"much slower\", \"slower\", \"as fast\", \"faster\", or \"much faster\".\n"
#             prompt += "R1. Compared to a walking human, how fast should the robot move?\n"
#             prompt += "\n"

#             # Add the prompt instructions (Absolute settings, not relative to the state)
#             prompt += "Please answer the following questions with \"yes\" or \"no\".\n"
#             prompt += "B1. For humans walking in the same direction as the robot, should the robot overtake on the left in this environment?\n"
#             prompt += "B2. For humans walking in the same direction as the robot, should the robot overtake on the right in this environment?\n\n"
        
#         if use_relative_importance:
#             # Explain how the answers should be structured

#             prompt += "Please indicate for the following aspects, which of the two is more important. "
#             prompt += "Please structure your response as follows: "
#             prompt += "<nr>. **<answer>** [<motivation>]. E.g., 1. **A** [Because comfort of humans is more important than efficiency]. "
#             prompt += "<answer> should be the letter before the most important aspect or **E** if they are equally important\n"
#             prompt += "Do not give information outside of the [<motivation>].\n\n"
                
#             # Provide a string for each setting to be able to trade them off
#             prompt += "1. [A] Following the path in the center of the space vs. [B] comfort of nearby humans\n"
#             prompt += "2. [A] Reaching the goal fast vs. [B] comfort of nearby humans\n"
#             prompt += "3. [A] Following the path in the center of the space vs. [B] Reaching the goal fast\n"

#             # This works but is not consistent

#         if use_ordinal:
#             prompt += "The following lists a set of aspects that are important for the robot's navigation behavior. "
#             prompt += "Please order the number before each aspect from most important to least important, e.g., [3, 1, 2].\n\n"
            
#             # prompt += "<nr>. **<answer>** [<motivation>]. E.g., 1. **A** [Because comfort of humans is more important than efficiency]. "
#             # prompt += "<answer> should be the letter before the most important aspect or **E** if they are equally important\n"
#             # prompt += "Do not give information outside of the [<motivation>].\n\n"

#             prompt += "1. Following the path in the center of the space.\n"
#             prompt += "2. Reaching the goal fast.\n"
#             prompt += "3. Comfort of nearby humans.\n"

#             prompt += "Additionally please provide an absolute importance for each aspect between 0 and 10."
        

#         self.prompt = prompt
#         return prompt
    
#     def handle_response(self, response : str):
#         self.response = response
#         print(response)

#         # Create an order for the settings
#         for line in response.splitlines():
#             split_line = line.split("[")
            
#             if len(split_line) == 1:
#                 continue

#             print(split_line[1].split("]")[0])

#             # nr = line.split(".")[0]
#             # answer = line.split("**")[1].split("**")[0]
#             # motivation = line.split("[")[1].split("]")[0]

