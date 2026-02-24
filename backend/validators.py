"""
Data validation functions for students, programs, and colleges.
"""

import re


def validate_student(record):
    """Validate a student record dict. Returns (True, '') or (False, 'error')."""
    required = ['id', 'firstname', 'lastname', 'gender', 'year', 'program']
    for k in required:
        if not record.get(k):
            return False, f"Missing field: {k}"

    # id must match format 202x-xxxx (e.g. 2023-0001)
    if not re.match(r'^202\d-\d{4}$', record.get('id', '')):
        return False, "Student ID must follow the format 202X-XXXX (e.g. 2024-0001)"

    # names should not contain digits
    if re.search(r'\d', record.get('firstname', '')) or re.search(r'\d', record.get('lastname', '')):
        return False, "Names cannot contain numbers"

    return True, ""


def validate_program(record):
    """Validate a program record dict. Returns (True, '') or (False, 'error')."""
    required = ['code', 'name', 'college']
    for k in required:
        if not record.get(k):
            return False, f"Missing field: {k}"

    if re.search(r'\d', record.get('name', '')):
        # allow digits in codes but not in names
        return False, "Program name cannot contain numbers"

    return True, ""


def validate_college(record):
    """Validate a college record dict. Returns (True, '') or (False, 'error')."""
    required = ['code', 'name']
    for k in required:
        if not record.get(k):
            return False, f"Missing field: {k}"

    if re.search(r'\d', record.get('name', '')):
        return False, "College name cannot contain numbers"

    return True, ""
