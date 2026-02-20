"""
Main entry point for EduMdge SIS application
"""

import customtkinter as ctk
from config import BG_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT
from data import init_files, load_csv
from auth import LoginFrame
from dashboard import DashboardFrame
import os
import time


class App(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.title("EduManage SIS")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Initialize data files
        init_files()
        
        # Load data (guarded)
        try:
            self.colleges = load_csv('college')
        except Exception:
            import traceback
            traceback.print_exc()
            self.colleges = []
        try:
            self.programs = load_csv('program')
        except Exception:
            import traceback
            traceback.print_exc()
            self.programs = []
        try:
            self.students = load_csv('student')
        except Exception:
            import traceback
            traceback.print_exc()
            self.students = []

        # Create container
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Create frames
        self.frames = {}
        for F in (LoginFrame, DashboardFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show login frame first
        self.show_frame(LoginFrame)

    def show_frame(self, cont):
        """Show a specific frame."""
        frame = self.frames[cont]
        frame.tkraise()


def main():
    """Run the application."""
    # Quick verification to show which file is being executed and its timestamp
    try:
        mtime = time.ctime(os.path.getmtime(__file__))
    except Exception:
        mtime = "unknown"
    print(f"Starting {os.path.abspath(__file__)} (mtime: {mtime})")

    try:
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback, sys
        traceback.print_exc()
        try:
            # try to show a dialog if tkinter is usable
            from tkinter import messagebox
            messagebox.showerror("Application Error", f"Unhandled exception during startup:\n{e}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
