"""
Students view module extracted from original views.py
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from config import (
    FONT_MAIN, FONT_BOLD, BG_COLOR, PANEL_COLOR, ACCENT_COLOR, 
    TEXT_MUTED, BORDER_COLOR, COLOR_PALETTE, TEXT_PRIMARY
)
from config import get_font
from ui import DepthCard, SearchableComboBox, StyledComboBox, setup_treeview_style, placeholder_image, get_icon
from data import validate_student, save_csv


class StudentsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.sort_column = None
        self.sort_reverse = False
        self.column_names = {}  # Store original column names
        self.setup_ui()

    def setup_ui(self):
        # Table Container
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", columnspan=2)
        
        setup_treeview_style()
        cols = ("ID", "First Name", "Last Name", "Gender", "Year", "Program", "College")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", style="Treeview")
        
        # Store original column names
        for c in cols:
            self.column_names[c] = c.upper()
            self.tree.heading(c, text=c.upper())
        
        # Column widths and anchoring - center-align all content
        self.tree.column("ID", width=70, anchor="center", stretch=False)
        self.tree.column("First Name", width=130, anchor="center", stretch=False)
        self.tree.column("Last Name", width=130, anchor="center", stretch=False)
        self.tree.column("Gender", width=80, anchor="center", stretch=False)
        self.tree.column("Year", width=70, anchor="center", stretch=False)
        self.tree.column("Program", width=120, anchor="center", stretch=False)
        self.tree.column("College", width=120, anchor="center", stretch=False)
        
        self.tree.pack(fill="both", expand=True, padx=15, pady=(15, 8))

        # Pagination controls
        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=(6,12))

        self.current_page = 1
        self.page_size = 12
        self._last_page_items = []
        self._last_hover = None
        self.table_container = table_container

        # Previous Button
        self.prev_btn = ctk.CTkButton(
            ctrl, 
            text="◀ Prev", 
            width=80, 
            fg_color="#6d28d9", 
            hover_color="#5b21b6",
            text_color="white",
            command=lambda: self.change_page(-1)
        )
        self.prev_btn.pack(side="left", padx=(0,8))

        # Pagination indicator frame
        self.pagination_frame = ctk.CTkFrame(ctrl, fg_color="transparent")
        self.pagination_frame.pack(side="left", padx=8)
        self.page_buttons = []

        # Next Button - Fixed Syntax
        self.next_btn = ctk.CTkButton(
            ctrl, 
            text="Next ▶", 
            width=80, 
            fg_color="#6d28d9", 
            hover_color="#5b21b6",
            text_color="white",
            command=lambda: self.change_page(1)
        )
        self.next_btn.pack(side="left", padx=(8,0))

        # Bind configure event to update page size dynamically
        table_container.bind('<Configure>', self._on_table_configure)
        
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.tag_configure('odd', background=PANEL_COLOR)
        self.tree.tag_configure('even', background=PANEL_COLOR)
        self.tree.tag_configure('hover', background="#6d5a8a", foreground="#ffffff")
        
        # Button-style tags for action columns
        self.tree.tag_configure('action_button', foreground=ACCENT_COLOR, font=get_font(10, True), background=PANEL_COLOR)
        self.tree.tag_configure('action_button_delete', foreground="#ff6b6b", font=get_font(10, True), background=PANEL_COLOR)
        
        self.refresh_table()

    def refresh_sidebar(self):
        """Sidebar removed - table now takes full width."""
        pass

    def _refresh_all_sidebars(self):
        """Sidebar removed - no longer needed."""
        pass

    def refresh_table(self):
        rows = []
        for student in self.controller.students:
            college = next((p['college'] for p in self.controller.programs if p['code'] == student.get('program', '')), 'N/A')
            rows.append((student.get('id', ''), student.get('firstname', ''), student.get('lastname', ''), student.get('gender', ''), student.get('year', ''), student.get('program', ''), college))

        self._last_page_items = rows
        self.current_page = min(max(1, self.current_page), max(1, (len(rows) + self.page_size - 1) // self.page_size))
        self._render_page()
        self._last_hover = None
        self._last_hover = None

    def _render_page(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        total = len(self._last_page_items)
        per = self.page_size
        total_pages = max(1, (total + per - 1) // per)
        self.current_page = min(self.current_page, total_pages)
        start = (self.current_page - 1) * per
        end = start + per
        for idx, row in enumerate(self._last_page_items[start:end], start + 1):
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.tree.insert("", "end", values=row, tags=(tag,))
        
        for btn in self.page_buttons:
            btn.destroy()
        self.page_buttons.clear()
        
        start_page = max(1, self.current_page - 2)
        end_page = min(total_pages, start_page + 4)
        if end_page - start_page < 4:
            start_page = max(1, end_page - 4)
        
        for p in range(start_page, end_page + 1):
            is_current = p == self.current_page
            btn = ctk.CTkButton(
                self.pagination_frame, 
                text=str(p), 
                width=32, 
                height=28,
                fg_color=ACCENT_COLOR if is_current else "#3b3b3f",
                command=lambda page=p: self.goto_page(page)
            )
            btn.pack(side="left", padx=2)
            self.page_buttons.append(btn)
        
        self.prev_btn.configure(state=("normal" if self.current_page > 1 else "disabled"))
        self.next_btn.configure(state=("normal" if self.current_page < total_pages else "disabled"))
    
    def goto_page(self, page):
        self.current_page = page
        self._render_page()

    def change_page(self, delta):
        total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
        self.current_page = min(max(1, self.current_page + delta), total_pages)
        self._render_page()

    def _on_table_configure(self, event):
        # Adjust column widths based on available width with proportions
        available_width = max(self.table_container.winfo_width() - 20, 200)
        cols = ["ID", "First Name", "Last Name", "Gender", "Year", "Program", "College"]
        props = [0.10, 0.18, 0.19, 0.11, 0.09, 0.17, 0.16]
        for i, col in enumerate(cols):
            self.tree.column(col, width=max(int(available_width * props[i]), 50))
        
        # Get actual available height including padding around table
        available_height = self.table_container.winfo_height()
        # Account for: Treeview header (~30px) + padding top/bottom (~15+15px) + pagination controls (~50px)
        reserved_height = 30 + 30 + 50
        usable_height = max(available_height - reserved_height, 50)
        row_height = 48
        new_page_size = max(10, usable_height // row_height)
        
        if new_page_size != self.page_size:
            old_page = self.current_page
            self.page_size = new_page_size
            total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
            self.current_page = min(old_page, total_pages)
            self._render_page()

    def _update_sidebar_heights(self):
        """Sidebar removed - no longer needed."""
        pass

    def _on_tree_motion(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if getattr(self, '_last_hover', None) == row:
            return
        if getattr(self, '_last_hover', None):
            prev_row = self._last_hover
            # Check if the previous row still exists
            if prev_row in self.tree.get_children():
                self.tree.item(prev_row, tags=())
        # Set hover tag as the only tag for this row
        self.tree.item(row, tags=('hover',))
        self._last_hover = row

    def _on_tree_leave(self, event):
        if getattr(self, '_last_hover', None):
            prev_row = self._last_hover
            # Check if the row still exists
            if prev_row in self.tree.get_children():
                self.tree.item(prev_row, tags=())
            self._last_hover = None

    def on_row_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region in ('cell', 'tree'):
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)

    def filter_table(self, query):
        rows = []
        for student in self.controller.students:
            if (query in student.get('firstname', '').lower() or 
                query in student.get('lastname', '').lower() or
                query in student.get('id', '').lower()):
                college = next((p['college'] for p in self.controller.programs if p['code'] == student.get('program', '')), 'N/A')
                rows.append((student.get('id', ''), student.get('firstname', ''), student.get('lastname', ''), student.get('gender', ''), student.get('year', ''), student.get('program', ''), college))
        self._last_page_items = rows
        self.current_page = 1
        self._render_page()

    def on_column_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            try:
                idx = int(col.replace('#', '')) - 1
                col_id = self.tree['columns'][idx]
            except Exception:
                col_id = self.tree.heading(col, "text")
            
            # Remove arrow from previous sort column
            if self.sort_column and self.sort_column != col_id:
                self.tree.heading(self.sort_column, text=self.column_names.get(self.sort_column, self.sort_column))
            
            if self.sort_column == col_id:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = col_id
                self.sort_reverse = False
            
            self.update_sort_arrow()
            self.sort_table()
        elif region == "cell":
            # Show student profile on row click
            row = self.tree.identify_row(event.y)
            if not row:
                return
            try:
                row_data = self.tree.item(row)['values']
                student_id = row_data[0]
                self._show_student_profile(student_id)
            except Exception:
                pass
    
    def update_sort_arrow(self):
        """Update column heading to show sort arrow indicator."""
        if not self.sort_column:
            return
        
        # Get the original column name
        col_name = self.column_names.get(self.sort_column, self.sort_column)
        arrow = " ▼" if self.sort_reverse else " ▲"
        self.tree.heading(self.sort_column, text=col_name + arrow)
    
    def sort_table(self):
        if not self.sort_column:
            return
        
        # Sort the entire _last_page_items list
        col_index = self.tree['columns'].index(self.sort_column) if self.sort_column in self.tree['columns'] else 0
        self._last_page_items.sort(key=lambda x: self.try_numeric(str(x[col_index])), reverse=self.sort_reverse)
        
        # Re-render the current page
        self._render_page()
    
    @staticmethod
    def try_numeric(val):
        try:
            return float(val)
        except ValueError:
            return val

    def _show_student_profile(self, student_id):
        """Show student profile in a new window."""
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            messagebox.showerror("Error", "Student not found")
            return

        profile_window = ctk.CTkToplevel(self)
        profile_window.title(f"Student Profile: {student.get('firstname')} {student.get('lastname')}")
        profile_window.geometry("750x600")
        profile_window.configure(fg_color=BG_COLOR)
        profile_window.attributes('-topmost', True)

        profile_window.update_idletasks()
        x = (profile_window.winfo_screenwidth() // 2) - (profile_window.winfo_width() // 2)
        y = (profile_window.winfo_screenheight() // 2) - (profile_window.winfo_height() // 2)
        profile_window.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(profile_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with avatar and name
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR, height=100)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        avatar = ctk.CTkFrame(header, width=72, height=72, fg_color="#2d1f45", corner_radius=10)
        avatar.place(x=20, y=14)
        ctk.CTkLabel(avatar, text="👤", font=get_font(32)).pack()

        name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
        ctk.CTkLabel(header, text=name, font=get_font(16, True)).place(x=110, y=20)
        ctk.CTkLabel(header, text=f"ID: {student.get('id', '')}", text_color=TEXT_MUTED, font=get_font(11)).place(x=110, y=50)

        # Info card with scrollable content
        info_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        info_card.pack(fill="both", expand=True, pady=(0, 15))

        info_scroll = ctk.CTkScrollableFrame(info_card, fg_color="transparent")
        info_scroll.pack(fill="both", expand=True, padx=15, pady=15)

        # Information grid
        def add_info_row(label, value):
            row = ctk.CTkFrame(info_scroll, fg_color="transparent")
            row.pack(fill="x", pady=8)
            lbl = ctk.CTkLabel(row, text=label, font=get_font(14, True), text_color=TEXT_MUTED, width=100)
            lbl.pack(side="left", anchor="w")
            val = ctk.CTkLabel(row, text=value, font=get_font(15))
            val.pack(side="left", padx=(20, 0), anchor="w")

        add_info_row("First Name:", student.get('firstname', 'N/A'))
        add_info_row("Last Name:", student.get('lastname', 'N/A'))
        add_info_row("Gender:", student.get('gender', 'N/A'))
        add_info_row("Year Level:", student.get('year', 'N/A'))
        add_info_row("Program:", student.get('program', 'N/A'))
        
        program_name = next((p['name'] for p in self.controller.programs if p['code'] == student.get('program')), 'N/A')
        college_name = next((c['name'] for c in self.controller.colleges if c['code'] == next((p['college'] for p in self.controller.programs if p['code'] == student.get('program')), '')), 'N/A')
        add_info_row("College:", college_name)

        # Action buttons - only show if authenticated
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        def _edit():
            profile_window.destroy()
            self._edit_student(student_id)

        def _delete():
            if messagebox.askyesno("Confirm Delete", f"Delete student {name}?"):
                profile_window.destroy()
                self._delete_student_by_id(student_id)

        # Only show edit/delete buttons if user is logged in
        if self.controller.logged_in:
            ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a", text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))
        else:
            # Show message prompting login
            login_msg = ctk.CTkLabel(btn_frame, text="🔒 Log in to edit or delete", font=get_font(11), text_color=TEXT_MUTED)
            login_msg.pack(fill="x", pady=10)

    def _edit_student(self, student_id):
        """Edit student in a modal window."""
        # Check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to edit students.")
            return
        
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            messagebox.showerror("Error", "Student not found")
            return

        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Student")
        edit_window.geometry("520x480")
        edit_window.configure(fg_color=BG_COLOR)
        edit_window.attributes('-topmost', True)

        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")

        form_frame = ctk.CTkScrollableFrame(edit_window, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Edit Student Information", font=get_font(16, True)).pack(pady=(0, 20))

        ctk.CTkLabel(form_frame, text="Student ID", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        id_entry = ctk.CTkEntry(form_frame, height=40)
        id_entry.insert(0, student['id'])
        id_entry.configure(state="disabled")
        id_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="First Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        fname_entry = ctk.CTkEntry(form_frame, height=40)
        fname_entry.insert(0, student['firstname'])
        fname_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Last Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        lname_entry = ctk.CTkEntry(form_frame, height=40)
        lname_entry.insert(0, student['lastname'])
        lname_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Gender", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        gender_combo = StyledComboBox(form_frame, ["Male", "Female", "Other"])
        gender_combo.set(student['gender'])
        gender_combo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Year Level", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        year_combo = StyledComboBox(form_frame, ["1", "2", "3", "4", "5"])
        year_combo.set(student['year'])
        year_combo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Program", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        program_values = [p['code'] for p in self.controller.programs]
        program_widget = SearchableComboBox(form_frame, program_values)
        program_widget.set(student['program'])
        program_widget.pack(fill="x", pady=(0, 20))

        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            fname = fname_entry.get().strip()
            lname = lname_entry.get().strip()
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()

            if not fname:
                return False, "First Name is required"
            if not lname:
                return False, "Last Name is required"
            if not gender or gender == "Select Gender":
                return False, "Gender must be selected"
            if not year or year == "Select Year":
                return False, "Year Level must be selected"
            if not program:
                return False, "Program must be selected"

            if not fname.replace(" ", "").isalpha():
                return False, "First Name must contain only letters and spaces"
            if not lname.replace(" ", "").isalpha():
                return False, "Last Name must contain only letters and spaces"

            return True, ""

        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return

            student['firstname'] = fname_entry.get().strip().title()
            student['lastname'] = lname_entry.get().strip().title()
            student['gender'] = gender_combo.get()
            student['year'] = year_combo.get()
            student['program'] = program_widget.get()

            ok, msg = validate_student(student)
            if not ok:
                messagebox.showerror("Error", msg)
                return

            try:
                save_csv('student', self.controller.students)
            except Exception:
                messagebox.showerror("Error", "Failed to save student")
                return

            edit_window.destroy()
            self.refresh_table()
            messagebox.showinfo("Success", "Student updated successfully!")

        def delete():
            if messagebox.askyesno("Confirm Delete", f"Delete {student['id']}?"):
                self.controller.students.remove(student)
                save_csv('student', self.controller.students)
                edit_window.destroy()
                self.refresh_table()
                messagebox.showinfo("Success", "Student deleted successfully!")

        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(btn_frame, text="Save Changes", command=save, height=40, fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Delete", command=delete, height=40, fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _delete_student_by_id(self, student_id):
        """Delete a student by ID."""
        # Check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete students.")
            return
        
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            messagebox.showerror("Error", "Student not found")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete student {student_id}?"):
            self.controller.students.remove(student)
            save_csv('student', self.controller.students)
            self.refresh_table()
            messagebox.showinfo("Success", "Student deleted successfully!")

    def delete_student(self):
        """Legacy method - use _delete_student_by_id instead."""
        pass

    def add_student(self):
        # Check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to add students.")
            return
        
        modal = ctk.CTkToplevel(self)
        modal.title("Add Student")
        screen_height = modal.winfo_screenheight()
        height = min(600, int(screen_height * 0.7))
        modal.geometry(f"500x{height}")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"500x{height}+{x}+{y}")
        
        form_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New Student Enrollment", font=get_font(16, True)).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Student ID", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        id_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., 2025-1234", height=40)
        id_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="First Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        fname_entry = ctk.CTkEntry(form_frame, placeholder_text="First Name", height=40)
        fname_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Last Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        lname_entry = ctk.CTkEntry(form_frame, placeholder_text="Last Name", height=40)
        lname_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Gender", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        gender_combo = StyledComboBox(form_frame, ["Male", "Female", "Other"])
        gender_combo.set("Male")
        gender_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Year Level", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        year_combo = StyledComboBox(form_frame, ["1", "2", "3", "4", "5"])
        year_combo.set("1")
        year_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        program_values = [p['code'] for p in self.controller.programs]
        program_widget = SearchableComboBox(form_frame, program_values)
        if program_values:
            program_widget.set(program_values[0])
        program_widget.pack(fill="x", pady=(0, 20))
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            student_id = id_entry.get().strip()
            fname = fname_entry.get().strip()
            lname = lname_entry.get().strip()
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()
            
            # Check empty fields
            if not student_id:
                return False, "Student ID is required"
            if not fname:
                return False, "First Name is required"
            if not lname:
                return False, "Last Name is required"
            if not gender or gender == "Select Gender":
                return False, "Gender must be selected"
            if not year or year == "Select Year":
                return False, "Year Level must be selected"
            if not program:
                return False, "Program must be selected"
            
            # Check ID format
            if len(student_id) < 3:
                return False, "Student ID must be at least 3 characters"
            
            # Check for duplicate ID
            if any(s['id'] == student_id for s in self.controller.students):
                return False, "Student ID already exists"
            
            # Check name format (only letters and spaces)
            if not fname.replace(" ", "").isalpha():
                return False, "First Name must contain only letters and spaces"
            if not lname.replace(" ", "").isalpha():
                return False, "Last Name must contain only letters and spaces"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return
            
            student_id = id_entry.get().strip()
            fname = fname_entry.get().strip().title()  # Capitalize
            lname = lname_entry.get().strip().title()  # Capitalize
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()
            
            new_student = {
                'id': student_id,
                'firstname': fname,
                'lastname': lname,
                'gender': gender,
                'year': year,
                'program': program,
            }
            ok, msg = validate_student(new_student)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            
            self.controller.students.append(new_student)
            save_csv('student', self.controller.students)
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            modal.destroy()
            messagebox.showinfo("Success", "Student added successfully!")
        
        ctk.CTkButton(form_frame, text="Save Student", command=save, height=40, 
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(fill="x")

    def import_data(self):
        """Import students from CSV file."""
        # Check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to import students.")
            return
        
        from tkinter import filedialog
        import csv
        
        file_path = filedialog.askopenfilename(
            title="Select CSV file to import",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            imported_count = 0
            error_count = 0
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_ids = set()
                
                # Load existing IDs
                try:
                    import csv as csv_module
                    with open('students.csv', 'r', encoding='utf-8') as existing:
                        existing_reader = csv_module.DictReader(existing)
                        for row in existing_reader:
                            existing_ids.add(row['id'])
                except:
                    pass
                
                rows_to_add = []
                for row_num, row in enumerate(reader, start=2):
                    # Validate the row
                    is_valid, error_msg = validate_student({
                        'id': row.get('id', ''),
                        'firstname': row.get('firstname', ''),
                        'lastname': row.get('lastname', ''),
                        'program': row.get('program', ''),
                        'year': row.get('year', ''),
                        'gender': row.get('gender', '')
                    })
                    
                    if not is_valid:
                        error_count += 1
                        errors.append(f"Row {row_num}: {error_msg}")
                        continue
                    
                    # Check if ID already exists
                    if row.get('id') in existing_ids:
                        error_count += 1
                        errors.append(f"Row {row_num}: Student ID {row.get('id')} already exists")
                        continue
                    
                    rows_to_add.append(row)
                    existing_ids.add(row.get('id'))
                    imported_count += 1
                
                # Append to CSV file
                if rows_to_add:
                    with open('students.csv', 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=['id', 'firstname', 'lastname', 'program', 'year', 'gender'])
                        for row in rows_to_add:
                            writer.writerow({
                                'id': row.get('id', ''),
                                'firstname': row.get('firstname', ''),
                                'lastname': row.get('lastname', ''),
                                'program': row.get('program', ''),
                                'year': row.get('year', ''),
                                'gender': row.get('gender', '')
                            })
                    
                    self.refresh_table()
            
            # Show results
            if error_count == 0:
                messagebox.showinfo("Import Success", f"Successfully imported {imported_count} students!")
            else:
                error_msg = "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                messagebox.showwarning("Import Complete", 
                    f"Imported {imported_count} students.\n{error_count} errors:\n\n{error_msg}")
        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")




