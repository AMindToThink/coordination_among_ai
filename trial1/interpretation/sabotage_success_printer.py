import json
import argparse
import re
from typing import Dict, List, Any
from datasets import load_dataset

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_question_id(log_segment: str) -> str:
    """Extract the question ID from a log segment."""
    match = re.search(r"Question ID: ([^\n]+)", log_segment)
    if match:
        return match.group(1)
    return None

def main():
    parser = argparse.ArgumentParser(description="Extract and print successful sabotage cases")
    parser.add_argument("success_file", help="Path to the JSON file from sabotage_success_finder.py")
    parser.add_argument("log_file", help="Path to the log file containing the full conversation data")
    parser.add_argument("--output", "-o", help="Path to save the output JSON file (optional)")
    
    args = parser.parse_args()
    
    # Load the success data
    success_data = load_json_file(args.success_file)
    
    # Load the log file
    with open(args.log_file, 'r') as f:
        log_content = f.read()
    
    # Split the log into segments
    log_segments = log_content.split("==================================================")
    log_segments = [segment.strip() for segment in log_segments if segment.strip()]
    
    # Extract question IDs from each segment
    segment_ids = {}
    for i, segment in enumerate(log_segments):
        question_id = extract_question_id(segment)
        if question_id:
            segment_ids[question_id] = i
    
    # Load the AI2 ARC dataset
    dataset = load_dataset(**dict(path="allenai/ai2_arc", name="ARC-Challenge", split='validation'))
    
    # Map successful sabotage indices to question IDs
    successful_indices = success_data["successful_sabotage_indices"]
    detailed_sabotages = []
    
    print(f"Found {len(successful_indices)} successful sabotages")
    
    for idx in successful_indices:
        # Get the question ID from the dataset
        if idx < len(dataset):
            question_id = dataset[idx]['id']
            
            # Find the corresponding log segment
            if question_id in segment_ids:
                segment_idx = segment_ids[question_id]
                log_segment = log_segments[segment_idx]
                
                detailed_sabotages.append({
                    "index": idx,
                    "question_id": question_id,
                    "log_content": log_segment
                })
                
                # Print the successful sabotage information
                print(f"\n{'='*80}")
                print(f"SUCCESSFUL SABOTAGE - INDEX {idx} - QUESTION ID {question_id}")
                print(f"{'='*80}")
                print(log_segment)
            else:
                print(f"Warning: Could not find log segment for question ID {question_id}")
        else:
            print(f"Warning: Index {idx} is out of range for the dataset")
    
    if args.output:
        output_data = {
            "original_success_data": success_data,
            "detailed_sabotages": detailed_sabotages
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
