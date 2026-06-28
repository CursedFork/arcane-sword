"""Settings tab — pick a theme (live) and toggle the training-wheels helpers."""
import customtkinter as ctk

from pages import theme

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
ACCENT_H = "#9472d8"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"

_TW_DESC = {
    "hints": "Show how computed values are built (saves, passives, slot math).",
    "tooltips": "Explanatory tips on tabs and fields for players new to 5e.",
    "warnings": "Confirmations for prerequisites, the attunement cap, over-preparing, etc.",
    "simple_mode": "Hide advanced controls (multiclass, custom actions, manual overrides).",
}


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=ACCENT)
        self._scroll.pack(fill="both", expand=True, padx=16, pady=16)

    def refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._render()

    def _render(self):
        ctk.CTkLabel(self._scroll, text="Settings", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 12))

        # ── Theme picker ─────────────────────────────────────────────────────
        ctk.CTkLabel(self._scroll, text="Theme", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(self._scroll, text="Pick a look. Drop a PNG in assets/themes/ "
                     "(named like the theme) to use your own backdrop art.",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 8))

        grid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 16))
        active = theme.active_theme()
        for i, name in enumerate(theme.theme_names()):
            pal = theme.palette(name)
            selected = name == active
            card = ctk.CTkFrame(grid, fg_color=pal["SURFACE"], corner_radius=10,
                                border_width=2 if selected else 1,
                                border_color=pal["ACCENT"] if selected else pal["BORDER"])
            card.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            grid.grid_columnconfigure(i % 3, weight=1, uniform="theme")
            # swatches
            sw = ctk.CTkFrame(card, fg_color="transparent")
            sw.pack(padx=12, pady=(12, 4), anchor="w")
            for key in ("ACCENT", "GOLD", "GOOD", "SURFACE2"):
                ctk.CTkFrame(sw, fg_color=pal.get(key, pal["ACCENT"]), width=22, height=22,
                             corner_radius=5).pack(side="left", padx=2)
            ctk.CTkLabel(card, text=name, text_color=pal["TEXT"],
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12)
            ctk.CTkButton(card, text=("✓ Active" if selected else "Use this theme"),
                          height=30, fg_color=(pal["ACCENT"] if selected else pal["SURFACE2"]),
                          hover_color=pal["ACCENT_H"], text_color=pal["TEXT"],
                          font=ctk.CTkFont(size=12), state=("disabled" if selected else "normal"),
                          command=lambda n=name: self._pick_theme(n)
                          ).pack(fill="x", padx=12, pady=12)

        # ── Backdrop frame (how much art shows around the panels) ────────────
        ctk.CTkLabel(self._scroll, text="Backdrop Frame", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(self._scroll, text="How much of the backdrop art shows around the "
                     "panels. Bolder frames reveal more art but leave less room for content.",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 8))
        frow = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frow.pack(fill="x", pady=(0, 16))
        for name in theme.PANEL_INSETS:
            sel = name == theme.panel_inset_name()
            ctk.CTkButton(frow, text=name, width=120, height=32,
                          fg_color=(ACCENT if sel else SURFACE2), hover_color=ACCENT_H,
                          text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold"),
                          state=("disabled" if sel else "normal"),
                          command=lambda n=name: self._pick_inset(n)).pack(side="left", padx=(0, 8))

        # ── Training wheels ──────────────────────────────────────────────────
        ctk.CTkLabel(self._scroll, text="Training Wheels", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(self._scroll, text="Beginner-friendly helpers. Turn them off as "
                     "you get comfortable.", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 8))

        for flag in theme.TRAINING_WHEELS:
            row = ctk.CTkFrame(self._scroll, fg_color=SURFACE, corner_radius=8,
                               border_width=1, border_color=BORDER)
            row.pack(fill="x", pady=3)
            txt = ctk.CTkFrame(row, fg_color="transparent")
            txt.pack(side="left", fill="x", expand=True, padx=14, pady=8)
            ctk.CTkLabel(txt, text=theme.tw_label(flag), text_color=TEXT,
                         font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(txt, text=_TW_DESC.get(flag, ""), text_color=MUTED,
                         font=ctk.CTkFont(size=11), anchor="w").pack(anchor="w")
            sw = ctk.CTkSwitch(row, text="", progress_color=ACCENT, button_color=TEXT,
                               command=lambda f=flag: self._toggle_tw(f))
            sw.pack(side="right", padx=16)
            sw.select() if theme.tw(flag) else sw.deselect()

    def _pick_theme(self, name):
        if self.app and hasattr(self.app, "apply_theme"):
            self.app.apply_theme(name)
        else:
            theme.set_active(name)
            self.refresh()

    def _pick_inset(self, name):
        theme.set_panel_inset(name)
        if self.app and hasattr(self.app, "apply_settings"):
            self.app.apply_settings()
        else:
            self.refresh()

    def _toggle_tw(self, flag):
        theme.set_tw(flag, not theme.tw(flag))
        if self.app and hasattr(self.app, "apply_settings"):
            self.app.apply_settings()
        else:
            self.refresh()
