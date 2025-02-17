import asyncio
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
import prompting
from VoteMentionTermination import VoteMentionTermination
class GroupChatEvaluator():
    def __init__(self, load_dataset_kwargs:dict=dict(path="allenai/ai2_arc", name="ARC-Challenge", split='validation')):
        self.ds = load_dataset(**load_dataset_kwargs)
    
    async def evaluate(self, groupchat:BaseGroupChat, task_formatter:Callable, num_agents:int, verbose:bool=False):
        print(f"{num_agents=}")
        given_answers_list = []
        answers_correct_list = []
        
        for i, row in enumerate(self.ds):
            if i > 4:
                return
            # 
            question = row['question']
            choices = row['choices']
            answer = row['answerKey']
            task = task_formatter(question=question, choices=choices, num_agents=num_agents)
            chat_result = await groupchat.run(task=task)
            await groupchat.reset()
            if verbose:
                print(prompting.format_question(question, choices))
                print(chat_result)
            # answers_correct_list.append(voteTerminator.result == answer)
            # given_answers_list.append(voteTerminator.result)
        

if __name__ == '__main__':
    chat_evaluator = GroupChatEvaluator()
    model_name = "gpt-4o-2024-08-06"
    gpt4o_client =OpenAIChatCompletionClient(
        model=model_name,

        # api_key="YOUR_API_KEY",
    )
    assistant1 = AssistantAgent(name="Pro", model_client = gpt4o_client,
        system_message="You are the creative idea guy.",
        )
    assistant2 = AssistantAgent(name="Con", model_client=gpt4o_client,
        system_message="You are the logical rules-based guy."
        )
    participants = [assistant1, assistant2]
    chat = RoundRobinGroupChat(participants=participants, max_turns=3, termination_condition=VoteMentionTermination(num_voters=len(participants)))
    asyncio.run(chat_evaluator.evaluate(chat, prompting.format_taskA, num_agents=len(participants), verbose=True))



        

# raise NotImplementedError("GroupChatEvaluator not yet implemented")