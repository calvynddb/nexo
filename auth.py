"""
Authentication and Login Frame for EduManage SIS
"""

import customtkinter as ctk
from tkinter import messagebox
from config import BG_COLOR, PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR, FONT_BOLD
from components import DepthCard, placeholder_image


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR) 
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Center Container
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0, sticky="nsew")
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        # Clean, flat card with depth effect - dark themed
        card = DepthCard(center_frame, fg_color=PANEL_COLOR, corner_radius=20, border_width=2, border_color=BORDER_COLOR, width=520, height=640)
        card.grid(row=0, column=0, padx=20, pady=20)
        card.grid_propagate(False)
        card.pack_propagate(False)

        logo_frame = ctk.CTkFrame(card, width=80, height=80, corner_radius=40, fg_color="#303035")
        logo_frame.pack(pady=(40, 20))
        # use placeholder image for logo to avoid emoji and allow scaling
        try:
            self._logo_img = placeholder_image(size=56, color="#4f6bed")
            lbl = ctk.CTkLabel(logo_frame, image=self._logo_img, text="")
            lbl.image = self._logo_img
            lbl.pack()
        except Exception:
            ctk.CTkLabel(logo_frame, text="SIS", font=("Segoe UI Variable", 24, "bold"), text_color="#4f6bed").pack()

        ctk.CTkLabel(card, text="SIS Administrator", font=("Segoe UI Variable", 28, "bold"), text_color="#d1d1d1").pack(pady=(0, 8))
        ctk.CTkLabel(card, text="Please sign in to access the dashboard", font=("Segoe UI Variable", 12), text_color=TEXT_MUTED).pack(pady=(0, 30))

        self.username_entry = self.create_input(card, "Username", "👤  Enter your username")
        self.password_entry = self.create_input(card, "Password", "🔒  Enter your password", show="*")

        ctk.CTkLabel(card, text="Forgot password?", font=("Segoe UI Variable", 11), text_color=ACCENT_COLOR, cursor="hand2").pack(anchor="e", padx=50)

        # Templated Login Function with enhanced button
        ctk.CTkButton(card, text="Sign In", font=("Segoe UI Variable", 13, "bold"), fg_color="#4f6bed", hover_color="#3b55c5", height=48, corner_radius=10, 
                      command=self.handle_login).pack(fill="x", padx=50, pady=(22, 12))
        
        ctk.CTkLabel(card, text="──────── Or ────────", text_color=TEXT_MUTED, font=("Segoe UI Variable", 11)).pack(pady=12)
        ctk.CTkButton(card, text="Register New Administrator", font=("Segoe UI Variable", 12, "bold"), fg_color="transparent", text_color=ACCENT_COLOR, border_width=2, border_color=ACCENT_COLOR, hover_color="#1f3a5a", height=48, corner_radius=10,
                      command=self.handle_register).pack(fill="x", padx=50, pady=(0, 40))


    def create_input(self, parent, label, placeholder, show=""):
        ctk.CTkLabel(parent, text=label, font=("Segoe UI Variable", 12, "bold"), text_color="#d1d1d1").pack(anchor="w", padx=50, pady=(10, 4))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=48, border_color=BORDER_COLOR, fg_color="#303035", text_color="#d1d1d1", show=show)
        entry.pack(fill="x", padx=50, pady=(0, 12))
        return entry

    def handle_login(self):
        user = self.username_entry.get()
        pwd = self.password_entry.get()
        
        if not user or not pwd:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        # Simple authentication (for demo)
        if user == "admin" and pwd == "admin":
            from dashboard import DashboardFrame
            self.controller.show_frame(DashboardFrame)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def handle_register(self):
        """Handle registration button press."""
        reg_window = ctk.CTkToplevel(self)
        reg_window.title("Register New Administrator")
        reg_window.geometry("450x500")
        reg_window.attributes('-topmost', True)
        
        reg_window.update_idletasks()
        x = (reg_window.winfo_screenwidth() // 2) - (reg_window.winfo_width() // 2)
        y = (reg_window.winfo_screenheight() // 2) - (reg_window.winfo_height() // 2)
        reg_window.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(reg_window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Register Administrator", 
                    font=("Segoe UI Variable", 18, "bold")).pack(pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Full Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        name_entry = ctk.CTkEntry(frame, placeholder_text="Enter full name", height=40)
        name_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Username", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        username_entry = ctk.CTkEntry(frame, placeholder_text="Choose username", height=40)
        username_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Email", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        email_entry = ctk.CTkEntry(frame, placeholder_text="Enter email", height=40)
        email_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        pass_entry = ctk.CTkEntry(frame, placeholder_text="Enter password", show="*", height=40)
        pass_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Confirm Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        confirm_entry = ctk.CTkEntry(frame, placeholder_text="Confirm password", show="*", height=40)
        confirm_entry.pack(fill="x", pady=(0, 20))
        
        def register_user():
            name = name_entry.get().strip()
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            password = pass_entry.get()
            confirm = confirm_entry.get()
            
            if not all([name, username, email, password, confirm]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
            
            messagebox.showinfo("Success", "Administrator registered successfully! Please log in.")
            reg_window.destroy()
        
        ctk.CTkButton(frame, text="Register", command=register_user, height=40,
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(fill="x")
