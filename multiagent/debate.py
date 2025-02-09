# pip install -U autogen-agentchat autogen-ext[openai,web-surfer]
# playwright install
import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

async def main() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    assistant1 = AssistantAgent(name="Pro", model_client=OpenAIChatCompletionClient(
            model="gpt-4o-2024-08-06",
            # api_key="YOUR_API_KEY",
        ),
        system_message="You are the 'Pro' AI who argues in favor of the proposition",
        )
    assistant2 = AssistantAgent(name="Con", model_client=OpenAIChatCompletionClient(
            model="gpt-4o-2024-08-06",
            # api_key="YOUR_API_KEY",
        ),
        system_message="You are the 'Con' AI who will argue against the proposition."
        )
    user_proxy = UserProxyAgent("user_proxy")
    termination = TextMentionTermination("exit") # Type 'exit' to end the conversation.
    team = RoundRobinGroupChat([assistant1, assistant2, user_proxy], termination_condition=termination)
    await Console(team.run_stream(task="The user will state a proposition. Assistant 'Pro' will argue in favor, and 'Con' will argue against."))

asyncio.run(main())
