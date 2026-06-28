"""Arcane Sword — Python desktop app entry point (player companion to Arcane Shield)."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import ctypes
import tkinter as tk
import customtkinter as ctk
from db import Database
from pages import theme
try:
    from PIL import Image, ImageTk
except Exception:  # Pillow is a dependency, but degrade gracefully
    Image = ImageTk = None

# Tell Windows this is its own app so the taskbar shows the custom icon
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("arcane.sword.player")
except Exception:
    pass

# Reference-browser pages reused from Arcane Shield (read-only spirit).
from pages.spells import SpellsPage
from pages.character_options import CharacterOptionsPage
from pages.conditions import ConditionsPage
from pages.skills import SkillsPage
from pages.languages import LanguagesPage
from pages.items import ItemsPage
from pages.character_sheet import CharacterSheetPage
from pages.spellcasting import SpellsAvailablePage, SpellbookPage
from pages.inventory import InventoryPage
from pages.actions import ActionsPage
from pages.features import FeaturesPage
from pages.background import BackgroundPage
from pages.leveling import LevelUpPage
from pages.rest import RestPage
from pages.campaign_notes import CampaignNotesPage
from pages.character_io import CharacterIOPage
from pages.settings_tab import SettingsPage
from pages.placeholder import PlaceholderPage

# ── Colour palette (kept identical to Arcane Shield) ─────────────────────────────
BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"

# Character Sheet is pinned to the top, Import Character to the bottom; content
# tabs sit between them. (New content tabs get added to NAV_CONTENT.)
NAV_TOP = [
    ("character_sheet", "🗡  Character Sheet"),
]
NAV_CONTENT = [
    # ── Your character ────────────────────────────────────────────
    ("actions",      "⚡  Actions"),
    ("inventory",    "🎒  Inventory"),
    ("spells_avail", "✨  Spells — Available"),
    ("spellbook",    "📕  Spellbook"),
    ("features",     "🌟  Features & Traits"),
    ("background",   "📜  Background"),
    ("level_up",     "⬆  Level-Up"),
    ("rest",         "🌙  Rest"),
    ("campaign",     "✎  Campaign Notes"),
    # ── Reference compendium ──────────────────────────────────────
    ("spells",       "📖  Spells (reference)"),
    ("char_opts",    "🧙  Character Options"),
    ("conditions",   "🜸  Conditions"),
    ("skills",       "🎯  Skills"),
    ("languages",    "🗣  Languages"),
    ("items",        "✦  Items"),
]
NAV_BOTTOM = [
    ("settings",     "⚙  Settings"),
    ("import",       "⬆  Import / Manage"),
]
NAV_ITEMS = NAV_TOP + NAV_CONTENT + NAV_BOTTOM


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Load saved theme + training-wheels and recolour every page module
        # before any UI is built.
        theme.load()
        theme.apply_all()

        self.title("Arcane Sword")
        self.geometry("1400x900")
        self.minsize(1000, 600)
        self.configure(fg_color=BG)

        # Try to set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.db = Database()

        # The currently-selected character. Every player tab reads this; the
        # Character Sheet tab owns the picker that sets it.
        self.active_character_id: int | None = None

        # Grid: sidebar col 0 (fixed) + content col 1 (flex)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._bg_label = None
        self._bg_photo = None
        self._bg_resize_id = None
        self._build_backdrop()

        self._build_sidebar()
        self._build_content()
        self.bind("<Configure>", self._on_root_resize)

    # ── Full-window backdrop ─────────────────────────────────────────────────────

    def _build_backdrop(self):
        if ImageTk is None:
            return
        self._bg_label = tk.Label(self, bd=0, highlightthickness=0)
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._bg_label.lower()
        self.after(60, self._render_backdrop)

    @staticmethod
    def _fit_cover(img, w, h):
        """Scale to fill (w, h) preserving aspect ratio, centre-cropping the
        overflow — so the backdrop is never stretched/distorted."""
        iw, ih = img.size
        scale = max(w / iw, h / ih)
        nw, nh = max(w, int(iw * scale)), max(h, int(ih * scale))
        img = img.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - w) // 2, (nh - h) // 2
        return img.crop((left, top, left + w, top + h))

    def _render_backdrop(self):
        if self._bg_label is None or Image is None:
            return
        w, h = max(self.winfo_width(), 100), max(self.winfo_height(), 100)
        src = theme.backdrop_source()
        if src is None:
            return
        try:
            img = self._fit_cover(src, w, h)
            self._bg_photo = ImageTk.PhotoImage(img)
            self._bg_label.configure(image=self._bg_photo)
            self._bg_label.lower()
        except Exception:
            pass

    def _on_root_resize(self, event):
        if event.widget is not self or self._bg_label is None:
            return
        if self._bg_resize_id is not None:
            self.after_cancel(self._bg_resize_id)
        self._bg_resize_id = self.after(180, self._render_backdrop)

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        pad = theme.panel_inset()  # margin that reveals the backdrop art
        sb = ctk.CTkFrame(self, width=200, fg_color=SURFACE, corner_radius=12,
                          border_width=1, border_color=BORDER)
        sb.grid(row=0, column=0, sticky="nsew", padx=(pad, pad // 2), pady=pad)
        sb.grid_propagate(False)
        self._sidebar = sb

        ctk.CTkLabel(
            sb, text="🗡 ARCANE SWORD",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ACCENT
        ).pack(pady=(24, 4), padx=16, anchor="w")

        ctk.CTkLabel(
            sb, text="Player Companion",
            font=ctk.CTkFont(size=11),
            text_color=MUTED
        ).pack(pady=(0, 20), padx=16, anchor="w")

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._nav_defaults: dict[str, dict] = {}

        def make_nav_btn(parent, key, label, *, fg="transparent", text=MUTED,
                         border=0, border_color=BORDER, **pack_kw):
            btn = ctk.CTkButton(
                parent, text=label, anchor="w",
                fg_color=fg, hover_color=SURFACE2,
                text_color=text, font=ctk.CTkFont(size=13),
                corner_radius=0 if not border else 6, height=38,
                border_width=border, border_color=border_color,
                command=lambda k=key: self.show_page(k)
            )
            btn.pack(**pack_kw)
            self._nav_btns[key] = btn
            self._nav_defaults[key] = {"fg_color": fg, "text_color": text}
            return btn

        # ── Top: Character Sheet (primary, emphasized) ───────────────────────
        for key, label in NAV_TOP:
            make_nav_btn(sb, key, label, text=TEXT, fill="x", padx=0, pady=0)
        ctk.CTkFrame(sb, height=1, fg_color=BORDER).pack(fill="x", padx=12, pady=(6, 6))

        # ── Bottom: pinned (packed before the expanding middle claims the rest) ─
        from db import _db_path
        db_p = str(_db_path())
        ctk.CTkLabel(
            sb, text=f"DB: {os.path.basename(db_p)}",
            font=ctk.CTkFont(size=9), text_color=MUTED, wraplength=180
        ).pack(side="bottom", pady=8, padx=8)
        for key, label in NAV_BOTTOM:
            make_nav_btn(sb, key, label, text=ACCENT, border=2, border_color=ACCENT,
                         side="bottom", fill="x", padx=10, pady=(0, 6))
        ctk.CTkFrame(sb, height=1, fg_color=BORDER).pack(side="bottom", fill="x",
                                                         padx=12, pady=(6, 4))

        # ── Middle: scrollable content tabs (fills the space between) ────────
        content_scroll = ctk.CTkScrollableFrame(sb, fg_color="transparent",
                                                scrollbar_button_color=ACCENT)
        content_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        for key, label in NAV_CONTENT:
            make_nav_btn(content_scroll, key, label, fill="x", padx=0, pady=0)

    # ── Content area ───────────────────────────────────────────────────────────

    def _build_content(self, start="character_sheet"):
        # Pages are parented to the window (over the backdrop) and float in the
        # content cell with a margin, so the art frames each panel.
        def stub(title, blurb):
            return PlaceholderPage(self, self.db, title=title, blurb=blurb)

        self._pages: dict[str, ctk.CTkFrame] = {
            # Reference browsers (live)
            "spells":     SpellsPage(self, self.db),
            "char_opts":  CharacterOptionsPage(self, self.db),
            "conditions": ConditionsPage(self, self.db),
            "skills":     SkillsPage(self, self.db),
            "languages":  LanguagesPage(self, self.db),
            "items":      ItemsPage(self, self.db),
            # Character Sheet (live) — owns the character picker
            "character_sheet": CharacterSheetPage(self, self.db, self),
            # Player tabs
            "actions":    ActionsPage(self, self.db, self),
            "inventory":  InventoryPage(self, self.db, self),
            "spells_avail": SpellsAvailablePage(self, self.db, self),
            "spellbook":    SpellbookPage(self, self.db, self),
            "features":   FeaturesPage(self, self.db, self),
            "background": BackgroundPage(self, self.db, self),
            "level_up":   LevelUpPage(self, self.db, self),
            "rest":       RestPage(self, self.db, self),
            "campaign":   CampaignNotesPage(self, self.db, self),
            "import":     CharacterIOPage(self, self.db, self),
            "settings":   SettingsPage(self, self.db, self),
        }

        pad = theme.panel_inset()
        for page in self._pages.values():
            page.configure(corner_radius=12)
            page.grid(row=0, column=1, sticky="nsew", padx=(pad // 2, pad), pady=pad)
            page.grid_remove()

        self._current: str | None = None
        self.show_page(start if start in self._pages else "character_sheet")
        if self._bg_label is not None:
            self._bg_label.lower()

    # ── Navigation ─────────────────────────────────────────────────────────────

    def show_page(self, name: str):
        if self._current:
            self._pages[self._current].grid_remove()
            btn = self._nav_btns.get(self._current)
            if btn:
                btn.configure(**self._nav_defaults.get(self._current,
                              {"fg_color": "transparent", "text_color": MUTED}))

        self._current = name
        self._pages[name].grid()
        self._pages[name].refresh()

        btn = self._nav_btns.get(name)
        if btn:
            btn.configure(text_color=TEXT, fg_color=SURFACE2)

    # ── Theme / settings application ─────────────────────────────────────────────

    def apply_theme(self, name: str):
        """Switch theme live: recolour modules, rebuild the UI, repaint backdrop."""
        theme.set_active(name)
        theme.apply_all()
        self._rebuild_ui()
        self._render_backdrop()

    def apply_settings(self):
        """Re-render after a training-wheels toggle (pages read the flags live)."""
        self._rebuild_ui()

    def _rebuild_ui(self):
        keep = self._current or "character_sheet"
        try:
            self._sidebar.destroy()
            for page in self._pages.values():
                page.destroy()
        except Exception:
            pass
        self.configure(fg_color=BG)
        self._build_sidebar()
        self._build_content(start=keep)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = App()
    app.mainloop()
