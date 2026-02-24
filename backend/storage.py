"""
CSV storage and file operations.
"""

import csv
import os
import sys
import shutil
from config import FILES, FIELDS, resource_path


def init_files():
    """Initialize CSV files with headers if they don't exist.
    
    When running as a PyInstaller bundle, copies bundled CSV seed files
    to the writable data directory on first run.
    """
    for key, filepath in FILES.items():
        if not os.path.exists(filepath):
            # If running frozen, try to copy the bundled seed CSV first
            if getattr(sys, 'frozen', False):
                bundled = resource_path(os.path.basename(filepath))
                if os.path.exists(bundled):
                    shutil.copy2(bundled, filepath)
                    continue
            # Otherwise create empty CSV with headers
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS[key])
                writer.writeheader()


def load_csv(key):
    """Load data from CSV file."""
    if not os.path.exists(FILES[key]):
        init_files()
    with open(FILES[key], 'r', newline='') as f:
        return list(csv.DictReader(f))


def save_csv(key, data):
    """Save data to CSV file."""
    with open(FILES[key], 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS[key])
        writer.writeheader()
        try:
            writer.writerows(data)
        except Exception:
            # Fail-safe: write rows that are dict-like only
            safe_rows = []
            for r in data:
                if isinstance(r, dict):
                    safe_rows.append(r)
            writer.writerows(safe_rows)


def create_backups():
    """Create backup of all CSV files (placeholder for future implementation)."""
    pass
