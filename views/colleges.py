"""
Colleges view module extracted from original views.py
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

from config import (
    FONT_MAIN, FONT_BOLD, BG_COLOR, PANEL_COLOR, ACCENT_COLOR, 
    TEXT_MUTED, BORDER_COLOR, COLOR_PALETTE, TEXT_PRIMARY
)
from config import get_font
from ui import DepthCard, placeholder_image, setup_treeview_style, get_icon
from data import validate_college, save_csv


class CollegesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.sort_column = None
        self.sort_reverse = False
        self.column_names = {}  # Store original column names
        self.current_page = 1
        self.page_size = 25
        self._last_page_items = []
        self.setup_ui()

    def setup_ui(self):
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))
        
        setup_treeview_style()
        cols = ("#", "College Code", "College Name")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", style="Treeview")
        
        # Store original column names
        for c in cols:
            self.column_names[c] = c.upper()
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor="center", stretch=False, width=120)
        self.tree.pack(fill="both", expand=True, padx=15, pady=15)
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.tag_configure('odd', background=PANEL_COLOR)
        self.tree.tag_configure('even', background=PANEL_COLOR)
        self.tree.tag_configure('hover', background="#6d5a8a", foreground="#ffffff")

        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=(6,12))
        self.table_container = table_container
        self._last_hover = None
        
        self.prev_btn = ctk.CTkButton(ctrl, text="◀ Prev", width=80, fg_color=ACCENT_COLOR, hover_color="#6d5a8a", text_color="white", command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left", padx=(0,8))
        
        self.pagination_frame = ctk.CTkFrame(ctrl, fg_color="transparent")
        self.pagination_frame.pack(side="left", padx=8)
        self.page_buttons = []
        
        self.next_btn = ctk.CTkButton(ctrl, text="Next ▶", width=80, fg_color=ACCENT_COLOR, hover_color="#6d5a8a", text_color="white", command=lambda: self.change_page(1))
        self.next_btn.pack(side="left", padx=(8,0))

        # table_container configure binding will be set below after cards are created

        right_panel = ctk.CTkFrame(self, width=280, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        
        ctk.CTkLabel(right_panel, text="DIRECTORY FACTS", font=get_font(11, True), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # Use icons like Students view and keep references to avoid GC
        self._fact_img_students = get_icon("users", size=28, fallback_color=ACCENT_COLOR)
        self._fact_img_programs = get_icon("books", size=28, fallback_color="#8b5cf6")
        self._fact_img_colleges = get_icon("building", size=28, fallback_color="#4f6bed")

        total_students = str(len(self.controller.students))
        total_programs = str(len(self.controller.programs))
        total_colleges = str(len(self.controller.colleges))
        avg_students_per_program = "0"
        try:
            avg_students_per_program = f"{len(self.controller.students) // max(len(self.controller.programs),1)}"
        except Exception:
            avg_students_per_program = "0"

        # Create stat cards matching Students view and remember them so we can size them evenly
        from ui import StatCard
        self._sidebar_cards = []
        c = StatCard(right_panel, self._fact_img_students, str(total_students), "TOTAL STUDENTS", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(right_panel, self._fact_img_programs, str(total_programs), "TOTAL PROGRAMS", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(right_panel, self._fact_img_colleges, str(total_colleges), "TOTAL COLLEGES", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(right_panel, self._fact_img_students, str(avg_students_per_program), "AVG STUDENTS/PROGRAM", height=120)
        self._sidebar_cards.append(c)

        # Defer a height update until after layout completes
        self.after(50, self._update_sidebar_heights)

        # Keep sidebar cards the same total height as the table by updating on resize
        def _on_table_config(e):
            total = max(e.width - 20, 200)
            props = [0.06, 0.32, 0.62]
            for i, col in enumerate(cols):
                self.tree.column(col, width=max(int(total * props[i]), 60))
            self._on_table_configure(e)
            self._update_sidebar_heights()

        table_container.bind('<Configure>', _on_table_config)

        self.refresh_table()

    def fact_card(self, parent, title, val, icon_img, color, height=80, expand=False):
        card = DepthCard(parent, fg_color=color, corner_radius=10, border_width=2, border_color=BORDER_COLOR, height=height)
        if expand:
            card.pack(fill="both", expand=True, pady=8)
        else:
            card.pack(fill="x", pady=8)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=get_font(11, True), text_color=ACCENT_COLOR).place(x=15, y=14)
        ctk.CTkLabel(card, text=val, font=get_font(22, True)).place(x=15, y=36)
        lbl = ctk.CTkLabel(card, image=icon_img, text="")
        lbl.image = icon_img
        lbl.place(relx=0.85, rely=0.5, anchor="center")

    def refresh_table(self):
        rows = []
        for idx, c in enumerate(self.controller.colleges, 1):
            rows.append((idx, c['code'], c['name']))
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
        self.current_page = max(1, self.current_page + delta)
        self._render_page()

    def _on_table_configure(self, event):
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
        try:
            if not hasattr(self, '_sidebar_cards') or not self._sidebar_cards:
                return
            total_h = self.table_container.winfo_height()
            # subtract header/title and some padding
            header_h = 48
            spacing = 12 * (len(self._sidebar_cards) + 1)
            avail = max(80, total_h - header_h - spacing)
            per = max(60, avail // len(self._sidebar_cards))
            from ui.utils import animate_height
            for c in self._sidebar_cards:
                try:
                    animate_height(c, per, duration=220)
                except Exception:
                    pass
        except Exception:
            pass

    def refresh_sidebar(self):
        for w in self.right_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.right_panel, text="DIRECTORY FACTS", font=get_font(11, True), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        self._fact_img_students = get_icon("users", size=28, fallback_color=ACCENT_COLOR)
        self._fact_img_programs = get_icon("books", size=28, fallback_color="#8b5cf6")
        self._fact_img_colleges = get_icon("building", size=28, fallback_color="#4f6bed")

        total_students = str(len(self.controller.students))
        total_programs = str(len(self.controller.programs))
        total_colleges = str(len(self.controller.colleges))
        avg_students_per_program = "0"
        try:
            avg_students_per_program = f"{len(self.controller.students) // max(len(self.controller.programs),1)}"
        except Exception:
            avg_students_per_program = "0"

        # rebuild sidebar cards and store references (use StatCard style)
        from ui import StatCard
        self._sidebar_cards = []
        c = StatCard(self.right_panel, self._fact_img_students, total_students, "TOTAL STUDENTS", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(self.right_panel, self._fact_img_programs, total_programs, "TOTAL PROGRAMS", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(self.right_panel, self._fact_img_colleges, total_colleges, "TOTAL COLLEGES", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(self.right_panel, self._fact_img_students, avg_students_per_program, "AVG STUDENTS/PROGRAM", height=120)
        self._sidebar_cards.append(c)

        # ensure heights get updated after layout changes (defer to allow layout)
        self.after(50, self._update_sidebar_heights)


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
                row_data = self.tree.item(item)['values']
                college_code = row_data[1]  # College code
                self._show_college_info(college_code)

    def _show_action_dialog(self, item):
        row_values = self.tree.item(item)['values']
        dlg = ctk.CTkToplevel(self)
        dlg.title("Row Actions")
        dlg.geometry("380x160")
        dlg.configure(fg_color=BG_COLOR)
        dlg.attributes('-topmost', True)
        
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - (dlg.winfo_width() // 2)
        y = (dlg.winfo_screenheight() // 2) - (dlg.winfo_height() // 2)
        dlg.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(dlg, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Card showing college info
        info_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        info_card.pack(fill="x", pady=(0, 12))
        info_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=12)
        
        ctk.CTkLabel(info_frame, text=f"{row_values[2]}", font=get_font(14, True)).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Code: {row_values[1]}", font=get_font(11), text_color=TEXT_MUTED).pack(anchor="w")
        
        # Button frame
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")
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

    def _show_college_info(self, college_code):
        """Show college information in a window."""
        college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
        if not college:
            messagebox.showerror("Error", "College not found")
            return

        profile_window = ctk.CTkToplevel(self)
        profile_window.title(f"College: {college_code}")
        profile_window.geometry("750x550")
        profile_window.configure(fg_color=BG_COLOR)
        profile_window.attributes('-topmost', True)

        profile_window.update_idletasks()
        x = (profile_window.winfo_screenwidth() // 2) - (profile_window.winfo_width() // 2)
        y = (profile_window.winfo_screenheight() // 2) - (profile_window.winfo_height() // 2)
        profile_window.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(profile_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with code and name
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR, height=100)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        avatar = ctk.CTkFrame(header, width=72, height=72, fg_color="#2d1f45", corner_radius=10)
        avatar.place(x=20, y=14)
        ctk.CTkLabel(avatar, text="🏫", font=get_font(32)).pack()

        ctk.CTkLabel(header, text=college.get('name', 'N/A'), font=get_font(16, True)).place(x=110, y=20)
        ctk.CTkLabel(header, text=f"Code: {college.get('code', '')}", text_color=TEXT_MUTED, font=get_font(11)).place(x=110, y=50)

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

        add_info_row("College Name:", college.get('name', 'N/A'))
        add_info_row("College Code:", college.get('code', 'N/A'))
        
        program_count = len([p for p in self.controller.programs if p.get('college') == college_code])
        add_info_row("Programs:", str(program_count))
        
        student_count = len([s for s in self.controller.students for p in self.controller.programs if p.get('college') == college_code and s.get('program') == p.get('code')])
        add_info_row("Students:", str(student_count))

        # Action buttons - only show if authenticated
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        def _edit():
            profile_window.destroy()
            # Trigger the edit dialog by finding and selecting the college
            selection = self.tree.selection()
            if not selection:
                self.on_row_select(None)
            else:
                self.on_row_select(None)

        def _delete():
            if messagebox.askyesno("Confirm Delete", f"Delete college {college_code}?"):
                profile_window.destroy()
                college_obj = next((c for c in self.controller.colleges if c['code'] == college_code), None)
                if college_obj:
                    self.controller.colleges.remove(college_obj)
                    save_csv('college', self.controller.colleges)
                    self.refresh_table()
                    messagebox.showinfo("Success", "College deleted successfully!")

        # Only show edit/delete buttons if user is logged in
        if self.controller.logged_in:
            ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a", text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))
        else:
            # Show message prompting login
            login_msg = ctk.CTkLabel(btn_frame, text="🔒 Log in to edit or delete", font=get_font(11), text_color=TEXT_MUTED)
            login_msg.pack(fill="x", pady=10)

    def filter_table(self, query):
        rows = []
        for idx, c in enumerate(self.controller.colleges, 1):
            if (query in c.get('name', '').lower() or 
                query in c.get('code', '').lower()):
                rows.append((idx, c['code'], c['name']))
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

    def add_college(self):
        # Check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to add colleges.")
            return
        
        modal = ctk.CTkToplevel(self)
        modal.title("Add College")
        screen_height = modal.winfo_screenheight()
        height = min(350, int(screen_height * 0.55))
        modal.geometry(f"450x{height}")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"450x{height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New College", font=get_font(16, True)).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="College Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., COE", height=40)
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="College Name", height=40)
        name_entry.pack(fill="x", pady=(0, 20))
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            
            if not code:
                return False, "College Code is required"
            
            if not name:
                return False, "College Name is required"
            
            if len(code) < 2:
                return False, "College Code must be at least 2 characters"
            
            if not code.isalpha():
                return False, "College Code must contain only letters"
            
            if not name.replace(" ", "").isalpha():
                return False, "College Name must contain only letters and spaces"
            
            if any(c['code'] == code for c in self.controller.colleges):
                return False, "College Code already exists"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return
            
            code = code_entry.get().strip()
            name = name_entry.get().strip().title()
            
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
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(fill="x")

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
        # Check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete colleges.")
            return
        
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
        edit_window.geometry("420x320")
        edit_window.configure(fg_color=BG_COLOR)
        edit_window.attributes('-topmost', True)
        
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(edit_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Header card
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR, height=80)
        header.pack(fill="x", pady=(0, 12))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{college_code}", font=get_font(16, True)).place(x=16, y=14)
        ctk.CTkLabel(header, text="College", font=get_font(11), text_color=TEXT_MUTED).place(x=16, y=44)
        
        # Form card
        form_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        form_card.pack(fill="both", expand=True)
        form_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
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
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            name = name_entry.get().strip()
            
            if not name:
                return False, "College Name is required"
            
            if not name.replace(" ", "").isalpha():
                return False, "College Name must contain only letters and spaces"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return
            
            college['name'] = name_entry.get().strip().title()
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
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=40,
                     fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def import_data(self):
        """Import colleges from CSV file."""
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
                existing_codes = set()
                
                # Load existing codes
                try:
                    import csv as csv_module
                    with open('colleges.csv', 'r', encoding='utf-8') as existing:
                        existing_reader = csv_module.DictReader(existing)
                        for row in existing_reader:
                            existing_codes.add(row['code'])
                except:
                    pass
                
                rows_to_add = []
                for row_num, row in enumerate(reader, start=2):
                    # Validate the row
                    is_valid, error_msg = validate_college({
                        'code': row.get('code', ''),
                        'name': row.get('name', '')
                    })
                    
                    if not is_valid:
                        error_count += 1
                        errors.append(f"Row {row_num}: {error_msg}")
                        continue
                    
                    # Check if code already exists
                    if row.get('code') in existing_codes:
                        error_count += 1
                        errors.append(f"Row {row_num}: College code {row.get('code')} already exists")
                        continue
                    
                    rows_to_add.append(row)
                    existing_codes.add(row.get('code'))
                    imported_count += 1
                
                # Append to CSV file
                if rows_to_add:
                    with open('colleges.csv', 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=['code', 'name'])
                        for row in rows_to_add:
                            writer.writerow({
                                'code': row.get('code', ''),
                                'name': row.get('name', '')
                            })
                    
                    self.refresh_table()
            
            # Show results
            if error_count == 0:
                messagebox.showinfo("Import Success", f"Successfully imported {imported_count} colleges!")
            else:
                error_msg = "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                messagebox.showwarning("Import Complete", 
                    f"Imported {imported_count} colleges.\n{error_count} errors:\n\n{error_msg}")
        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")

