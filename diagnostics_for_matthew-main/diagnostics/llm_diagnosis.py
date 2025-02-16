import json
from typing import Dict, Any
from prompts import llm_possible_diseases_prompt, llm_possible_diseases_prompt_thought_action, llm_next_action_prompt, claude_suggested_diagnosis_prompt
from llm_utils import query_gpt
from simulate import Simulator
from evaluate_llm_grading import grade_diagnosis, grade_diagnosis_top_k

def get_possible_diagnoses(medical_history: str) -> Dict[str, Any]:
    """
    Get possible diagnoses from medical history using LLM with standard JSON response.
    
    Args:
        medical_history (str): The current medical history/report
        
    Returns:
        Dict containing most likely diseases and rare possibilities
    """
    formatted_prompt = llm_possible_diseases_prompt.format(
        medical_report=medical_history
    )
    
    response = query_gpt(formatted_prompt)
    print(response)
    
    try:
        # Clean the response by removing markdown code blocks if present
        cleaned_response = response
        if "```json" in response:
            cleaned_response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            cleaned_response = response.split("```", 1)[1].rsplit("```", 1)[0].strip()
        
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        print(f"Raw response: {response}")
        return {
            "most_likely_diseases": [],
            "rare_possibilities": []
        }
    

def get_possible_diagnoses_baseline(medical_history):
    """
    A baseline implementation for getting possible diagnoses from medical history.
    Uses the simple llm_possible_diseases prompt without structured output.
    
    Args:
        medical_history (str): The patient's medical history/report
        
    Returns:
        str: Raw LLM response listing possible diagnoses
    """
    from prompts import llm_possible_diseases
    
    # Format the prompt with the medical history
    formatted_prompt = llm_possible_diseases.format(
        medical_report=medical_history
    )
    
    # Get response from LLM (assuming you have a function to do this)
    response = query_gpt(formatted_prompt)
    
    return response

def get_possible_diagnoses_with_thought_action(medical_history: str) -> Dict[str, Any]:
    """
    Get possible diagnoses from medical history using LLM with thought-action format.
    
    Args:
        medical_history (str): The current medical history/report
        
    Returns:
        Dict containing most likely diseases and rare possibilities
    """
    claude = False
    if claude is True:
        formatted_prompt = claude_suggested_diagnosis_prompt.format(
            medical_report=medical_history
        )
        response = query_gpt(formatted_prompt)
        print(response)
    if claude is False:
        formatted_prompt = llm_possible_diseases_prompt_thought_action.format(
            medical_report=medical_history
        )
        response = query_gpt(formatted_prompt)
        print(response)
    
    try:
        # Clean the response by removing markdown code blocks if present
        action_part = response.split("Action:")[1].strip()
        cleaned_response = action_part
        if "```json" in action_part:
            cleaned_response = action_part.split("```json")[1].split("```")[0].strip()
        elif "```" in action_part:
            cleaned_response = action_part.split("```", 1)[1].rsplit("```", 1)[0].strip()
        #print(f"\n\n\n\nCleaned response: {cleaned_response}\n\n\n\n")
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Raw response: {response}")
        return {
            "most_likely_diseases": [],
            "rare_possibilities": []
        }


def get_next_action(simulator, possible_diagnoses):
    medical_history = simulator.get_history()
    rsp = llm_next_action_prompt.format(medical_history=medical_history, possible_diagnoses=possible_diagnoses)
    next_action = query_gpt(rsp)
    return next_action

def main_llm_diagnosis_loop(patient_file):
    simulator = Simulator(ground_truth_final_diagnosis=patient_file['true_diagnosis'], ground_truth_diagnosis_data=patient_file['context'])
    possible_diagnoses = get_possible_diagnoses(simulator.get_history)
    for i in range(6):
        next_action = get_next_action(simulator, possible_diagnoses)
        print(f"\n\n\nNext action: {next_action}\n\n\n")
        if "Diagnosis:" in next_action:
            final_diagnosis = next_action.split("Diagnosis:")[1].strip()
            print(f"Final diagnosis: {final_diagnosis}")
            return possible_diagnoses, final_diagnosis, i
        else:
            if "Next Action:" in next_action:
                next_action = next_action.split("Next Action:")[1].strip()
            #print(f"Taking action: {next_action}")
            simulator.simulate(next_action)
            possible_diagnoses = get_possible_diagnoses(simulator.get_history())
    # take the most likely disease as the diagnosis
    return possible_diagnoses, possible_diagnoses['most_likely_diseases'][0], i


def main_llm_final_diagnosis_only(patient_file, thought_action=False):
    simulator = Simulator(ground_truth_final_diagnosis=patient_file['true_diagnosis'], ground_truth_diagnosis_data=patient_file['context'])
    simulator.history = None
    simulator.history = []
    lines = patient_file['context'].split('\n')
    for line in lines:
        if ':' in line:
            action, result = line.split(':', 1)
            simulator.history.append({
                "action": action.strip(),
                "result": result.strip()
            })
    if thought_action:
        possible_diagnoses = get_possible_diagnoses_with_thought_action(simulator.get_history())
    else:
        possible_diagnoses = get_possible_diagnoses(simulator.get_history())
    most_likely_disease = possible_diagnoses.get('most_likely_diseases', [])
    if not most_likely_disease:
        return possible_diagnoses, "none", 0
    return possible_diagnoses, most_likely_disease[0], 0


def main(top_k_grading=False, use_thought_action=False):
    from data_loaders import PatientFileLoader
    from itertools import islice
    correct_count = 0
    incorrect_count = 0
    for patient_file in islice(PatientFileLoader(), 10):
        #possible_diagnoses, final_diagnosis, i = main_llm_diagnosis_loop(patient_file)
        possible_diagnoses, final_diagnosis, i = main_llm_final_diagnosis_only(patient_file, thought_action=use_thought_action)
        print(f"Possible diagnoses: {possible_diagnoses}")
        print(f"Final diagnosis: {final_diagnosis}")
        print(f"Iteration: {i}")
        if top_k_grading:
            grade, rationale = grade_diagnosis_top_k(llm_diagnosis_list=possible_diagnoses['most_likely_diseases'], ground_truth_diagnosis=patient_file['true_diagnosis'])
        else:
            grade, rationale = grade_diagnosis(llm_diagnosis=final_diagnosis, ground_truth_diagnosis=patient_file['true_diagnosis'])
        if grade == 1.0:
            correct_count += 1
        else:
            incorrect_count += 1
        print(f"correct rate: {correct_count / (correct_count + incorrect_count)}")


def test_main_diagnosis_loop():
    from data_loaders import randomly_sample_patient_file
    patient_file = randomly_sample_patient_file()
    
    #possible_diagnoses, final_diagnosis, iterations = main_llm_diagnosis_loop(patient_file)
    possible_diagnoses, final_diagnosis, iterations = main_llm_final_diagnosis_only(patient_file)
    
    print(f"Test Results:\n\n\n")
    print(f"Possible diagnoses: {possible_diagnoses}")
    print(f"Final diagnosis: {final_diagnosis}")
    print(f"Number of iterations: {iterations}")
    print(f"Ground truth diagnosis: {patient_file['true_diagnosis']}")

    #grade = grade_diagnosis(llm_diagnosis=possible_diagnoses['most_likely_diseases'][0], ground_truth_diagnosis=patient_file['true_diagnosis'])
    grade, rationale = grade_diagnosis_top_k(llm_diagnosis_list=possible_diagnoses['most_likely_diseases'], ground_truth_diagnosis=patient_file['true_diagnosis'])
    print(f"Grade: {grade}")
    #print(f"Rationale: {rationale}")

def test_get_possible_diagnoses():
    from data_loaders import randomly_sample_patient_file
    patient_file = randomly_sample_patient_file()
    simulator = Simulator(patient_file["context"], ground_truth_final_diagnosis=patient_file['true_diagnosis'])
    result = simulator.simulate("Physical examination of the patient's abdominal area")
    possible_diagnoses = get_possible_diagnoses(simulator.get_history())
    print(F"Possible diagnoses: {possible_diagnoses}")
    print(F"Actual Ground Truth: {patient_file['true_diagnosis']}")
    grade, rationale = grade_diagnosis(llm_diagnosis=possible_diagnoses['most_likely_diseases'][0], ground_truth_diagnosis=patient_file['true_diagnosis'])
    print(f"Grade: {grade}")
    #print(f"Rationale: {rationale}")

if __name__ == "__main__":
    #test_main_diagnosis_loop()
    main(top_k_grading=True, use_thought_action=True)