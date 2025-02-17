import time
from typing import List, Sequence

from autogen_core import Component
from pydantic import BaseModel
from typing_extensions import Self

from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.messages import AgentEvent, TextMessage, BaseChatMessage, ChatMessage, HandoffMessage, MultiModalMessage, StopMessage


class VoteMentionTerminationConfig(BaseModel):
    num_voters:int
    quorum_fraction:float=.5
    answer_format:str="Answer: {}"
    sources: Sequence[str] | None = None # Can sources even be serialized?



class VoteMentionTermination(TerminationCondition, Component[VoteMentionTerminationConfig]):
    """Terminate the conversation if enough agents have voted.
    Based on TextMentionTermination.


    Args:
        text: The text to look for in the messages.
        sources: Check only messages of the specified agents for the text to look for.
    """

    component_config_schema = VoteMentionTerminationConfig
    component_provider_override = "autogen_agentchat.conditions.VoteMentionTermination"

    def __init__(self, num_voters:int, quorum_fraction:float=.5, answer_format:str="Answer: {}", sources: Sequence[str] | None = None) -> None:
        self._num_voters = num_voters
        self.quorum_fraction = quorum_fraction
        self._answer_format = answer_format
        self._terminated = False
        self._sources = sources

        self.vote_dict:dict[str, str|None] = {} # Which source has voted for what?
        self._brace_pos = self._answer_format.find("{}")
        assert self._brace_pos != -1, "The Answer format needs to have {} for the answer's position."

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[AgentEvent | ChatMessage]) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        # import pdb;pdb.set_trace()
        for message in messages:
            if self._sources is not None and message.source not in self._sources:
                continue
            assert isinstance(message.content, str)
            prefix = self._answer_format[:self._brace_pos]
            suffix = self._answer_format[self._brace_pos+2:]
            start_idx = message.content.find(prefix)
            if start_idx == -1:
                continue
            answer_start = start_idx + len(prefix)

            if answer_start >= len(message.content):
                continue
            
            answer = message.content[answer_start]
            # if suffix:
            #     answer_end = message.content.find(suffix, answer_start)
            #     assert answer_end != -1, "Why was nothing found after the answer, when empty string should be allowed? Something is wrong here."
            #     answer = message.content[answer_start:answer_end]
            # else:
            #     answer = message.content[answer_start:]
            # answer = answer.strip()
            if not answer.isupper():
                continue
            self.vote_dict[message.source] = answer

        votes = {}
        for _, answer in self.vote_dict.items():
            votes[answer] = votes.get(answer, 0) + 1
        # import pdb;pdb.set_trace()
        # print(votes)

        for option, count in votes.items():
            if count > self._num_voters * self.quorum_fraction:
                self._terminated = True
                # The answer must be first so that message.content[0] is the answer.
                return StopMessage(content=f"{option} answer chosen", source="VoteMentionTermination")

        # if isinstance(message.content, str) and self._answer_format in message.content:
        #     self._terminated = True
        #     return StopMessage(content=f"Text '{self._text}' mentioned", source="TextMentionTermination")
            
            # No multimodal messages; we aren't dealing with images.
            # elif isinstance(message, MultiModalMessage):
            #     for item in message.content:
            #         if isinstance(item, str) and self._text in item:
            #             self._terminated = True
            #             return StopMessage(content=f"Text '{self._text}' mentioned", source="TextMentionTermination")
        return None


    async def reset(self) -> None:
        self.vote_dict = {}
        self._terminated = False

    def _to_config(self) -> VoteMentionTerminationConfig:
        return VoteMentionTerminationConfig(
            num_voters=self._num_voters,
            quorum_fraction=self.quorum_fraction,
            answer_format=self._answer_format,
            sources=self._sources,
        )

    @classmethod
    def _from_config(cls, config: VoteMentionTerminationConfig) -> Self:
        return cls(
            num_voters=config.num_voters,
            quorum_fraction=config.quorum_fraction,
            answer_format=config.answer_format,
            sources=config.sources
        )
    

if __name__ == "__main__":
    import asyncio

    # Test basic voting functionality
    terminator = VoteMentionTermination(num_voters=3, quorum_fraction=0.5)
    
    # Create test messages
    msg1 = TextMessage(content="Answer: A", source="agent1")
    msg2 = TextMessage(content="Answer: A", source="agent2") 
    msg3 = TextMessage(content="Answer: B", source="agent3")

    # Test voting process
    async def run_tests():
        result1 = await terminator([msg1])
        print(f"First vote result: {result1}")  # Should be None
        
        result2 = await terminator([msg2, msg1])
        print(f"Second vote result: {result2}")  # Should be StopMessage with 'A'
        
        # Reset and test again
        await terminator.reset()
        result3 = await terminator([msg3, msg1, msg2])
        print(f"After reset, new vote: {result3}")  # Should be A

    asyncio.run(run_tests())

