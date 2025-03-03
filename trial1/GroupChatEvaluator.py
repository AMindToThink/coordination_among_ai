import asyncio
from typing import Callable, Sequence
from datasets import load_dataset
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent, ChatAgent
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

        async def process_row(row):
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
                
                # Log the question and task if logging is enabled
                if log_file_handle:
                    log_file_handle.write(f"Question ID: {row.get('id', 'unknown')}\n")
                    log_file_handle.write(f"Question: {question}\n")
                    log_file_handle.write(f"Choices: {choices}\n")
                    log_file_handle.write(f"Correct Answer: {answer}\n")
                    log_file_handle.write(f"Task: {task}\n\n")
                    log_file_handle.write("=== Conversation ===\n")
                
                chat_result = await groupchat.run(task=task)
                # Add async-compatible breakpoint for debugging
                # import pdb; pdb.set_trace()
                # Log the conversation if logging is enabled
                if log_file_handle:
                    for msg in chat_result.messages:
                        if hasattr(msg, 'name') and hasattr(msg, 'content'):
                            log_file_handle.write(f"{msg.name}: {msg.content}\n")
                        elif hasattr(msg, 'content'):
                            log_file_handle.write(f"System: {msg.content}\n")
                    log_file_handle.write("\n")
                    
                    chosen_answer = chat_result.stop_reason[0] if chat_result.stop_reason else None
                    log_file_handle.write(f"Selected Answer: {chosen_answer}\n")
                    log_file_handle.write(f"Correct: {chosen_answer == answer}\n")
                    log_file_handle.write("\n" + "="*50 + "\n\n")
                
                await groupchat.reset()
                chosen_answer = chat_result.stop_reason[0] if chat_result.stop_reason else None
                if verbose:
                    print(prompting.format_question(question, choices))
                    print(chat_result)
                return chosen_answer, (chosen_answer == answer)
        
        # Create tasks up to the specified limit.
        tasks = []
        actual_limit = limit if limit != float("inf") else (
            len(self.ds) if hasattr(self.ds, '__len__') else float('inf')
        )
        for i, row in enumerate(self.ds):
            if i >= actual_limit:
                break
            tasks.append(asyncio.create_task(process_row(row)))
        
        # Set up a progress bar that updates as each task completes.
        progress_bar = tqdm(total=len(tasks), desc="Evaluating (parallel)")
        
        try:
            results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                progress_bar.update(1)
            progress_bar.close()
            
            for chosen_answer, is_correct in results:
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
    def groupchat_factory() -> RoundRobinGroupChat:
        return RoundRobinGroupChat(
            participants=participants,  # type: Sequence[ChatAgent]
            max_turns=3,
            termination_condition=VoteMentionTermination(num_voters=len(participants))
        )
    chat = RoundRobinGroupChat(
        participants=participants,  # type: Sequence[ChatAgent]
        max_turns=3, 
        termination_condition=VoteMentionTermination(num_voters=len(participants))
    )
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