"""
Reusable UI Components for EduManage SIS
"""

import customtkinter as ctk
import tkinter as tk
from config import PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR, FONT_BOLD
import re

class DepthCard(ctk.CTkFrame):
    """Frame component with depth styling."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SmartSearchEntry(ctk.CTkEntry):
    """Entry widget with smart dropdown suggestions."""
    def __init__(self, parent, options, placeholder="", **kwargs):
        super().__init__(parent, placeholder_text=placeholder, **kwargs)
        self.options = options
        self.dropdown = None
        
        self.bind("<KeyRelease>", self._on_type)
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", lambda e: self.after(200, self._close_dropdown))

    def _on_type(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
            
        typed = self.get().strip().lower()
        if not typed:
            self._close_dropdown()
            return

        matches = [opt for opt in self.options if typed in opt.lower()]
        
        if matches and self.focus_get() == self:
            self._show_dropdown(matches)
        else:
            self._close_dropdown()

    def _on_focus(self, event):
        """When entry gains focus, show a shortlist if options are many and input empty."""
        typed = self.get().strip().lower()
        if typed:
            return

        # show top N suggestions when focused and options exist
        if len(self.options) > 0:
            matches = self.options[:min(len(self.options), 10)]
            self._show_dropdown(matches)

    def _show_dropdown(self, matches):
        if not self.dropdown or not self.dropdown.winfo_exists():
            self.dropdown = ctk.CTkToplevel(self)
            self.dropdown.wm_overrideredirect(True)
            self.dropdown.attributes("-topmost", True)
            self.dropdown.configure(fg_color=PANEL_COLOR)
            
            self.list_frame = ctk.CTkFrame(self.dropdown, fg_color=PANEL_COLOR, 
                                            border_width=1, border_color=ACCENT_COLOR, corner_radius=8)
            self.list_frame.pack(fill="both", expand=True)

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        width = self.winfo_width()
        
        display_count = min(len(matches), 5)
        self.dropdown.geometry(f"{width}x{display_count * 35 + 10}+{x}+{y}")

        for opt in matches:
            btn = ctk.CTkButton(self.list_frame, text=opt, anchor="w", 
                                fg_color="transparent", text_color="#d1d1d1",
                                hover_color="#303035", height=30, corner_radius=0,
                                command=lambda o=opt: self._select_option(o))
            btn.pack(fill="x", padx=5, pady=1)

    def _select_option(self, option):
        self.delete(0, tk.END)
        self.insert(0, option)
        self._close_dropdown()

    def _close_dropdown(self):
        if self.dropdown:
            self.dropdown.destroy()
            self.dropdown = None

def setup_treeview_style():
    """Configure styling for ttk.Treeview widgets."""
    from tkinter import ttk
    from config import PANEL_COLOR, TEXT_MUTED
    
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview", 
        background=PANEL_COLOR,
        foreground="#dcdcdc",
        rowheight=42,
        fieldbackground=PANEL_COLOR,
        borderwidth=0,
        font=("Segoe UI Variable", 13)
    )
    style.map('Treeview', background=[('selected', '#303035')])
    # Make headings and separators subtle
    style.configure(
        "Treeview.Heading",
        background=PANEL_COLOR,
        foreground=TEXT_MUTED,
        relief="flat",
        borderwidth=0,
        font=("Segoe UI Variable", 13, "bold")
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
