"""
Dashboard frame and main navigation for EduManage SIS
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
from ui import DepthCard, placeholder_image, get_main_logo
from views import StudentsView, ProgramsView, CollegesView
from data import create_backups


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard with unified topbar, main content, and right sidebar."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_view = None
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_topbar()
        try:
            self.create_topbar()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Dashboard Init Error", f"Failed to create topbar: {e}")
            except Exception:
                pass

        # Main container with left content and right sidebar
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
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
        """Create unified top navigation bar with title, tabs, and controls."""
        topbar = DepthCard(self, height=85, fg_color=PANEL_COLOR, corner_radius=0, 
                          border_width=2, border_color=BORDER_COLOR)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        
        # Main container with 3 sections
        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        topbar.grid_rowconfigure(0, weight=1)
        topbar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)  # Center expands
        
        # LEFT SECTION: Title card with add button
        left_card = DepthCard(inner, fg_color="#2a2a2e", corner_radius=8, 
                     border_width=1, border_color=BORDER_COLOR, height=65)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        left_inner = ctk.CTkFrame(left_card, fg_color="transparent")
        left_inner.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
        left_inner.grid_columnconfigure(0, weight=1)
        left_inner.grid_columnconfigure(1, weight=0)
        left_inner.grid_rowconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(left_inner, text="Students", 
                           font=get_font(22, True), 
                           text_color=ACCENT_COLOR,
                           anchor="center")
        self.title_label.grid(row=0, column=0, sticky="ew", padx=20)
        
        self.add_btn = ctk.CTkButton(left_inner, text="Add Entry", width=120, height=40,
                        font=get_font(12, True),
                                    fg_color=ACCENT_COLOR, text_color="white",
                        hover_color="#7C3AED", command=self.handle_add_entry)
        self.add_btn.grid(row=0, column=1, sticky="e", padx=(15, 0))
        
        # Disable add button initially (guest mode)
        if not self.controller.logged_in:
            self.add_btn.configure(state="disabled", fg_color="#555555")
        
        # CENTER SECTION: Centralized navigation tabs
        center_frame = ctk.CTkFrame(inner, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="ew", padx=15)
        
        self.nav_btns = {}
        
        # Create small placeholder icons for tabs (kept as attributes to avoid GC)
        self._tab_icon_students = placeholder_image(size=22, color=ACCENT_COLOR)
        self._tab_icon_programs = placeholder_image(size=22, color="#8b5cf6")
        self._tab_icon_colleges = placeholder_image(size=22, color="#4f6bed")

        # Students tab
        self.nav_btns[StudentsView] = ctk.CTkButton(
            center_frame,
            text="Students",
            image=self._tab_icon_students,
            compound="left",
            fg_color="transparent",
            text_color="#d1d1d1",
            hover_color="#2A1F3D",
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
            text_color="#d1d1d1",
            hover_color="#2A1F3D",
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
            text_color="#d1d1d1",
            hover_color="#2A1F3D",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(CollegesView)
        )
        self.nav_btns[CollegesView].pack(side="left", padx=6, fill="both", expand=True)
        
        # RIGHT SECTION: Search, Login/Logout, Notifications
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(15, 0))
        
        self.search_entry = ctk.CTkEntry(right_frame, placeholder_text="Search...", width=220, 
                border_width=2, border_color=ACCENT_COLOR, fg_color="#2A1F3D", 
                corner_radius=20, font=get_font(11), height=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.handle_search_dynamic)
        
        # Login/Logout button - will be updated based on session
        self.auth_btn = ctk.CTkButton(right_frame, text="Login", fg_color=ACCENT_COLOR, 
             text_color="white", hover_color="#7C3AED", font=get_font(11, True),
             height=40, width=100, command=self.handle_login_click)
        self.auth_btn.pack(side="left", padx=5)
        
        self.update_auth_button()

    def handle_add_entry(self):
        """Handle add entry button - delegates to current view."""
        if not self.controller.logged_in:
            self._show_custom_dialog("Access Denied", "Please log in first to add new entries.")
            self.handle_login_click()
            return
        
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
                btn.configure(fg_color=ACCENT_COLOR, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#d1d1d1")
        
        # Update title and button label based on view
        self.update_title_card(view_class)
        
        self.search_entry.delete(0, tk.END)
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


    
    def handle_logout(self):
        """Handle logout."""
        self._show_custom_dialog("Logout Confirmation", "Are you sure you want to logout?", "yesno", 
                                callback=self._confirm_logout)
    
    def _confirm_logout(self, result):
        """Callback for logout confirmation."""
        if result:
            create_backups()
            self.controller.logged_in = False
            self.update_auth_button()
            self.add_btn.configure(state="disabled")
            self.search_entry.configure(state="disabled")
            for view in self.views.values():
                self.disable_edit_delete_buttons(view)
    
    def handle_login_click(self):
        """Handle login button click - show login window."""
        login_window = ctk.CTkToplevel(self)
        login_window.title("Login - nexo")
        login_window.geometry("520x650")
        login_window.attributes('-topmost', True)
        
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (login_window.winfo_width() // 2)
        y = (login_window.winfo_screenheight() // 2) - (login_window.winfo_height() // 2)
        login_window.geometry(f"+{x}+{y}")
        
        login_window.configure(fg_color=BG_COLOR)
        
        # Center Container
        center_frame = ctk.CTkFrame(login_window, fg_color="transparent")
        center_frame.pack(fill="both", expand=True)
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        # Clean, flat card with depth effect - dark themed
        card = DepthCard(center_frame, fg_color=PANEL_COLOR, corner_radius=20, border_width=2, border_color=BORDER_COLOR)
        card.grid(row=0, column=0, padx=20, pady=20)
        card.pack_propagate(False)

        # Logo - extra large for prominent display
        logo_frame = ctk.CTkFrame(card, fg_color="transparent")
        logo_frame.pack(pady=(30, 25))
        
        # Load main logo - extra big
        try:
            self._logo_img_login = get_main_logo(size=120)
            lbl = ctk.CTkLabel(logo_frame, image=self._logo_img_login, text="")
            lbl.image = self._logo_img_login
            lbl.pack()
        except Exception:
            ctk.CTkLabel(logo_frame, text="nexo", font=get_font(28, True), text_color=ACCENT_COLOR).pack()

        ctk.CTkLabel(card, text="Welcome Back", font=get_font(24, True), text_color=TEXT_PRIMARY).pack(pady=(0, 8))
        ctk.CTkLabel(card, text="Please sign in to access admin features", font=get_font(12), text_color=TEXT_MUTED).pack(pady=(0, 25))

        # Username input
        ctk.CTkLabel(card, text="Username", font=get_font(12, True), text_color=TEXT_PRIMARY).pack(anchor="w", padx=40, pady=(10, 4))
        username_entry = ctk.CTkEntry(card, placeholder_text="👤  Enter your username", height=48, 
                                      border_color=BORDER_COLOR, fg_color="#2A1F3D", 
                                      text_color="#d1d1d1")
        username_entry.pack(fill="x", padx=40, pady=(0, 12))

        # Password input
        ctk.CTkLabel(card, text="Password", font=get_font(12, True), text_color=TEXT_PRIMARY).pack(anchor="w", padx=40, pady=(10, 4))
        password_entry = ctk.CTkEntry(card, placeholder_text="🔒  Enter your password", height=48, 
                                      border_color=BORDER_COLOR, fg_color="#2A1F3D", 
                                      text_color="#d1d1d1", show="*")
        password_entry.pack(fill="x", padx=40, pady=(0, 22))

        def _handle_login():
            user = username_entry.get()
            pwd = password_entry.get()
            
            if not user or not pwd:
                messagebox.showerror("Error", "Please enter username and password")
                return
            
            # Simple authentication (for demo)
            if user == "admin" and pwd == "admin":
                self.controller.logged_in = True
                self.update_auth_button()
                self.add_btn.configure(state="normal")
                self.search_entry.configure(state="normal")
                for view in self.views.values():
                    self.enable_edit_delete_buttons(view)
                login_window.destroy()
            else:
                messagebox.showerror("Error", "Invalid username or password")

        # Sign In button
        ctk.CTkButton(card, text="Sign In", font=get_font(13, True), fg_color=ACCENT_COLOR, 
                     text_color="white", hover_color="#7C3AED", height=50, corner_radius=10,
                     command=_handle_login).pack(fill="x", padx=40, pady=(0, 15))
        
        # Cancel button
        ctk.CTkButton(card, text="Cancel", font=get_font(13, True), fg_color="transparent", 
                     text_color=TEXT_MUTED, hover_color="#2A1F3D", height=48, corner_radius=10,
                     border_width=2, border_color=BORDER_COLOR,
                     command=login_window.destroy).pack(fill="x", padx=40, pady=(0, 40))
    
    def update_auth_button(self):
        """Update the auth button based on login state."""
        if self.controller.logged_in:
            self.auth_btn.configure(text="Logout", fg_color="#c41e3a", hover_color="#a01830", 
                                    command=self.handle_logout)
            self.add_btn.configure(state="normal", fg_color=ACCENT_COLOR)
        else:
            self.auth_btn.configure(text="Login", fg_color=ACCENT_COLOR, hover_color="#7C3AED", 
                                    command=self.handle_login_click)
            self.add_btn.configure(state="disabled", fg_color="#555555")
    
    def disable_edit_delete_buttons(self, view):
        """Disable edit/delete buttons in a view."""
        # This will be called when user logs out
        if hasattr(view, 'tree'):
            for item in view.tree.get_children():
                view.tree.item(item, tags=())
    
    def enable_edit_delete_buttons(self, view):
        """Enable edit/delete buttons in a view."""
        # This will be called when user logs in
        if hasattr(view, 'refresh_table'):
            view.refresh_table()

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
                self._show_custom_dialog("Theme Error", f"Could not apply theme '{choice}': {e}", "error")
            except Exception:
                pass

    def _show_custom_dialog(self, title, message, dialog_type="info", callback=None):
        """Show a custom styled dialog matching the app theme."""
        dialog_window = ctk.CTkToplevel(self)
        dialog_window.title(title)
        dialog_window.geometry("450x200")
        dialog_window.attributes('-topmost', True)
        dialog_window.configure(fg_color=BG_COLOR)
        
        dialog_window.update_idletasks()
        x = (dialog_window.winfo_screenwidth() // 2) - (dialog_window.winfo_width() // 2)
        y = (dialog_window.winfo_screenheight() // 2) - (dialog_window.winfo_height() // 2)
        dialog_window.geometry(f"+{x}+{y}")
        
        # Content frame
        frame = ctk.CTkFrame(dialog_window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title_label = ctk.CTkLabel(frame, text=title, font=get_font(16, True), text_color=TEXT_PRIMARY)
        title_label.pack(pady=(0, 15))
        
        # Message
        msg_label = ctk.CTkLabel(frame, text=message, font=get_font(11), text_color=TEXT_MUTED, wraplength=350)
        msg_label.pack(pady=(0, 25), fill="both", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        if dialog_type == "yesno":
            def _yes():
                if callback:
                    callback(True)
                dialog_window.destroy()
            
            def _no():
                if callback:
                    callback(False)
                dialog_window.destroy()
            
            ctk.CTkButton(button_frame, text="Yes", fg_color=ACCENT_COLOR, text_color="white",
                         hover_color="#7C3AED", font=get_font(11, True), command=_yes).pack(side="left", fill="x", expand=True, padx=(0, 8))
            ctk.CTkButton(button_frame, text="No", fg_color="#555555", text_color="white",
                         hover_color="#666666", font=get_font(11, True), command=_no).pack(side="left", fill="x", expand=True, padx=(8, 0))
        else:
            # Info or error dialog with single OK button
            ctk.CTkButton(button_frame, text="OK", fg_color=ACCENT_COLOR, text_color="white",
                         hover_color="#7C3AED", font=get_font(11, True), 
                         command=dialog_window.destroy).pack(fill="x")
    


