"""
Utility functions for UI styling and assets.
"""

import customtkinter as ctk
import tkinter as tk
from pathlib import Path
from config import PANEL_COLOR, TEXT_MUTED, BORDER_COLOR, PANEL_SELECTED, get_font, resource_path


# Icon cache to avoid reloading
_icon_cache = {}


def get_icon(name: str, size: int = 36, fallback_color: str = "#6d28d9"):
    """Load an icon from assets/icons directory, with fallback to colored square.
    
    Args:
        name: Icon name (e.g., 'users', 'settings', 'search')
        size: Icon size in pixels (18, 22, 28, or 36)
        fallback_color: Color to use if icon file not found
    
    Returns:
        CTkImage or PhotoImage suitable for CustomTkinter widgets
    """
    cache_key = f"{name}_{size}"
    
    # Return from cache if available
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    
    # Try to load base icon first and scale it (prioritize custom icons)
    base_icon_path = Path(resource_path(f"assets/icons/{name}.png"))
    if base_icon_path.exists():
        try:
            from PIL import Image
            pil = Image.open(base_icon_path)
            # Resize to requested size
            pil = pil.resize((size, size), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=pil, size=(size, size))
            _icon_cache[cache_key] = img
            return img
        except Exception as e:
            print(f"Error loading icon {base_icon_path}: {e}")
    
    # Fallback: try to load PNG icon with exact size
    icon_path = Path(resource_path(f"assets/icons/{name}_{size}.png"))
    
    if icon_path.exists():
        try:
            from PIL import Image
            pil = Image.open(icon_path)
            img = ctk.CTkImage(light_image=pil, size=(size, size))
            _icon_cache[cache_key] = img
            return img
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
    
    # Fallback: return colored square placeholder
    return placeholder_image(size=size, color=fallback_color)


def get_main_logo(size: int = 56):
    """Load the main logo from assets/Main Logo.png.
    
    Args:
        size: Size to scale the logo to in pixels
    
    Returns:
        CTkImage
    """
    logo_path = Path(resource_path("assets/Main Logo.png"))
    
    if logo_path.exists():
        try:
            from PIL import Image
            pil = Image.open(logo_path)
            # Resize to requested size, maintaining aspect ratio
            pil.thumbnail((size, size), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=pil, size=(size, size))
            return img
        except Exception as e:
            print(f"Error loading logo {logo_path}: {e}")
    
    # Fallback to user icon if logo not found
    return get_icon("user", size=size)


def setup_treeview_style():
    """Configure styling for ttk.Treeview widgets."""
    from tkinter import ttk
    
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview", 
        background=PANEL_COLOR,
        foreground="#dcdcdc",
        rowheight=48,
        fieldbackground=PANEL_COLOR,
        borderwidth=0,
        highlightthickness=0,
        focuscolor="",
        font=get_font(14),
        padding=2
    )
    style.map('Treeview', background=[('selected', PANEL_SELECTED)])
    # Make headings look like interactive buttons with distinct styling
    HEADING_BG = "#13101a"       # Slightly darker than panel — distinct header row
    HEADING_HOVER = "#2d1f45"    # Purple tint on hover — signals interactivity
    HEADING_FG = "#a8a8b5"       # Slightly brighter than TEXT_MUTED for contrast
    style.configure(
        "Treeview.Heading",
        background=HEADING_BG,
        foreground=HEADING_FG,
        relief="flat",
        borderwidth=0,
        padding=(8, 12),
        font=get_font(13, True)
    )
    style.map("Treeview.Heading", 
              background=[('active', HEADING_HOVER)],
              foreground=[('active', '#e8e8f0')])

    # Remove focus ring highlight
    try:
        style.configure('Treeview', highlightthickness=0, focuscolor="")
    except Exception:
        pass


def placeholder_image(size=36, color="#303035"):
    """Return a square PhotoImage filled with `color` to be used as an icon placeholder.

    The PhotoImage should be kept referenced by the caller (e.g., widget.image = img)
    to avoid garbage collection.
    """
    # Prefer creating a CTkImage from a PIL Image so CustomTkinter can scale it on HiDPI
    try:
        from PIL import Image
        pil = Image.new('RGBA', (size, size), color)
        return ctk.CTkImage(light_image=pil, size=(size, size))
    except Exception:
        # Fallback: create a tkinter.PhotoImage and try to wrap it in CTkImage
        img = tk.PhotoImage(width=size, height=size)
        try:
            img.put(color, to=(0, 0, size - 1, size - 1))
        except Exception:
            img.put(color, to=(0, 0))
        try:
            return ctk.CTkImage(light_image=img, size=(size, size))
        except Exception:
            return img


# --- Simple animation helpers ---
def _lerp(a, b, t):
    return a + (b - a) * t


def animate_height(widget, target_height, duration=200):
    """Smoothly animate a widget's `height` option to target_height (px).

    Uses `after` and small steps to interpolate. Non-blocking.
    """
    try:
        start = widget.winfo_height()
    except Exception:
        try:
            start = int(widget.cget('height') or 0)
        except Exception:
            start = 0
    steps = max(2, int(duration // 15))
    delta = target_height - start

    def step(i=1):
        t = i / steps
        h = int(_lerp(start, target_height, t))
        try:
            widget.configure(height=h)
        except Exception:
            pass
        if i < steps:
            widget.after(15, lambda: step(i + 1))

    step()


def animate_progress(bar, target, duration=400):
    """Animate a CTkProgressBar `bar` from current value to `target` (0..1)."""
    try:
        start = float(getattr(bar, '_value', bar._progress))
    except Exception:
        try:
            start = float(bar.get())
        except Exception:
            start = 0.0
    steps = max(2, int(duration // 15))

    def step(i=1):
        t = i / steps
        v = _lerp(start, target, t)
        try:
            bar.set(v)
            bar._value = v
        except Exception:
            pass
        if i < steps:
            bar.after(15, lambda: step(i + 1))

    step()


def apply_button_hover(root, hover_scale=1.03):
    """Placeholder function - no longer needed (button sizing conflicts disabled)."""
    pass

