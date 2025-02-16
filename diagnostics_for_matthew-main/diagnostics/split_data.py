from pathlib import Path
import pandas as pd

def split_data_into_files(input_csv_path: str, output_dir: Path):
    """
    Split data into different files with specified percentages
    
    Percentages:
    - simulator_calibrate: 5%
    - grader_calibrate: 5%
    - diagnostic_calibrate: 5%
    - demo: 5%
    - no_help: 10%
    - generic_chatgpt_help: 10%
    - lamp_help: 10%
    - test: 50%
    """



    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Read data
    df = pd.read_csv(input_csv_path)

    # Add global PKs before splitting
    df['global_pk'] = range(len(df))
    
    # Calculate sizes
    total_rows = len(df)
    splits = {
        'simulator_calibrate': int(0.05 * total_rows),
        'grader_calibrate': int(0.05 * total_rows),
        'diagnostic_calibrate': int(0.05 * total_rows),
        'demo': int(0.05 * total_rows),
        'no_help': int(0.10 * total_rows),
        'generic_chatgpt_help': int(0.10 * total_rows),
        'lamp_help': int(0.10 * total_rows)
    }
    # Test gets the remainder to ensure we use all rows
    splits['test'] = total_rows - sum(splits.values())
    
    # Shuffle the dataframe
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Split and save
    start_idx = 0
    for name, size in splits.items():
        end_idx = start_idx + size
        subset = df.iloc[start_idx:end_idx]
        
        # Save as CSV
        output_file = output_dir / f"{name}.csv"
        subset.to_csv(output_file, index=False)
        print(f"Saved {name}.csv with {len(subset)} rows ({len(subset)/total_rows*100:.1f}%)")
        
        start_idx = end_idx

if __name__ == "__main__":
    input_path = "/Users/youngko/Downloads/case_reports_extracted_formatted.csv"
    output_dir = Path("data_splits_cleaned")
    split_data_into_files(input_path, output_dir)