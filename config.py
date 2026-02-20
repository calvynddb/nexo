"""
Configuration and Constants for EduManage SIS
"""

import customtkinter as ctk

# --- Theme Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- Fonts ---
# Uses Inter/Montserrat (sleek modern fonts); falls back to system fonts if unavailable
FONT_MAIN = ("Montserrat", 13)
FONT_BOLD = ("Montserrat", 13, "bold")
FONT_FAMILY = "Montserrat"

def get_font(size: int = 13, bold: bool = False):
    """Return a font tuple for widgets: (family, size[, 'bold'])."""
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)

# --- Colors --- Modern Dark Purple Theme (sophisticated, muted tones)
BG_COLOR = "#0a0a15"  # Very dark background (almost black with purple tint)
PANEL_COLOR = "#0f0b1f"  # Dark card background (even darker for subdued look)
ACCENT_COLOR = "#6d28d9"  # Muted purple/indigo (primary accent, less vibrant)
TEXT_MUTED = "#9090a8"  # Muted gray-blue
TEXT_PRIMARY = "#e5e5f0"  # Softer off-white for main text
BORDER_COLOR = "#5b21b6"  # Darker purple border

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

# --- Chart Colors --- Muted purple & indigo palette
COLOR_PALETTE = [
    '#6d28d9',  # Muted purple (primary)
    '#7c3aed',  # Indigo
    '#8b5cf6',  # Medium purple
    '#5b21b6',  # Deep purple
    '#4c1d95',  # Very deep purple
    '#06b6d4',  # Cyan (subtle complement)
    '#6366f1',  # Indigo (deep blue)
    '#10b981'   # Emerald (fresh, less vibrant)
]

# --- Global Theme Manager ---
class ThemeManager:
    """Manages theme changes and notifies listeners globally."""
    _listeners = []
    _current_mode = "dark"
    
    @classmethod
    def register_listener(cls, callback):
        """Register a callback to be called when theme changes."""
        if callback not in cls._listeners:
            cls._listeners.append(callback)
    
    @classmethod
    def unregister_listener(cls, callback):
        """Unregister a theme change callback."""
        if callback in cls._listeners:
            cls._listeners.remove(callback)
    
    @classmethod
    def notify_theme_change(cls, mode: str):
        """Notify all listeners of a theme change."""
        cls._current_mode = mode
        for callback in cls._listeners:
            try:
                callback(mode)
            except Exception as e:
                print(f"Error in theme callback: {e}")
    
    @classmethod
    def get_current_mode(cls) -> str:
        """Get the current theme mode."""
        return cls._current_mode


# Global theme manager instance
THEME_MANAGER = ThemeManager()