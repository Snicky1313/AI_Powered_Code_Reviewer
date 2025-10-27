"""
Storage module for saving and loading submissions.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


# Directory for storing submissions
STORAGE_DIR = Path(__file__).parent / "data" / "submissions"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_submission(submission_id: str, submission_data: Dict[str, Any]) -> bool:
    """
    Save submission data to disk.
    
    Args:
        submission_id: Unique identifier for the submission
        submission_data: Dictionary containing submission data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = STORAGE_DIR / f"{submission_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(submission_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving submission {submission_id}: {e}")
        return False


def load_submission(submission_id: str) -> Optional[Dict[str, Any]]:
    """
    Load submission data from disk.
    
    Args:
        submission_id: Unique identifier for the submission
        
    Returns:
        Dictionary containing submission data, or None if not found
    """
    try:
        file_path = STORAGE_DIR / f"{submission_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading submission {submission_id}: {e}")
        return None


def list_submissions() -> list:
    """
    List all submission IDs that have been saved.
    
    Returns:
        List of submission IDs
    """
    try:
        return [f.stem for f in STORAGE_DIR.glob("*.json")]
    except Exception:
        return []


def delete_submission(submission_id: str) -> bool:
    """
    Delete a submission from disk.
    
    Args:
        submission_id: Unique identifier for the submission
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = STORAGE_DIR / f"{submission_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting submission {submission_id}: {e}")
        return False

