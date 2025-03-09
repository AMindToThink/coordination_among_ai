import os
import json
import matplotlib.pyplot as plt
import re
import sys

def extract_i_from_dirname(dirname):
    """Extract the i value from a directory name like 'i=X'"""
    match = re.search(r'i_(\d+)', dirname)
    if match:
        return int(match.group(1))
    return None

def find_evaluation_files(base_dir):
    """Find all evaluation JSON files in the directory structure"""
    evaluation_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith('evaluation_') and file.endswith('.json'):
                i_value = extract_i_from_dirname(os.path.basename(root))
                if i_value is not None:
                    evaluation_files.append((i_value, os.path.join(root, file)))
    
    return evaluation_files

def extract_accuracy(file_path):
    """Extract accuracy from an evaluation file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if 'evaluation' in data and 'accuracy' in data['evaluation']:
                return data['evaluation']['accuracy']
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python i_plus_one_vs_i_viewer.py <base_directory>")
        return
    
    base_dir = sys.argv[1]
    evaluation_files = find_evaluation_files(base_dir)
    
    if not evaluation_files:
        print(f"No evaluation files found in directory structure: {base_dir}")
        return
    
    # Sort by i value
    evaluation_files.sort()
    
    i_values = []
    accuracies = []
    
    for i_value, file_path in evaluation_files:
        accuracy = extract_accuracy(file_path)
        if accuracy is not None:
            i_values.append(i_value)
            accuracies.append(accuracy)
            print(f"i={i_value}, accuracy={accuracy:.4f}, file={os.path.basename(file_path)}")
    
    if not accuracies:
        print("No accuracy data found in the evaluation files")
        return
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(i_values, accuracies, 'o-', linewidth=2, markersize=8, label='Team Accuracy')
    plt.xlabel('i (Number of Saboteurs)', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Accuracy vs. Number of Saboteurs (i+1 collaborators vs i saboteurs)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add a horizontal line at y=0.25 (random guessing for 4 options)
    plt.axhline(y=0.25, color='r', linestyle='--', alpha=0.5, label='Random Guessing (0.25)')
    
    # Set y-axis limits with some padding
    plt.ylim([0, 1.05])
    
    # Add data points labels
    for i, acc in zip(i_values, accuracies):
        plt.annotate(f'{acc:.4f}', 
                     xy=(i, acc), 
                     xytext=(0, 10),
                     textcoords='offset points',
                     ha='center',
                     fontsize=9)
    
    plt.legend()
    plt.tight_layout()
    
    # Save the figure
    output_path = os.path.join(base_dir, 'i_plus_one_vs_i_accuracy.png')
    plt.savefig(output_path)
    print(f"Graph saved to: {output_path}")
    
    plt.show()

if __name__ == "__main__":
    main()
