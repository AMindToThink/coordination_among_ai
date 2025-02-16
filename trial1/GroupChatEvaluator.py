from autogen_agentchat.teams import BaseGroupChat
from datasets import load_dataset
import prompting
from VoteTermination import VoteTermination

class GroupChatEvaluator():
    def __init__(self, load_dataset_kwargs:dict=dict(path="allenai/ai2_arc", name="ARC-Challenge", split='validation')):
        self.ds = load_dataset(**load_dataset_kwargs)
    
    def evaluate(self, groupchat:BaseGroupChat):
        num_agents = len(groupchat.agents)
        print(f"{num_agents=}")
        for i, row in enumerate(self.ds):
            if i > 4:
                return
            voteTerminator = VoteTermination(num_voters=num_agents)
            question = row['question']
            choices = row['choices']
            answer = row['answerKey']
            print(prompting.format_question(question, choices))
            # task = prompting.format_task(question=question, choices=choices, num_agens=num_agents)

if __name__ == '__main__':
    chat = GroupChatEvaluator()
    from dataclasses import dataclass
    @dataclass
    class dummyGC():
        agents = [1,2,3,4]
    gc = dummyGC()
    chat.evaluate(gc)


        

# raise NotImplementedError("GroupChatEvaluator not yet implemented")