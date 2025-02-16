import os
import time
import boto3
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from local_path import BASE_PATH

RESULTS_DIR = BASE_PATH / "diagnostics" / "results"
S3_BUCKET = "your-bucket-name"  # Replace with your S3 bucket name
BACKUP_PREFIX = "results_backups/"

def has_recent_changes(directory, hours=24):
    """Check if directory has been modified in the last n hours."""
    now = time.time()
    cutoff = now - (hours * 3600)
    
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.getmtime(filepath) > cutoff:
                return True
    return False

def create_backup(source_dir):
    """Create a timestamped tar.gz backup of the directory."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"results_backup_{timestamp}.tar.gz"
    backup_path = Path("/tmp") / backup_filename
    
    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    
    return backup_path

def upload_to_s3(file_path, bucket, prefix):
    """Upload file to S3."""
    s3_client = boto3.client('s3')
    s3_key = prefix + os.path.basename(file_path)
    
    try:
        s3_client.upload_file(str(file_path), bucket, s3_key)
        print(f"Successfully uploaded backup to s3://{bucket}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload to S3: {e}")

def main():
    if not has_recent_changes(RESULTS_DIR):
        print("No recent changes in results directory. Skipping backup.")
        return
    
    print("Creating backup...")
    backup_path = create_backup(RESULTS_DIR)
    
    print("Uploading to S3...")
    upload_to_s3(backup_path, S3_BUCKET, BACKUP_PREFIX)
    
    # Clean up local backup file
    backup_path.unlink()
    print("Backup complete!")

if __name__ == "__main__":
    main()