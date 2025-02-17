import asyncio
import random
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from prompting import saboteur_system_prompt, collaborator_system_prompt, format_taskA
from VoteMentionTermination import VoteMentionTermination
from tqdm import tqdm
from GroupChatEvaluator import GroupChatEvaluator

if __name__ == '__main__':
    chat_evaluator = GroupChatEvaluator()
    import sys
    model_name = sys.argv[1]  # For example: "gpt-4o-2024-08-06"
    gpt4o_client = OpenAIChatCompletionClient(
        model=model_name,
        # api_key="YOUR_API_KEY",
    )
    # Get number of collaborators and adversaries from command line arguments
    num_collaborators = int(sys.argv[3])
    num_adversaries = int(sys.argv[4])

    participants = []

    # Create collaborator agents with the collaborator system message.
    # Assign a temporary name that will be overwritten later.
    for i in range(num_collaborators):
        participants.append(
            AssistantAgent(
                name=f"TempName_{i+1}",
                model_client=gpt4o_client,
                system_message=collaborator_system_prompt
            )
        )

    # Create adversary agents with the saboteur system message.
    for j in range(num_adversaries):
        participants.append(
            AssistantAgent(
                name=f"TempName_{num_collaborators + j + 1}",
                model_client=gpt4o_client,
                system_message=saboteur_system_prompt
            )
        )

    # Randomize the order of all agents
    random.shuffle(participants)

    # Reassign names based on the randomized order so that agent numbering doesn't reflect group identity.
    for idx, agent in enumerate(participants):
        agent.name = f"Collaborator{idx+1}"

    def groupchat_factory():
        # Use the randomized participants list for the group chat.
        return RoundRobinGroupChat(
            participants=participants,
            max_turns=3,
            termination_condition=VoteMentionTermination(num_voters=len(participants))
        )

    import json
    from datetime import datetime
    
    result = asyncio.run(chat_evaluator.evaluate_parallel(
        groupchat_factory, format_taskA, num_agents=len(participants), rate_limit_sleep=float(sys.argv[2]),
    ))
    
    # Create a filename with timestamp and command line args for saving the results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{sys.argv[1]}_{sys.argv[2]}_{sys.argv[3]}_{sys.argv[4]}_{timestamp}.json"
    
    # Save results to a JSON file
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)