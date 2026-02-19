"""
View classes for Students, Programs, and Colleges
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
    TEXT_MUTED, BORDER_COLOR, COLOR_PALETTE
)
from components import DepthCard, SmartSearchEntry, setup_treeview_style, placeholder_image
from data import validate_student, validate_program, validate_college
from data import save_csv

# ==========================================
# STUDENTS VIEW
# ==========================================
class StudentsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.sort_column = None
        self.sort_reverse = False
        self.setup_ui()

    def setup_ui(self):
        # Table Container
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))
        
        setup_treeview_style()
        cols = ("ID", "First Name", "Last Name", "Gender", "Year", "Program", "College")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", style="Treeview")
        
        for c in cols: 
            self.tree.heading(c, text=c.upper())
            
        # FIX: Reduced base widths, all set to stretch proportionally, and all centered
        self.tree.column("ID", width=80, anchor="center", stretch=True)
        self.tree.column("First Name", width=110, anchor="center", stretch=True)
        self.tree.column("Last Name", width=110, anchor="center", stretch=True)
        self.tree.column("Gender", width=70, anchor="center", stretch=True)
        self.tree.column("Year", width=60, anchor="center", stretch=True)
        self.tree.column("Program", width=80, anchor="center", stretch=True)
        self.tree.column("College", width=80, anchor="center", stretch=True)
        
        self.tree.pack(fill="both", expand=True, padx=15, pady=(15, 8))

        # Pagination controls
        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=(0,12))
        self.current_page = 1
        self.page_size = 25
        self._last_page_items = []

        self.prev_btn = ctk.CTkButton(ctrl, text="◀ Prev", width=90, command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left")
        self.page_label = ctk.CTkLabel(ctrl, text="Page 1/1")
        self.page_label.pack(side="left", padx=8)
        self.next_btn = ctk.CTkButton(ctrl, text="Next ▶", width=90, command=lambda: self.change_page(1))
        self.next_btn.pack(side="left")
        # page size selector
        self.page_size_menu = ctk.CTkOptionMenu(ctrl, values=[10,25,50,100], command=self.set_page_size)
        self.page_size_menu.set(self.page_size)
        self.page_size_menu.pack(side="right")
        
        self.tree.bind("<Double-1>", self.on_row_select)
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        # row tag styles for subtle striping
        self.tree.tag_configure('odd', background=PANEL_COLOR)
        self.tree.tag_configure('even', background="#2b2b2d")
        self.tree.tag_configure('hover', background="#2f2f31")
        
        # New Sidebar Charts Panel
        right_panel = ctk.CTkFrame(self, width=240, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        self.right_panel = right_panel
        self.right_panel = right_panel
        ctk.CTkLabel(right_panel, text="OVERVIEW STATS", font=("Segoe UI Variable", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # Create small square placeholders for the stat icons and keep references
        self._stat_img_students = placeholder_image(size=28, color=ACCENT_COLOR)
        self._stat_img_programs = placeholder_image(size=28, color="#8b5cf6")
        self._stat_img_colleges = placeholder_image(size=28, color="#4f6bed")

        self.stat_card(right_panel, self._stat_img_students, str(len(self.controller.students)), "Total Students")
        self.stat_card(right_panel, self._stat_img_programs, str(len(self.controller.programs)), "Total Programs")
        self.stat_card(right_panel, self._stat_img_colleges, str(len(self.controller.colleges)), "Total Colleges")
        
        self.refresh_table()

    def refresh_sidebar(self):
        """Rebuild the right-panel overview stats for StudentsView."""
        # clear existing
        for w in self.right_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.right_panel, text="OVERVIEW STATS", font=("Segoe UI Variable", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # recreate placeholders and stat cards
        self._stat_img_students = placeholder_image(size=28, color=ACCENT_COLOR)
        self._stat_img_programs = placeholder_image(size=28, color="#8b5cf6")
        self._stat_img_colleges = placeholder_image(size=28, color="#4f6bed")

        self.stat_card(self.right_panel, self._stat_img_students, str(len(self.controller.students)), "Total Students")
        self.stat_card(self.right_panel, self._stat_img_programs, str(len(self.controller.programs)), "Total Programs")
        self.stat_card(self.right_panel, self._stat_img_colleges, str(len(self.controller.colleges)), "Total Colleges")
        # keep symmetry: ensure same number and sizing of cards
        # (stat_card already enforces uniform height)
        # no extra action required

    def _refresh_all_sidebars(self):
        """Trigger refresh_sidebar() on every view in the DashboardFrame."""
        try:
            from dashboard import DashboardFrame
            df = self.controller.frames.get(DashboardFrame)
            if not df:
                return
            for v in df.views.values():
                try:
                    if hasattr(v, 'refresh_sidebar'):
                        v.refresh_sidebar()
                except Exception:
                    pass
        except Exception:
            pass

    def refresh_table(self):
        # Build list of rows
        rows = []
        for student in self.controller.students:
            college = next((p['college'] for p in self.controller.programs if p['code'] == student.get('program', '')), 'N/A')
            rows.append((student.get('id', ''), student.get('firstname', ''), student.get('lastname', ''), student.get('gender', ''), student.get('year', ''), student.get('program', ''), college))

        self._last_page_items = rows
        self.current_page = min(max(1, self.current_page), max(1, (len(rows) + self.page_size - 1) // self.page_size))
        self._render_page()
        self._last_hover = None

    def _render_page(self):
        # clear tree
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
        self.page_label.configure(text=f"Page {self.current_page}/{total_pages}")
        self.prev_btn.configure(state=("normal" if self.current_page > 1 else "disabled"))
        self.next_btn.configure(state=("normal" if self.current_page < total_pages else "disabled"))

    def change_page(self, delta):
        self.current_page = max(1, self.current_page + delta)
        self._render_page()

    def set_page_size(self, val):
        try:
            self.page_size = int(val)
        except Exception:
            return
        self.current_page = 1
        self._render_page()

    def _on_tree_motion(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if getattr(self, '_last_hover', None) == row:
            return
        # remove hover tag from previous
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
        # add hover tag
        tags = list(self.tree.item(row, 'tags'))
        if 'hover' not in tags:
            tags.append('hover')
            self.tree.item(row, tags=tags)
        self._last_hover = row

    def _on_tree_leave(self, event):
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
            self._last_hover = None

    def on_row_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region in ('cell', 'tree'):
            item = self.tree.identify_row(event.y)
            if item:
                # show action dialog
                self._show_action_dialog(item)

    def _show_action_dialog(self, item):
        row_values = self.tree.item(item)['values']
        dlg = ctk.CTkToplevel(self)
        dlg.title("Row Actions")
        dlg.geometry("300x160")
        dlg.attributes('-topmost', True)
        ctk.CTkLabel(dlg, text=str(row_values), wraplength=280).pack(pady=12, padx=8)
        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=8)
        def _edit():
            self.tree.selection_set(item)
            dlg.destroy()
            self.on_row_select(None)
        def _delete():
            self.tree.selection_set(item)
            dlg.destroy()
            self.delete_student()
        ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a").pack(side="left", expand=True, fill="x", padx=(6,0))
        ctk.CTkButton(dlg, text="Cancel", command=dlg.destroy).pack(pady=(6,0))
        
    def _on_tree_motion(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if getattr(self, '_last_hover', None) == row:
            return
        # remove hover tag from previous
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
        # add hover tag
        tags = list(self.tree.item(row, 'tags'))
        if 'hover' not in tags:
            tags.append('hover')
            self.tree.item(row, tags=tags)
        self._last_hover = row

    def _on_tree_leave(self, event):
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
            self._last_hover = None

    def on_row_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region in ('cell', 'tree'):
            item = self.tree.identify_row(event.y)
            if item:
                # show action dialog
                self._show_action_dialog(item)

    def _show_action_dialog(self, item):
        row_values = self.tree.item(item)['values']
        dlg = ctk.CTkToplevel(self)
        dlg.title("Row Actions")
        dlg.geometry("300x160")
        dlg.attributes('-topmost', True)
        ctk.CTkLabel(dlg, text=str(row_values), wraplength=280).pack(pady=12, padx=8)
        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=8)
        def _edit():
            self.tree.selection_set(item)
            dlg.destroy()
            self.on_row_select(None)
        def _delete():
            self.tree.selection_set(item)
            dlg.destroy()
            self.delete_student()
        ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a").pack(side="left", expand=True, fill="x", padx=(6,0))
        ctk.CTkButton(dlg, text="Cancel", command=dlg.destroy).pack(pady=(6,0))

    def filter_table(self, query):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for student in self.controller.students:
            if (query in student.get('firstname', '').lower() or 
                query in student.get('lastname', '').lower() or
                query in student.get('id', '').lower()):
                college = next((p['college'] for p in self.controller.programs if p['code'] == student.get('program', '')), 'N/A')
                self.tree.insert("", "end", values=(
                    student.get('id', ''), 
                    student.get('firstname', ''), 
                    student.get('lastname', ''), 
                    student.get('gender', ''), 
                    student.get('year', ''), 
                    student.get('program', ''), 
                    college
                ))

    def on_column_click(self, event):
        """Handle column header click for sorting."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            # map #n to actual column id
            try:
                idx = int(col.replace('#', '')) - 1
                col_id = self.tree['columns'][idx]
            except Exception:
                col_id = self.tree.heading(col, "text")
            if self.sort_column == col_id:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = col_id
                self.sort_reverse = False
            self.sort_table()
    
    def sort_table(self):
        """Sort table by current sort column."""
        if not self.sort_column:
            return
        
        items = [(self.tree.set(k, self.sort_column), k) for k in self.tree.get_children("")]
        items.sort(key=lambda x: self.try_numeric(x[0]), reverse=self.sort_reverse)
        
        for idx, (val, k) in enumerate(items):
            self.tree.move(k, "", idx)
    
    @staticmethod
    def try_numeric(val):
        """Try to convert string to number for sorting."""
        try:
            return float(val)
        except ValueError:
            return val

    def stat_card(self, parent, icon_img, num, sub):
        # Uniform stat card height for symmetry
        height = 120
        card = DepthCard(parent, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR, height=height)
        card.pack(fill="x", pady=(0, 12))
        card.pack_propagate(False)
        icon_f = ctk.CTkFrame(card, width=45, height=45, fg_color="#303035", corner_radius=10)
        icon_f.place(x=20, y=16)
        lbl = ctk.CTkLabel(icon_f, image=icon_img, text="")
        lbl.image = icon_img
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text=num, font=("Segoe UI Variable", 22, "bold")).place(x=20, y=54)
        ctk.CTkLabel(card, text=sub, font=("Segoe UI Variable", 12), text_color=TEXT_MUTED).place(x=20, y=84)
        return card

    # ... keep refresh_table, on_column_click, add_student, etc. from your original code ...
    def add_student(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Student")
        screen_height = modal.winfo_screenheight()
        height = min(600, int(screen_height * 0.7))
        modal.geometry(f"500x{height}")
        modal.attributes('-topmost', True)
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"500x{height}+{x}+{y}")
        
        form_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New Student Enrollment", font=("Segoe UI Variable", 16, "bold")).pack(pady=(0, 20))
        
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
        gender_combo = ctk.CTkOptionMenu(form_frame, values=["Male", "Female", "Other"], height=40)
        gender_combo.set("Male")
        gender_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Year Level", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        year_combo = ctk.CTkOptionMenu(form_frame, values=["1", "2", "3", "4", "5"], height=40)
        year_combo.set("1")
        year_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        program_values = [p['code'] for p in self.controller.programs]
        # Always use SmartSearchEntry for program selection for faster typing
        program_widget = SmartSearchEntry(form_frame, program_values, placeholder="Select Program", height=40)
        if program_values:
            program_widget.insert(0, program_values[0])
        program_widget.pack(fill="x", pady=(0, 20))
        
        def save():
            student_id = id_entry.get().strip()
            fname = fname_entry.get().strip()
            lname = lname_entry.get().strip()
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()
            
            if not all([student_id, fname, lname, gender, year, program]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if any(s['id'] == student_id for s in self.controller.students):
                messagebox.showerror("Error", "Student ID already exists")
                return
            
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
            # update right panel stats
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            modal.destroy()
            messagebox.showinfo("Success", "Student added successfully!")
        
        ctk.CTkButton(form_frame, text="Save Student", command=save, height=40, 
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(fill="x")

    def show_context_menu_student(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.on_row_select(None))
        menu.add_command(label="Delete", command=self.delete_student)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_student(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        student_id = row_data[0]
        
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            messagebox.showerror("Error", "Student not found")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete {student['firstname']} {student['lastname']}?"):
            self.controller.students.remove(student)
            save_csv('student', self.controller.students)
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            messagebox.showinfo("Success", "Student deleted successfully!")

    def on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Student")
        edit_window.geometry("450x550")
        edit_window.attributes('-topmost', True)
        
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        form_frame = ctk.CTkScrollableFrame(edit_window, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text=f"Edit Student - {row_data[0]}", font=("Segoe UI Variable", 16, "bold")).pack(pady=(0, 20))
        
        student = next((s for s in self.controller.students if s['id'] == row_data[0]), None)
        if not student:
            messagebox.showerror("Error", "Student not found")
            return
        
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
        gender_combo = ctk.CTkOptionMenu(form_frame, values=["Male", "Female", "Other"], height=40)
        gender_combo.set(student['gender'])
        gender_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Year Level", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        year_combo = ctk.CTkOptionMenu(form_frame, values=["1", "2", "3", "4", "5"], height=40)
        year_combo.set(student['year'])
        year_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        program_values = [p['code'] for p in self.controller.programs]
        # Always use SmartSearchEntry for program selection in edit form as well
        program_widget = SmartSearchEntry(form_frame, program_values, placeholder="Select Program", height=40)
        program_widget.insert(0, student['program'])
        program_widget.pack(fill="x", pady=(0, 20))
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        def save():
            student['firstname'] = fname_entry.get().strip()
            student['lastname'] = lname_entry.get().strip()
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
                messagebox.showerror("Error", "Failed to save student data")
                return
            edit_window.destroy()
            self.refresh_table()
            messagebox.showinfo("Success", "Student updated successfully!")
        
        def delete():
            if messagebox.askyesno("Confirm Delete", f"Delete {student['firstname']} {student['lastname']}?"):
                self.controller.students.remove(student)
                save_csv('student', self.controller.students)
                edit_window.destroy()
                self.refresh_table()
                messagebox.showinfo("Success", "Student deleted successfully!")
        
        ctk.CTkButton(button_frame, text="Save Changes", command=save, height=40, 
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=40, 
                     fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))


# ==========================================
# PROGRAMS VIEW
# ==========================================
class ProgramsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        # We need two columns: 0 for the table, 1 for the sidebar
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) 
        self.setup_ui()

    def setup_ui(self):
        # 1. Initialize the Table Container (Left Side)
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))

        setup_treeview_style()
        cols = ("#", "Code", "Program Name", "College", "Students")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", style="Treeview")
        for c in cols:
            self.tree.heading(c, text=c.upper())
            # center all columns and allow stretching
            self.tree.column(c, anchor="center", stretch=True, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.tag_configure('odd', background=PANEL_COLOR)
        self.tree.tag_configure('even', background="#272729")
        self.tree.tag_configure('hover', background="#303035")

        # Pagination controls for Programs view
        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=(6,12))
        self.current_page = 1
        self.page_size = 25
        self._last_page_items = []
        self.prev_btn = ctk.CTkButton(ctrl, text="◀ Prev", width=90, command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left")
        self.page_label = ctk.CTkLabel(ctrl, text="Page 1/1")
        self.page_label.pack(side="left", padx=8)
        self.next_btn = ctk.CTkButton(ctrl, text="Next ▶", width=90, command=lambda: self.change_page(1))
        self.next_btn.pack(side="left")
        self.page_size_menu = ctk.CTkOptionMenu(ctrl, values=[10,25,50,100], command=self.set_page_size)
        self.page_size_menu.set(self.page_size)
        self.page_size_menu.pack(side="right")

        # auto-fit columns to container width
        def _on_table_config(e):
            total = max(e.width - 20, 200)
            # proportions: idx, code, name, college, students
            props = [0.06, 0.14, 0.6, 0.12, 0.08]
            for i, col in enumerate(cols):
                self.tree.column(col, width=max(int(total * props[i]), 50))

        table_container.bind('<Configure>', _on_table_config)

        # 2. Initialize the Right Panel (The part that was missing!)
        right_panel = ctk.CTkFrame(self, width=280, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        self.right_panel = right_panel

        # 3. Add the Progress Bars to the newly created right_panel
        top_card = DepthCard(right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        top_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_card, text="Top Enrolled", font=("Segoe UI Variable", 13, "bold")).pack(anchor="w", padx=20, pady=15)
        
        enrollments = {}
        for student in self.controller.students:
            prog = student.get('program', 'Unknown')
            enrollments[prog] = enrollments.get(prog, 0) + 1
        
        sorted_progs = sorted(enrollments.items(), key=lambda x: x[1], reverse=True)[:3]
        colors_list = [ACCENT_COLOR, "#8b5cf6", "#4f6bed"]
        
        for i, (p, val) in enumerate(sorted_progs):
            f = ctk.CTkFrame(top_card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=p, font=("Segoe UI Variable", 13, "bold")).pack(side="left")
            ctk.CTkLabel(f, text=f"{val} Students", text_color=TEXT_MUTED).pack(side="right")
            bar = ctk.CTkProgressBar(top_card, progress_color=colors_list[i], fg_color="#303035", height=8)
            bar.pack(fill="x", padx=20, pady=(0, 15))
            bar.set(min(val / 50, 1.0))

        # 4. Add the Donut Chart to the newly created right_panel
        dist_card = DepthCard(right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        dist_card.pack(fill="both", expand=True)
        ctk.CTkLabel(dist_card, text="College Program Distribution", font=("Segoe UI Variable", 13, "bold")).pack(anchor="w", padx=20, pady=15)

        self.create_donut_chart(dist_card)
        self.right_dist_card = dist_card
        self.refresh_table()

    def _refresh_all_sidebars(self):
        """Trigger refresh_sidebar() on every view in the DashboardFrame."""
        try:
            from dashboard import DashboardFrame
            df = self.controller.frames.get(DashboardFrame)
            if not df:
                return
            for v in df.views.values():
                try:
                    if hasattr(v, 'refresh_sidebar'):
                        v.refresh_sidebar()
                except Exception:
                    pass
        except Exception:
            pass

    def create_donut_chart(self, parent):
        if not MATPLOTLIB_AVAILABLE:
            ctk.CTkLabel(parent, text="Matplotlib required", text_color=TEXT_MUTED).pack(pady=40)
            return
        
        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)

        # Specific colors per college code
        color_map = {
            'CCS': '#87CEEB',   # Sky Blue
            'COE': '#800000',   # Maroon
            'CSM': '#FF0000',   # Red
            'CED': '#00008B',   # Dark Blue
            'CASS': '#008000',  # Green (capitalized alias 'CASS')
            'Cass': '#008000',
            'CEBA': '#FFD700',  # Gold
            'CHS': '#FFFFFF',   # White
        }

        # Collect counts per college code present in programs
        college_counts = {}
        for p in self.controller.programs:
            coll = p.get('college', 'Unknown')
            college_counts[coll] = college_counts.get(coll, 0) + 1

        labels = list(college_counts.keys())
        data = [college_counts[k] for k in labels]

        if sum(data) > 0:
            # assign colors from map, fallback to COLOR_PALETTE or a default
            colors = [color_map.get(k, COLOR_PALETTE[i % len(COLOR_PALETTE)]) for i, k in enumerate(labels)]
            wedges, texts = ax.pie(data, colors=colors, startangle=90,
                                   wedgeprops=dict(width=0.4, edgecolor=PANEL_COLOR, linewidth=2))
            ax.axis('equal')

            # Draw the chart canvas first
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=(6, 2))

            # Legend: place as two-column vertical grid below the chart
            legend_frame = ctk.CTkFrame(parent, fg_color="transparent")
            legend_frame.pack(side="bottom", pady=(6, 12), padx=8)

            for i, (lab, col) in enumerate(zip(labels, colors)):
                r = i // 2
                c = i % 2
                f = ctk.CTkFrame(legend_frame, fg_color="transparent")
                f.grid(row=r, column=c, padx=8, pady=4, sticky="w")
                # small color square
                sq = ctk.CTkFrame(f, width=14, height=14, fg_color=col, corner_radius=3)
                sq.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(f, text=f"{lab} ({college_counts.get(lab,0)})", font=("Segoe UI Variable", 10)).pack(side="left")

    def refresh_table(self):
        rows = []
        for idx, p in enumerate(self.controller.programs, 1):
            student_count = len([s for s in self.controller.students if s.get('program') == p['code']])
            rows.append((idx, p['code'], p['name'], p['college'], student_count))
        self._last_page_items = rows
        self.current_page = min(max(1, self.current_page), max(1, (len(rows) + self.page_size - 1) // self.page_size))
        self._render_page()
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
        self.page_label.configure(text=f"Page {self.current_page}/{total_pages}")
        self.prev_btn.configure(state=("normal" if self.current_page > 1 else "disabled"))
        self.next_btn.configure(state=("normal" if self.current_page < total_pages else "disabled"))

    def change_page(self, delta):
        self.current_page = max(1, self.current_page + delta)
        self._render_page()

    def set_page_size(self, val):
        try:
            self.page_size = int(val)
        except Exception:
            return
        self.current_page = 1
        self._render_page()

    def refresh_sidebar(self):
        """Rebuild the programs right-panel (donut + legend)."""
        for w in self.right_panel.winfo_children():
            w.destroy()
        # Recreate Top Enrolled and Donut sections
        # Top Enrolled
        top_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        top_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_card, text="Top Enrolled", font=("Segoe UI Variable", 13, "bold")).pack(anchor="w", padx=20, pady=15)

        enrollments = {}
        for student in self.controller.students:
            prog = student.get('program', 'Unknown')
            enrollments[prog] = enrollments.get(prog, 0) + 1
        sorted_progs = sorted(enrollments.items(), key=lambda x: x[1], reverse=True)[:3]
        colors_list = [ACCENT_COLOR, "#8b5cf6", "#4f6bed"]
        for i, (p, val) in enumerate(sorted_progs):
            f = ctk.CTkFrame(top_card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=p, font=("Segoe UI Variable", 13, "bold")).pack(side="left")
            ctk.CTkLabel(f, text=f"{val} Students", text_color=TEXT_MUTED).pack(side="right")
            bar = ctk.CTkProgressBar(top_card, progress_color=colors_list[i], fg_color="#303035", height=8)
            bar.pack(fill="x", padx=20, pady=(0, 15))
            bar.set(min(val / 50, 1.0))

        # Donut
        dist_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        dist_card.pack(fill="both", expand=True)
        ctk.CTkLabel(dist_card, text="College Program Distribution", font=("Segoe UI Variable", 13, "bold")).pack(anchor="w", padx=20, pady=15)
        self.create_donut_chart(dist_card)

    def _on_tree_motion(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if getattr(self, '_last_hover', None) == row:
            return
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
        tags = list(self.tree.item(row, 'tags'))
        if 'hover' not in tags:
            tags.append('hover')
            self.tree.item(row, tags=tags)
        self._last_hover = row

    def _on_tree_leave(self, event):
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
            self._last_hover = None

    def on_row_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region in ('cell', 'tree'):
            item = self.tree.identify_row(event.y)
            if item:
                self._show_action_dialog(item)

    def _show_action_dialog(self, item):
        row_values = self.tree.item(item)['values']
        dlg = ctk.CTkToplevel(self)
        dlg.title("Row Actions")
        dlg.geometry("340x160")
        dlg.attributes('-topmost', True)
        ctk.CTkLabel(dlg, text=str(row_values), wraplength=320).pack(pady=12, padx=8)
        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=8)
        def _edit():
            self.tree.selection_set(item)
            dlg.destroy()
            self.on_row_select(None)
        def _delete():
            self.tree.selection_set(item)
            dlg.destroy()
            self.delete_program()
        ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a").pack(side="left", expand=True, fill="x", padx=(6,0))
        ctk.CTkButton(dlg, text="Cancel", command=dlg.destroy).pack(pady=(6,0))

    def filter_table(self, query):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        idx = 1
        for p in self.controller.programs:
            if (query in p.get('name', '').lower() or 
                query in p.get('code', '').lower() or
                query in p.get('college', '').lower()):
                student_count = len([s for s in self.controller.students if s.get('program') == p['code']])
                self.tree.insert("", "end", values=(idx, p['code'], p['name'], p['college'], student_count))
                idx += 1

    def on_column_click(self, event):
        """Handle column header click for sorting."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            # map #n to actual column id
            try:
                idx = int(col.replace('#', '')) - 1
                col_id = self.tree['columns'][idx]
            except Exception:
                col_id = self.tree.heading(col, "text")
            if self.sort_column == col_id:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = col_id
                self.sort_reverse = False
            self.sort_table()
    
    def sort_table(self):
        """Sort table by current sort column."""
        if not self.sort_column:
            return
        
        items = [(self.tree.set(k, self.sort_column), k) for k in self.tree.get_children("")]
        items.sort(key=lambda x: self.try_numeric(x[0]), reverse=self.sort_reverse)
        
        for idx, (val, k) in enumerate(items):
            self.tree.move(k, "", idx)
    
    @staticmethod
    def try_numeric(val):
        """Try to convert string to number for sorting."""
        try:
            return float(val)
        except ValueError:
            return val


    def add_program(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Program")
        screen_height = modal.winfo_screenheight()
        height = min(400, int(screen_height * 0.6))
        modal.geometry(f"500x{height}")
        modal.attributes('-topmost', True)
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"500x{height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New Program", font=("Segoe UI Variable", 16, "bold")).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Program Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., BSCS", height=40)
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="Program Name", height=40)
        name_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College", font=FONT_BOLD).pack(anchor="w")
        college_values = [c['code'] for c in self.controller.colleges]
        if len(college_values) > 10:
            college_widget = SmartSearchEntry(form_frame, college_values, placeholder="Select College", height=40)
            if college_values:
                college_widget.insert(0, college_values[0])
        else:
            college_widget = ctk.CTkOptionMenu(form_frame, values=college_values, height=40)
            college_widget.set(college_values[0] if college_values else "")
        college_widget.pack(fill="x", pady=(0, 20))
        
        def save():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            college = college_widget.get()
            
            if not all([code, name, college]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if any(p['code'] == code for p in self.controller.programs):
                messagebox.showerror("Error", "Program code already exists")
                return

            new_prog = {'code': code, 'name': name, 'college': college}
            ok, msg = validate_program(new_prog)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            
            self.controller.programs.append(new_prog)
            save_csv('program', self.controller.programs)
            self.refresh_table()
            try:
                # rebuild the distribution card
                for w in self.right_panel.winfo_children():
                    w.destroy()
                # Recreate dist card and legend
                dist_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
                dist_card.pack(fill="both", expand=True)
                ctk.CTkLabel(dist_card, text="College Program Distribution", font=("Segoe UI Variable", 13, "bold")).pack(anchor="w", padx=20, pady=15)
                self.create_donut_chart(dist_card)
                try:
                    self._refresh_all_sidebars()
                except Exception:
                    pass
            except Exception:
                pass
            modal.destroy()
            messagebox.showinfo("Success", "Program added successfully!")
        
        ctk.CTkButton(form_frame, text="Save Program", command=save, height=40,
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(fill="x")

            # ensure sidebar updates when program added
            

    def show_context_menu_program(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.on_row_select(None))
        menu.add_command(label="Delete", command=self.delete_program)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_program(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        prog_code = row_data[1]
        
        program = next((p for p in self.controller.programs if p['code'] == prog_code), None)
        if not program:
            messagebox.showerror("Error", "Program not found")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete {prog_code}?"):
            self.controller.programs.remove(program)
            save_csv('program', self.controller.programs)
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            messagebox.showinfo("Success", "Program deleted successfully!")

    def on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        prog_code = row_data[1]
        
        program = next((p for p in self.controller.programs if p['code'] == prog_code), None)
        if not program:
            return
        
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Program")
        edit_window.geometry("450x350")
        edit_window.attributes('-topmost', True)
        
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        form_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text=f"Edit Program - {prog_code}", font=("Segoe UI Variable", 16, "bold")).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Program Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, height=40)
        code_entry.insert(0, program['code'])
        code_entry.configure(state="disabled")
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, height=40)
        name_entry.insert(0, program['name'])
        name_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College", font=FONT_BOLD).pack(anchor="w")
        college_values = [c['code'] for c in self.controller.colleges]
        if len(college_values) > 10:
            college_widget = SmartSearchEntry(form_frame, college_values, placeholder="Select College", height=40)
            college_widget.insert(0, program['college'])
        else:
            college_widget = ctk.CTkOptionMenu(form_frame, values=college_values, height=40)
            college_widget.set(program['college'])
        college_widget.pack(fill="x", pady=(0, 20))
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def save():
            program['name'] = name_entry.get().strip()
            program['college'] = college_widget.get()
            ok, msg = validate_program(program)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            try:
                save_csv('program', self.controller.programs)
            except Exception:
                messagebox.showerror("Error", "Failed to save program")
                return
            edit_window.destroy()
            self.refresh_table()
            messagebox.showinfo("Success", "Program updated successfully!")
        
        def delete():
            if messagebox.askyesno("Confirm Delete", f"Delete {program['code']}?"):
                self.controller.programs.remove(program)
                save_csv('program', self.controller.programs)
                edit_window.destroy()
                self.refresh_table()
                messagebox.showinfo("Success", "Program deleted successfully!")
        
        ctk.CTkButton(button_frame, text="Save Changes", command=save, height=40,
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=40,
                     fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))


# ==========================================
# COLLEGES VIEW
# ==========================================
class CollegesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) # Space for the sidebar
        self.sort_column = None
        self.sort_reverse = False
        self.setup_ui()

    def setup_ui(self):
        # Table Container
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))
        
        setup_treeview_style()
        cols = ("#", "College Code", "College Name")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", style="Treeview")
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor="center", stretch=True, width=120)
        self.tree.pack(fill="both", expand=True, padx=15, pady=15)
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        # row tag styles for subtle striping
        self.tree.tag_configure('odd', background=PANEL_COLOR)
        self.tree.tag_configure('even', background="#2b2b2d")
        self.tree.tag_configure('hover', background="#2f2f31")

        # auto-fit columns to container width
        def _on_table_config(e):
            total = max(e.width - 20, 200)
            props = [0.06, 0.32, 0.62]
            for i, col in enumerate(cols):
                self.tree.column(col, width=max(int(total * props[i]), 60))

        table_container.bind('<Configure>', _on_table_config)

        # Initialize Right Panel
        right_panel = ctk.CTkFrame(self, width=240, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        
        ctk.CTkLabel(right_panel, text="DIRECTORY FACTS", font=("Segoe UI Variable", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # Add larger Fact Cards to the Right Panel (use image placeholders)
        self._fact_img_students = placeholder_image(size=22, color=ACCENT_COLOR)
        self._fact_img_programs = placeholder_image(size=22, color="#8b5cf6")
        self._fact_img_colleges = placeholder_image(size=22, color="#4f6bed")

        total_students = str(len(self.controller.students))
        total_programs = str(len(self.controller.programs))
        total_colleges = str(len(self.controller.colleges))
        avg_students_per_program = "0"
        try:
            avg_students_per_program = f"{len(self.controller.students) // max(len(self.controller.programs),1)}"
        except Exception:
            avg_students_per_program = "0"

        self.fact_card(right_panel, "TOTAL STUDENTS", total_students, self._fact_img_students, "#1d2335", height=120)
        self.fact_card(right_panel, "TOTAL PROGRAMS", total_programs, self._fact_img_programs, "#2c2c30", height=120)
        self.fact_card(right_panel, "TOTAL COLLEGES", total_colleges, self._fact_img_colleges, "#2c2c30", height=120)
        self.fact_card(right_panel, "AVG STUDENTS/PROGRAM", avg_students_per_program, self._fact_img_students, "#2c2c30", height=120, expand=True)

        self.refresh_table()

    def fact_card(self, parent, title, val, icon_img, color, height=80, expand=False):
        card = DepthCard(parent, fg_color=color, corner_radius=10, border_width=2, border_color=BORDER_COLOR, height=height)
        if expand:
            card.pack(fill="both", expand=True, pady=8)
        else:
            card.pack(fill="x", pady=8)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Segoe UI Variable", 11, "bold"), text_color=ACCENT_COLOR).place(x=15, y=14)
        ctk.CTkLabel(card, text=val, font=("Segoe UI Variable", 22, "bold")).place(x=15, y=36)
        lbl = ctk.CTkLabel(card, image=icon_img, text="")
        lbl.image = icon_img
        lbl.place(relx=0.85, rely=0.5, anchor="center")

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for idx, c in enumerate(self.controller.colleges, 1):
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.tree.insert("", "end", values=(idx, c['code'], c['name']), tags=(tag,))

        # reset hover tracker
        self._last_hover = None

    def refresh_sidebar(self):
        """Rebuild the right-panel fact cards for CollegesView."""
        for w in self.right_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.right_panel, text="DIRECTORY FACTS", font=("Segoe UI Variable", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # recreate placeholders and fact cards
        self._fact_img_students = placeholder_image(size=22, color=ACCENT_COLOR)
        self._fact_img_programs = placeholder_image(size=22, color="#8b5cf6")
        self._fact_img_colleges = placeholder_image(size=22, color="#4f6bed")

        total_students = str(len(self.controller.students))
        total_programs = str(len(self.controller.programs))
        total_colleges = str(len(self.controller.colleges))
        avg_students_per_program = "0"
        try:
            avg_students_per_program = f"{len(self.controller.students) // max(len(self.controller.programs),1)}"
        except Exception:
            avg_students_per_program = "0"

        self.fact_card(self.right_panel, "TOTAL STUDENTS", total_students, self._fact_img_students, "#1d2335", height=120)
        self.fact_card(self.right_panel, "TOTAL PROGRAMS", total_programs, self._fact_img_programs, "#2c2c30", height=120)
        self.fact_card(self.right_panel, "TOTAL COLLEGES", total_colleges, self._fact_img_colleges, "#2c2c30", height=120)
        self.fact_card(self.right_panel, "AVG STUDENTS/PROGRAM", avg_students_per_program, self._fact_img_students, "#2c2c30", height=120, expand=True)

    def _on_tree_motion(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if getattr(self, '_last_hover', None) == row:
            return
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
        tags = list(self.tree.item(row, 'tags'))
        if 'hover' not in tags:
            tags.append('hover')
            self.tree.item(row, tags=tags)
        self._last_hover = row

    def _on_tree_leave(self, event):
        if getattr(self, '_last_hover', None):
            prev_tags = list(self.tree.item(self._last_hover, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._last_hover, tags=prev_tags)
            self._last_hover = None

    def on_row_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region in ('cell', 'tree'):
            item = self.tree.identify_row(event.y)
            if item:
                self._show_action_dialog(item)

    def _show_action_dialog(self, item):
        row_values = self.tree.item(item)['values']
        dlg = ctk.CTkToplevel(self)
        dlg.title("Row Actions")
        dlg.geometry("340x160")
        dlg.attributes('-topmost', True)
        ctk.CTkLabel(dlg, text=str(row_values), wraplength=320).pack(pady=12, padx=8)
        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=8)
        def _edit():
            self.tree.selection_set(item)
            dlg.destroy()
            self.on_row_select(None)
        def _delete():
            self.tree.selection_set(item)
            dlg.destroy()
            self.delete_college()
        ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a").pack(side="left", expand=True, fill="x", padx=(6,0))
        ctk.CTkButton(dlg, text="Cancel", command=dlg.destroy).pack(pady=(6,0))

    def filter_table(self, query):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        idx = 1
        for c in self.controller.colleges:
            if (query in c.get('name', '').lower() or 
                query in c.get('code', '').lower()):
                self.tree.insert("", "end", values=(idx, c['code'], c['name']))
                idx += 1

    def on_column_click(self, event):
        """Handle column header click for sorting."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            # map #n to actual column id
            try:
                idx = int(col.replace('#', '')) - 1
                col_id = self.tree['columns'][idx]
            except Exception:
                col_id = self.tree.heading(col, "text")
            if self.sort_column == col_id:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = col_id
                self.sort_reverse = False
            self.sort_table()
    
    def sort_table(self):
        """Sort table by current sort column."""
        if not self.sort_column:
            return
        
        items = [(self.tree.set(k, self.sort_column), k) for k in self.tree.get_children("")]
        items.sort(key=lambda x: self.try_numeric(x[0]), reverse=self.sort_reverse)
        
        for idx, (val, k) in enumerate(items):
            self.tree.move(k, "", idx)
    
    @staticmethod
    def try_numeric(val):
        """Try to convert string to number for sorting."""
        try:
            return float(val)
        except ValueError:
            return val

    def add_college(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add College")
        screen_height = modal.winfo_screenheight()
        height = min(350, int(screen_height * 0.55))
        modal.geometry(f"450x{height}")
        modal.attributes('-topmost', True)
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"450x{height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New College", font=("Segoe UI Variable", 16, "bold")).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="College Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., COE", height=40)
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="College Name", height=40)
        name_entry.pack(fill="x", pady=(0, 20))
        
        def save():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            
            if not code or not name:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            if any(c['code'] == code for c in self.controller.colleges):
                messagebox.showerror("Error", "College code already exists")
                return
            new_col = {'code': code, 'name': name}
            ok, msg = validate_college(new_col)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            self.controller.colleges.append(new_col)
            save_csv('college', self.controller.colleges)
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            modal.destroy()
            messagebox.showinfo("Success", "College added successfully!")
        
        ctk.CTkButton(form_frame, text="Save College", command=save, height=40,
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(fill="x")

    def show_context_menu_college(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.on_row_select(None))
        menu.add_command(label="Delete", command=self.delete_college)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_college(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        college_code = row_data[1]
        
        college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
        if not college:
            messagebox.showerror("Error", "College not found")
            return
        
        has_programs = any(p['college'] == college['code'] for p in self.controller.programs)
        if has_programs:
            messagebox.showerror("Error", "Cannot delete college with associated programs")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete {college_code}?"):
            self.controller.colleges.remove(college)
            save_csv('college', self.controller.colleges)
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            messagebox.showinfo("Success", "College deleted successfully!")

    def on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        college_code = row_data[1]
        
        college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
        if not college:
            return
        
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit College")
        edit_window.geometry("400x300")
        edit_window.attributes('-topmost', True)
        
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        form_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text=f"Edit College - {college_code}", 
                    font=("Segoe UI Variable", 16, "bold")).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="College Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, height=40)
        code_entry.insert(0, college['code'])
        code_entry.configure(state="disabled")
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, height=40)
        name_entry.insert(0, college['name'])
        name_entry.pack(fill="x", pady=(0, 20))
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def save():
            college['name'] = name_entry.get().strip()
            save_csv('college', self.controller.colleges)
            edit_window.destroy()
            self.refresh_table()
            messagebox.showinfo("Success", "College updated successfully!")
        
        def delete():
            has_programs = any(p['college'] == college['code'] for p in self.controller.programs)
            if has_programs:
                messagebox.showerror("Error", "Cannot delete college with associated programs")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Delete {college['code']}?"):
                self.controller.colleges.remove(college)
                save_csv('college', self.controller.colleges)
                edit_window.destroy()
                self.refresh_table()
                messagebox.showinfo("Success", "College deleted successfully!")
        
        ctk.CTkButton(button_frame, text="Save Changes", command=save, height=40,
                     fg_color=ACCENT_COLOR, text_color="black", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=40,
                     fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))
