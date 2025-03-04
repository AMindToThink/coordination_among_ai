import asyncio
import warnings
import random
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelFamily
from prompting import type_to_system_message, format_taskA
from VoteMentionTermination import VoteMentionTermination
from tqdm import tqdm
from GroupChatEvaluator import GroupChatEvaluator
import argparse
import json
from datetime import datetime
import os

r1_models = {"deepseek/deepseek-r1"} # so that we can use the slightly more complicated OpenAIChatCompletionClient

def make_groupchat_factory_and_run(participants_factory, num_participants, rate_limit, turns, end_condition, log_file=None, limit=float('inf')):
    chat_evaluator = GroupChatEvaluator()
    assert end_condition in {'quorum', 'turns'}
    def groupchat_factory():
        # Use the randomized participants list for the group chat.
        participants = participants_factory()
        quorum_fraction = .5
        # Configure termination based on end condition
        if end_condition == "quorum":
            termination = VoteMentionTermination(
                num_voters=len(participants),
                quorum_fraction=quorum_fraction
            )
        elif end_condition == "turns":  # turns
            termination = VoteMentionTermination(
                num_voters=len(participants),
                num_turns=turns
            )
            
        return RoundRobinGroupChat(
            participants=participants,
            max_turns=turns if end_condition == "quorum" else None,
            termination_condition=termination,
        )

    result = asyncio.run(
        chat_evaluator.evaluate_parallel(
            groupchat_factory,
            format_taskA,
            num_agents=num_participants,
            rate_limit_sleep=rate_limit,
            log_file=log_file,
            limit=limit,
        )
    )
    return result

def count_participants_from_pairs(model_role_pairs:list):
    return len(model_role_pairs)

def participants_from_pairs(model_role_pairs:list, max_tokens=1000):
    random.shuffle(model_role_pairs)
    model_clients = {}
    for model, _ in model_role_pairs:
        if model not in model_clients:
            if model not in r1_models:
                model_clients[model] = OpenAIChatCompletionClient(
                    model=model,
                    # api_key="YOUR_API_KEY",
                )
                continue

            model_clients[model] = OpenAIChatCompletionClient(
                model=model,
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ['OPENROUTER_API_KEY'],
                max_tokens=max_tokens,
                max_retries=2,
                model_info={
                    "vision": False,
                    "function_calling": False,
                    "json_output": False,
                    "family": ModelFamily.R1,
                },
            )
    
    participants = []
    for i, (model, agent_type) in enumerate(model_role_pairs):
        participants.append(
            AssistantAgent(
                name=f"Collaborator_{i}",
                model_client=model_clients[model],
                system_message=type_to_system_message[agent_type],
            )
        )

    return participants

def numbers_to_pairs(model:str, collaborators:int, saboteurs:int):
    colab_or_saboteur = ["collaborator"] * collaborators + ["saboteur"] * saboteurs
    random.shuffle(colab_or_saboteur)
    result = []
    for i, agent_type in enumerate(colab_or_saboteur):
        result.append(
            (model, agent_type)
        )
    return result

def count_participants_from_numbers(collaborators:int, saboteurs:int):
    return collaborators + saboteurs

def participants_from_numbers(model, collaborators:int, saboteurs:int):
    assert False, "I swapped this to numbers_to_pairs and participants_from_pairs"
    model_client = OpenAIChatCompletionClient(
        model=model,
        # api_key="YOUR_API_KEY",
    )

    participants = []
    colab_or_saboteur = ["collaborator"] * collaborators + ["saboteur"] * saboteurs
    random.shuffle(colab_or_saboteur)
    for i, agent_type in enumerate(colab_or_saboteur):
        participants.append(
            AssistantAgent(
                name=f"Collaborator_{i}",
                model_client=model_client,
                system_message=type_to_system_message[agent_type],
            )
        )

    return participants


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="""Run group chat evaluation with collaborators and saboteurs using a JSON config file.
        Example:
            python 2v1Evaluation.py --config config.json
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to JSON configuration file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=-1,
        help="Only do the first limit questions. Defaults to -1 which means all questions."
    )
    args = parser.parse_args()
    
    # Load configuration from JSON file
    with open(args.config, 'r') as f:
        config = json.load(f)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create a descriptive filename
    if "model_role_pairs" in config:
        filename = f"evaluation_custom_pairs_{timestamp}.json"
    else:
        model = config["model"]
        collaborators = config["collaborators"]
        saboteurs = config["saboteurs"]
        filename = f"evaluation_{model}_{collaborators}c_{saboteurs}s_{timestamp}.json"
    # Extract common parameters
    rate_limit = config.get("rate_limit")
    turns = config.get("turns", 3)
    end_condition = config.get("end_condition", "quorum")
    output_dir = config.get("output_dir", "./2v1Evaluation_results")
    log_file = config.get("log_file", None)
    
    log_file = log_file.format(filename=filename) if log_file else None
    # Create timestamp for filenames
    
    
    # If log_file is specified but doesn't have a path, add the output directory
    if log_file and not os.path.dirname(log_file):
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        # Add timestamp to log filename if it doesn't already have one
        if "." in log_file:
            name, ext = log_file.rsplit(".", 1)
            log_file = os.path.join(output_dir, f"{name}_{timestamp}.{ext}")
        else:
            log_file = os.path.join(output_dir, f"{log_file}_{timestamp}.txt")
    
    # Determine which method was used to specify participants
    if "model_role_pairs" in config:
        # Use the model-role pairs directly
        model_role_pairs = config["model_role_pairs"]
        participants_factory = lambda: participants_from_pairs(model_role_pairs, max_tokens=max_tokens)
        num_participants = count_participants_from_pairs(model_role_pairs)
    elif all(k in config for k in ["model", "collaborators", "saboteurs"]):
        # Use the model and counts to generate pairs
        model = config["model"]
        collaborators = config["collaborators"]
        saboteurs = config["saboteurs"]
        model_role_pairs = numbers_to_pairs(model, collaborators, saboteurs)
        participants_factory = lambda: participants_from_pairs(model_role_pairs, max_tokens=max_tokens)
        num_participants = count_participants_from_pairs(model_role_pairs)
    else:
        raise ValueError("Config must contain either 'model_role_pairs' or all of 'model', 'collaborators', and 'saboteurs'")
    max_tokens = config.get("max_tokens", None)  # Default to 1000 if not specified
    if max_tokens is None:
        # Warn about potential long completion times with r1 models
        if any(str(pair[0]).lower() in r1_models for pair in model_role_pairs):
            warnings.warn(
                "Using r1 models may result in very long completion times due to their verbose responses.You probably want to put a max_tokens in your config.",
                RuntimeWarning
            )
    result = make_groupchat_factory_and_run(
        participants_factory=participants_factory, 
        num_participants=num_participants, 
        rate_limit=rate_limit, 
        turns=turns,
        end_condition=end_condition,
        log_file=log_file,
        limit=float('inf') if args.limit == -1 else args.limit,
    )
    
    # Include the configuration and actual model-role pairs used in the result
    result = dict(
        config=config,
        model_role_pairs=model_role_pairs,
        evaluation=result
    )
    
    # Create a filename with timestamp for saving the results
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save results to a JSON file
    with open(os.path.join(output_dir, filename), "w") as f:
        json.dump(result, f, indent=4)
