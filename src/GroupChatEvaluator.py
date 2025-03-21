import json
import asyncio
from typing import Callable
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import (
    SystemMessage,
)
import prompting
from VoteMentionTermination import VoteMentionTermination
from tqdm import tqdm

class GroupChatEvaluator():
    def __init__(self, load_dataset_kwargs:dict=dict(path="allenai/ai2_arc", name="ARC-Challenge", split='validation')):
        self.ds = load_dataset(**load_dataset_kwargs)

    async def evaluate_parallel(
        self,
        groupchat_factory: Callable[[], BaseGroupChat],
        task_formatter: Callable,
        num_agents: int,
        verbose: bool = False,
        limit: float = float('inf'),
        max_concurrent: int = 10,
        rate_limit_sleep: float = 0.5,  # seconds to wait between successive API calls
        log_file: str|None = None  # New parameter for saving logs
    ):
        """
        Evaluate questions in parallel with a progress bar and rate limiting.
        
        Args:
            groupchat_factory (Callable[[], BaseGroupChat]): Factory to create a new groupchat instance.
            task_formatter (Callable): Function to format the question and choices into a task prompt.
            num_agents (int): Number of agents in the group chat.
            verbose (bool, optional): Whether to print detailed output. Defaults to False.
            limit (float, optional): Maximum number of questions to evaluate. Defaults to infinity.
            max_concurrent (int, optional): Maximum number of concurrent tasks. Defaults to 10.
            rate_limit_sleep (float, optional): Minimum delay between successive API calls.
            log_file (str, optional): Path to save detailed conversation logs. Defaults to None.
            
        Returns:
            dict: Results dictionary containing accuracy, given_answers, and question_grades.
        """
        given_answers_list: list[str | None] = []
        answers_correct_list: list[bool] = []
        semaphore = asyncio.Semaphore(max_concurrent)
        rate_limit_lock = asyncio.Lock()
        last_call = {"time": 0.0}  # shared variable to store the time of the last API call
        
        # Set up logging if a log file is specified
        log_file_handle = None
        if log_file:
            log_file_handle = open(log_file, 'w', encoding='utf-8')
            log_file_handle.write("=== Group Chat Evaluation Logs ===\n\n")

        async def process_row(idx, row):
            async with semaphore:
                # Enforce a minimum time delay between API calls to avoid rate limits.
                async with rate_limit_lock:
                    now = asyncio.get_event_loop().time()
                    elapsed = now - last_call["time"]
                    if elapsed < rate_limit_sleep:
                        await asyncio.sleep(rate_limit_sleep - elapsed)
                    last_call["time"] = asyncio.get_event_loop().time()
                
                # Process the question using a fresh group chat instance.
                groupchat = groupchat_factory()
                question = row['question']
                choices = row['choices']
                answer = row['answerKey']
                task = task_formatter(question=question, choices=choices, num_agents=num_agents)
                
                chat_result = await groupchat.run(task=task)
                chosen_answer = json.loads(chat_result.stop_reason)['answer'] if chat_result.stop_reason else None
                
                # Log the conversation if logging is enabled
                if log_file_handle:
                    log_file_handle.write(f"Question ID: {row.get('id', 'unknown')}\n")
                    log_file_handle.write(f"Question: {question}\n")
                    log_file_handle.write(f"Choices: {choices}\n")
                    log_file_handle.write(f"Correct Answer: {answer}\n")
                    log_file_handle.write(f"Task: {task}\n\n")
                    log_file_handle.write(f"=== Roles ===\n")
                    # Assuming you have a BaseGroupChat instance called 'group_chat'
                    for participant in groupchat._participants:
                        log_file_handle.write(f"Name: {participant.name}")
                        if isinstance(participant, AssistantAgent):
                            if participant._system_messages and isinstance(participant._system_messages[0], SystemMessage):
                                system_message = participant._system_messages[0].content
                                log_file_handle.write(f"System message: {system_message}")
                            else:
                                print(f"Agent {participant.name} has no system message")
                        else:
                            log_file_handle.write("This is not an assistant agent, so no system message given.")
                    # for participant in groupchat._participants:
                    #     # Do something with each participant
                    #     print(participant.name)
                    #     print("\tparticipant.description")
                    #     assert isinstance(participant, AssistantAgent)
                    #     print(f"\t{prompting.system_message_to_type[participant._system_messages[0].content]}")
                    #     # Access other properties or methods of the ChatAgent
                    log_file_handle.write("=== Conversation ===\n")
                    log_file_handle.write(str(chat_result))
                    log_file_handle.write("\n")
                    log_file_handle.write(f"Selected Answer: {chosen_answer}\n")
                    log_file_handle.write(f"Correct: {chosen_answer == answer}\n")
                    log_file_handle.write("\n")
                    log_file_handle.write("\n" + "="*50 + "\n\n")
                    log_file_handle.write("\n")
                
                await groupchat.reset()
                if verbose:
                    print(prompting.format_question(question, choices))
                    print(chat_result)
                return idx, chosen_answer, (chosen_answer == answer)
        
        # Create tasks up to the specified limit.
        tasks = []
        actual_limit = limit if limit != float("inf") else len(self.ds)
        for i, row in enumerate(self.ds):
            if i >= actual_limit:
                break
            tasks.append(asyncio.create_task(process_row(i, row)))
        
        # Set up a progress bar that updates as each task completes.
        progress_bar = tqdm(total=len(tasks), desc="Evaluating (parallel)")
        
        try:
            # Store results with their indices
            indexed_results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                indexed_results.append(result)
                progress_bar.update(1)
            progress_bar.close()
            
            # Sort results by the original index
            indexed_results.sort(key=lambda x: x[0])
            
            # Extract the sorted answers and correctness
            for _, chosen_answer, is_correct in indexed_results:
                given_answers_list.append(chosen_answer)
                answers_correct_list.append(is_correct)
            
            return dict(
                accuracy=sum(answers_correct_list) / len(answers_correct_list) if answers_correct_list else 0,
                given_answers=given_answers_list,
                question_grades=answers_correct_list
            )
        finally:
            # Close the log file if it was opened
            if log_file_handle:
                log_file_handle.close()
                log_file_handle = None  # Explicitly set to None to avoid later references
            # Make sure to close any other resources
            progress_bar.close()  # Ensure progress bar is closed even if an exception occurs

if __name__ == '__main__':
    chat_evaluator = GroupChatEvaluator()
    import sys
    model_name = sys.argv[1]#"gpt-4o-2024-08-06"
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
    def groupchat_factory():
        return RoundRobinGroupChat(
            participants=participants,
            max_turns=3,
            termination_condition=VoteMentionTermination(num_voters=len(participants))
        )
    chat = RoundRobinGroupChat(participants=participants, max_turns=3, termination_condition=VoteMentionTermination(num_voters=len(participants)))
    import json
    from datetime import datetime
    # import pdb;pdb.set_trace()
    
    result = asyncio.run(chat_evaluator.evaluate_parallel(
        groupchat_factory, prompting.format_taskA, num_agents=len(participants), verbose=False, rate_limit_sleep=float(sys.argv[2]),
    ))
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{model_name}_parallel_{timestamp}.json"
    
    # Save results to JSON file
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)

    # import pdb;pdb.set_trace()




        

# raise NotImplementedError("GroupChatEvaluator not yet implemented")