"""
Data handling and CSV operations for EduManage SIS
"""

import csv
import os
from config import FILES, FIELDS
import re

def init_files():
    """Initialize CSV files with headers if they don't exist."""
    for key, filename in FILES.items():
        if not os.path.exists(filename):
            with open(filename, 'w', newline='') as f:
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


def validate_student(record):
    """Validate a student record dict. Returns (True, '') or (False, 'error')."""
    required = ['id', 'firstname', 'lastname', 'gender', 'year', 'program']
    for k in required:
        if not record.get(k):
            return False, f"Missing field: {k}"

    # ID must not contain letters
    if re.search(r'[A-Za-z]', record.get('id', '')):
        return False, "Student ID cannot contain letters"

    # Names should not contain digits
    if re.search(r'\d', record.get('firstname', '')) or re.search(r'\d', record.get('lastname', '')):
        return False, "Names cannot contain numbers"

    return True, ""


def validate_program(record):
    required = ['code', 'name', 'college']
    for k in required:
        if not record.get(k):
            return False, f"Missing field: {k}"

    if re.search(r'\d', record.get('name', '')):
        # allow digits in codes but not in names
        return False, "Program name cannot contain numbers"

    return True, ""


def validate_college(record):
    required = ['code', 'name']
    for k in required:
        if not record.get(k):
            return False, f"Missing field: {k}"

    if re.search(r'\d', record.get('name', '')):
        return False, "College name cannot contain numbers"

    return True, ""

def create_backups():
    """Create backup of all CSV files (placeholder for future implementation)."""
    pass
