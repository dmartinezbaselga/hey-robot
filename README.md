# Hey robot! personalizing robot navigation through model predictive control with a large language model
This repo provides the code of the work for out paper Hey robot! personalizing robot navigation through model predictive control with a large language model, published in 2025 IEEE International Conference on Robotics and Automation (ICRA).
# [Paper](https://arxiv.org/pdf/2409.13393) || [Video](https://youtu.be/gB5UZBbDxUA)

## Abstract
Robot navigation methods allow mobile robots to operate in applications such as warehouses or hospitals. While the environment in which the robot operates imposes requirements on its navigation behavior, most existing methods do not allow the end-user to configure the robot's behavior and priorities, possibly leading to undesirable behavior (e.g., fast driving in a hospital). We propose a novel approach to adapt robot motion behavior based on natural language instructions provided by the end-user. Our zero-shot method uses an existing Visual Language Model to interpret a user text query or an image of the environment. This information is used to generate the cost function and reconfigure the parameters of a Model Predictive Controller, translating the user's instruction to the robot's motion behavior. This allows our method to safely and effectively navigate in dynamic and challenging environments. We extensively evaluate our method's individual components and demonstrate the effectiveness of our method on a ground robot in simulation and real-world experiments, and across a variety of environments and user specifications.

## Try it yourself
### Assistants Installation
You will have to set your OpenAI API key in all the files used having:
```
# Write your API key here
client = OpenAI(api_key='') # Opens the client
```

To install the Python environment using poetry:
```
sudo apt-get install portaudio19-dev
poetry install --no-root
```
You can already try the assistants alone, without the planner and the simulator, to check how they work offline. To do so, run:
```
python hey_robot.py
```
Set `continuous_mode` to `True` or `False` if to set it to interactive mode or not. Note than you can already try all the LLMs functionalities using this,

Set `verbose = True` to print the prompts and responses to terminal (otherwise you just get a short summary)
Set `save_prompt = True`,  to save your prompts under `prompts/<environment_description>.txt`

### Planner and Simulator Installation
There are two ways to install all the necessary packages. The first one is creating a ROS1 workspace and cloning the following repos in the `src` directory:
```
git clone --branch hey-robot --single-branch https://github.com/dmartinezbaselga/mpc_planner.git
git clone --branch hey-robot --single-branch https://github.com/dmartinezbaselga/guidance_planner.git
git clone --branch hey-robot --single-branch https://github.com/dmartinezbaselga/DecompUtil.git
git clone https://github.com/oscardegroot/asr_rapidxml.git
git clone --branch hey-robot --single-branch https://github.com/dmartinezbaselga/jackal_simulator.git
git clone --branch hey-robot --single-branch https://github.com/dmartinezbaselga/jackal_socialsim.git
git archive --remote=https://github.com/oscardegroot/pedestrian_simulator.git 614f34c | tar -x
git clone https://github.com/oscardegroot/pedsim_original.git
git clone https://github.com/oscardegroot/roadmap.git
git archive --remote=https://github.com/oscardegroot/ros_tools.git 908a6ec | tar -x
git clone https://github.com/lucasw/rviz_camera_stream.git
git clone --branch hey-robot --single-branch 
git archive --remote=https://github.com/cor-mobile-robotics/vicon_bridge.git fe21ad8 | tar -x
git archive --remote=https://github.com/tud-amr/vicon_util.git 5b9f176 | tar -x

```
You need to follow the installation instructions of the cloned repos. The specific versions of the repos are the ones used for the experiments in the paper. Then, move this repo inside the `src` directory too. You should be able to build the workspace.

Alternatively, a very convenient way to create a workspace in a container is following `https://github.com/tud-amr/mpc_planner_ws.git`. Then, substitute the repos automatically downloaded for the specific versions stated above. 

### Run with simulator
This is now as simple as `roslaunch hey_robot hey_robot_with_planner.launch`. It has `scenario` as argument that defines the simulation scenario and `experiment` that is currently the prompt supplied to `hey_robot_node` at start-up. Set `enable_input` to `True` in `hey_robot_node.py` to interactively send queries to the robot using the keyboard.

### Run experiments
Install `dvc`: `sudo apt install dvc`. Then:

```
dvc repro
```

This will run all non-cached experiments. Simulation data is saved in `data/` and will be used in `experiments/try.py` to generate metrics and a table.

To force run (even if data is cached already) use the `-f` flag.

To run one stage use `-s <stage>@<scenario>`.

## Citation
If you use this work in your own research or wish to refer to the paper's results, please use the following BibTeX entries.
```bibtex
@inproceedings{martinez2025hey,
  author={Martinez-Baselga, Diego and de Groot, Oscar and Knoedler, Luzia and Alonso-Mora, Javier and Riazuelo, Luis and Montano, Luis},
  booktitle={2025 IEEE International Conference on Robotics and Automation (ICRA)}, 
  title={Hey Robot! Personalizing Robot Navigation Through Model Predictive Control with a Large Language Model}, 
  year={2025},
  volume={},
  number={},
  pages={11002-11009},
  doi={10.1109/ICRA55743.2025.11128826}
}
```
## Bug Reports and Support
For issues related to the work, please contact:
- Diego Martinez-Baselga: `diegomartinez@unizar.es`
