raise NotImplementedError("This is made up of hallucinations")
import os
import autogen
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent, runtime_logging
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily

# Configure the DeepSeek R1 client.
# This client connects to a local endpoint that serves the deepseek-r1:1.5b model.
deepseek_client = OpenAIChatCompletionClient(
    model="deepseek-r1:1.5b",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ['OPENROUTER_API_KEY'],
    model_info={
        "vision": False,
        "function_calling": False,
        "json_output": False,
        "family": ModelFamily.R1,
    },
)

# Define the LLM configuration to use our deepseek client.
llm_config = {
    "model_client": deepseek_client,
    "temperature": 0.7,
}

# Create a system prompt that instructs DeepSeek R1 to reveal its internal chain-of-thought.
system_prompt = (
    "You are DeepSeek R1, a powerful reasoning assistant. "
    "When solving a problem, think step by step. "
    "Enclose your internal reasoning within <think> and </think> tags, "
    "and provide your final answer enclosed within <answer> and </answer> tags. "
    "Do not include any extra text."
)

# Create the assistant agent with our custom system prompt.
assistant = AssistantAgent(name="assistant", llm_config=llm_config, system_message=system_prompt)

# Create a user proxy agent that initiates the conversation.
# We set human_input_mode to "NEVER" so that the conversation runs automatically.
user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
)

# Start runtime logging—this will store logs (including full conversation and costs) in a SQLite database.
logging_session_id = runtime_logging.start(config={"dbname": "deepseek_logs.db"})
print("Logging session ID:", logging_session_id)

# Initiate a chat by sending a task to the assistant.
# The task asks the assistant to solve a simple math problem and display its internal reasoning.
task_message = "Solve the following problem and show your internal thoughts: What is 2 + 3?"
user_proxy.initiate_chat(assistant, message=task_message)

# Once the conversation is done, stop logging.
runtime_logging.stop()