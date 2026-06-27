"""Arcane Sword — Python desktop app entry point (player companion to Arcane Shield)."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import ctypes
import customtkinter as ctk
from db import Database

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
    # Reference browsers (fully working) ──────────────────────────
    ("spells",       "✨  Spells"),
    ("char_opts",    "🧙  Character Options"),
    ("conditions",   "🜸  Conditions"),
    ("skills",       "🎯  Skills"),
    ("languages",    "🗣  Languages"),
    ("items",        "✦  Items"),
    # Player tabs (placeholders for now) ──────────────────────────
    ("actions",      "⚡  Actions"),
    ("inventory",    "🎒  Inventory"),
    ("spells_avail", "✨  Spells — Available"),
    ("spellbook",    "📕  Spellbook"),
    ("features",     "🌟  Features & Traits"),
    ("level_up",     "⬆  Level-Up"),
    ("rest",         "🌙  Rest"),
    ("campaign",     "✎  Campaign Notes"),
]
NAV_BOTTOM = [
    ("import",       "⬆  Import Character"),
]
NAV_ITEMS = NAV_TOP + NAV_CONTENT + NAV_BOTTOM


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
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

        self._build_sidebar()
        self._build_content()

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=200, fg_color=SURFACE, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

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

    def _build_content(self):
        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        def stub(title, blurb):
            return PlaceholderPage(self._content, self.db, title=title, blurb=blurb)

        self._pages: dict[str, ctk.CTkFrame] = {
            # Reference browsers (live)
            "spells":     SpellsPage(self._content, self.db),
            "char_opts":  CharacterOptionsPage(self._content, self.db),
            "conditions": ConditionsPage(self._content, self.db),
            "skills":     SkillsPage(self._content, self.db),
            "languages":  LanguagesPage(self._content, self.db),
            "items":      ItemsPage(self._content, self.db),
            # Character Sheet (live) — owns the character picker
            "character_sheet": CharacterSheetPage(self._content, self.db, self),
            # Player tabs (placeholders)
            "actions":    stub("Actions", "Track your attacks, spells, and other actions in combat."),
            "inventory":  stub("Inventory", "Carry, equip, and manage your gear and treasure."),
            "spells_avail": SpellsAvailablePage(self._content, self.db, self),
            "spellbook":    SpellbookPage(self._content, self.db, self),
            "features":   stub("Features & Traits", "Class features, racial traits, and feats you've gained."),
            "level_up":   stub("Level-Up", "Step through choices as your character gains a level."),
            "rest":       stub("Rest", "Take short and long rests to recover resources."),
            "campaign":   stub("Campaign Notes", "Keep session notes, quests, and contacts for your campaign."),
            "import":     stub("Import Character", "Import a character built elsewhere into Arcane Sword."),
        }

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            page.grid_remove()

        self._current: str | None = None
        self.show_page("spells")

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


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = App()
    app.mainloop()
