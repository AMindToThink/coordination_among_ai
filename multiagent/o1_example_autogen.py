# from https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.agents.html#:~:text=following%20example%20shows%20how%20to%20use%20o1%2Dmini%20model%20with%20the%20assistant%20agent
import asyncio
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage


async def main() -> None:
    model_client = OpenAIChatCompletionClient(
        model="o1-mini",
        # api_key = "your_openai_api_key"
    )
    # The system message is not supported by the o1 series model.
    agent = AssistantAgent(name="assistant", model_client=model_client, system_message=None)

    response = await agent.on_messages(
        [TextMessage(content="What is the capital of France?", source="user")], CancellationToken()
    )
    print(response)


asyncio.run(main())