"""
Dashboard main frame and navigation for nexo.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from config import (
    BG_COLOR, PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR, 
    FONT_MAIN, FONT_BOLD, COLOR_PALETTE, get_font, TEXT_PRIMARY, THEME_MANAGER
)
from ui import DepthCard, placeholder_image, get_icon, get_main_logo
from views import StudentsView, ProgramsView, CollegesView
from data import create_backups


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard with unified topbar, main content, and right sidebar."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_view = None
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Register as theme listener for dynamic updates
        THEME_MANAGER.register_listener(self.on_theme_change)

        self.create_topbar()
        self.create_title_bar()

        # Main container with left content and right sidebar
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=0)
        
        # Left content area
        self.content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Create views
        self.views = {}
        for V in (StudentsView, ProgramsView, CollegesView):
            view = V(self.content_area, controller)
            self.views[V] = view
            view.grid(row=0, column=0, sticky="nsew")

        self.show_view(StudentsView)

    def create_topbar(self):
        """Create unified top navigation bar with logo, text, tabs, and controls."""
        topbar = DepthCard(self, height=90, fg_color=PANEL_COLOR, corner_radius=0, 
                          border_width=2, border_color=BORDER_COLOR)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        
        # Main container with three sections
        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=20, pady=12)
        topbar.grid_rowconfigure(0, weight=1)
        topbar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)  # Center expands
        
        # LEFT SECTION: Logo and "nexo." text
        left_section = ctk.CTkFrame(inner, fg_color="transparent")
        left_section.grid(row=0, column=0, sticky="nsew", padx=(0, 30))
        
        # Load main logo - bigger
        logo_img = get_main_logo(size=70)
        logo_label = ctk.CTkLabel(left_section, image=logo_img, text="")
        logo_label.image = logo_img  # Keep reference to avoid GC
        logo_label.pack(side="left", padx=(0, 15))
        self._logo_img = logo_img  # Store as instance variable
        
        # "nexo." text - same size, bold Century Gothic
        nexo_label = ctk.CTkLabel(left_section, text="nexo.", font=get_font(32, True), text_color=ACCENT_COLOR)
        nexo_label.pack(side="left")
        
        # CENTER SECTION: Centralized navigation tabs
        center_frame = ctk.CTkFrame(inner, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="ew", padx=(0, 30))
        
        self.nav_btns = {}
        
        # Create small placeholder icons for tabs (kept as attributes to avoid GC)
        self._tab_icon_students = get_icon("users", size=28, fallback_color=ACCENT_COLOR)
        self._tab_icon_programs = get_icon("books", size=28, fallback_color="#6d5a8a")
        self._tab_icon_colleges = get_icon("building", size=28, fallback_color="#7a6a95")

        # Students tab
        self.nav_btns[StudentsView] = ctk.CTkButton(
            center_frame,
            text="Students",
            image=self._tab_icon_students,
            compound="left",
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_COLOR,
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(StudentsView)
        )
        self.nav_btns[StudentsView].pack(side="left", padx=6, fill="both", expand=True)

        # Programs tab
        self.nav_btns[ProgramsView] = ctk.CTkButton(
            center_frame,
            text="Programs",
            image=self._tab_icon_programs,
            compound="left",
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_COLOR,
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(ProgramsView)
        )
        self.nav_btns[ProgramsView].pack(side="left", padx=6, fill="both", expand=True)

        # Colleges tab
        self.nav_btns[CollegesView] = ctk.CTkButton(
            center_frame,
            text="Colleges",
            image=self._tab_icon_colleges,
            compound="left",
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_COLOR,
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(CollegesView)
        )
        self.nav_btns[CollegesView].pack(side="left", padx=6, fill="both", expand=True)
        
        # RIGHT SECTION: Settings and Logout only
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew")
        
        # settings icon - larger for better visibility
        self._settings_icon = get_icon("settings", size=28, fallback_color=ACCENT_COLOR)
        ctk.CTkButton(right_frame, image=self._settings_icon, text="", fg_color="transparent", 
                 hover_color=ACCENT_COLOR, width=50, height=50, command=self.open_settings).pack(side="left", padx=3)

        ctk.CTkButton(right_frame, text="Logout", fg_color="transparent", 
                 text_color=TEXT_MUTED, hover_color=ACCENT_COLOR, font=get_font(11, True),
                 height=40, command=self.handle_logout).pack(side="left", padx=3)

    def create_title_bar(self):
        """Create title bar with page title on left and action buttons on right."""
        title_bar = DepthCard(self, height=70, fg_color=PANEL_COLOR, corner_radius=0,
                             border_width=1, border_color=BORDER_COLOR)
        title_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=(10, 0))
        title_bar.grid_propagate(False)
        
        inner = ctk.CTkFrame(title_bar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=15, pady=12)
        title_bar.grid_rowconfigure(0, weight=1)
        title_bar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0)
        
        # Left: Page Title
        self.title_label = ctk.CTkLabel(inner, text="Students",
                                       font=get_font(22, True),
                                       text_color=ACCENT_COLOR)
        self.title_label.grid(row=0, column=0, sticky="w")
        
        # Right: Button Container
        button_container = ctk.CTkFrame(inner, fg_color="transparent")
        button_container.grid(row=0, column=1, sticky="e", padx=(20, 0))
        
        # Import Button
        self.import_btn = ctk.CTkButton(button_container, text="Import", width=100, height=45,
                                       font=get_font(12, True),
                                       fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY,
                                       hover_color="#7C3AED", 
                                       command=self.handle_import)
        self.import_btn.pack(side="left", padx=(0, 10))
        
        # Add Entry Button
        self.add_btn = ctk.CTkButton(button_container, text="Add Entry", width=100, height=45,
                                    font=get_font(12, True),
                                    fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY,
                                    hover_color="#7C3AED",
                                    command=self.handle_add_entry)
        self.add_btn.pack(side="left", padx=(0, 0))

    def handle_import(self):
        """Handle import button - delegates to current view."""
        if self.current_view and self.current_view in self.views:
            if hasattr(self.views[self.current_view], 'import_data'):
                self.views[self.current_view].import_data()

    def handle_add_entry(self):
        """Handle add entry button - delegates to current view."""
        if self.current_view == StudentsView:
            self.views[StudentsView].add_student()
        elif self.current_view == ProgramsView:
            self.views[ProgramsView].add_program()
        elif self.current_view == CollegesView:
            self.views[CollegesView].add_college()

    def show_view(self, view_class):
        """Show a specific view."""
        view = self.views[view_class]
        view.tkraise()
        self.current_view = view_class

        # Update active tab styling
        for vc, btn in self.nav_btns.items():
            if vc == view_class:
                btn.configure(fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_PRIMARY)
        
        # Update title and button label based on view
        self.update_title_card(view_class)
        
        self.views[view_class].refresh_table()
    
    def update_title_card(self, view_class):
        """Update title card label and button based on active view."""
        if view_class == StudentsView:
            self.title_label.configure(text="Students")
        elif view_class == ProgramsView:
            self.title_label.configure(text="Programs")
        elif view_class == CollegesView:
            self.title_label.configure(text="Colleges")

    def handle_search_dynamic(self, event):
        """Filter current view's table based on search query."""
        query = self.search_entry.get().strip().lower()
        
        if self.current_view:
            if len(query) < 1:
                self.views[self.current_view].refresh_table()
            else:
                self.views[self.current_view].filter_table(query)

    def open_settings(self):
        """Open Settings window."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("580x680")
        settings_window.configure(fg_color=BG_COLOR)
        settings_window.attributes('-topmost', True)
        
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(settings_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        from ui import DepthCard
        settings_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        settings_card.pack(fill="both", expand=True)
        frame = ctk.CTkScrollableFrame(settings_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        ctk.CTkLabel(frame, text="Settings", font=get_font(22, True)).pack(anchor="w", pady=(0, 25))
        
        # Appearance
        ctk.CTkLabel(frame, text="Appearance", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkLabel(frame, text="Theme", font=FONT_BOLD).pack(anchor="w", pady=(5, 4))
        theme_combo = ctk.CTkOptionMenu(frame, values=["Dark", "Light"], height=40, font=FONT_MAIN,
                                       fg_color=ACCENT_COLOR, button_color=ACCENT_COLOR,
                                       button_hover_color="#7C3AED", text_color=TEXT_PRIMARY)
        theme_combo.pack(fill="x", pady=(0, 8))
        # set current appearance
        try:
            theme_combo.set(ctk.get_appearance_mode())
        except Exception:
            pass
        # Apply button to change theme immediately
        def _apply_theme():
            choice = theme_combo.get()
            self.apply_theme(choice)
        
        ctk.CTkButton(frame, text="Apply Theme", height=36, command=_apply_theme,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=(0, 10))
        
        # System
        ctk.CTkLabel(frame, text="System", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkCheckBox(frame, text="Enable Notifications", height=30, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Auto Backup on Exit", height=30, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Show Debug Info", height=30, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        
        # Account
        ctk.CTkLabel(frame, text="Account", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Change Password", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Manage Admins", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
        
        # Data
        ctk.CTkLabel(frame, text="Data Management", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Create Backup", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED",
                     command=lambda: messagebox.showinfo("Success", "Backup created successfully!")).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="View Backups", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Export Data", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
    
    def handle_logout(self):
        """Handle logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            create_backups()
            from auth import LoginFrame
            self.controller.show_frame(LoginFrame)
    def apply_theme(self, choice: str):
        """Apply appearance mode safely and notify all listeners."""
        try:
            mode = choice.lower() if isinstance(choice, str) else str(choice).lower()
            if mode not in ("dark", "light", "system"):
                mode = "dark"
            
            # Set the appearance mode globally
            ctk.set_appearance_mode(mode)
            
            # Notify all listeners of the theme change
            THEME_MANAGER.notify_theme_change(mode)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Theme Error", f"Could not apply theme '{choice}': {e}")
            except Exception:
                pass
    
    def on_theme_change(self, mode: str):
        """Callback when theme changes - refreshes all visible views."""
        try:
            # Update current view if it exists
            if self.current_view and self.current_view in self.views:
                view = self.views[self.current_view]
                # Force re-render of the view
                if hasattr(view, 'refresh_table'):
                    view.refresh_table()
        except Exception as e:
            print(f"Error refreshing view on theme change: {e}")