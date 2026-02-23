"""
Input and entry widgets for EduManage SIS.
"""

import customtkinter as ctk
import tkinter as tk
from config import PANEL_COLOR, ACCENT_COLOR, TEXT_PRIMARY, BORDER_COLOR, get_font


class SearchableComboBox(ctk.CTkFrame):
    """A combo box widget with search/type functionality and visual dropdown appearance."""
    def __init__(self, parent, options, **kwargs):
        super().__init__(parent, fg_color="transparent")
        
        self.options = options
        self.selected_value = None
        self.dropdown = None
        
        # Main frame with entry and button
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="x")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)
        
        # Text entry
        self.entry = ctk.CTkEntry(main_frame, placeholder_text=kwargs.get("placeholder", "Select..."), 
                                   height=kwargs.get("height", 40), fg_color="#2A1F3D",
                                   border_width=1, border_color=BORDER_COLOR)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        # Dropdown button with arrow
        self.dropdown_btn = ctk.CTkButton(main_frame, text="▼", width=40, height=kwargs.get("height", 40),
                                         fg_color="#2A1F3D", text_color=TEXT_PRIMARY,
                                         border_width=1, border_color=BORDER_COLOR,
                                         command=self._toggle_dropdown)
        self.dropdown_btn.grid(row=0, column=1, sticky="e")
        
        # Bind events
        self.entry.bind("<KeyRelease>", self._on_type)
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", lambda e: self.after(200, self._close_dropdown))
        self.entry.bind("<Return>", lambda e: self._close_dropdown())
        
    def _on_type(self, event):
        """Filter options as user types."""
        if event.keysym in ("Up", "Down", "Escape"):
            return
        
        typed = self.entry.get().strip().lower()
        
        if not typed:
            self._close_dropdown()
            return
        
        matches = [opt for opt in self.options if typed in opt.lower()]
        
        if matches and self.entry.focus_get() == self.entry:
            self._show_dropdown(matches)
        else:
            self._close_dropdown()
    
    def _on_focus(self, event):
        """Show all options when focused."""
        typed = self.entry.get().strip()
        if typed:
            return
        
        if self.options:
            self._show_dropdown(self.options[:min(len(self.options), 10)])
    
    def _toggle_dropdown(self):
        """Toggle dropdown visibility."""
        if self.dropdown and self.dropdown.winfo_exists():
            self._close_dropdown()
        else:
            typed = self.entry.get().strip().lower()
            if typed:
                matches = [opt for opt in self.options if typed in opt.lower()]
            else:
                matches = self.options[:min(len(self.options), 10)]
            
            if matches:
                self._show_dropdown(matches)
    
    def _show_dropdown(self, matches):
        """Display filtered dropdown menu."""
        if not self.dropdown or not self.dropdown.winfo_exists():
            self.dropdown = ctk.CTkToplevel(self.entry)
            self.dropdown.wm_overrideredirect(True)
            self.dropdown.attributes("-topmost", True)
            self.dropdown.configure(fg_color=PANEL_COLOR)
            
            self.list_frame = ctk.CTkFrame(self.dropdown, fg_color=PANEL_COLOR,
                                          border_width=1, border_color=ACCENT_COLOR, corner_radius=6)
            self.list_frame.pack(fill="both", expand=True)
        
        # Clear previous items
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        # Position dropdown below entry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        width = self.entry.winfo_width() + self.dropdown_btn.winfo_width() + 4
        
        display_count = min(len(matches), 5)
        self.dropdown.geometry(f"{width}x{display_count * 35 + 10}+{x}+{y}")
        
        # Add option buttons
        for opt in matches:
            btn = ctk.CTkButton(self.list_frame, text=opt, anchor="w",
                               fg_color="transparent", text_color=TEXT_PRIMARY,
                               hover_color="#2A1F3D", height=30, corner_radius=0,
                               font=get_font(11), command=lambda o=opt: self._select_option(o))
            btn.pack(fill="x", padx=1, pady=1)
    
    def _select_option(self, option):
        """Select an option from dropdown."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, option)
        self.selected_value = option
        self._close_dropdown()
    
    def _close_dropdown(self):
        """Close the dropdown menu."""
        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
    
    def get(self):
        """Get the current value."""
        return self.entry.get().strip()
    
    def insert(self, index, value):
        """Insert value into entry."""
        self.entry.insert(index, value)
        self.selected_value = value
    
    def set(self, value):
        """Set the value."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.selected_value = value


class StyledComboBox(ctk.CTkFrame):
    """A styled combo box widget matching SearchableComboBox appearance."""
    def __init__(self, parent, values, **kwargs):
        super().__init__(parent, fg_color="transparent")
        
        self.values = values
        self._value = None
        
        # Main frame with entry and button
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="x")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)
        
        # Display label
        self.entry = ctk.CTkEntry(main_frame, placeholder_text=kwargs.get("placeholder", "Select..."), 
                                   height=kwargs.get("height", 40), fg_color="#2A1F3D",
                                   border_width=1, border_color=BORDER_COLOR)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        # Dropdown button with arrow
        self.dropdown_btn = ctk.CTkButton(main_frame, text="▼", width=40, height=kwargs.get("height", 40),
                                         fg_color="#2A1F3D", text_color=TEXT_PRIMARY,
                                         border_width=1, border_color=BORDER_COLOR,
                                         command=self._show_menu)
        self.dropdown_btn.grid(row=0, column=1, sticky="e")
        
        self.dropdown = None
    
    def _show_menu(self):
        """Show dropdown menu."""
        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
            return
        
        self.dropdown = ctk.CTkToplevel(self.entry)
        self.dropdown.wm_overrideredirect(True)
        self.dropdown.attributes("-topmost", True)
        self.dropdown.configure(fg_color=PANEL_COLOR)
        
        list_frame = ctk.CTkFrame(self.dropdown, fg_color=PANEL_COLOR,
                                 border_width=1, border_color=ACCENT_COLOR, corner_radius=6)
        list_frame.pack(fill="both", expand=True)
        
        # Position dropdown below button
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        width = self.entry.winfo_width() + self.dropdown_btn.winfo_width() + 4
        
        display_count = min(len(self.values), 5)
        self.dropdown.geometry(f"{width}x{display_count * 35 + 10}+{x}+{y}")
        
        # Add option buttons
        for val in self.values:
            btn = ctk.CTkButton(list_frame, text=val, anchor="w",
                               fg_color="transparent", text_color=TEXT_PRIMARY,
                               hover_color="#2A1F3D", height=30, corner_radius=0,
                               font=get_font(11), command=lambda v=val: self._select_option(v))
            btn.pack(fill="x", padx=1, pady=1)
    
    def _select_option(self, value):
        """Select an option."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self._value = value
        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
    
    def get(self):
        """Get the current value."""
        return self.entry.get().strip()
    
    def set(self, value):
        """Set the value."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self._value = value


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
                                hover_color="#2A1F3D", height=30, corner_radius=0,
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
