"""Spellcasting tabs for the active character.

Two pages that reuse the Spells reference look (filters, school colours,
MarkdownText, ScrollList):

  • SpellsAvailablePage — every spell the character's class(es) can use, with
    "＋ Know" / "＋ Prepare" actions.
  • SpellbookPage — the character's picked spells grouped by level, prepared
    toggles, always-prepared, a Prepared X/max counter, and a spell-slot
    tracker (multiclass table + Warlock Pact Magic).

All edits persist immediately through the Database (character_spells +
character_spell_slots). Slot totals are derived; only `used` is stored.
"""
import tkinter as tk
import customtkinter as ctk

from pages.md_widget import MarkdownText
from pages.ui_util import ScrollList, bind_row
from pages import spell_rules

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

SCHOOLS = ["Abjuration", "Conjuration", "Divination", "Enchantment",
           "Evocation", "Illusion", "Necromancy", "Transmutation"]
CLASSES = ["Artificer", "Bard", "Cleric", "Druid", "Paladin",
           "Ranger", "Sorcerer", "Warlock", "Wizard"]
LEVELS = ["Cantrip"] + [str(i) for i in range(1, 10)]
SCHOOL_COLORS = {
    "Abjuration": "#5dade2", "Conjuration": "#f5b041", "Divination": "#aab7b8",
    "Enchantment": "#ec7063", "Evocation": "#e74c3c", "Illusion": "#bb8fce",
    "Necromancy": "#52be80", "Transmutation": "#48c9b0",
}
PACT_SLOT_LEVEL_KEY = 0   # character_spell_slots row with level=0 holds Pact used


def _lvl_label(lv: int) -> str:
    return "Cantrip" if lv == 0 else f"Level {lv}"


def build_spell_detail(parent, spell: dict | None):
    """Render a full spell into `parent` (clears it first)."""
    for w in parent.winfo_children():
        w.destroy()
    if not spell:
        ctk.CTkLabel(parent, text="Select a spell to view it", text_color=MUTED,
                     font=ctk.CTkFont(size=13)).pack(expand=True)
        return
    ctk.CTkLabel(parent, text=spell["name"], font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=TEXT, anchor="w").pack(fill="x", padx=16, pady=(16, 2))
    sub = f"{_lvl_label(spell.get('level', 0))} · {spell.get('school', '—')}"
    badges = []
    if spell.get("ritual"):
        badges.append("ritual")
    if spell.get("concentration"):
        badges.append("concentration")
    if badges:
        sub += "  (" + ", ".join(badges) + ")"
    ctk.CTkLabel(parent, text=sub, text_color=SCHOOL_COLORS.get(spell.get("school", ""), MUTED),
                 font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=(0, 6))
    ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(0, 8))

    meta = ctk.CTkFrame(parent, fg_color="transparent")
    meta.pack(fill="x", padx=16, pady=(0, 6))
    meta.columnconfigure(1, weight=1)
    r = 0
    for label, key in [("Casting Time", "casting_time"), ("Range", "range"),
                       ("Components", "components"), ("Duration", "duration"),
                       ("Classes", "classes"), ("Source", "source")]:
        val = spell.get(key)
        if not val:
            continue
        ctk.CTkLabel(meta, text=label, text_color=MUTED, font=ctk.CTkFont(size=11),
                     width=110, anchor="w").grid(row=r, column=0, sticky="w", pady=1)
        ctk.CTkLabel(meta, text=str(val), text_color=TEXT, font=ctk.CTkFont(size=12),
                     anchor="w", justify="left", wraplength=420).grid(row=r, column=1,
                                                                      sticky="w", pady=1)
        r += 1
    md = MarkdownText(parent, bg=SURFACE2)
    md.pack(fill="both", expand=True, padx=16, pady=(6, 16))
    md.set_markdown(spell.get("description", "") or "*(no description)*")


def _empty(parent, msg):
    for w in parent.winfo_children():
        w.destroy()
    card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12)
    card.pack(expand=True, pady=80, padx=80, ipadx=30, ipady=20)
    ctk.CTkLabel(card, text="No character selected",
                 font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT
                 ).pack(pady=(20, 6), padx=30)
    ctk.CTkLabel(card, text=msg, text_color=MUTED, font=ctk.CTkFont(size=12)
                 ).pack(pady=(0, 20), padx=30)


# ════════════════════════════════════════════════════════════════════════════
#  (1) Spells — Available
# ════════════════════════════════════════════════════════════════════════════

class SpellsAvailablePage(ctk.CTkFrame):
    RENDER_CAP = 300

    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._spells: list[dict] = []
        self._index: dict[str, dict] = {}   # char spell rows by lower name
        self._my_classes: list[str] = []
        self._selected: dict | None = None
        self._debounce_id = None
        self._build()

    def _debounce(self, fn, ms=160):
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(ms, fn)

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, width=340, fg_color=SURFACE, corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_propagate(False)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        ctk.CTkLabel(hdr, text="Available Spells", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TEXT).pack(side="left")

        flt = ctk.CTkFrame(left, fg_color="transparent")
        flt.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        flt.columnconfigure((0, 1, 2), weight=1)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._debounce(self._apply_filters))
        ctk.CTkEntry(flt, textvariable=self._search_var, placeholder_text="Search…",
                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT, height=30
                     ).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 4))

        self._level_var = tk.StringVar(value="All Levels")
        ctk.CTkComboBox(flt, variable=self._level_var, values=["All Levels"] + LEVELS,
                        fg_color=SURFACE2, border_color=BORDER, button_color=ACCENT,
                        text_color=TEXT, dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT,
                        height=28, font=ctk.CTkFont(size=12),
                        command=lambda _: self._apply_filters()
                        ).grid(row=1, column=0, sticky="ew", padx=(0, 3))
        self._school_var = tk.StringVar(value="All Schools")
        ctk.CTkComboBox(flt, variable=self._school_var, values=["All Schools"] + SCHOOLS,
                        fg_color=SURFACE2, border_color=BORDER, button_color=ACCENT,
                        text_color=TEXT, dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT,
                        height=28, font=ctk.CTkFont(size=12),
                        command=lambda _: self._apply_filters()
                        ).grid(row=1, column=1, sticky="ew", padx=3)
        self._class_var = tk.StringVar(value="All My Classes")
        self._class_combo = ctk.CTkComboBox(
            flt, variable=self._class_var, values=["All My Classes"],
            fg_color=SURFACE2, border_color=BORDER, button_color=ACCENT,
            text_color=TEXT, dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT,
            height=28, font=ctk.CTkFont(size=12), command=lambda _: self._apply_filters())
        self._class_combo.grid(row=1, column=2, sticky="ew", padx=(3, 0))

        self._list_frame = ScrollList(left, bg=SURFACE, accent=ACCENT)
        self._list_frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=(4, 8))

        self._right = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        self._right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=1)
        build_spell_detail(self._right, None)

    # ── data ────────────────────────────────────────────────────────────────
    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        if not self._char:
            self._list_frame.clear(); self._list_frame.finalize()
            _empty(self._right, "Create or select a character on the Character Sheet tab.")
            return
        self._my_classes = [c["class"] for c in self._char["classes"] if c.get("class")] or CLASSES
        all_label = "All My Classes" if self._char["classes"] else "All Classes"
        values = [all_label] + self._my_classes
        self._class_combo.configure(values=values)
        if self._class_var.get() not in values:
            self._class_var.set(all_label)
        self._apply_filters()

    def _apply_filters(self):
        if not self._char:
            return
        lvl = self._level_var.get()
        level = "" if lvl == "All Levels" else (0 if lvl == "Cantrip" else int(lvl))
        school = self._school_var.get()
        rows = self.db.list_spells(
            search=self._search_var.get().strip(), level=level,
            school="" if school == "All Schools" else school)
        sel = self._class_var.get()
        if sel.startswith("All"):
            targets = [c.lower() for c in self._my_classes]
        else:
            targets = [sel.lower()]
        self._spells = [s for s in rows
                        if any(t in (s.get("classes", "") or "").lower() for t in targets)]
        self._index = {cs["spell_name"].lower(): cs
                       for cs in self.db.list_character_spells(self._cid)}
        self._render_list()

    def _render_list(self):
        self._list_frame.clear()
        body = self._list_frame.body
        for s in self._spells[:self.RENDER_CAP]:
            cs = self._index.get(s["name"].lower())
            color = SCHOOL_COLORS.get(s.get("school", ""), MUTED)
            lv = "C" if s.get("level", 0) == 0 else str(s["level"])
            row = tk.Frame(body, bg=SURFACE, cursor="hand2")
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=lv, fg=ACCENT, bg=SURFACE, width=2,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(6, 2))
            # action buttons (don't trigger the row-select binding)
            tk.Button(row, text="Prep", font=("Segoe UI", 8), bd=0, padx=4,
                      bg=(GOOD if cs and cs.get("prepared") else SURFACE2),
                      fg=(BG if cs and cs.get("prepared") else TEXT),
                      activebackground=ACCENT_H, cursor="hand2",
                      command=lambda sp=s: self._set_flag(sp, "prepared")
                      ).pack(side="right", padx=(2, 6))
            tk.Button(row, text="Know", font=("Segoe UI", 8), bd=0, padx=4,
                      bg=(ACCENT if cs and cs.get("known") else SURFACE2),
                      fg=TEXT, activebackground=ACCENT_H, cursor="hand2",
                      command=lambda sp=s: self._set_flag(sp, "known")
                      ).pack(side="right", padx=2)
            name = tk.Label(row, text=s["name"], anchor="w", fg=TEXT, bg=SURFACE,
                            font=("Segoe UI", 11))
            name.pack(side="left", fill="x", expand=True, pady=4)
            tk.Label(row, text=s.get("school", ""), fg=color, bg=SURFACE,
                     font=("Segoe UI", 8)).pack(side="right", padx=4)
            # Clicking the name/level area opens the detail (buttons handle their own).
            for w in (row, name):
                w.bind("<Button-1>", lambda e, sp=s: self._select(sp))
        if len(self._spells) > self.RENDER_CAP:
            tk.Label(body, text=f"Showing {self.RENDER_CAP} of {len(self._spells)} — "
                              f"narrow with Search or the filters.",
                     bg=SURFACE, fg=MUTED, font=("Segoe UI", 9), wraplength=260
                     ).pack(fill="x", padx=8, pady=8)
        self._list_frame.finalize()

    def _select(self, spell):
        self._selected = spell
        build_spell_detail(self._right, spell)
        self._add_detail_actions(spell)

    def _add_detail_actions(self, spell):
        cs = self._index.get(spell["name"].lower())
        bar = ctk.CTkFrame(self._right, fg_color="transparent")
        bar.place(relx=1.0, rely=0.0, anchor="ne", x=-16, y=16)
        ctk.CTkButton(bar, text=("✓ Known" if cs and cs.get("known") else "＋ Know"),
                      width=84, height=28, fg_color=(ACCENT if cs and cs.get("known") else SURFACE2),
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=lambda: self._set_flag(spell, "known")).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bar, text=("✓ Prepared" if cs and cs.get("prepared") else "＋ Prepare"),
                      width=96, height=28, fg_color=(GOOD if cs and cs.get("prepared") else SURFACE2),
                      hover_color="#6fd89a", text_color=(BG if cs and cs.get("prepared") else TEXT),
                      font=ctk.CTkFont(size=12),
                      command=lambda: self._set_flag(spell, "prepared")).pack(side="left")

    def _set_flag(self, spell, flag):
        """Toggle known/prepared for this spell on the character."""
        cs = self._index.get(spell["name"].lower())
        if cs:
            self.db.update_character_spell(cs["id"], {flag: 0 if cs.get(flag) else 1})
        else:
            self.db.create_character_spell(self._cid, {
                "spell_name": spell["name"],
                "spell_ref_id": spell.get("id"),
                flag: 1})
        self._index = {c["spell_name"].lower(): c
                       for c in self.db.list_character_spells(self._cid)}
        self._render_list()
        if self._selected and self._selected["name"] == spell["name"]:
            self._select(self._selected)


# ════════════════════════════════════════════════════════════════════════════
#  (2) Spellbook
# ════════════════════════════════════════════════════════════════════════════

class SpellbookPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._ref_by_id: dict[int, dict] = {}
        self._ref_by_name: dict[str, dict] = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._left = ctk.CTkFrame(self, width=420, fg_color=SURFACE, corner_radius=8)
        self._left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        self._left.grid_propagate(False)
        self._left.grid_rowconfigure(1, weight=1)
        self._left.grid_columnconfigure(0, weight=1)

        self._top = ctk.CTkFrame(self._left, fg_color="transparent")
        self._top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))

        self._scroll = ctk.CTkScrollableFrame(self._left, fg_color=SURFACE,
                                              scrollbar_button_color=ACCENT)
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 8))

        self._right = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        self._right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=1)
        build_spell_detail(self._right, None)

    # ── data ────────────────────────────────────────────────────────────────
    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        for w in self._top.winfo_children():
            w.destroy()
        for w in self._scroll.winfo_children():
            w.destroy()
        if not self._char:
            _empty(self._right, "Create or select a character on the Character Sheet tab.")
            return
        if not self._ref_by_id:
            for sp in self.db.list_spells():
                self._ref_by_id[sp["id"]] = sp
                self._ref_by_name[sp["name"].lower()] = sp
        self._rebuild_top()
        self._render_spells()

    def _rebuild_top(self):
        """Rebuild the prepared counter + slot tracker (both live in _top)."""
        for w in self._top.winfo_children():
            w.destroy()
        self._render_header()
        self._render_slots()

    def _ref_for(self, cs) -> dict:
        if cs.get("spell_ref_id") and cs["spell_ref_id"] in self._ref_by_id:
            return self._ref_by_id[cs["spell_ref_id"]]
        return self._ref_by_name.get((cs.get("spell_name") or "").lower(), {})

    def _slots_used(self) -> dict[int, int]:
        return {r["level"]: r["used"] for r in self.db.list_character_spell_slots(self._cid)}

    # ── header: prepared counter ──────────────────────────────────────────────
    def _prepared_counts(self) -> tuple[int, int]:
        """(spells currently prepared, prepared maximum). Cantrips and
        always-prepared spells don't count toward the prepared total."""
        prepared = 0
        for cs in self.db.list_character_spells(self._cid):
            ref = self._ref_for(cs)
            lvl = ref.get("level", 0) if ref else 0
            if cs.get("prepared") and not cs.get("always_prepared") and lvl and lvl > 0:
                prepared += 1
        override = self._char.get("prepared_max_override")
        max_prep = override if override is not None else \
            spell_rules.prepared_max(self._char["classes"], self._char)
        return prepared, max_prep

    def _render_header(self):
        prepared, max_prep = self._prepared_counts()
        override = self._char.get("prepared_max_override")

        row = ctk.CTkFrame(self._top, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Prepared", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        over = bool(max_prep) and prepared > max_prep
        ctk.CTkLabel(row, text=f"  {prepared} / {max_prep if max_prep else '—'}",
                     text_color=(DANGER if over else TEXT),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkLabel(row, text="max override:", text_color=MUTED,
                     font=ctk.CTkFont(size=10)).pack(side="left", padx=(12, 4))
        ov_var = tk.StringVar(value="" if override is None else str(override))
        e = ctk.CTkEntry(row, textvariable=ov_var, width=56, height=26, justify="center",
                         placeholder_text="auto", fg_color=SURFACE2, border_color=BORDER,
                         text_color=TEXT)
        e.pack(side="left")

        def commit(_=None):
            raw = ov_var.get().strip()
            self._char["prepared_max_override"] = int(raw) if raw.lstrip("-").isdigit() else None
            if raw and self._char["prepared_max_override"] is None:
                ov_var.set("")
            self.db.update_character(self._cid, self._char)
            self._rebuild_top()
        e.bind("<FocusOut>", commit)
        e.bind("<Return>", commit)

    # ── spell-slot tracker ────────────────────────────────────────────────────
    def _render_slots(self):
        card = ctk.CTkFrame(self._top, fg_color=SURFACE2, corner_radius=8)
        card.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(card, text="Spell Slots", text_color=ACCENT,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(6, 0))
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=(2, 8))

        slots = spell_rules.spell_slots(self._char["classes"])
        used = self._slots_used()
        pact = spell_rules.pact_magic(self._char["classes"])

        def slot_row(label, total, used_n, expend, restore, color):
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.pack(fill="x", pady=1)
            ctk.CTkLabel(f, text=label, text_color=TEXT, width=64, anchor="w",
                         font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkButton(f, text="−", width=26, height=24, fg_color=SURFACE,
                          hover_color=BORDER, text_color=TEXT, command=restore
                          ).pack(side="left", padx=2)
            ctk.CTkLabel(f, text=f"{max(0, total - used_n)}/{total}", text_color=color,
                         width=44, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            ctk.CTkButton(f, text="+", width=26, height=24, fg_color=SURFACE,
                          hover_color=BORDER, text_color=TEXT, command=expend
                          ).pack(side="left", padx=2)

        if not slots and not pact:
            ctk.CTkLabel(grid, text="No spell slots (non-caster or level too low).",
                         text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=4)
        for lv in sorted(slots):
            total = slots[lv]
            slot_row(f"Level {lv}", total, min(total, used.get(lv, 0)),
                     lambda l=lv: self._spend_slot(l, +1),
                     lambda l=lv: self._spend_slot(l, -1), TEXT)
        if pact:
            slot_row(f"Pact (L{pact['level']})", pact["count"],
                     min(pact["count"], used.get(PACT_SLOT_LEVEL_KEY, 0)),
                     lambda: self._spend_slot(PACT_SLOT_LEVEL_KEY, +1),
                     lambda: self._spend_slot(PACT_SLOT_LEVEL_KEY, -1), GOLD)

    def _spend_slot(self, level_key, delta):
        slots = spell_rules.spell_slots(self._char["classes"])
        pact = spell_rules.pact_magic(self._char["classes"])
        total = (pact["count"] if pact else 0) if level_key == PACT_SLOT_LEVEL_KEY \
            else slots.get(level_key, 0)
        rows = {r["level"]: r for r in self.db.list_character_spell_slots(self._cid)}
        cur = rows.get(level_key, {}).get("used", 0)
        new = max(0, min(total, cur + delta))
        if level_key in rows:
            self.db.update_character_spell_slot(rows[level_key]["id"], {"used": new})
        else:
            self.db.create_character_spell_slot(self._cid, {"level": level_key, "used": new})
        self._rebuild_top()

    # ── grouped spell list ────────────────────────────────────────────────────
    def _render_spells(self):
        spells = self.db.list_character_spells(self._cid)
        groups: dict[int, list] = {}
        for cs in spells:
            ref = self._ref_for(cs)
            lvl = ref.get("level", 0) if ref else 0
            groups.setdefault(lvl if lvl is not None else 0, []).append((cs, ref))

        if not spells:
            ctk.CTkLabel(self._scroll, text="No spells yet — add some from “Spells — Available”.",
                         text_color=MUTED, font=ctk.CTkFont(size=12)).pack(pady=20)
            return

        for lvl in sorted(groups):
            head = "Cantrips" if lvl == 0 else f"Level {lvl}"
            ctk.CTkLabel(self._scroll, text=head, text_color=ACCENT,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).pack(anchor="w", padx=6, pady=(10, 2))
            for cs, ref in sorted(groups[lvl], key=lambda t: (t[0].get("spell_name") or "").lower()):
                self._spell_row(cs, ref, lvl)

    def _spell_row(self, cs, ref, lvl):
        row = ctk.CTkFrame(self._scroll, fg_color=SURFACE2, corner_radius=6)
        row.pack(fill="x", padx=4, pady=1)
        school = (ref.get("school", "") if ref else "")
        color = SCHOOL_COLORS.get(school, MUTED)

        name_btn = ctk.CTkButton(
            row, text=cs["spell_name"], anchor="w", height=30, fg_color="transparent",
            hover_color=BORDER, text_color=(TEXT if ref else MUTED), font=ctk.CTkFont(size=12),
            command=lambda: build_spell_detail(self._right, ref or {
                "name": cs["spell_name"], "level": lvl,
                "description": "*Not found in the reference compendium.*"}))
        name_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # remove
        ctk.CTkButton(row, text="✕", width=26, height=26, fg_color="transparent",
                      hover_color=DANGER, text_color=MUTED, font=ctk.CTkFont(size=11),
                      command=lambda: self._remove(cs)).pack(side="right", padx=(0, 4))
        # always-prepared (domain/oath, etc.) — not shown for cantrips
        if lvl and lvl > 0:
            ap = bool(cs.get("always_prepared"))
            ctk.CTkButton(row, text="Always", width=58, height=24,
                          fg_color=(GOLD if ap else SURFACE), hover_color=ACCENT_H,
                          text_color=(BG if ap else MUTED), font=ctk.CTkFont(size=10),
                          command=lambda: self._toggle(cs, "always_prepared")
                          ).pack(side="right", padx=2)
            prep = bool(cs.get("prepared"))
            ctk.CTkButton(row, text=("Prepared" if prep else "Prepare"), width=74, height=24,
                          fg_color=(GOOD if prep else SURFACE), hover_color="#6fd89a",
                          text_color=(BG if prep else MUTED), font=ctk.CTkFont(size=10),
                          command=lambda: self._toggle(cs, "prepared")).pack(side="right", padx=2)
        else:
            ctk.CTkLabel(row, text="at will", text_color=MUTED,
                         font=ctk.CTkFont(size=10)).pack(side="right", padx=8)
        if school:
            ctk.CTkLabel(row, text=school, text_color=color,
                         font=ctk.CTkFont(size=9)).pack(side="right", padx=4)

    def _toggle(self, cs, flag):
        self.db.update_character_spell(cs["id"], {flag: 0 if cs.get(flag) else 1})
        self.refresh()

    def _remove(self, cs):
        self.db.delete_character_spell(cs["id"])
        self.refresh()
