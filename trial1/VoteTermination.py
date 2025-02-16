class VoteTermination():
	def __init__(self, num_voters:int, quorum_fraction:float=.5, answer_format:str="Answer: {}"):
		"""
		A class to make is_termination_msg stateful.
		params:
			num_voters: how many voters there will be
			quorum_fraction: greater than this fraction of voters must select an answer before it is selected by the group. Defaults to .5
		"""
		self.num_voters:int = num_voters
		self.vote_queue:list[str | None] = [None] * self.num_voters
		self.quorum_fraction:float = quorum_fraction
		self.answer_format:str = answer_format
		self.result:str|None = None

	
	def check_termination(self, msg: dict) -> bool:
		def no_vote():
			self.vote_queue.pop(0)
			self.vote_queue.append(None)
			# The answer_format is not in the expected format if no "{}" is found.
			return False	
		# Check if the answer format appears within the message.
		content = msg['content']
		
		# Find the position of "{}" in the answer format
		brace_pos = self.answer_format.find("{}")
		if brace_pos == -1:
			return no_vote()

		# Split the answer_format into a prefix and suffix.
		prefix = self.answer_format[:brace_pos]
		suffix = self.answer_format[brace_pos+2:]
		
		# Ensure that the prefix exists in the content.
		start_idx = content.find(prefix)
		if start_idx == -1:
			return no_vote()
		
		# The answer should immediately follow the prefix.
		answer_start = start_idx + len(prefix)
		
		# If there's a suffix, use it to determine where the answer ends.
		if suffix:
			answer_end = content.find(suffix, answer_start)
			if answer_end == -1:
				return no_vote()
			answer = content[answer_start:answer_end]
		else:
			# If no suffix is defined, assume the answer extends to the rest of the content.
			answer = content[answer_start:]
		
		# Strip any extra whitespace from the extracted answer.
		answer = answer.strip()
		
		# Make sure the answer is valid (in this case, a single letter among the valid options).
		if answer not in {'A', 'B', 'C', 'D'}:
			return no_vote()

		# Update the vote queue with the new vote.
		self.vote_queue.pop(0)
		self.vote_queue.append(answer)
		
		# Count votes for each option.
		votes = {}
		for vote in self.vote_queue:
			if vote is not None:
				votes[vote] = votes.get(vote, 0) + 1
		
		# Check if any option has reached quorum.
		quorum = self.num_voters * self.quorum_fraction
		for option, count in votes.items():
			if count > quorum:
				self.result = option
				return True

		return False





