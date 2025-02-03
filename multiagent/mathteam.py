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
    assistant1 = AssistantAgent("Assistant", model_client)
    assistant2 = AssistantAgent("Assistant", model_client)
    assistant3 = AssistantAgent("Assistant", model_client)
    user_proxy = UserProxyAgent("user_proxy")
    termination = TextMentionTermination("exit") # Type 'exit' to end the conversation.
    team = RoundRobinGroupChat([assistant1, assistant2, assistant3, user_proxy], termination_condition=termination)
    await Console(team.run_stream(task="What is the Nash equilibrium of the following game: 3 players each say a positive integer at the same time. The player who says the smallest unique number wins. If all say the same number, the winner is chosen at random."))

asyncio.run(main())
