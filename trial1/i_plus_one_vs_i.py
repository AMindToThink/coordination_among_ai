import argparse
import json
import os
import time
from datetime import datetime
import NvKEvaluation

def i_plus_one_vs_i(config_path):
    # Load configuration from JSON file
    with open(config_path, 'r') as f:
        base_config = json.load(f)
    
    # Extract parameters from config
    max_i = base_config["max_i"]
    iterations = base_config["iterations"]
    model = base_config["model"]
    
    # Create output directory based on config filename
    config_filename = os.path.basename(config_path)
    config_name = os.path.splitext(config_filename)[0]
    output_dir = os.path.join("./results/i_plus_one_vs_i", config_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create subfolders for each i value upfront
    for i in range(0, max_i + 1):
        i_output_dir = os.path.join(output_dir, f"i_{i}")
        os.makedirs(i_output_dir, exist_ok=True)
    
    # Run evaluations for each iteration and i
    for iteration in range(iterations):
        for i in range(0, max_i + 1):
            # Get the i-specific output directory
            i_output_dir = os.path.join(output_dir, f"i_{i}")
            
            # Check if this run has already been completed successfully
            completed = False
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Look for existing evaluation files in the directory
            for filename in os.listdir(i_output_dir):
                if filename.endswith('.json') and f"i{i}_iter{iteration}" in filename:
                    try:
                        with open(os.path.join(i_output_dir, filename), 'r') as f:
                            existing_result = json.load(f)
                        
                        # Check if the evaluation has valid answers (no nulls)
                        if ('evaluation' in existing_result and 
                            'given_answers' in existing_result['evaluation'] and 
                            None not in existing_result['evaluation']['given_answers']):
                            print(f"Found complete evaluation for iteration {iteration}, i={i}. Skipping.")
                            completed = True
                            break
                    except (json.JSONDecodeError, FileNotFoundError):
                        # If file is corrupted or can't be read, we'll redo this run
                        pass
            
            if completed:
                continue
                
            # Create config for this run
            run_config = {
                "model": model,
                "collaborators": i + 1,  # i+1 collaborators
                "saboteurs": i,          # i saboteurs
                "rate_limit": base_config.get("rate_limit", 1.0),
                "turns": base_config["turns"],
                "output_dir": i_output_dir,  # Use the i-specific subfolder
                "log_file": f"i{i}_iter{iteration}_{config_name}_{{filename}}_chat_logs.txt",
                "end_condition": base_config["end_condition"],
                "randomize_order": True,
                "max_tokens": base_config.get("max_tokens", None)
            }
            
            # Run evaluation with this config
            print(f"Running iteration {iteration}, i={i} ({i+1} collaborators vs {i} saboteurs)")
            
            # Run and check for null answers
            max_retries = 3
            retry_count = 0
            success = False
            
            while not success and retry_count < max_retries:
                result = NvKEvaluation.main(run_config)
                
                # Check if result contains null answers
                if result and 'evaluation' in result and 'given_answers' in result['evaluation']:
                    null_count = result['evaluation']['given_answers'].count(None)
                    valid_count = len(result['evaluation']['given_answers']) - null_count
                    
                    if null_count > 0:
                        print(f"Found {null_count} null answers out of {len(result['evaluation']['given_answers'])}. Retrying...")
                        retry_count += 1
                        # Wait before retrying to avoid rate limits
                        time.sleep(base_config.get("retry_delay", 60))
                    else:
                        print(f"All {valid_count} answers are valid. Moving to next configuration.")
                        success = True
                else:
                    print("Couldn't verify answers. Retrying...")
                    retry_count += 1
                    time.sleep(base_config.get("retry_delay", 60))
            
            if not success:
                print(f"Warning: Maximum retries reached for iteration {iteration}, i={i}. Moving to next configuration.")

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Find how accuracy decreases as the number of saboteurs increases.')
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to JSON configuration file"
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Run the evaluation
    i_plus_one_vs_i(args.config)
    