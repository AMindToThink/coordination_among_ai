from prompts import llm_grader_prompt
from llm_utils import query_gpt
from data_loaders import PatientFileLoader, randomly_sample_patient_file

def grade_diagnosis(llm_diagnosis: str, ground_truth_diagnosis: str, llm=query_gpt) -> float:
    """
    Grade an LLM's diagnosis against a ground truth diagnosis using another LLM as a grader.
    
    Args:
        llm_diagnosis: The diagnosis provided by the LLM being evaluated
        ground_truth_diagnosis: The correct diagnosis to compare against
        llm: The LLM instance to use as a grader
    
    Returns:
        float: 1.0 if correct, 0.0 if incorrect
    """
    # Format the prompt with the diagnoses
    formatted_prompt = llm_grader_prompt.format(
        llm_diagnosis=llm_diagnosis,
        ground_truth_diagnosis=ground_truth_diagnosis
    )
    
    # Get the grader's response
    response = llm(formatted_prompt)
    print(response)
    
    # Extract the action score using regex
    import re
    match = re.search(r"Action:\s*(0\.0|1\.0)", response)
    if not match:
        raise ValueError("Could not find valid grade (0.0 or 1.0) in LLM response")
        
    # Convert the matched score to float
    final_grade = float(match.group(1))
    return final_grade, response



def grade_diagnosis_top_k(llm_diagnosis_list, ground_truth_diagnosis: str, llm=query_gpt) -> float:
    """
    Grade an LLM's diagnosis against a ground truth diagnosis using another LLM as a grader.
    
    Args:
        llm_diagnosis: The diagnosis provided by the LLM being evaluated
        ground_truth_diagnosis: The correct diagnosis to compare against
        llm: The LLM instance to use as a grader
    
    Returns:
        float: 1.0 if correct, 0.0 if incorrect
    """
    # Format the prompt with the diagnoses
    found_correct = 0.0
    all_rationales = []
    for llm_diagnosis in llm_diagnosis_list:
        formatted_prompt = llm_grader_prompt.format(
            llm_diagnosis=llm_diagnosis,
            ground_truth_diagnosis=ground_truth_diagnosis
        )
        
        # Get the grader's response
        response = llm(formatted_prompt)
        print(response)
        
        # Extract the action score using regex
        import re
        match = re.search(r"Action:\s*(0\.0|1\.0)", response)
        if not match:
            raise ValueError("Could not find valid grade (0.0 or 1.0) in LLM response")
            
        # Convert the matched score to float
        final_grade = float(match.group(1))
        all_rationales.append({"final_grade": final_grade, "rationale": response})
        if final_grade == 1.0:
            found_correct = 1.0
    return found_correct, all_rationales



def evaluate_llm_grading():
    from itertools import islice
    import pandas as pd  # Add import at top
    
    patient_loader = PatientFileLoader()
    incorrect_count = 0
    results = []  # List to store results
    
    # Limit to first K entries using islice
    entries_to_grade = 30
    for patient_file in islice(patient_loader, entries_to_grade):
        grade, thought = grade_diagnosis(patient_file["previous_llm_diagnosis"], patient_file["true_diagnosis"])
        true_grade = patient_file["true_grade"]
        if true_grade == 'INCORRECT':
            true_grade = 0.0
        else:
            true_grade = 1.0
        
        # Store results
        results.append({
            'previous_llm_diagnosis': patient_file["previous_llm_diagnosis"],
            'true_diagnosis': patient_file["true_diagnosis"],
            'Dennis Grade': true_grade,
            'llm automatic grade': grade,
            'llm rationale': thought
        })
        
        if grade != true_grade:
            incorrect_count += 1
            print(f"Incorrect: {patient_file['previous_llm_diagnosis'], patient_file['true_diagnosis']}")
    
    # Create and save DataFrame
    df = pd.DataFrame(results)
    df.to_csv('grading_results.csv', index=False)
    
    success_rate = 1 - (incorrect_count / entries_to_grade)
    print(f"\n\n\nFinal success rate: {success_rate}\n\n\n")
    return success_rate

import asyncio
from typing import List
from itertools import islice

async def grade_diagnosis_async(llm_diagnosis: str, ground_truth_diagnosis: str) -> float:
    """Async version of grade_diagnosis"""
    formatted_prompt = llm_grader_prompt.format(
        llm_diagnosis=llm_diagnosis,
        ground_truth_diagnosis=ground_truth_diagnosis
    )
    
    # Use query_gpt directly
    response = query_gpt(formatted_prompt)
    
    import re
    match = re.search(r"Action:\s*(0\.0|1\.0)", response)
    if not match:
        raise ValueError("Could not find valid grade (0.0 or 1.0) in LLM response")
    return float(match.group(1))

async def process_batch(batch: List[dict]) -> List[float]:
    """Process a batch of patient files concurrently"""
    tasks = [
        grade_diagnosis_async(
            patient_file["previous_llm_diagnosis"],
            patient_file["true_diagnosis"]
        )
        for patient_file in batch
    ]
    return await asyncio.gather(*tasks)

async def evaluate_llm_grading_async():
    BATCH_SIZE = 30
    incorrect_count = 0
    patient_loader = PatientFileLoader()
    
    while True:
        batch = list(islice(patient_loader, BATCH_SIZE))
        if not batch:
            break
            
        grades = await process_batch(batch)
        
        for patient_file, grade in zip(batch, grades):
            true_grade = 1.0 if patient_file["true_grade"] != 'INCORRECT' else 0.0
            if grade != true_grade:
                incorrect_count += 1
    
    success_rate = 1 - (incorrect_count / patient_loader.get_total_records())
    print(f"\n\n\nFinal success rate: {success_rate}\n\n\n")
    return success_rate

# Entry point
def run_evaluation():
    return asyncio.run(evaluate_llm_grading_async())

def test_grade_diagnosis():
    patient_file = randomly_sample_patient_file()
    llm_diagnosis = patient_file["previous_llm_diagnosis"]
    ground_truth_diagnosis = patient_file["true_diagnosis"]
    grade, thought = grade_diagnosis(llm_diagnosis, ground_truth_diagnosis)
    print(f"Grade: {grade}")


if __name__ == "__main__":
    #test_grade_diagnosis()
    evaluate_llm_grading()