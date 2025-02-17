import asyncio
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
import prompting
from VoteMentionTermination import VoteMentionTermination
from tqdm import tqdm

class GroupChatEvaluator():
    def __init__(self, load_dataset_kwargs:dict=dict(path="allenai/ai2_arc", name="ARC-Challenge", split='validation')):
        self.ds = load_dataset(**load_dataset_kwargs)
    
    async def evaluate(self, groupchat:BaseGroupChat, task_formatter:Callable, num_agents:int, verbose:bool=False, limit:float=float('inf')):
        """Evaluate a group chat's performance on a dataset of questions.

        Args:
            groupchat (BaseGroupChat): The group chat to evaluate
            task_formatter (Callable): Function that formats the question and choices into a task prompt
            num_agents (int): Number of agents in the group chat
            verbose (bool, optional): Whether to print detailed output. Defaults to False.
            limit (float, optional): Maximum number of questions to evaluate. Defaults to infinity.

        Returns:
            dict: Results dictionary containing:
                - accuracy: Fraction of questions answered correctly
                - given_answers: List of answers given by the group chat
                - question_grades: List of booleans indicating correctness of each answer
        """
        if verbose:
            print(f"{num_agents=}")
        given_answers_list:list[str|None] = []
        answers_correct_list:list[bool] = []
        
        for i, row in enumerate(tqdm(self.ds)):
            if i > limit:
                break
            # 
            question = row['question']
            choices = row['choices']
            answer = row['answerKey']
            task = task_formatter(question=question, choices=choices, num_agents=num_agents)
            chat_result = await groupchat.run(task=task)
            await groupchat.reset()
            chosen_answer = chat_result.stop_reason[0] if chat_result.stop_reason else None
            given_answers_list.append(chosen_answer)
            answers_correct_list.append(chosen_answer == answer)

            if verbose:
                print(prompting.format_question(question, choices))
                print(chat_result)
            # answers_correct_list.append(voteTerminator.result == answer)
            # given_answers_list.append(voteTerminator.result)
        return dict(accuracy=sum(answers_correct_list) / len(answers_correct_list), given_answers=given_answers_list, question_grades=answers_correct_list)

if __name__ == '__main__':
    chat_evaluator = GroupChatEvaluator()
    model_name = "gpt-4o-mini-2024-07-18"
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
    import json
    from datetime import datetime
    
    result = asyncio.run(chat_evaluator.evaluate(chat, prompting.format_taskA, num_agents=len(participants), verbose=False))
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{timestamp}.json"
    
    # Save results to JSON file
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)

    import pdb;pdb.set_trace()




        

# raise NotImplementedError("GroupChatEvaluator not yet implemented")