"""
Utility functions for UI styling and assets.
"""

import customtkinter as ctk
import tkinter as tk
from config import PANEL_COLOR, TEXT_MUTED, get_font


def setup_treeview_style():
    """Configure styling for ttk.Treeview widgets."""
    from tkinter import ttk
    
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview", 
        background=PANEL_COLOR,
        foreground="#dcdcdc",
        rowheight=42,
        fieldbackground=PANEL_COLOR,
        borderwidth=0,
        font=get_font(13)
    )
    style.map('Treeview', background=[('selected', '#2A1F3D')])
    # Make headings and separators subtle
    style.configure(
        "Treeview.Heading",
        background=PANEL_COLOR,
        foreground=TEXT_MUTED,
        relief="flat",
        borderwidth=0,
        font=get_font(13, True)
    )
    style.map("Treeview.Heading", background=[('active', PANEL_COLOR)])

    # Tweak indicators to make vertical separators minimal: remove strong focus highlight
    try:
        style.configure('Treeview', highlightthickness=0)
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
