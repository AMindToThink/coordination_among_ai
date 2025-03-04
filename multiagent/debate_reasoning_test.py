# pip install -U autogen-agentchat autogen-ext[openai,web-surfer]
# playwright install
import os
import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_core.models import ModelFamily
async def main() -> None:
    
    assistant2 = AssistantAgent(name="Con", model_client=OpenAIChatCompletionClient(
                model="deepseek/deepseek-r1",
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ['OPENROUTER_API_KEY'],
                max_tokens=500,
                max_retries=2,
                model_info={
                    "vision": False,
                    "function_calling": False,
                    "json_output": False,
                    "family": ModelFamily.R1,
                },
            ),
        system_message="You will argue against the proposition. Think for one sentence before responding."
        )
    user_proxy = UserProxyAgent("user_proxy")
    termination = TextMentionTermination("exit") # Type 'exit' to end the conversation.
    team = RoundRobinGroupChat([user_proxy, assistant2], termination_condition=termination)
    await Console(team.run_stream(task="The user will state a proposition."))

asyncio.run(main())
