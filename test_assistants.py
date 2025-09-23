from util.logging import print_warning, print_success, print_value
import os

from openai import OpenAI
import shutil
import yaml

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from assistants.code_generation_assistant import CostGenerationAssistant
from assistants.code_capability_assistant import CodeCapabilityAssistant
from assistants.weight_retrieval_assistant import WeightRetrievalAssistant
from assistants.behavior_or_task_assistant import BehaviorOrTaskAssistant
from camera_to_environment_description import OfflineCameraToEnvironment
# from ..mpc_planner.solver_generator.util.files import load_settings
# from ..mpc_planner.solver_generator.util.realtime_parameters import AcadosRealTimeModel
# from mpc_planner_py.scripts.generate_system_solver import generate

import rospkg
r = rospkg.RosPack()

import sys
sys.path.insert(0, r.get_path("mpc_planner_py") + "/scripts")
from generate_system_solver import configuration_generated_llm
from generate_solver import generate_solver
plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ["Computer Modern"]

class AssistantsTester:
    def __init__(self, verbose) -> None:
        self.verbose = verbose
        # Initialize the OpenAI client with your API key
        self.client = OpenAI(api_key='') # Opens the client
        self.num_times = 10
        if not os.path.exists("results"):
            os.makedirs("results")
    
    def load_settings(self, setting_file_name="settings", package=None):
        path = os.path.join(r.get_path("mpc_planner_py"), "config", f"{setting_file_name}.yaml")
        with open(path, "r") as stream:
            settings = yaml.safe_load(stream)
        return settings

    def generate_acados_solver(self):
        try:
            settings = self.load_settings()
            model, modules = configuration_generated_llm(settings)

            _, _ = generate_solver(modules, model, settings)
            return True
        except (RuntimeError, KeyError) as e:
            print(str(e))
            return False

    def test_capability_assistant(self):
        generated_files = ["llm_path.py", "llm_goal.py", "llm_human.py"]
        prompts = ["Go to the goal. You are navigating through a hospital.", "Stick to the path.", "Follow the closest human.", "Go to the goal while keeping a safe distance from humans.", "Adapt to the environment."]
        results = np.zeros((len(prompts), len(generated_files), 3))
        times = []
        for _ in range(self.num_times):
            for file_idx, file in enumerate(generated_files):
                for prompt_idx, prompt in enumerate(prompts):
                    capability_assistant = CodeCapabilityAssistant(client=self.client, verbose=self.verbose, generated_code_file=file)
                    capability_assistant.query(prompt)
                    times.append(capability_assistant.timing.get_last())
                    if capability_assistant.environment:
                        results[prompt_idx, file_idx, 0] += 1
                    elif capability_assistant.capable:
                        results[prompt_idx, file_idx, 1] += 1
                    else:
                        results[prompt_idx, file_idx, 2] += 1
                    if self.verbose:
                        print(file, prompt, "=======>", capability_assistant.print_status())
                        print("---------------------------------")
        with open('results/capability_assistant_text.npy', 'wb') as f:
            np.save(f, results/float(self.num_times))
        with open('results/times_capability_assistant.txt', "w") as text_file:
            text_file.write(f'Mean time: {np.mean(times)}\nStd. dev.: {np.std(times)}')


    def test_capability_assistant_v2(self):
        generated_files = ["llm_human.py"]
        prompts = ["Follow the closest human.", "Go to the goal while keeping a safe distance from humans.",]
        results = np.zeros((len(generated_files), len(prompts)))
        desired_output = np.zeros((len(generated_files), len(prompts)), dtype=bool)
        desired_output[0, 0] = True
        for _ in range(10):
            for file_idx, file in enumerate(generated_files):
                for prompt_idx, prompt in enumerate(prompts):
                    capability_assistant = CodeCapabilityAssistant(client=self.client, verbose=self.verbose, generated_code_file=file)
                    capability_assistant.query(prompt)
                    results[file_idx, prompt_idx] += capability_assistant.capable == desired_output[file_idx, prompt_idx]
                    if self.verbose:
                        print(file, prompt, "=======>", capability_assistant.capable==desired_output[file_idx, prompt_idx])
                        print("---------------------------------")
    
    def save_capability_assistant_plot(self):
        with open('results/capability_assistant_text.npy', 'rb') as f:
            data = np.load(f)
        # Example Data: Replace this with your actual data
        methods = [r'$J_{path}$', r'$J_{goal}$', r'$J_{hf}$']
        inputs = ['C1', 'C2', 'C3', 'C4', 'C5']
        results = ['Environment', 'Capable', 'Generate']

        # Create a custom color palette
        colors = sns.color_palette("pastel", len(results))
        colors[1], colors[2] = colors[2],colors[1]

        # Plotting
        fig, ax = plt.subplots(figsize=(6.5, 2))

        # Positions for the bars, with extra space for separation between inputs
        bar_width = 0.9
        spacing = 0.05
        index = np.arange(len(inputs)) * (len(methods) * (bar_width + spacing))

        # Plot each method with stacking
        for i, method in enumerate(methods):
            bottom_values = np.zeros(len(inputs))
            
            for j, result in enumerate(results):
                ax.bar(index + i * bar_width, data[:, i, j], bar_width, bottom=bottom_values, 
                    color=colors[j], edgecolor='black', label=result if i == 0 else "")
                bottom_values += data[:, i, j]
            
            # Label each method below the bars
            # for k in range(len(inputs)):
            #     ax.text(index[k] + (i-0.5) * bar_width + bar_width / 2, -0.2, method, ha='center', 
            #             va='top', fontsize=12, rotation=0)
        for k, inp in enumerate(inputs):
            ax.text(index[k] + ((len(methods)-1) / 2.0) * bar_width, -0.2, inp, ha='center', 
                    va='top', fontsize=12, rotation=0)

        # Customizations
        # ax.set_xlabel('Inputs', fontsize=14, labelpad=20)
        # ax.set_ylabel('Number of times', fontsize=14)
        # ax.set_title('Stacked Bar Chart of Methods and Results', fontsize=16, weight='bold')
        ax.set_xticks(index + ((len(methods)-1) / 2.0) * bar_width)
        ax.set_xticklabels(inputs, fontsize=12)
        ax.set_xticks([index[k] + (i-0.5) * bar_width + bar_width / 2 for k in range(len(inputs)) for i in range(len(methods))])
        ax.set_xticklabels(methods*len(inputs), fontsize=12)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        ax.margins(x=0)

        # Add legend
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[:len(results)], labels[:len(results)], fontsize=11)

        # Adjust layout to make room for method labels
        # plt.tight_layout(rect=[0, 0.05, 1, 1])
        # plt.show()
        plt.savefig('results/capability_assistant_bar_chart.png', dpi=300, bbox_inches='tight')
    
    def test_cost_generation_assistant(self):
        prompts = [
            "Follow the path.",
            "Reach the goal.",
            "Minimize the distance to the closest human.",
            "Maximize the distance to the closest human.",
            "Reach the goal while trying to keep a safe distance from humans.",
            "Follow the closest human.",
            "Reach the goal as fast as possible.",
        ]     
        times = []
        for time in range(self.num_times):
            for prompt in prompts:
                if self.verbose:
                    print(prompt, time)
                cost_generation_assistant = CostGenerationAssistant(client=self.client, verbose=self.verbose)
                path_name = "results/" + prompt.replace(" ", "_")
                if not os.path.exists(path_name):
                    os.makedirs(path_name)
                # cost_generation_assistant.generated_python_path = path_name + "/" + str(time) + ".py"
                cost_generation_assistant.query_cost(prompt)
                times.append(cost_generation_assistant.timing.get_last())
                if self.generate_acados_solver():
                    shutil.copyfile(os.path.join("/workspace/src/mpc_planner/mpc_planner_modules/scripts/llm_generated.py"), path_name + "/" + str(time) + "_generation_success.py")
                else:
                    shutil.copyfile(os.path.join("/workspace/src/mpc_planner/mpc_planner_modules/scripts/llm_generated.py"), path_name + "/" + str(time) + "_generation_failure.py")
        with open('results/times_generation_assistant.txt', "w") as text_file:
            text_file.write(f'Mean time: {np.mean(times)}\nStd. dev.: {np.std(times)}')

    def test_cost_generation_assistant_v2(self):
        prompts = [
            "Reach the goal.",
            "Follow the path.",
            "Follow the closest human."
        ]     
        for time in range(1):
            for prompt in prompts:
                if self.verbose:
                    print(prompt, time)
                cost_generation_assistant = CostGenerationAssistant(client=self.client, verbose=self.verbose)
                path_name = "results/" + prompt.replace(" ", "_")
                if not os.path.exists(path_name):
                    os.makedirs(path_name)
                # cost_generation_assistant.generated_python_path = path_name + "/" + str(time) + ".py"
                cost_generation_assistant.query_cost(prompt)
                if self.generate_acados_solver():
                    shutil.copyfile(os.path.join("/workspace/src/mpc_planner/mpc_planner_modules/scripts/llm_generated.py"), path_name + "/" + str(time) + "_generation_success.py")
                else:
                    shutil.copyfile(os.path.join("/workspace/src/mpc_planner/mpc_planner_modules/scripts/llm_generated.py"), path_name + "/" + str(time) + "_generation_failure.py")

    def save_cost_generation_assistant_plot(self):
        p1_succ = 10
        p2_succ = 10
        p3_succ = 9
        p4_succ = 10
        p5_succ = 9
        p6_succ = 10
        p7_succ = 10
        successes = np.array([p1_succ, p2_succ, p3_succ, p4_succ, p5_succ, p6_succ, p7_succ])/self.num_times
        prompts = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
        df = pd.DataFrame({
            'Tasks': prompts,
            'Success Rates': successes,
        })
        sns.set(style="whitegrid", context="talk")
        plt.figure(figsize=(8, 3))
        sns.barplot(x='Tasks', y='Success Rates', data=df, palette='Blues_d', )
        # plt.title('Success Rates per Task', fontsize=20)
        # plt.xlabel('Tasks', fontsize=16)
        # plt.ylabel('Success Rate', fontsize=16)
        for i, rate in enumerate(successes):
            plt.text(i, rate + 0.02, f'{rate:.2f}', ha='center', fontsize=14)
        plt.ylim(0, 1)
        plt.savefig('results/cost_generation_histogram.png', dpi=300, bbox_inches='tight')

    def test_weight_assistant(self):
        times = []
        prompts = [
            "Be faster.",
            "Take more distance to humans.",
            "Stick to the path.",
            "Be smoother.",
            "Increase rotation capabilities.",
            "You can rotate more.",
        ]
        files = ["llm_path.py", "llm_safe_dist.py", "llm_path.py", "llm_path.py", "llm_path.py", "llm_path.py"]
        enabled_weights = [
            ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
            ["goal", "closest_human_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
            ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
            ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
            ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
            ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
        ]
        disabled_weights =[
            None, None, None, None, None, None
        ]
        weights = [
            {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
            {"goal": 5.0, "closest_human_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
            {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
            {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
            {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
            {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
        ]
        doubles = [
            {"reference_velocity": 1.5},
            {"reference_velocity": 1.5, "min_safe_distance": 0.75},
            {"reference_velocity": 1.5},
            {"reference_velocity": 1.5},
            {"reference_velocity": 1.5},
            {"reference_velocity": 1.5},
        ]
        def relative_importance(weights_dict, name):
            return float(weights_dict[name]) / np.mean(np.array([*weights_dict.values()]))
        test_functions = [
            lambda w, d, prev_w, prev_d : d["reference_velocity"] > prev_d["reference_velocity"],
            lambda w, d, prev_w, prev_d : d["min_safe_distance"] > prev_d["min_safe_distance"],
            lambda w, d, prev_w, prev_d : relative_importance(w, "contour_weight") > relative_importance(prev_w, "contour_weight"),
            lambda w, d, prev_w, prev_d : relative_importance(w, "acceleration_resistance_weight") > relative_importance(prev_w, "acceleration_resistance_weight") and relative_importance(w, "rotation_resistance_weight") > relative_importance(prev_w, "rotation_resistance_weight"),
            lambda w, d, prev_w, prev_d : relative_importance(w, "rotation_resistance_weight") < relative_importance(prev_w, "rotation_resistance_weight"),
            lambda w, d, prev_w, prev_d : relative_importance(w, "rotation_resistance_weight") < relative_importance(prev_w, "rotation_resistance_weight"),
        ]
        results = np.zeros((len(prompts)))
        for _ in range(self.num_times):
            for prompt_idx, prompt in enumerate(prompts):
                weight_test_assistant = WeightRetrievalAssistant(client=self.client, verbose=self.verbose)
                weight_test_assistant.enabled_weights = enabled_weights[prompt_idx].copy()
                weight_test_assistant.disabled_weights = disabled_weights[prompt_idx]
                weight_test_assistant.weights = weights[prompt_idx].copy()
                weight_test_assistant.doubles = doubles[prompt_idx].copy()
                weight_test_assistant.query(prompt)
                times.append(weight_test_assistant.timing.get_last())
                result = test_functions[prompt_idx](weight_test_assistant.weights, weight_test_assistant.doubles,
                                                     weights[prompt_idx], doubles[prompt_idx])
                results[prompt_idx] += result
                if self.verbose:
                    print(prompt, result)
        np.savetxt('results/weight_assistant_text.txt', results/float(self.num_times))
        with open('results/times_weight_assistant.txt', "w") as text_file:
            text_file.write(f'Mean time: {np.mean(times)}\nStd. dev.: {np.std(times)}')

    def test_weight_assistant_v2(self):
        prompts = [
            "Be smoother.",
        ]
        files = ["llm_path.py"]
        enabled_weights = [
            ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"],
        ]
        disabled_weights =[
            None
        ]
        weights = [
            {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0},
        ]
        doubles = [
            {"reference_velocity": 1.5}
        ]
        def relative_importance(weights_dict, name):
            return float(weights_dict[name]) / np.mean(np.array([*weights_dict.values()]))
        test_functions = [
            lambda w, d, prev_w, prev_d : relative_importance(w, "acceleration_resistance_weight") > relative_importance(prev_w, "acceleration_resistance_weight") and relative_importance(w, "rotation_resistance_weight") > relative_importance(prev_w, "rotation_resistance_weight")
        ]
        results = np.zeros((len(prompts)))
        for _ in range(self.num_times):
            for prompt_idx, prompt in enumerate(prompts):
                weight_test_assistant = WeightRetrievalAssistant(client=self.client, verbose=True)
                weight_test_assistant.enabled_weights = enabled_weights[prompt_idx].copy()
                weight_test_assistant.disabled_weights = disabled_weights[prompt_idx]
                weight_test_assistant.weights = weights[prompt_idx].copy()
                weight_test_assistant.doubles = doubles[prompt_idx].copy()
                weight_test_assistant.query(prompt)
                print(relative_importance(weight_test_assistant.weights, "acceleration_resistance_weight"), relative_importance(weights[prompt_idx], "acceleration_resistance_weight"), relative_importance(weight_test_assistant.weights, "rotation_resistance_weight"), relative_importance(weights[prompt_idx], "rotation_resistance_weight"),)
                result = test_functions[prompt_idx](weight_test_assistant.weights, weight_test_assistant.doubles,
                                                     weights[prompt_idx], doubles[prompt_idx])
                results[prompt_idx] += result
                if self.verbose:
                    print(prompt, result)

    def save_weight_assistant_plot(self):
        successes = np.loadtxt('results/weight_assistant_text.txt')
        prompts = ["W1", "W2", "W3", "W4", "W5", "W6"]
        df = pd.DataFrame({
            'Tasks': prompts,
            'Success Rates': successes,
        })
        sns.set(style="whitegrid", context="talk")
        plt.figure(figsize=(8, 3))
        sns.barplot(x='Tasks', y='Success Rates', data=df, palette='Blues_d', )
        # plt.title('Success Rates per Task', fontsize=20)
        # plt.xlabel('Tasks', fontsize=16)
        # plt.ylabel('Success Rate', fontsize=16)
        for i, rate in enumerate(successes):
            plt.text(i, rate + 0.02, f'{rate:.2f}', ha='center', fontsize=14)
        plt.ylim(0, 1)
        plt.savefig('results/weight_retrieval_histogram.png', dpi=300, bbox_inches='tight')

    def test_camera(self):
        times = []
        images = [
            "corridor.png",
            "crowded_corridor.png",
            "crowded_open.png",
        ]
        enabled_weights = ["contour_weight", "lag_weight", "acceleration_resistance_weight", "rotation_resistance_weight", "velocity_tracking_weight"]
        # disabled_weights = None
        weights = {"contour_weight": 5.0, "lag_weight": 5.0, "acceleration_resistance_weight": 5.0, "rotation_resistance_weight": 5.0, "velocity_tracking_weight": 5.0}
        doubles = {"reference_velocity": 1.5}
        for _ in range(10):
            for image in images:
                camera_assistant = OfflineCameraToEnvironment()
                camera_assistant.analyze_photo("results/camera_images/" + image)
                print(camera_assistant.environment_description)
                times.append(camera_assistant.timing.get_last())
                weight_test_assistant = WeightRetrievalAssistant(client=self.client, verbose=False)
                weight_test_assistant.enabled_weights = enabled_weights.copy()
                weight_test_assistant.disabled_weights = None
                weight_test_assistant.weights = weights.copy()
                weight_test_assistant.doubles = doubles.copy()

                weight_test_assistant.query("Adapt to an environment with the following features:\n" + camera_assistant.environment_description)
                weight_test_assistant.print_status()
        with open('results/times_camera_assistant.txt', "w") as text_file:
            text_file.write(f'Mean time: {np.mean(times)}\nStd. dev.: {np.std(times)}')


tester = AssistantsTester(True)
# tester.test_capability_assistant()
# tester.test_weight_assistant()
# tester.save_weight_assistant_plot()
# tester.save_capability_assistant_plot()

# tester.test_cost_generation_assistant()
# tester.save_cost_generation_assistant_plot()

# tester.test_capability_assistant_v2()
# tester.test_cost_generation_assistant_v2()
# tester.test_weight_assistant_v2()

tester.test_camera()

# plot_barchart()