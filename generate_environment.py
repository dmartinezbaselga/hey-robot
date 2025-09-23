from openai import OpenAI
# from assistant_base import Assistant

# Initialize the OpenAI client with your API key
client = OpenAI(api_key='') # Opens the client

def generate_environment():

    query = '''
You are an assistant to help encode a hallway environment. You have the commands hallway_x, hallway_y and intersection.

Here is an example that encodes four hallways in a square shape.

<hallway_x x="0" y="0" length="15.0" width="6.0"/>
<intersection x="15" y="0" length="3.0" width="6.0"/>
<hallway_y x="15" y="0" length="15.0" width="6.0"/>
<intersection x="15" y="15" length="3.0" width="6.0"/>
<hallway_x x="15" y="15" length="-15.0" width="6.0"/>
<intersection x="0" y="15" length="3.0" width="6.0"/>
<hallway_y x="0" y="15" length="-15.0" width="6.0"/>


In addition, you can select spawn points (and goals) for pedestrians with:
<random>
    <range_x min="11" max="15"/>
    <range_y min="-12" max="-3"/>
    <range_v min="1.14" max="1.66"/>
    <goal_offset x="0" y="30"/>   
</random>
Here, `range_x` and `range_y` is the range of x and y where pedestrians can spawn and the goal offset determines in which direction they will move.

Generate 8 hallways with intersections with each hallway length between 16 and 24. Make sure that the hallways and intersections align and that hallways are not placed on top of each other. Then select 2 suitable spawn locations for pedestrians inside of the hallways. Use a hallway width of 4.0 and intersection length of 2. Only respond with xml code without \"```xml\".
    '''

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages= [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": query
                }
            ]
            }
        ]
    )
    response = response.choices[0].message.content

    response += "\n<random_pedestrians value=\"8\"/>"

    # Specify the output file name
    output_file = "/workspace/src/pedestrian_simulator/scenarios/llm/"
    output_file += "generated.xml"

    # Write the XML content to the file
    with open(output_file, "w") as file:
        file.write(response)

    print(f"XML content has been written to {output_file}")

if __name__ == "__main__":
    generate_environment()