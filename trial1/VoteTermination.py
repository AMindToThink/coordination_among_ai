class VoteTermination():
	def __init__(self, num_voters:int, num_options:int, quorum_fraction:float=.5, answer_format:str="Answer: {}"):
		"""
		A class to make is_termination_msg stateful.
		params:
			num_voters: how many voters there will be
			num_options: number of letter choices (eg A,B,C, and D would mean num_options = 4)
			quorum_fraction: greater than this fraction of voters must select an answer before it is selected by the group. Defaults to .5
		"""
		self.num_voters:int = num_voters
		self.num_options:int = num_options
		self.vote_queue:list[str | None] = [None] * self.num_voters
		self.quorum_fraction:float = quorum_fraction
		self.answer_format:str = answer_format
		self.result:str|None = None

	
	def check_termination(self, msg:dict) -> bool:
		# Check if answer format appears in message
		content = msg['content']
		count = content.count(self.answer_format.format(""))
		
		# Return False if multiple instances or no instances found
		if count != 1:
			return False
		
		# Extract answer from message by finding what's between the format braces
		start_idx = content.find(self.answer_format.format(""))
		answer = content[start_idx + len(self.answer_format.format(""))]
		
		# Convert letter to index (A=0, B=1, etc)
		
		# Check if valid option
		if answer not in {'A', 'B', 'C', 'D'}:
			return False
			
		# Add vote to queue
		# Remove oldest vote and add new vote
		self.vote_queue.pop(0)
		self.vote_queue.append(answer)
		
		# Count votes for each option
		votes = {}
		for vote in self.vote_queue:
			if vote is not None:
				votes[vote] = votes.get(vote, 0) + 1
		
		# Check if any option has reached quorum
		quorum = self.num_voters * self.quorum_fraction
		for option, count in votes.items():
			if count > quorum:
				self.result = option
				return True
				
		return False





