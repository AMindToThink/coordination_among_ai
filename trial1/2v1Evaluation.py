import asyncio
import random
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from prompting import type_to_system_message, format_taskA
from VoteMentionTermination import VoteMentionTermination
from tqdm import tqdm
from GroupChatEvaluator import GroupChatEvaluator
import argparse
import json
from datetime import datetime


def collaborators_vs_saboteurs(model, rate_limit, collaborators, saboteurs, turns=3):
    chat_evaluator = GroupChatEvaluator()
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

    def groupchat_factory():
        # Use the randomized participants list for the group chat.
        return RoundRobinGroupChat(
            participants=participants,
            max_turns=3,
            termination_condition=VoteMentionTermination(num_voters=len(participants)),
        )

    result = asyncio.run(
        chat_evaluator.evaluate_parallel(
            groupchat_factory,
            format_taskA,
            num_agents=len(participants),
            rate_limit_sleep=rate_limit,
        )
    )
    return result


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run group chat evaluation with collaborators and saboteurs"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help='Model name (e.g., "gpt-4o-2024-08-06")',
    )
    parser.add_argument(
        "--rate_limit",
        type=float,
        required=True,
        help="Rate limit sleep duration between API calls",
    )
    parser.add_argument(
        "--collaborators", type=int, required=True, help="Number of collaborator agents"
    )
    parser.add_argument(
        "--saboteurs", type=int, required=True, help="Number of saboteur agents"
    )
    parser.add_argument(
        "--turns", type=int, default=3, help="Maximum number of turns in the conversation"
    )

    args = parser.parse_args()
    result = collaborators_vs_saboteurs(**vars(args))
    result['arguments'] = vars(args)
    # Create a filename with timestamp and command line args for saving the results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{args.model=}_{args.rate_limit=}_{args.collaborators=}_{args.saboteurs=}_{timestamp=}.json"

    # Save results to a JSON file
    with open(filename, "w") as f:
        json.dump(result, f, indent=4)
