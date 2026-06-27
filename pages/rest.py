"""Rest tab — long rest, short rest, and spending hit dice for the active
character. The actual rules live in pages.rest_logic (shared with the Character
Sheet's quick-rest buttons).
"""
from tkinter import messagebox
import customtkinter as ctk

from pages import rest_logic

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
ACCENT_H = "#9472d8"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"
GOOD     = "#52be80"
GOLD     = "#e0b040"


class RestPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._wrap = ctk.CTkFrame(self, fg_color="transparent")
        self._wrap.pack(expand=True, fill="both", padx=40, pady=40)

    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        for w in self._wrap.winfo_children():
            w.destroy()
        if not self._char:
            ctk.CTkLabel(self._wrap, text="No character selected — create or select one "
                         "on the Character Sheet tab.", text_color=MUTED,
                         font=ctk.CTkFont(size=13)).pack(pady=40)
            return
        self._render()

    def _render(self):
        c = self._char
        ctk.CTkLabel(self._wrap, text=f"Rest — {c['name']}", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 4))
        remaining, total = rest_logic.hit_dice_status(self.db, self._cid)
        ctk.CTkLabel(self._wrap, text=f"HP {c['hp_current']}/{c['hp_max']}"
                     + (f"  (+{c['hp_temp']} temp)" if c['hp_temp'] else "")
                     + f"      Hit Dice {remaining}/{total}",
                     text_color=MUTED, font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 18))

        cards = ctk.CTkFrame(self._wrap, fg_color="transparent")
        cards.pack(fill="x")
        cards.grid_columnconfigure((0, 1), weight=1, uniform="rest")

        # Long rest
        lr_card = ctk.CTkFrame(cards, fg_color=SURFACE, corner_radius=12,
                               border_width=1, border_color=BORDER)
        lr_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(lr_card, text="🌙  Long Rest", text_color=ACCENT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(18, 4), padx=20)
        ctk.CTkLabel(lr_card, text="Restore HP to maximum, recover half your total\n"
                     "hit dice, reset all spell slots, and refresh resources.",
                     text_color=MUTED, font=ctk.CTkFont(size=11), justify="left"
                     ).pack(padx=20, pady=(0, 12))
        ctk.CTkButton(lr_card, text="Take a Long Rest", height=38, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=13),
                      command=self._long_rest).pack(fill="x", padx=20, pady=(0, 18))

        # Short rest
        sr_card = ctk.CTkFrame(cards, fg_color=SURFACE, corner_radius=12,
                               border_width=1, border_color=BORDER)
        sr_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(sr_card, text="☾  Short Rest", text_color=GOLD,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(18, 4), padx=20)
        ctk.CTkLabel(sr_card, text="Spend hit dice to heal and restore\n"
                     "short-recharge resources.", text_color=MUTED,
                     font=ctk.CTkFont(size=11), justify="left").pack(padx=20, pady=(0, 12))
        ctk.CTkButton(sr_card, text=f"Spend a Hit Die ({remaining}/{total})", height=34,
                      fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT,
                      font=ctk.CTkFont(size=12), command=self._spend_hd
                      ).pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkButton(sr_card, text="Finish Short Rest", height=34, fg_color=GOLD,
                      hover_color=ACCENT_H, text_color=BG, font=ctk.CTkFont(size=12),
                      command=self._short_rest).pack(fill="x", padx=20, pady=(0, 18))

    # ── actions ───────────────────────────────────────────────────────────────
    def _long_rest(self):
        r = rest_logic.long_rest(self.db, self._cid)
        self.refresh()
        messagebox.showinfo("Long Rest", f"Fully rested.\nHP restored to {r['hp']}.\n"
                            f"Recovered {r['hit_dice_recovered']} hit dice; reset "
                            f"{r['slots_reset']} spell-slot level(s).")

    def _short_rest(self):
        r = rest_logic.short_rest(self.db, self._cid)
        self.refresh()
        messagebox.showinfo("Short Rest",
                            f"Short rest complete. Restored {r['resources_reset']} "
                            f"short-recharge resource(s).")

    def _spend_hd(self):
        r = rest_logic.spend_hit_die(self.db, self._cid)
        if not r.get("spent"):
            messagebox.showwarning("Hit Dice", "No hit dice remaining.")
            return
        self.refresh()
        messagebox.showinfo("Hit Die", f"Spent a {r['die']} and healed {r['healed']} HP.")
