"""A simple 'Coming soon' page used for player tabs that aren't built yet.

Mirrors the page contract the App's router expects (a CTkFrame with a
`refresh()` method), so placeholders can be swapped for real pages later
without touching main.py's routing.
"""
import customtkinter as ctk

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"


class PlaceholderPage(ctk.CTkFrame):
    def __init__(self, parent, db, *, title: str, blurb: str = ""):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self._title = title
        self._blurb = blurb
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=self._title,
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT).pack(padx=48, pady=(36, 6))
        ctk.CTkLabel(card, text="Coming soon",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=ACCENT).pack(padx=48, pady=(0, 12))
        if self._blurb:
            ctk.CTkLabel(card, text=self._blurb, font=ctk.CTkFont(size=12),
                         text_color=MUTED, wraplength=360, justify="center"
                         ).pack(padx=48, pady=(0, 36))
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=12).pack(pady=(0, 24))

    def refresh(self):
        """No-op — the router calls refresh() on every page it shows."""
        pass
