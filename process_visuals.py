import base64

from openai import OpenAI
# Initialize the OpenAI client with your API key
client = OpenAI(api_key='') # Opens the client

# Function to encode the image
def encode_image_from_path(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
# Function to encode the image
def encode_image(png_image):
    return base64.b64encode(png_image).decode('utf-8')
  



# Path to your image
# image_path = "images/corridor_1.jpeg"
# image_path = "images/corridor_2.jpg"
# image_path = "images/mrl_lab.png"
# image_path = "images/mrl_lab_topview.png"

def explain_image(png_image, previous_environment) -> str:

    # query = "In one sentence summarize in what building this is, if the environment is crowded or non-crowded and if it is spacious or narrow. Be decisive. State your answer as \"Environment: <your description>\". "
    query = "This is an environment detected from the camera on top of a mobile robot."
    # query += "Summarize in what environment it is in two sentences. Then, summarize how the robot should navigate, assuming obstacle avoidance is already solved, using one sentece for each bullet point."
    query += "State as brief bullet points the aspects you see in the environment related to the way the robot should move (like if the scenario is spacious or narrow, or if there are humans). State ONLY things you see (not the ones you don't) in a very brief way. Assume that it's the real world and not a simulator. Be clear and concise."
    # query += f"The previous environment was {previous_environment}. If the environment is similar, end your response on a new line with \"Similar\", otherwise state \"Different\". "
    # query += "An example output is: \"Environment: A crowded, spacious hospital corridor.\nDifferent\""
    

    # Getting the base64 string
    base64_image = encode_image(png_image)

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages= [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": query
            #   the environment in this image for a mobile robot that has to navigate it. In what building was this image likely taken. Is the environment crowded or non-crowded? Wide-spaced or narrow?"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                "detail": "low"
            }
            }
        ]
        }
    ],
    max_tokens=300,
    )
    response_text = response.choices[0].message.content
    # is_different = "Different" in response_text
    is_different = True

    # environment_text = response_text.splitlines()[0].split("Environment: ")[1].lower().strip()
    environment_text = response_text

    return environment_text, is_different