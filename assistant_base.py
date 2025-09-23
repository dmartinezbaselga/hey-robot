
from util.logging import print_header, print_value, print_warning, print_success

def call_openai_api(client, conversation, model="gpt-4o-mini", **kwargs):

        response = client.chat.completions.create(
            model = model,
            messages=conversation,
            **kwargs)

        return response.choices[0].message.content

class Assistant:
    
    def __init__(self, client, verbose=False, system_prompt=None, temperature=0.05, presence_penalty=0.0, top_p=1.0) -> None:

        self.client = client
        self.verbose = verbose

        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.top_p = top_p
        self.previous_user_inputs = []
    
        if system_prompt is None:
            self.system_prompt = "You specify the navigation behavior of a mobile robot based on its context and user input."
        else:
            self.system_prompt = system_prompt
        
        self.conversation = []
        self.conversation.append({"role": "system", "content": self.system_prompt})
        self.conversation.append({"role": "system", "content": self.get_instructions()})
        self.get_internal_examples()

    def clear_conversation(self):
        self.conversation = []
        self.conversation.append({"role": "system", "content": self.system_prompt})
        self.conversation.append({"role": "system", "content": self.get_instructions()})
        self.get_internal_examples()

    def get_instructions(self) -> str:
        pass

    def get_internal_examples(self) -> str:
        pass

        # conversation.append({"role": "user", "content": prompt})
    def call(self, model="gpt-4o-mini", max_trials=1, **kwargs):
        for _ in range(max_trials):
            response = call_openai_api(self.client, self.conversation, **kwargs)
            self.conversation.append({"role": "assistant", "content": response})
            success = self.read_response(response)
            if success:
                break
        if not success:
            print("Could not fulfil the task. Try it again with other prompt.")
        return response

    def query_base(self, prompt):
        self.conversation.append({"role": "user", "content": prompt})
        response = self.call(temperature=self.temperature, presence_penalty=self.presence_penalty, top_p=self.top_p)
        if self.verbose:
            print_header("Response")
            print(response)

            print_header("Status")
            self.print_status()

    def query_environment(self, environment_description, task, prompt=""):
        prompt += f"Our robot will navigate in {environment_description} "
        prompt += f"Its task is: {task} "
        prompt += "Please provide initial settings that are appropriate in this environment."

        if self.verbose:
            print_header("Environment Query")
            print(prompt)

        self.query_base(prompt)

    def print_status(self):
        pass
    
    def query_user_input(self, user_input, prompt=""):
        prompt += f"For the same robot, the main user has given the following instructions: \"{user_input}\". "
        prompt += "How should these settings be changed to fulfill the user's instructions? "
        prompt += "Please try to follow the user input as accurately as possible "
        prompt += "but also try to stick to previous user inputs if they are not mutually exclusive.\n\n"
        prompt += "\n"

        prompt += "Explain the main change in one brief sentence at the end of your response, formatted as \"**Main Change:** <main_change>\". "
        prompt += "If you have changed the order of the navigation objectives then you must also modify their importance."

        if self.verbose:
            print_header(f"User Input: {user_input}")
            print(prompt)

        self.query_base(prompt)
