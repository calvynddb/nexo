"""
Configuration and Constants for EduManage SIS
"""

import customtkinter as ctk

# --- Theme Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- Fonts ---
FONT_MAIN = ("Segoe UI Variable", 13)
FONT_BOLD = ("Segoe UI Variable", 13, "bold")

# --- Colors ---
BG_COLOR = "#18181a"
PANEL_COLOR = "#222225"
ACCENT_COLOR = "#2babbd"
TEXT_MUTED = "#8a8a8e"
BORDER_COLOR = "#333338"

# --- CSV Files and Fields ---
FILES = {
    'college': 'colleges.csv',
    'program': 'programs.csv',
    'student': 'students.csv'
}

FIELDS = {
    'college': ['code', 'name'],
    'program': ['code', 'name', 'college'],
    'student': ['id', 'firstname', 'lastname', 'program', 'year', 'gender'],
}

# --- Window Dimensions ---
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# --- Chart Colors ---
COLOR_PALETTE = [
    ACCENT_COLOR, '#4f6bed', '#8b5cf6', '#eab308', 
    '#ec4899', '#06b6d4', '#f59e0b', '#8b5cf6'
]
