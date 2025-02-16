from prompts import simulation_prompt, sim_example
from llm_utils import query_gpt


class Simulator:
    def __init__(self, ground_truth_diagnosis_data: str, ground_truth_final_diagnosis: str, sim_prompt: str=simulation_prompt, sim_example: str=sim_example):
        self.sim_prompt = sim_prompt
        self.sim_example = sim_example
        self.ground_truth_final_diagnosis = ground_truth_final_diagnosis
        self.history = []  # List of dictionaries
        self.diagnosis_result = None # This is the result of the diagnosis for the current simulation
        self.ground_truth_diagnosis_data = ground_truth_diagnosis_data
        self.add_patient_presentation_to_history()
    
    def add_patient_presentation_to_history(self):
        # Extract patient presentation from ground truth data
        lines = self.ground_truth_diagnosis_data.split('\n')
        presentation = []
        
        # Collect relevant presentation information
        for line in lines:
            if line.startswith('patient_presentation:'):
                presentation.append(line.replace('patient_presentation:', '').strip())
            elif line.startswith('additional_history:'):
                presentation.append(line.replace('additional_history:', '').strip())
        
        # Combine all presentation details
        full_presentation = ' '.join(presentation)
        
        # Add to history as the initial "presentation" action
        self.history.append({
            "action": "Initial patient presentation",
            "result": full_presentation, 
            "feedback": "",
            "feedback_comment": ""
        })
    
    def get_history(self) -> str:
        """Returns the history of actions and results as a formatted string."""
        formatted_history = ""
        for step in self.history:
            formatted_history += f"Action: {step['action']}\n"
            formatted_history += f"Results: {step['result']}\n\n"
            #formatted_history += f"Feedback: {step['feedback']}\n\n"
        return formatted_history.strip()
    
    def get_history_json(self) -> str:
        """Returns the history of actions, results, and feedback as a JSON string."""
        import json
        return json.dumps(self.history)

    def simulate(self, action: str) -> str:
        # Format previous actions and results for the prompt
        formatted_history = ""
        for step in self.history:
            formatted_history += f"Action: {step['action']}\n"
            formatted_history += f"Results: {step['result']}\n\n"

        prompt = self.sim_prompt.format(
            simulation_example=self.sim_example,
            full_patient_file=self.ground_truth_diagnosis_data,
            action_history=formatted_history,
            action=action
        )
        
        result = query_gpt(prompt)
        
        # Add new action and result to history
        self.history.append({
            "action": action,
            "result": result, 
            "feedback": "",
            "feedback_comment": ""
        })
        
        return result
    
    def add_feedback(self, feedback: str, feedback_comment: str):
        if len(self.history) > 0:
            self.history[-1]["feedback"] = feedback
            self.history[-1]["feedback_comment"] = feedback_comment

def test_simulate():
    from data_loaders import randomly_sample_patient_file
    patient_file = randomly_sample_patient_file()
    simulator = Simulator(ground_truth_diagnosis_data=patient_file["context"], ground_truth_final_diagnosis=patient_file["true_diagnosis"])
    result = simulator.simulate("Physical examination of the patient's abdominal area")
    print(F"Result is: \n\n\n {result}")
    print(F"Full history is: \n\n\n {simulator.history}")

if __name__ == "__main__":
    test_simulate()