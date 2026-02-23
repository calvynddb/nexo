"""
Card and container components for EduManage SIS.

Provides `DepthCard` as a thin wrapper around `CTkFrame` to keep card
styling centralized.
"""

import customtkinter as ctk
from config import get_font, PANEL_COLOR, BORDER_COLOR, TEXT_MUTED


class DepthCard(ctk.CTkFrame):
    """Frame component with depth styling."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StatCard(DepthCard):
    """Reusable stat card matching the Students sidebar style.

    Parameters mirror the previous `stat_card` helper used in `StudentsView`.
    """
    def __init__(self, parent, icon_img, num, sub, *, height=120, **kwargs):
        super().__init__(parent, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR, height=height, **kwargs)
        self.pack(fill="x", pady=(0, 12))
        self.pack_propagate(False)
        icon_f = ctk.CTkFrame(self, width=45, height=45, fg_color="#2d1f45", corner_radius=10)
        icon_f.place(x=20, y=16)
        lbl = ctk.CTkLabel(icon_f, image=icon_img, text="")
        lbl.image = icon_img
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self, text=num, font=get_font(22, True)).place(x=20, y=54)
        ctk.CTkLabel(self, text=sub, font=get_font(12), text_color=TEXT_MUTED).place(x=20, y=84)
