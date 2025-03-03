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

    def __init__(self, num_voters:int, quorum_fraction:float|None=None, answer_format:str="Answer: {}", sources: Sequence[str] | None = None, num_turns:int|None=None) -> None:
        """Termination condition that checks for votes from agents and terminates when enough have voted.

        Args:
            num_voters (int): Total number of agents that can vote
            quorum_fraction (float, optional): Fraction of voters needed to reach consensus. 0.5 is reasonable.
            answer_format (str, optional): Format string for how answers should appear. Must contain {}. Defaults to "Answer: {}".
            sources (Sequence[str] | None, optional): List of agent names to check for votes. If None, check all agents. Defaults to None.
            num_turns (int | None, optional): Maximum number of turns before terminating. If None, voting ends early if quota agree.
        """
        assert quorum_fraction is None != num_turns is None, "Must set quorum fraction or num turns to determine when voting ends, but not both."
        self._num_voters = num_voters
        self.quorum_fraction = quorum_fraction
        self._answer_format = answer_format
        self._terminated = False
        self._sources = sources
        self._num_turns = num_turns
        self._brace_pos = self._answer_format.find("{}")
        assert self._brace_pos != -1, "The Answer format needs to have {} for the answer's position."

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[AgentEvent | ChatMessage]) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        # import pdb;pdb.set_trace()
        vote_dict:dict[str, str|None] = {} # Which source has voted for what?
        def quorum_system():
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
                
                if not answer.isupper():
                    continue
                vote_dict[message.source] = answer

            votes = {}
            for _, answer in vote_dict.items():
                votes[answer] = votes.get(answer, 0) + 1

            assert self.quorum_fraction is not None, "Wait, how did you get here if quorum fraction is None?"
            for option, count in votes.items():
                if count > self._num_voters * self.quorum_fraction:
                    self._terminated = True
                    # The answer must be first so that message.content[0] is the answer.
                    return StopMessage(content=f"{option} answer chosen", source="VoteMentionTermination")
            return None
        def turn_system():
            assert self._num_turns is not None, "Wait, how did you get here if num_turns is None?"
            if sum(1 for i in messages if i.models_usage is not None) != self._num_turns * self._num_voters:
                return None
            last_messages = list(messages)[-self._num_voters:]
            for m in last_messages:
                last_answer_idx = m.content.rfind("Answer: ")
                if last_answer_idx == -1:
                    continue
                answer_pos = last_answer_idx + len("Answer: ")
                if answer_pos >= len(m.content):
                    continue
                answer = m.content[answer_pos]
                answer = answer.upper()
                vote_dict[m.source] = answer
            
            votes = {}
            for _, answer in vote_dict.items():
                votes[answer] = votes.get(answer, 0) + 1

            if not votes:
                return None

            # Get answer with most votes
            max_choice = max(votes, key=votes.get)
            # max_votes = max(votes.values())
            # winning_answers = [ans for ans, count in votes.items() if count == max_votes]
            self._terminated = True
            return StopMessage(content=f"{max_choice} answer chosen", source="VoteMentionTermination")
            

        if self.quorum_fraction is not None:
            return quorum_system()
        return turn_system()
    
    async def reset(self) -> None:
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

