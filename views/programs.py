"""
Programs view module extracted from original views.py
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
from ui import DepthCard, SmartSearchEntry, StyledComboBox, setup_treeview_style, placeholder_image, get_icon
from data import validate_program, save_csv


class ProgramsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.sort_column = None
        self.sort_reverse = False
        self.column_names = {}  # Store original column names
        self.setup_ui()

    def setup_ui(self):
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))

        setup_treeview_style()
        cols = ("#", "Code", "Program Name", "College", "Students")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", style="Treeview")
        
        # Store original column names
        for c in cols:
            self.column_names[c] = c.upper()
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor="center", stretch=False, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.tag_configure('odd', background=PANEL_COLOR)
        self.tree.tag_configure('even', background=PANEL_COLOR)
        self.tree.tag_configure('hover', background="#6d5a8a", foreground="#ffffff")

        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=(6,12))
        self.current_page = 1
        self.page_size = 12
        self._last_page_items = []
        self._last_hover = None
        self.table_container = table_container
        
        self.prev_btn = ctk.CTkButton(ctrl, text="◀ Prev", width=80, fg_color=ACCENT_COLOR, hover_color="#6d5a8a", text_color="white", command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left", padx=(0,8))
        
        self.pagination_frame = ctk.CTkFrame(ctrl, fg_color="transparent")
        self.pagination_frame.pack(side="left", padx=8)
        self.page_buttons = []
        
        self.next_btn = ctk.CTkButton(ctrl, text="Next ▶", width=80, fg_color=ACCENT_COLOR, hover_color="#6d5a8a", text_color="white", command=lambda: self.change_page(1))
        self.next_btn.pack(side="left", padx=(8,0))

        def _on_table_config(e):
            total = max(e.width - 20, 200)
            # Adjust column proportions to fit better
            props = [0.08, 0.15, 0.50, 0.15, 0.12]
            for i, col in enumerate(cols):
                self.tree.column(col, width=max(int(total * props[i]), 50))
            self._on_table_configure(e)

        table_container.bind('<Configure>', _on_table_config)

        right_panel = ctk.CTkFrame(self, width=280, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        self.right_panel = right_panel

        top_card = DepthCard(right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        top_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_card, text="Top Enrolled", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)
        
        enrollments = {}
        for student in self.controller.students:
            prog = student.get('program', 'Unknown')
            enrollments[prog] = enrollments.get(prog, 0) + 1
        
        sorted_progs = sorted(enrollments.items(), key=lambda x: x[1], reverse=True)[:3]
        colors_list = [ACCENT_COLOR, "#a78bfa", "#6366f1"]
        
        for i, (p, val) in enumerate(sorted_progs):
            f = ctk.CTkFrame(top_card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=p, font=get_font(13, True)).pack(side="left")
            ctk.CTkLabel(f, text=f"{val} Students", text_color=TEXT_MUTED).pack(side="right")
            bar = ctk.CTkProgressBar(top_card, progress_color=colors_list[i], fg_color="#2A1F3D", height=8)
            bar.pack(fill="x", padx=20, pady=(0, 15))
            try:
                from ui.utils import animate_progress
                animate_progress(bar, min(val / 50, 1.0), duration=420)
            except Exception:
                bar.set(min(val / 50, 1.0))

        dist_card = DepthCard(right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        dist_card.pack(fill="both", expand=True)
        ctk.CTkLabel(dist_card, text="College Program Distribution", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)

        self.create_donut_chart(dist_card)
        self.right_dist_card = dist_card
        self.refresh_table()

    def _refresh_all_sidebars(self):
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

        color_map = {
            'CCS': '#87CEEB',
            'COE': '#800000',
            'CSM': '#FF0000',
            'CED': '#00008B',
            'CASS': '#008000',
            'Cass': '#008000',
            'CEBA': '#FFD700',
            'CHS': '#FFFFFF',
        }

        college_counts = {}
        for p in self.controller.programs:
            coll = p.get('college', 'Unknown')
            college_counts[coll] = college_counts.get(coll, 0) + 1

        labels = list(college_counts.keys())
        data = [college_counts[k] for k in labels]

        if sum(data) > 0:
            colors = [color_map.get(k, COLOR_PALETTE[i % len(COLOR_PALETTE)]) for i, k in enumerate(labels)]
            wedges, texts = ax.pie(data, colors=colors, startangle=90,
                                   wedgeprops=dict(width=0.4, edgecolor=PANEL_COLOR, linewidth=2))
            ax.axis('equal')

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=(6, 2))

            legend_frame = ctk.CTkFrame(parent, fg_color="transparent")
            legend_frame.pack(side="bottom", pady=(6, 12), padx=8)

            for i, (lab, col) in enumerate(zip(labels, colors)):
                r = i // 2
                c = i % 2
                f = ctk.CTkFrame(legend_frame, fg_color="transparent")
                f.grid(row=r, column=c, padx=8, pady=4, sticky="w")
                sq = ctk.CTkFrame(f, width=14, height=14, fg_color=col, corner_radius=3)
                sq.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(f, text=f"{lab} ({college_counts.get(lab,0)})", font=get_font(10)).pack(side="left")

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

    def refresh_sidebar(self):
        for w in self.right_panel.winfo_children():
            w.destroy()
        top_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        top_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_card, text="Top Enrolled", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)

        enrollments = {}
        for student in self.controller.students:
            prog = student.get('program', 'Unknown')
            enrollments[prog] = enrollments.get(prog, 0) + 1
        sorted_progs = sorted(enrollments.items(), key=lambda x: x[1], reverse=True)[:3]
        colors_list = [ACCENT_COLOR, "#a78bfa", "#6366f1"]
        for i, (p, val) in enumerate(sorted_progs):
            f = ctk.CTkFrame(top_card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=p, font=get_font(13, True)).pack(side="left")
            ctk.CTkLabel(f, text=f"{val} Students", text_color=TEXT_MUTED).pack(side="right")
            bar = ctk.CTkProgressBar(top_card, progress_color=colors_list[i], fg_color="#2A1F3D", height=8)
            bar.pack(fill="x", padx=20, pady=(0, 15))
            try:
                from ui.utils import animate_progress
                animate_progress(bar, min(val / 50, 1.0), duration=420)
            except Exception:
                bar.set(min(val / 50, 1.0))

        dist_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        dist_card.pack(fill="both", expand=True)
        ctk.CTkLabel(dist_card, text="College Program Distribution", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)
        self.create_donut_chart(dist_card)

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
                prog_code = row_data[1]  # Program code
                self._show_program_info(prog_code)

    def filter_table(self, query):
        rows = []
        for idx, p in enumerate(self.controller.programs, 1):
            if (query in p.get('name', '').lower() or 
                query in p.get('code', '').lower() or
                query in p.get('college', '').lower()):
                student_count = len([s for s in self.controller.students if s.get('program') == p['code']])
                rows.append((idx, p['code'], p['name'], p['college'], student_count))
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

    def _show_program_info(self, prog_code):
        """Show program information in a window."""
        program = next((p for p in self.controller.programs if p['code'] == prog_code), None)
        if not program:
            messagebox.showerror("Error", "Program not found")
            return

        profile_window = ctk.CTkToplevel(self)
        profile_window.title(f"Program: {prog_code}")
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
        ctk.CTkLabel(avatar, text="📚", font=get_font(32)).pack()

        ctk.CTkLabel(header, text=program.get('name', 'N/A'), font=get_font(16, True)).place(x=110, y=20)
        ctk.CTkLabel(header, text=f"Code: {program.get('code', '')}", text_color=TEXT_MUTED, font=get_font(11)).place(x=110, y=50)

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

        add_info_row("Program Name:", program.get('name', 'N/A'))
        add_info_row("Program Code:", program.get('code', 'N/A'))
        add_info_row("College:", program.get('college', 'N/A'))
        
        student_count = len([s for s in self.controller.students if s.get('program') == prog_code])
        add_info_row("Enrolled Students:", str(student_count))

        # Action buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        def _edit():
            profile_window.destroy()
            # Trigger the edit dialog by simulating a row selection
            selection = self.tree.selection()
            if not selection:
                self.on_row_select(None)
            else:
                self.on_row_select(None)

        def _delete():
            if messagebox.askyesno("Confirm Delete", f"Delete program {prog_code}?"):
                profile_window.destroy()
                program_obj = next((p for p in self.controller.programs if p['code'] == prog_code), None)
                if program_obj:
                    self.controller.programs.remove(program_obj)
                    save_csv('program', self.controller.programs)
                    self.refresh_table()
                    messagebox.showinfo("Success", "Program deleted successfully!")

        ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a", text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def add_program(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Program")
        screen_height = modal.winfo_screenheight()
        height = min(400, int(screen_height * 0.6))
        modal.geometry(f"500x{height}")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"500x{height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New Program", font=get_font(16, True)).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Program Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., BSCS", height=40)
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="Program Name", height=40)
        name_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College", font=FONT_BOLD).pack(anchor="w")
        college_values = [c['code'] for c in self.controller.colleges]
        college_widget = StyledComboBox(form_frame, college_values)
        college_widget.set(college_values[0] if college_values else "")
        college_widget.pack(fill="x", pady=(0, 20))
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            college = college_widget.get()
            
            if not code:
                return False, "Program Code is required"
            
            if not name:
                return False, "Program Name is required"
            
            if not college:
                return False, "College must be selected"
            
            if len(code) < 2:
                return False, "Program Code must be at least 2 characters"
            
            if not code.isalnum():
                return False, "Program Code must contain only letters and numbers"
            
            if not name.replace(" ", "").isalpha():
                return False, "Program Name must contain only letters and spaces"
            
            if any(p['code'] == code for p in self.controller.programs):
                return False, "Program Code already exists"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return
            
            code = code_entry.get().strip()
            name = name_entry.get().strip().title()
            college = college_widget.get()

            new_prog = {'code': code, 'name': name, 'college': college}
            ok, msg = validate_program(new_prog)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            
            self.controller.programs.append(new_prog)
            save_csv('program', self.controller.programs)
            self.refresh_table()
            try:
                for w in self.right_panel.winfo_children():
                    w.destroy()
                dist_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
                dist_card.pack(fill="both", expand=True)
                ctk.CTkLabel(dist_card, text="College Program Distribution", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)
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
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(fill="x")

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
        edit_window.geometry("480x380")
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
        ctk.CTkLabel(header, text=f"{prog_code}", font=get_font(16, True)).place(x=16, y=14)
        ctk.CTkLabel(header, text="Program", font=get_font(11), text_color=TEXT_MUTED).place(x=16, y=44)
        
        # Form card
        form_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        form_card.pack(fill="both", expand=True)
        form_frame = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(form_frame, text="Edit Program Information", font=get_font(13, True)).pack(anchor="w", pady=(0, 12))
        
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
        college_widget = StyledComboBox(form_frame, college_values)
        college_widget.set(program['college'])
        college_widget.pack(fill="x", pady=(0, 20))
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            name = name_entry.get().strip()
            college = college_widget.get()
            
            if not name:
                return False, "Program Name is required"
            
            if not college:
                return False, "College must be selected"
            
            if not name.replace(" ", "").isalpha():
                return False, "Program Name must contain only letters and spaces"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return
            
            program['name'] = name_entry.get().strip().title()
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
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=40,
                     fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def import_data(self):
        """Import programs from CSV file."""
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
                    with open('programs.csv', 'r', encoding='utf-8') as existing:
                        existing_reader = csv_module.DictReader(existing)
                        for row in existing_reader:
                            existing_codes.add(row['code'])
                except:
                    pass
                
                rows_to_add = []
                for row_num, row in enumerate(reader, start=2):
                    # Validate the row
                    is_valid, error_msg = validate_program({
                        'code': row.get('code', ''),
                        'name': row.get('name', ''),
                        'college': row.get('college', '')
                    })
                    
                    if not is_valid:
                        error_count += 1
                        errors.append(f"Row {row_num}: {error_msg}")
                        continue
                    
                    # Check if code already exists
                    if row.get('code') in existing_codes:
                        error_count += 1
                        errors.append(f"Row {row_num}: Program code {row.get('code')} already exists")
                        continue
                    
                    rows_to_add.append(row)
                    existing_codes.add(row.get('code'))
                    imported_count += 1
                
                # Append to CSV file
                if rows_to_add:
                    with open('programs.csv', 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=['code', 'name', 'college'])
                        for row in rows_to_add:
                            writer.writerow({
                                'code': row.get('code', ''),
                                'name': row.get('name', ''),
                                'college': row.get('college', '')
                            })
                    
                    self.refresh_table()
            
            # Show results
            if error_count == 0:
                messagebox.showinfo("Import Success", f"Successfully imported {imported_count} programs!")
            else:
                error_msg = "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                messagebox.showwarning("Import Complete", 
                    f"Imported {imported_count} programs.\n{error_count} errors:\n\n{error_msg}")
        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")

