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
    assistant1 = AssistantAgent(name="Memory Assistant", model_client=OpenAIChatCompletionClient(
            model="gpt-4o-2024-08-06",
            # api_key="YOUR_API_KEY",
        ),
        system_message="You will remember what the user asks you to remember, and tell it to them when prompted.",
        )
    
    user_proxy = UserProxyAgent("user_proxy")
    termination = TextMentionTermination("exit") # Type 'exit' to end the conversation.
    team1 = RoundRobinGroupChat([user_proxy, assistant1], termination_condition=termination)
    await Console(team1.run_stream(task="The user has a question for you."))
    team2 = RoundRobinGroupChat([user_proxy, assistant1], termination_condition=termination) 
    await Console(team2.run_stream(task="The user has a question for you."))


asyncio.run(main())
