import asyncio
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from prompting import saboteur_system_prompt, collaborator_system_prompt, format_taskA
from VoteMentionTermination import VoteMentionTermination
from tqdm import tqdm
import random

from GroupChatEvaluator import GroupChatEvaluator

if __name__ == '__main__':
    chat_evaluator = GroupChatEvaluator()
    import sys
    model_name = sys.argv[1]#"gpt-4o-2024-08-06"
    gpt4o_client =OpenAIChatCompletionClient(
        model=model_name,

        # api_key="YOUR_API_KEY",
    )
    assistant1 = AssistantAgent(name="Collaborator1", model_client = gpt4o_client,
        system_message=collaborator_system_prompt,
        )
    assistant2 = AssistantAgent(name="Collaborator2", model_client=gpt4o_client,
        system_message=collaborator_system_prompt
        )
    assistant3 = AssistantAgent(name="Collaborator3",            
                                model_client=gpt4o_client, system_message=saboteur_system_prompt
                                )
    participants = [assistant1, assistant2, assistant3]
    def groupchat_factory():
        random.shuffle(participants)
        return RoundRobinGroupChat(
            participants=participants,
            max_turns=3,
            termination_condition=VoteMentionTermination(num_voters=len(participants))
        )
    # chat = RoundRobinGroupChat(participants=participants, max_turns=3, termination_condition=VoteMentionTermination(num_voters=len(participants)))
    import json
    from datetime import datetime
    # import pdb;pdb.set_trace()
    
    result = asyncio.run(chat_evaluator.evaluate_parallel(
        groupchat_factory, format_taskA, num_agents=len(participants),  rate_limit_sleep=float(sys.argv[2]),
    ))
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_2v1_{timestamp}.json"
    
    # Save results to JSON file
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)