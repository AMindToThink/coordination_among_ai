import time
from typing import List, Sequence

from autogen_core import Component
from pydantic import BaseModel
from typing_extensions import Self

from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.messages import AgentEvent, BaseChatMessage, ChatMessage, HandoffMessage, MultiModalMessage, StopMessage


class VoteMentionTerminationConfig(BaseModel):
    text: str



class VoteMentionTermination(TerminationCondition, Component[VoteMentionTerminationConfig]):
    """Terminate the conversation if enough agents have voted.
    Based on TextMentionTermination.


    Args:
        text: The text to look for in the messages.
        sources: Check only messages of the specified agents for the text to look for.
    """

    component_config_schema = VoteMentionTerminationConfig
    component_provider_override = "autogen_agentchat.conditions.TextMentionTermination"

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
            # Todo: this logic isn't finished
            if isinstance(message.content, str) and self._answer_format in message.content:
                self._terminated = True
                return StopMessage(content=f"Text '{self._text}' mentioned", source="TextMentionTermination")
            
            # No multimodal messages; we aren't dealing with images.
            # elif isinstance(message, MultiModalMessage):
            #     for item in message.content:
            #         if isinstance(item, str) and self._text in item:
            #             self._terminated = True
            #             return StopMessage(content=f"Text '{self._text}' mentioned", source="TextMentionTermination")
        return None


    async def reset(self) -> None:
        self._terminated = False




    def _to_config(self) -> TextMentionTerminationConfig:
        return TextMentionTerminationConfig(text=self._text)




    @classmethod
    def _from_config(cls, config: TextMentionTerminationConfig) -> Self:
        return cls(text=config.text)