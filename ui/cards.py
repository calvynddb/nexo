"""
Card and container components for EduManage SIS.
"""

import customtkinter as ctk


class DepthCard(ctk.CTkFrame):
    """Frame component with depth styling."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
