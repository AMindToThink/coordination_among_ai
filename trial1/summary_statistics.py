import os
import json
import numpy as np
import scipy.stats as stats
import glob
import argparse

def calculate_statistics(directory_path):
    """
    Calculate mean accuracy and 95% confidence interval for evaluation results in a directory.
    
    Args:
        directory_path: Path to the directory containing evaluation JSON files
    
    Returns:
        tuple: (mean_accuracy, confidence_interval)
    """
    # Find all evaluation JSON files in the directory
    file_pattern = os.path.join(directory_path, "evaluation_*.json")
    evaluation_files = glob.glob(file_pattern)
    
    if not evaluation_files:
        print(f"No evaluation files found in {directory_path}")
        return None, None
    
    # Extract accuracies from each file
    accuracies = []
    for file_path in evaluation_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'evaluation' in data and 'accuracy' in data['evaluation']:
                    accuracies.append(data['evaluation']['accuracy'])
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    if not accuracies:
        print("No valid accuracy data found")
        return None, None
    
    # Calculate statistics
    mean_accuracy = np.mean(accuracies)
    std_dev = np.std(accuracies, ddof=1)  # Using n-1 for sample standard deviation
    n = len(accuracies)
    
    # Calculate 95% confidence interval using t-distribution
    t_value = stats.t.ppf(0.975, n-1)  # 95% CI (two-tailed)
    margin_of_error = t_value * (std_dev / np.sqrt(n))
    confidence_interval = (mean_accuracy - margin_of_error, mean_accuracy + margin_of_error)
    
    return mean_accuracy, confidence_interval

def main(directory):
    mean_accuracy, confidence_interval = calculate_statistics(directory)
    
    if mean_accuracy is not None:
        print(f"Mean Accuracy: {mean_accuracy:.4f}")
        print(f"95% Confidence Interval: ({confidence_interval[0]:.4f}, {confidence_interval[1]:.4f})")
        print(f"Sample Size: {len(glob.glob(os.path.join(directory, 'evaluation_*.json')))}")
    else:
        print("Failed to calculate statistics")

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Calculate accuracy statistics from evaluation files')
    parser.add_argument('directory', type=str, 
                        help='Directory containing evaluation JSON files (e.g., "./results/model_counts/triple_sabotage_no_colab")')
    
    args = parser.parse_args()
    
    main(args.directory)
