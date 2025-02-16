from pathlib import Path
import sys
from datetime import datetime as dt
import json
import random
import pandas as pd

# Add project root to Python path to allow imports from parent directory
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from local_path import BASE_PATH

# Define diagnostics-specific paths
DIAGNOSTICS_DIR = BASE_PATH / "diagnostics"
RESULTS_DIR = DIAGNOSTICS_DIR / "results"
DATA_SPLITS_DIR = DIAGNOSTICS_DIR / "data_splits"

# Create necessary directories
RESULTS_DIR.mkdir(exist_ok=True)
DATA_SPLITS_DIR.mkdir(exist_ok=True)

# Track completed cases in memory
completed_indices = {}  # username -> mode -> set of indices

def get_user_dir(username: str) -> Path:
    """Get or create user directory"""
    user_dir = RESULTS_DIR / username
    user_dir.mkdir(exist_ok=True)
    return user_dir

def load_completed_indices(username: str) -> dict:
    """Load dict of completed indices for user, organized by mode"""
    if username in completed_indices:
        return completed_indices[username]
    
    # Try to load from local file
    completed = {}  # mode -> set of indices
    completion_file = get_user_dir(username) / "completed_indices.json"
    
    if completion_file.exists():
        with open(completion_file) as f:
            completed = {mode: set(indices) for mode, indices in json.load(f).items()}
    
    completed_indices[username] = completed
    return completed

def save_completed_case(username: str, case_data: dict, idx: int, mode: str = 'demo'):
    """Save case to user's mode-specific CSV and update completion tracking"""
    user_dir = get_user_dir(username)
    
    # Add metadata
    case_data.update({
        'username': username,
        'case_index': idx,
        'timestamp': dt.now().isoformat(),
        'mode': mode
    })
    
    # Load or create mode-specific CSV
    mode_file = user_dir / f"{mode}.csv"
    if mode_file.exists():
        df = pd.read_csv(mode_file)
    else:
        df = pd.DataFrame()
    
    # Append new row
    df = pd.concat([df, pd.DataFrame([case_data])], ignore_index=True)
    df.to_csv(mode_file, index=False)
    
    # Update completion tracking
    if username not in completed_indices:
        completed_indices[username] = {}
    if mode not in completed_indices[username]:
        completed_indices[username][mode] = set()
    completed_indices[username][mode].add(idx)
    
    # Save completion indices
    completion_file = user_dir / "completed_indices.json"
    with open(completion_file, 'w') as f:
        # Convert to regular Python types for JSON serialization
        indices_dict = {
            m: [int(x) for x in indices] 
            for m, indices in completed_indices[username].items()
        }
        json.dump(indices_dict, f)

def save_diagnosis_result(username: str, diagnosis_result: dict, idx:int, mode: str = 'demo'):
    user_dir = get_user_dir(username)
    
    # Add metadata
    diagnosis_result.update({
        'username': username,
        'case_index': idx,
        'timestamp': dt.now().isoformat(),
        'mode': mode
    })
    
    # Load or create mode-specific CSV
    mode_file = user_dir / f"{mode}_diagnosis.csv"
    if mode_file.exists():
        df = pd.read_csv(mode_file)
    else:
        df = pd.DataFrame()
    
    # Append new row
    df = pd.concat([df, pd.DataFrame([diagnosis_result])], ignore_index=True)
    df.to_csv(mode_file, index=False)


def randomly_sample_patient_file(mode: str = 'demo', username: str = None) -> dict:
    """
    Randomly sample a patient file from a specific mode's dataset
    
    Args:
        mode (str): Which dataset to sample from ('demo', 'no_help', 'lamp_help', etc.)
        username (str): Username of current user to track completed cases
        
    Returns:
        dict: Patient case data including index, context, diagnoses, and grade
        
    Raises:
        ValueError: If no more unseen cases are available for non-demo modes
    """
    # Load the appropriate dataset based on mode
    file_path = DATA_SPLITS_DIR / f"{mode}.csv"
    print(f"Loading from: {file_path}")
    
    if not file_path.exists():
        raise ValueError(f"No dataset found for mode: {mode}")
        
    df = pd.read_csv(file_path)
    
    # Add index if it doesn't exist
    if 'global_pk' not in df.columns:
        df['global_pk'] = range(len(df))
        df.to_csv(file_path, index=False)  # Save back to file with the new column
    
    # For non-demo modes, check if all cases have been completed
    if mode != 'demo' and username:
        completed = load_completed_indices(username)
        completed_for_mode = completed.get(mode, set())
        available_indices = set(range(len(df))) - completed_for_mode
        
        if not available_indices:
            raise ValueError(f"You have completed all available cases for mode: {mode}")
            
        # Sample only from available (unselected) cases
        sampled_row = df.iloc[random.choice(list(available_indices))]
    else:
        # For demo mode, sample from all cases
        sampled_row = df.sample(n=1).iloc[0]
    
    return {
        "index": sampled_row.name,
        "context": sampled_row["context"],
        "true_diagnosis": sampled_row["diagnosis"],
        "case_id": sampled_row["case_id"],
        "common_uncommon": sampled_row["COMMON_UNCOMMON"]
    }

def sample_new_patient_file(username: str, mode: str = 'demo'):
    """Sample an unseen patient file from the appropriate mode's dataset"""
    completed = load_completed_indices(username)
    completed_for_mode = completed.get(mode, set())
    
    # Load the appropriate dataset based on mode
    file_path = DATA_SPLITS_DIR / f"{mode}.csv"
    df = pd.read_csv(file_path)
    
    # Add index if it doesn't exist
    if 'global_pk' not in df.columns:
        df['global_pk'] = range(len(df))
        df.to_csv(file_path, index=False)
    
    # Filter out completed indices for this mode
    available_indices = set(range(len(df))) - completed_for_mode
    
    # For demo mode, reset completed cases if we've seen everything
    if not available_indices and mode == 'demo':
        available_indices = set(range(len(df)))
        completed_indices[username][mode] = set()  # Reset completed cases for this mode
        # Save the reset state
        completion_file = get_user_dir(username) / "completed_indices.json"
        with open(completion_file, 'w') as f:
            indices_dict = {
                m: [int(x) for x in indices] 
                for m, indices in completed_indices[username].items()
            }
            json.dump(indices_dict, f)
    elif not available_indices:
        raise ValueError(f"No more unseen patient files available for mode: {mode}!")
    
    # Sample a random index from available ones
    idx = random.choice(list(available_indices))
    row = df.iloc[idx]
    
    return {
        "index": idx,
        "context": row["context"],
        "true_diagnosis": row["diagnosis"],
        "previous_llm_diagnosis": row["generated_diagnosis"],
        "true_grade": row["evaluation"],
        "case_id": row["case_id"],
        "common_uncommon": row["COMMON_UNCOMMON"]
    }

def get_user_results(username: str, mode: str = None) -> pd.DataFrame:
    """Get results for a user, optionally filtered by mode"""
    user_dir = get_user_dir(username)
    
    if mode:
        # Return specific mode results
        mode_file = user_dir / f"{mode}.csv"
        return pd.read_csv(mode_file) if mode_file.exists() else pd.DataFrame()
    else:
        # Combine all mode results
        dfs = []
        for csv_file in user_dir.glob("*.csv"):
            if csv_file.stem != "completed_indices":  # Skip the completion tracking file
                df = pd.read_csv(csv_file)
                dfs.append(df)
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def get_all_results() -> pd.DataFrame:
    """Combine results from all users"""
    dfs = []
    for user_dir in RESULTS_DIR.glob("*"):
        if user_dir.is_dir():
            user_df = get_user_results(user_dir.name)
            if not user_df.empty:
                dfs.append(user_df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

class PatientFileLoader:
    def __init__(self, mode: str = 'demo'):
        self.file_path = DATA_SPLITS_DIR / f"{mode}.csv"
        self.df = pd.read_csv(self.file_path)
        
        # Add index if it doesn't exist
        if 'global_pk' not in self.df.columns:
            self.df['global_pk'] = range(len(self.df))
            self.df.to_csv(self.file_path, index=False)
            
        self.current_index = 0
        self.total_records = len(self.df)
    
    def __next__(self):
        if self.current_index >= self.total_records:
            raise StopIteration
        
        row = self.df.iloc[self.current_index]
        self.current_index += 1
        
        return {
            "index": self.current_index - 1,  # Use the actual index
            "context": row["context"],
            "true_diagnosis": row["diagnosis"],
            "previous_llm_diagnosis": row["generated_diagnosis"],
            "true_grade": row["evaluation"],
            "case_id": row["case_id"],
            "common_uncommon": row["COMMON_UNCOMMON"]
        }

def test_patient_file_loader():
    loader = PatientFileLoader()
    
    # Test iteration through all records
    count = 0
    for patient in loader:
        assert isinstance(patient, dict)
        assert "context" in patient
        assert "true_diagnosis" in patient
        assert isinstance(patient["context"], (str, type(None)))
        assert isinstance(patient["true_diagnosis"], (str, type(None)))
        count += 1
    
    # Verify we processed all records
    assert count == loader.total_records, f"Expected {loader.total_records} records, but processed {count}"
    
    print(f"PatientFileLoader tests passed! Validated all {count} records.")

def test_randomly_sample_patient_file():
    # Call the function
    result = randomly_sample_patient_file()
    print(f"Patient file is: {result}")
    
    # Check that the result is a dictionary
    assert isinstance(result, dict)
    
    # Check that it has the expected keys
    assert "context" in result
    assert "true_diagnosis" in result
    
    # Check that the values are strings (or None)
    assert isinstance(result["context"], (str, type(None)))
    assert isinstance(result["true_diagnosis"], (str, type(None)))
    print("Test passed!")

if __name__ == "__main__":
    test_randomly_sample_patient_file()
    test_patient_file_loader()