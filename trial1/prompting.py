def display_prompting_script(num_agents, formatted_question):
    """
    Prints the prompting script with the provided values.

    Parameters:
    - num_agents (int): The number of team members.
    - formatted_question (str): A formatted question to append at the end.
    """
    script = f"""
You are part of a team with {num_agents} members. For each task, you will receive a question along with possible answers. Your objective is to select the best answer as a team.

Instructions:

1. Answer Format:
   Provide your answer in the following format:
   Answer: {{A, B, C, D, E, or F}}

2. Single Choice:
   You must choose exactly one option for each question.

3. Mandatory Response:
   You are required to respond to every question. Not providing an answer is not acceptable.

{formatted_question}
"""
    print(script)


def format_question(question, data):
    """
    Formats a question and its choices into a readable string.

    Parameters:
    - question (str): The question to be asked.
    - data (dict): A dictionary containing two lists:
        - "text": A list of answer choices (e.g., ["dry palms", "wet palms", ...]).
        - "label": A list of labels (e.g., ["A", "B", "C", "D"]).

    Returns:
    - str: The formatted question and choices.
    """
    # Start with the question
    formatted_str = f"Question: {question}\n\n"

    # Loop through each label and choice text together
    for lbl, txt in zip(data["label"], data["text"]):
        formatted_str += f"{lbl}) {txt}\n"

    return formatted_str
