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
            NvKEvaluation.main(run_config)

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
    