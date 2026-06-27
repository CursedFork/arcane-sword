"""Character Sheet — the main player tab.

A single scrollable 5e-style sheet for the app's currently-selected character.
Reuses Arcane Shield's theme + widgets. All edits persist immediately through the
Database; derived values (ability mods, proficiency bonus, save/skill totals,
initiative, passive senses) recompute live without a full rebuild.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk

from db import Database
from pages.md_widget import MarkdownText

# ── palette (kept identical to the rest of the app) ─────────────────────────────
BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
ACCENT_H = "#9472d8"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"
DANGER   = "#c0392b"
GOOD     = "#52be80"
GOLD     = "#e0b040"

ABILITIES = [("str", "STR"), ("dex", "DEX"), ("con", "CON"),
             ("int", "INT"), ("wis", "WIS"), ("cha", "CHA")]
_ABILITY_FROM_NAME = {
    "strength": "str", "dexterity": "dex", "constitution": "con",
    "intelligence": "int", "wisdom": "wis", "charisma": "cha",
}
# Passive sense -> (governing skill, stored override column)
PASSIVES = [
    ("Perception", "Perception", "passive_perception"),
    ("Insight", "Insight", "passive_insight"),
    ("Investigation", "Investigation", "passive_investigation"),
]


def _norm_ability(a: str) -> str:
    """Normalize a save/ability label ('INT', 'Intelligence') to a 3-letter code."""
    a = (a or "").strip().lower()
    return _ABILITY_FROM_NAME.get(a, a[:3])


def _join(items) -> str:
    return "; ".join(items or [])


def _split(text: str) -> list[str]:
    return [s.strip() for s in (text or "").split(";") if s.strip()]


class CharacterSheetPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._char: dict | None = None
        self._cid: int | None = None
        self._label_to_id: dict[str, int] = {}

        # Live-updated widget registries (rebuilt on each sheet render).
        self._mod_lbls: dict[str, ctk.CTkLabel] = {}
        self._save_lbls: dict[str, ctk.CTkLabel] = {}
        self._save_dots: dict[str, ctk.CTkButton] = {}
        self._skill_lbls: dict[str, ctk.CTkLabel] = {}
        self._skill_dots: dict[str, ctk.CTkButton] = {}
        self._passive_lbls: dict[str, ctk.CTkLabel] = {}
        self._prof_lbl: ctk.CTkLabel | None = None
        self._init_lbl: ctk.CTkLabel | None = None

        # Reference data (skills' governing abilities + condition rules).
        self._skill_ability = {r["name"]: _norm_ability(r["ability"])
                               for r in self.db.list_skills()}
        self._skill_names = [r["name"] for r in self.db.list_skills()]
        self._cond_rules = {r["name"]: r["description"] for r in self.db.list_conditions()}

        self._build_topbar()
        self._body = ctk.CTkScrollableFrame(self, fg_color=BG,
                                            scrollbar_button_color=ACCENT)
        self._body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ── Top bar: character picker + actions ─────────────────────────────────────

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=56)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)

        ctk.CTkLabel(bar, text="Character", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(16, 6))

        self._picker = ctk.CTkOptionMenu(
            bar, values=["—"], command=self._on_pick, width=240,
            fg_color=SURFACE2, button_color=ACCENT, button_hover_color=ACCENT_H,
            text_color=TEXT, dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT,
            font=ctk.CTkFont(size=13))
        self._picker.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkButton(bar, text="+ New", width=64, height=30, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._new_character).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bar, text="Delete", width=64, height=30, fg_color="transparent",
                      hover_color=DANGER, text_color=MUTED, font=ctk.CTkFont(size=12),
                      command=self._delete_character).pack(side="left", padx=(0, 4))

        # Quick rest buttons (logic wired in a later task).
        ctk.CTkButton(bar, text="🌙 Long Rest", width=96, height=30, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._long_rest).pack(side="right", padx=(4, 16), pady=10)
        ctk.CTkButton(bar, text="☾ Short Rest", width=96, height=30, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._short_rest).pack(side="right", padx=4, pady=10)

    # ── Public refresh (called by the router on show) ───────────────────────────

    def refresh(self):
        chars = self.db.list_characters()
        # Build the picker labels (index-prefixed so duplicates stay unique).
        self._label_to_id = {}
        labels = []
        for i, c in enumerate(chars):
            lbl = f"{i+1}. {c['name']}"
            if c.get("total_level"):
                lbl += f"  (L{c['total_level']})"
            labels.append(lbl)
            self._label_to_id[lbl] = c["id"]

        # Resolve the active character id (app-shared) against the current list.
        active = getattr(self.app, "active_character_id", None) if self.app else self._cid
        ids = [c["id"] for c in chars]
        if active not in ids:
            active = ids[0] if ids else None
        self._cid = active
        if self.app is not None:
            self.app.active_character_id = active

        self._picker.configure(values=labels or ["—"])
        cur_label = next((l for l, i in self._label_to_id.items() if i == active), None)
        self._picker.set(cur_label or "—")

        self._render_sheet()

    def _on_pick(self, label: str):
        cid = self._label_to_id.get(label)
        if cid is None:
            return
        self._cid = cid
        if self.app is not None:
            self.app.active_character_id = cid
        self._render_sheet()

    # ── Sheet render ────────────────────────────────────────────────────────────

    def _clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()
        self._mod_lbls.clear(); self._save_lbls.clear(); self._save_dots.clear()
        self._skill_lbls.clear(); self._skill_dots.clear(); self._passive_lbls.clear()
        self._prof_lbl = None; self._init_lbl = None

    def _render_sheet(self):
        self._clear_body()
        if self._cid is None:
            self._char = None
            self._empty_state()
            return
        self._char = self.db.get_character(self._cid)
        if not self._char:
            self._empty_state()
            return

        self._body.grid_columnconfigure(0, weight=1)
        self._header(self._body).grid(row=0, column=0, columnspan=2, sticky="ew",
                                      padx=12, pady=(12, 6))

        cols = ctk.CTkFrame(self._body, fg_color="transparent")
        cols.grid(row=1, column=0, sticky="nsew", padx=8, pady=0)
        cols.grid_columnconfigure(0, weight=1, uniform="c")
        cols.grid_columnconfigure(1, weight=1, uniform="c")

        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=4)
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=4)

        self._abilities(left).pack(fill="x", pady=6)
        self._saves(left).pack(fill="x", pady=6)
        self._skills(left).pack(fill="x", pady=6)

        self._combat(right).pack(fill="x", pady=6)
        self._passives(right).pack(fill="x", pady=6)
        self._conditions(right).pack(fill="x", pady=6)
        self._defenses(right).pack(fill="x", pady=6)

        self._recompute()

    def _empty_state(self):
        card = ctk.CTkFrame(self._body, fg_color=SURFACE, corner_radius=12)
        card.pack(expand=True, pady=80, padx=80, ipadx=40, ipady=30)
        ctk.CTkLabel(card, text="No character selected",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT
                     ).pack(pady=(20, 6), padx=30)
        ctk.CTkLabel(card, text="Create one with “+ New” above, or import a character.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(pady=(0, 20), padx=30)

    # ── Card helper ─────────────────────────────────────────────────────────────

    def _card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        if title:
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=ACCENT).pack(anchor="w", padx=14, pady=(10, 2))
        return card

    # ── Header ──────────────────────────────────────────────────────────────────

    def _header(self, parent):
        c = self._char
        card = self._card(parent, None)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))
        top.grid_columnconfigure(0, weight=1)

        name_var = tk.StringVar(value=c["name"])
        name_e = ctk.CTkEntry(top, textvariable=name_var, fg_color=SURFACE2,
                              border_color=BORDER, text_color=TEXT,
                              font=ctk.CTkFont(size=18, weight="bold"), height=34)
        name_e.grid(row=0, column=0, sticky="ew")
        self._bind_text(name_e, name_var, "name")

        # Inspiration toggle
        insp = bool(c.get("inspiration"))
        self._insp_btn = ctk.CTkButton(
            top, width=130, height=30, command=self._toggle_inspiration,
            text=("★ Inspiration" if insp else "☆ Inspiration"),
            fg_color=(GOLD if insp else SURFACE2), hover_color=ACCENT_H,
            text_color=(BG if insp else MUTED), font=ctk.CTkFont(size=12, weight="bold"))
        self._insp_btn.grid(row=0, column=1, padx=(8, 0))

        classes = " / ".join(
            f"{k['class']}{(' (' + k['subclass'] + ')') if k['subclass'] else ''} {k['level']}"
            for k in c["classes"]) or "No classes yet"
        sub = " • ".join(x for x in (
            f"{c['race']}{(' (' + c['subrace'] + ')') if c['subrace'] else ''}".strip(),
            classes, c["background"]) if x)
        ctk.CTkLabel(card, text=sub, text_color=MUTED, font=ctk.CTkFont(size=12),
                     anchor="w", justify="left").pack(fill="x", padx=14, pady=(0, 8))

        stats = ctk.CTkFrame(card, fg_color="transparent")
        stats.pack(fill="x", padx=14, pady=(0, 12))

        def stat_entry(label, col):
            f = ctk.CTkFrame(stats, fg_color="transparent")
            f.pack(side="left", padx=(0, 18))
            ctk.CTkLabel(f, text=label, text_color=MUTED,
                         font=ctk.CTkFont(size=10)).pack(anchor="w")
            var = tk.StringVar(value=str(c.get(col, "") if c.get(col) is not None else ""))
            e = ctk.CTkEntry(f, textvariable=var, width=86, height=28, justify="center",
                             fg_color=SURFACE2, border_color=BORDER, text_color=TEXT)
            e.pack()
            self._bind_text(e, var, col, is_int=(col == "xp"))
            return e

        stat_entry("XP", "xp")
        stat_entry("Alignment", "alignment")

        # Total level (read-only) + proficiency bonus (derived, read-only)
        lvl_f = ctk.CTkFrame(stats, fg_color="transparent")
        lvl_f.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(lvl_f, text="Total Level", text_color=MUTED,
                     font=ctk.CTkFont(size=10)).pack(anchor="w")
        ctk.CTkLabel(lvl_f, text=str(c.get("total_level", 0)), text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack()

        pb_f = ctk.CTkFrame(stats, fg_color="transparent")
        pb_f.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(pb_f, text="Prof. Bonus", text_color=MUTED,
                     font=ctk.CTkFont(size=10)).pack(anchor="w")
        self._prof_lbl = ctk.CTkLabel(pb_f, text="+2", text_color=ACCENT,
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self._prof_lbl.pack()
        return card

    # ── Ability scores ──────────────────────────────────────────────────────────

    def _abilities(self, parent):
        card = self._card(parent, "Ability Scores")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(2, 12))
        for code, label in ABILITIES:
            blk = ctk.CTkFrame(row, fg_color=SURFACE2, corner_radius=8,
                               border_width=1, border_color=BORDER)
            blk.pack(side="left", expand=True, fill="x", padx=3)
            ctk.CTkLabel(blk, text=label, text_color=MUTED,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 0))
            mod = ctk.CTkLabel(blk, text="+0", text_color=TEXT,
                               font=ctk.CTkFont(size=20, weight="bold"))
            mod.pack()
            self._mod_lbls[code] = mod
            var = tk.StringVar(value=str(self._char.get(code, 10)))
            e = ctk.CTkEntry(blk, textvariable=var, width=52, height=28, justify="center",
                             fg_color=SURFACE, border_color=BORDER, text_color=TEXT)
            e.pack(pady=(0, 8))
            self._bind_ability(e, var, code)
        return card

    # ── Saving throws ───────────────────────────────────────────────────────────

    def _saves(self, parent):
        card = self._card(parent, "Saving Throws")
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(2, 12))
        grid.grid_columnconfigure((0, 1), weight=1)
        for i, (code, label) in enumerate(ABILITIES):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=2)
            dot = ctk.CTkButton(cell, text="○", width=26, height=26, corner_radius=13,
                                fg_color="transparent", hover_color=SURFACE2,
                                text_color=MUTED, font=ctk.CTkFont(size=16),
                                command=lambda c=code: self._toggle_save(c))
            dot.pack(side="left")
            self._save_dots[code] = dot
            ctk.CTkLabel(cell, text=label, text_color=TEXT,
                         font=ctk.CTkFont(size=12), width=44, anchor="w").pack(side="left", padx=4)
            total = ctk.CTkLabel(cell, text="+0", text_color=TEXT,
                                 font=ctk.CTkFont(size=13, weight="bold"))
            total.pack(side="left")
            self._save_lbls[code] = total
        return card

    # ── Skills ──────────────────────────────────────────────────────────────────

    def _skills(self, parent):
        card = self._card(parent, "Skills")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(2, 12))
        for skill in self._skill_names:
            code = self._skill_ability.get(skill, "")
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=1)
            dot = ctk.CTkButton(row, text="○", width=24, height=24, corner_radius=12,
                                fg_color="transparent", hover_color=SURFACE2,
                                text_color=MUTED, font=ctk.CTkFont(size=15),
                                command=lambda s=skill: self._cycle_skill(s))
            dot.pack(side="left")
            self._skill_dots[skill] = dot
            ctk.CTkLabel(row, text=(code.upper() or "—"), text_color=MUTED,
                         font=ctk.CTkFont(size=9), width=30).pack(side="left", padx=(2, 4))
            ctk.CTkLabel(row, text=skill, text_color=TEXT, font=ctk.CTkFont(size=12),
                         anchor="w").pack(side="left", fill="x", expand=True)
            total = ctk.CTkLabel(row, text="+0", text_color=TEXT,
                                 font=ctk.CTkFont(size=12, weight="bold"))
            total.pack(side="right", padx=(0, 4))
            self._skill_lbls[skill] = total
        return card

    # ── Combat block ────────────────────────────────────────────────────────────

    def _combat(self, parent):
        c = self._char
        card = self._card(parent, "Combat")
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(2, 6))

        def box(label, col=None, value=None, init=False):
            f = ctk.CTkFrame(grid, fg_color=SURFACE2, corner_radius=8)
            f.pack(side="left", expand=True, fill="x", padx=3)
            ctk.CTkLabel(f, text=label, text_color=MUTED,
                         font=ctk.CTkFont(size=10)).pack(pady=(8, 0))
            if init:
                lbl = ctk.CTkLabel(f, text="+0", text_color=TEXT,
                                   font=ctk.CTkFont(size=18, weight="bold"))
                lbl.pack(pady=(0, 8))
                self._init_lbl = lbl
            elif value is not None:
                ctk.CTkLabel(f, text=str(value), text_color=TEXT,
                             font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 8))
            else:
                var = tk.StringVar(value=str(c.get(col, 0)))
                e = ctk.CTkEntry(f, textvariable=var, width=52, height=26, justify="center",
                                 fg_color=SURFACE, border_color=BORDER, text_color=TEXT)
                e.pack(pady=(0, 8))
                self._bind_text(e, var, col, is_int=True,
                                recompute=(col == "initiative_misc"))

        box("AC", "ac")
        box("Initiative", init=True)
        box("Speed", "speed")
        total_hd = c.get("total_level", 0)
        used_hd = c.get("hit_dice_used", 0)
        box("Hit Dice", value=f"{max(0, total_hd - used_hd)}/{total_hd}")

        # Hit-dice spend / recover
        hd = ctk.CTkFrame(card, fg_color="transparent")
        hd.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkLabel(hd, text="Hit Dice", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left")
        ctk.CTkButton(hd, text="− Spend", width=72, height=26, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=11),
                      command=lambda: self._adjust_hit_dice(+1)).pack(side="left", padx=4)
        ctk.CTkButton(hd, text="+ Recover", width=78, height=26, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=11),
                      command=lambda: self._adjust_hit_dice(-1)).pack(side="left", padx=4)
        by_class = ", ".join(f"{k['class']} {k['level']}" for k in c["classes"])
        if by_class:
            ctk.CTkLabel(hd, text=by_class, text_color=MUTED,
                         font=ctk.CTkFont(size=10)).pack(side="left", padx=8)

        # HP bar
        self._hp_block(card)

        # Death saves (only at 0 HP)
        if c.get("hp_current", 0) <= 0:
            self._death_saves(card)
        return card

    def _hp_block(self, card):
        c = self._char
        cur, mx, tmp = c.get("hp_current", 0), c.get("hp_max", 0), c.get("hp_temp", 0)
        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.pack(fill="x", padx=14, pady=(4, 4))
        head = ctk.CTkFrame(wrap, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(head, text="Hit Points", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left")
        txt = f"{cur} / {mx}" + (f"  (+{tmp} temp)" if tmp else "")
        ctk.CTkLabel(head, text=txt, text_color=(DANGER if cur <= 0 else TEXT),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="right")
        bar = ctk.CTkProgressBar(wrap, height=14, progress_color=(DANGER if cur <= 0 else GOOD),
                                 fg_color=SURFACE2)
        bar.pack(fill="x", pady=4)
        bar.set((cur / mx) if mx else 0)

        btns = ctk.CTkFrame(wrap, fg_color="transparent")
        btns.pack(fill="x", pady=(2, 6))
        ctk.CTkButton(btns, text="Damage", width=80, height=28, fg_color=DANGER,
                      hover_color="#e74c3c", text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._damage).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(btns, text="Heal", width=80, height=28, fg_color=GOOD,
                      hover_color="#6fd89a", text_color=BG, font=ctk.CTkFont(size=12),
                      command=self._heal).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(btns, text="Temp HP", width=80, height=28, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._temp_hp).pack(side="left", expand=True, fill="x", padx=2)

    def _death_saves(self, card):
        c = self._char
        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.pack(fill="x", padx=14, pady=(2, 10))
        succ = c.get("death_save_success", 0)
        fail = c.get("death_save_fail", 0)

        def dots(label, count, col, color):
            f = ctk.CTkFrame(wrap, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=label, text_color=MUTED, font=ctk.CTkFont(size=11),
                         width=70, anchor="w").pack(side="left")
            for i in range(1, 4):
                filled = i <= count
                ctk.CTkButton(f, text=("●" if filled else "○"), width=26, height=26,
                              corner_radius=13, fg_color="transparent", hover_color=SURFACE2,
                              text_color=(color if filled else MUTED),
                              font=ctk.CTkFont(size=16),
                              command=lambda n=i, cc=col, cur=count: self._set_death_save(cc, n, cur)
                              ).pack(side="left", padx=2)

        ctk.CTkLabel(wrap, text="Death Saves", text_color=DANGER,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        dots("Successes", succ, "death_save_success", GOOD)
        dots("Failures", fail, "death_save_fail", DANGER)

    # ── Passive senses ──────────────────────────────────────────────────────────

    def _passives(self, parent):
        card = self._card(parent, "Passive Senses")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(2, 12))
        for label, skill, col in PASSIVES:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=2)
            val = ctk.CTkLabel(row, text="10", text_color=TEXT, width=34,
                               font=ctk.CTkFont(size=15, weight="bold"))
            val.pack(side="left")
            self._passive_lbls[label] = val
            ctk.CTkLabel(row, text=f"Passive {label}", text_color=TEXT,
                         font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=6,
                                                                     fill="x", expand=True)
            ov = self._char.get(col)
            ov_var = tk.StringVar(value=("" if ov is None else str(ov)))
            e = ctk.CTkEntry(row, textvariable=ov_var, width=64, height=26, justify="center",
                             placeholder_text="auto", fg_color=SURFACE2,
                             border_color=BORDER, text_color=TEXT)
            e.pack(side="right")
            self._bind_override(e, ov_var, col)
        return card

    # ── Conditions ──────────────────────────────────────────────────────────────

    def _conditions(self, parent):
        card = self._card(parent, "Conditions")
        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.pack(fill="x", padx=12, pady=(2, 12))
        active = self._char.get("conditions", [])
        if not active:
            ctk.CTkLabel(wrap, text="None", text_color=MUTED,
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        for cond in active:
            chip = ctk.CTkFrame(wrap, fg_color=SURFACE2, corner_radius=12,
                                border_width=1, border_color=DANGER)
            chip.pack(side="left", padx=3, pady=3)
            ctk.CTkButton(chip, text=cond, height=24, fg_color="transparent",
                          hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=11),
                          command=lambda c=cond: self._show_condition_rules(c)
                          ).pack(side="left", padx=(6, 0))
            ctk.CTkButton(chip, text="✕", width=22, height=24, fg_color="transparent",
                          hover_color=DANGER, text_color=MUTED, font=ctk.CTkFont(size=11),
                          command=lambda c=cond: self._remove_condition(c)).pack(side="left")
        ctk.CTkButton(wrap, text="＋ Add", height=26, width=64, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=11),
                      command=self._conditions_popup).pack(side="left", padx=6)
        return card

    # ── Defenses ────────────────────────────────────────────────────────────────

    def _defenses(self, parent):
        card = self._card(parent, "Defenses")
        d = self._char.get("defenses", {}) or {}
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(2, 12))
        body.grid_columnconfigure(1, weight=1)
        for i, (label, key) in enumerate([("Resistances", "resist"),
                                          ("Immunities", "immune"),
                                          ("Vulnerabilities", "vuln")]):
            ctk.CTkLabel(body, text=label, text_color=MUTED, font=ctk.CTkFont(size=11),
                         width=110, anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=_join(d.get(key, [])))
            e = ctk.CTkEntry(body, textvariable=var, fg_color=SURFACE2, border_color=BORDER,
                             text_color=TEXT, height=28, placeholder_text="semicolon; separated")
            e.grid(row=i, column=1, sticky="ew", pady=3)
            self._bind_defense(e, var, key)
        return card

    # ── Live recompute of derived values ────────────────────────────────────────

    def _mod(self, code) -> int:
        return Database.ability_mod(self._char.get(code, 10))

    def _prof(self) -> int:
        ov = self._char.get("prof_bonus_override")
        if ov is not None:
            return int(ov)
        return 2 + (max(int(self._char.get("total_level", 0) or 1), 1) - 1) // 4

    def _save_prof_set(self) -> set:
        return {_norm_ability(s["ability"]) for s in self._char.get("saves", [])
                if s.get("proficient")}

    def _skill_state(self, skill) -> str:
        for s in self._char.get("skills", []):
            if s["skill"] == skill:
                return s.get("proficiency", "none")
        return "none"

    def _skill_total(self, skill) -> int:
        code = self._skill_ability.get(skill, "")
        base = self._mod(code) if code else 0
        state = self._skill_state(skill)
        prof = self._prof()
        return base + (prof if state == "proficient" else 2 * prof if state == "expertise" else 0)

    def _recompute(self):
        if not self._char:
            return
        prof = self._prof()
        if self._prof_lbl:
            self._prof_lbl.configure(text=f"+{prof}")
        save_prof = self._save_prof_set()
        for code, _ in ABILITIES:
            mod = self._mod(code)
            if code in self._mod_lbls:
                self._mod_lbls[code].configure(text=f"{mod:+d}")
            if code in self._save_dots:
                on = code in save_prof
                self._save_dots[code].configure(text=("●" if on else "○"),
                                                text_color=(ACCENT if on else MUTED))
                self._save_lbls[code].configure(
                    text=f"{mod + (prof if on else 0):+d}")
        for skill in self._skill_names:
            state = self._skill_state(skill)
            if skill in self._skill_dots:
                glyph, color = {"proficient": ("●", ACCENT), "expertise": ("★", GOLD)}.get(
                    state, ("○", MUTED))
                self._skill_dots[skill].configure(text=glyph, text_color=color)
                self._skill_lbls[skill].configure(text=f"{self._skill_total(skill):+d}")
        if self._init_lbl:
            init = self._mod("dex") + int(self._char.get("initiative_misc", 0) or 0)
            self._init_lbl.configure(text=f"{init:+d}")
        for label, skill, col in PASSIVES:
            ov = self._char.get(col)
            value = int(ov) if ov is not None else 10 + self._skill_total(skill)
            if label in self._passive_lbls:
                self._passive_lbls[label].configure(text=str(value))

    # ── Persistence helpers ─────────────────────────────────────────────────────

    def _persist(self):
        if self._cid is not None and self._char is not None:
            self.db.update_character(self._cid, self._char)

    def _bind_text(self, widget, var, col, *, is_int=False, recompute=False):
        def commit(_=None):
            raw = var.get().strip()
            if is_int:
                try:
                    val = int(raw)
                except ValueError:
                    val = self._char.get(col, 0) or 0
                    var.set(str(val))
            else:
                val = raw
            self._char[col] = val
            self._persist()
            if recompute:
                self._recompute()
        widget.bind("<FocusOut>", commit)
        widget.bind("<Return>", commit)

    def _bind_ability(self, widget, var, code):
        def live(_=None):
            try:
                self._char[code] = int(var.get())
            except ValueError:
                return
            self._recompute()
        def commit(_=None):
            try:
                self._char[code] = int(var.get())
            except ValueError:
                self._char[code] = self._char.get(code, 10)
                var.set(str(self._char[code]))
            self._persist()
            self._recompute()
        widget.bind("<KeyRelease>", live)
        widget.bind("<FocusOut>", commit)
        widget.bind("<Return>", commit)

    def _bind_override(self, widget, var, col):
        def commit(_=None):
            raw = var.get().strip()
            self._char[col] = int(raw) if raw.lstrip("-").isdigit() else None
            if raw and self._char[col] is None:
                var.set("")  # reject non-numeric
            self._persist()
            self._recompute()
        widget.bind("<FocusOut>", commit)
        widget.bind("<Return>", commit)

    def _bind_defense(self, widget, var, key):
        def commit(_=None):
            d = self._char.get("defenses") or {}
            d[key] = _split(var.get())
            self._char["defenses"] = d
            self._persist()
        widget.bind("<FocusOut>", commit)
        widget.bind("<Return>", commit)

    # ── Actions ─────────────────────────────────────────────────────────────────

    def _toggle_inspiration(self):
        new = 0 if self._char.get("inspiration") else 1
        self._char["inspiration"] = new
        self._persist()
        self._insp_btn.configure(
            text=("★ Inspiration" if new else "☆ Inspiration"),
            fg_color=(GOLD if new else SURFACE2), text_color=(BG if new else MUTED))

    def _toggle_save(self, code):
        existing = next((s for s in self._char.get("saves", [])
                         if _norm_ability(s["ability"]) == code), None)
        if existing and existing.get("proficient"):
            self.db.delete_character_save(existing["id"])
        elif existing:
            self.db.update_character_save(existing["id"], {"proficient": 1})
        else:
            self.db.create_character_save(self._cid, {"ability": code, "proficient": 1})
        self._char["saves"] = self.db.list_character_saves(self._cid)
        self._recompute()

    def _cycle_skill(self, skill):
        order = {"none": "proficient", "proficient": "expertise", "expertise": "none"}
        nxt = order[self._skill_state(skill)]
        existing = next((s for s in self._char.get("skills", []) if s["skill"] == skill), None)
        if nxt == "none":
            if existing:
                self.db.delete_character_skill(existing["id"])
        elif existing:
            self.db.update_character_skill(existing["id"], {"proficiency": nxt})
        else:
            self.db.create_character_skill(self._cid, {"skill": skill, "proficiency": nxt})
        self._char["skills"] = self.db.list_character_skills(self._cid)
        self._recompute()

    def _adjust_hit_dice(self, delta):
        total = self._char.get("total_level", 0)
        used = max(0, min(total, self._char.get("hit_dice_used", 0) + delta))
        self._char["hit_dice_used"] = used
        self._persist()
        self._render_sheet()

    def _ask_int(self, title, prompt):
        return simpledialog.askinteger(title, prompt, minvalue=0, parent=self)

    def _damage(self):
        val = self._ask_int("Damage", "Damage amount:")
        if val is None:
            return
        tmp = self._char.get("hp_temp", 0)
        absorbed = min(tmp, val)
        self._char["hp_temp"] = tmp - absorbed
        remaining = val - absorbed
        self._char["hp_current"] = max(0, self._char.get("hp_current", 0) - remaining)
        self._persist()
        self._render_sheet()

    def _heal(self):
        val = self._ask_int("Heal", "Healing amount:")
        if val is None:
            return
        mx = self._char.get("hp_max", 0)
        self._char["hp_current"] = min(mx, self._char.get("hp_current", 0) + val)
        # Healing above 0 clears death saves.
        if self._char["hp_current"] > 0:
            self._char["death_save_success"] = 0
            self._char["death_save_fail"] = 0
        self._persist()
        self._render_sheet()

    def _temp_hp(self):
        val = self._ask_int("Temporary HP", "Temporary HP (replaces if higher):")
        if val is None:
            return
        self._char["hp_temp"] = max(self._char.get("hp_temp", 0), val)
        self._persist()
        self._render_sheet()

    def _set_death_save(self, col, n, current):
        self._char[col] = (n - 1) if current == n else n  # click filled top dot to clear it
        self._persist()
        self._render_sheet()

    # ── Conditions popup + rules ────────────────────────────────────────────────

    def _conditions_popup(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Conditions")
        dlg.geometry("280x460")
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="Toggle Conditions", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT).pack(pady=(14, 6))
        scroll = ctk.CTkScrollableFrame(dlg, fg_color=SURFACE, scrollbar_button_color=ACCENT)
        scroll.pack(fill="both", expand=True, padx=8)
        current = set(self._char.get("conditions", []))
        vars_: dict[str, tk.BooleanVar] = {}
        for cond in self.db.condition_names():
            v = tk.BooleanVar(value=cond in current)
            ctk.CTkCheckBox(scroll, text=cond, variable=v, text_color=TEXT,
                            checkbox_width=18, checkbox_height=18, fg_color=DANGER,
                            hover_color="#e74c3c", border_color=BORDER).pack(anchor="w", pady=2)
            vars_[cond] = v

        def apply():
            self._char["conditions"] = [c for c, v in vars_.items() if v.get()]
            self._persist()
            dlg.destroy()
            self._render_sheet()
        ctk.CTkButton(dlg, text="Apply", fg_color=ACCENT, hover_color=ACCENT_H,
                      text_color=TEXT, height=34, command=apply).pack(fill="x", padx=12, pady=12)

    def _remove_condition(self, cond):
        self._char["conditions"] = [c for c in self._char.get("conditions", []) if c != cond]
        self._persist()
        self._render_sheet()

    def _show_condition_rules(self, cond):
        dlg = ctk.CTkToplevel(self)
        dlg.title(cond)
        dlg.geometry("440x360")
        dlg.configure(fg_color=SURFACE)
        ctk.CTkLabel(dlg, text=cond, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ACCENT).pack(anchor="w", padx=16, pady=(14, 4))
        md = MarkdownText(dlg, bg=SURFACE2)
        md.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        md.set_markdown(self._cond_rules.get(cond, "*No reference entry found.*"))

    # ── Character picker actions ────────────────────────────────────────────────

    def _new_character(self):
        cid = self.db.create_character({"name": "New Character"})
        if self.app is not None:
            self.app.active_character_id = cid
        self._cid = cid
        self.refresh()

    def _delete_character(self):
        if self._cid is None:
            return
        if not messagebox.askyesno("Delete Character",
                                   f"Permanently delete '{self._char['name']}' and all its data?"):
            return
        self.db.delete_character(self._cid)
        self._cid = None
        if self.app is not None:
            self.app.active_character_id = None
        self.refresh()

    # ── Rest stubs (wired in a later task) ──────────────────────────────────────

    def _short_rest(self):
        messagebox.showinfo("Short Rest", "Short-rest recovery will be wired up in a later update.")

    def _long_rest(self):
        messagebox.showinfo("Long Rest", "Long-rest recovery will be wired up in a later update.")
