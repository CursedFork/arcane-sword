"""Character creation wizard — guided multi-step flow for building a new 5e character.

The wizard is a full-window page (sidebar hidden by App while it's active).
Navigating back to 'character_sheet' re-shows the sidebar.

Steps:
  1. Identity      — name, player name, alignment, XP tracking
  2. Race          — pick race + subrace from compendium
  3. Class & Level — class, starting level, subclass
  4. Ability Scores— point buy / standard array / manual roll (with dice roller)
  5. Background & Skills — background + class skill picks
  6. Equipment     — package A / package B / starting gold
  7. Spells        — cantrips + known spells (skipped for non-casters)
  8. Review        — summary then create
"""
import random
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from db import Database
from pages import theme
from pages import wizard_data as wd
from pages import levelup_rules as lr
from pages import spell_rules as sr
from pages import reference_lookup as ref

# Colour palette — rewritten by theme.apply_all() at theme change.
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

_ABILITIES = [("str", "STR"), ("dex", "DEX"), ("con", "CON"),
              ("int", "INT"), ("wis", "WIS"), ("cha", "CHA")]

_STEP_NAMES = ["Identity", "Race", "Class & Level", "Ability Scores",
               "Background & Skills", "Equipment", "Spells", "Review"]


class CharacterWizardPage(ctk.CTkFrame):
    def __init__(self, parent, db: Database, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._data: dict = {}
        self._step_idx = 0
        self._collector = None   # callable that reads current step's widgets

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Reference data cached once
        self._races = []
        self._backgrounds = []

        self._build_chrome()

    # ── Outer chrome ─────────────────────────────────────────────────────────

    def _build_chrome(self):
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        ctk.CTkLabel(hdr, text="✦  Create New Character",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=24, pady=14)

        self._step_lbl = ctk.CTkLabel(hdr, text="", text_color=MUTED,
                                       font=ctk.CTkFont(size=12))
        self._step_lbl.pack(side="right", padx=24)

        self._content = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                                scrollbar_button_color=ACCENT)
        self._content.grid(row=1, column=0, sticky="nsew")

        ftr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=68)
        ftr.grid(row=2, column=0, sticky="ew")
        ftr.grid_propagate(False)

        self._back_btn = ctk.CTkButton(
            ftr, text="← Back", width=120, height=40,
            fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT,
            font=ctk.CTkFont(size=13), command=self._go_back)
        self._back_btn.pack(side="left", padx=(20, 6), pady=14)

        ctk.CTkButton(
            ftr, text="✕ Cancel", width=90, height=40,
            fg_color="transparent", hover_color=DANGER, text_color=MUTED,
            font=ctk.CTkFont(size=13), command=self._cancel
        ).pack(side="left", padx=0, pady=14)

        self._next_btn = ctk.CTkButton(
            ftr, text="Next →", width=180, height=40,
            fg_color=ACCENT, hover_color=ACCENT_H, text_color=TEXT,
            font=ctk.CTkFont(size=14, weight="bold"), command=self._go_next)
        self._next_btn.pack(side="right", padx=20, pady=14)

        self._dots_frame = ctk.CTkFrame(ftr, fg_color="transparent")
        self._dots_frame.pack(side="right", padx=20)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _active_steps(self) -> list[str]:
        steps = ["Identity", "Race", "Class & Level", "Ability Scores",
                 "Background & Skills", "Equipment"]
        if wd.is_spellcaster(self._data.get("class_name", "")):
            steps.append("Spells")
        steps.append("Review")
        return steps

    def refresh(self):
        self._races = self.db.list_char_options(category="race")
        self._backgrounds = self.db.list_char_options(category="background")
        self._data = {
            "name": "", "player_name": "", "alignment": "True Neutral",
            "xp_tracking": "milestone", "xp": 0,
            "race": "", "subrace": "",
            "class_name": "", "level": 1, "subclass": "",
            "score_method": "standard_array",
            "scores": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
            "background": "", "class_skills": [], "background_skills": [],
            "equipment_choice": "A",
            "cantrips_chosen": [], "spells_chosen": [],
        }
        self._step_idx = 0
        self._collector = None
        self._render_step()

    def _render_step(self):
        steps = self._active_steps()
        idx = self._step_idx
        name = steps[idx]
        total = len(steps)

        self._step_lbl.configure(text=f"Step {idx+1} of {total}  —  {name}")
        self._back_btn.configure(state="normal" if idx > 0 else "disabled")

        is_last = idx == total - 1
        self._next_btn.configure(
            text="✓  Create Character" if is_last else "Next  →",
            fg_color=GOOD if is_last else ACCENT,
            hover_color="#3fa86a" if is_last else ACCENT_H,
        )

        for w in self._dots_frame.winfo_children():
            w.destroy()
        for i, sn in enumerate(steps):
            if i < idx:
                col = GOOD
            elif i == idx:
                col = ACCENT
            else:
                col = SURFACE2
            ctk.CTkFrame(self._dots_frame, fg_color=col,
                         width=10, height=10, corner_radius=5).pack(side="left", padx=3)

        for w in self._content.winfo_children():
            w.destroy()
        self._collector = None

        renderers = {
            "Identity":           self._step_identity,
            "Race":               self._step_race,
            "Class & Level":      self._step_class,
            "Ability Scores":     self._step_scores,
            "Background & Skills":self._step_background,
            "Equipment":          self._step_equipment,
            "Spells":             self._step_spells,
            "Review":             self._step_review,
        }
        renderers[name]()

    def _go_next(self):
        steps = self._active_steps()
        name = steps[self._step_idx]
        if self._collector:
            self._collector()
        err = self._validate(name)
        if err:
            messagebox.showwarning("Complete this step", err, parent=self)
            return
        if self._step_idx == len(steps) - 1:
            self._create_character()
        else:
            self._step_idx += 1
            self._render_step()

    def _go_back(self):
        if self._step_idx > 0:
            if self._collector:
                self._collector()
            self._step_idx -= 1
            self._render_step()

    def _cancel(self):
        if messagebox.askyesno("Cancel", "Discard and go back to the character list?",
                               parent=self):
            self._go_home()

    def _go_home(self):
        if self.app and hasattr(self.app, "show_page"):
            self.app.show_page("character_sheet")

    def _validate(self, step: str) -> str:
        d = self._data
        if step == "Identity":
            if not d.get("name", "").strip():
                return "Please enter a character name."
        elif step == "Race":
            if not d.get("race", "").strip():
                return "Please choose a race."
        elif step == "Class & Level":
            if not d.get("class_name", "").strip():
                return "Please choose a class."
        elif step == "Ability Scores":
            m = d.get("score_method", "")
            sc = d.get("scores", {})
            if m == "standard_array":
                vals = [sc.get(a, 0) for a, _ in _ABILITIES]
                if sorted(vals) != sorted(wd.STANDARD_ARRAY):
                    return "Assign each Standard Array value (15, 14, 13, 12, 10, 8) exactly once."
            elif m == "point_buy":
                spent = sum(wd.POINT_BUY_COST.get(sc.get(a, 8), 0) for a, _ in _ABILITIES)
                if spent != wd.POINT_BUY_BUDGET:
                    remaining = wd.POINT_BUY_BUDGET - spent
                    if remaining > 0:
                        return f"You have {remaining} unspent point-buy point(s). Spend them all."
                    return f"You have overspent your point-buy budget by {-remaining} point(s)."
        elif step == "Background & Skills":
            if not d.get("background", "").strip():
                return "Please choose a background."
            cn = d.get("class_name", "").lower()
            spec = wd.CLASS_SKILL_CHOICES.get(cn, {})
            needed = spec.get("count", 0)
            if len(d.get("class_skills", [])) < needed:
                return f"Choose {needed} skill(s) for your class (you have {len(d.get('class_skills', []))})."
        elif step == "Spells":
            cn = d.get("class_name", "").lower()
            level = d.get("level", 1)
            need_c = wd.cantrips_known(cn, level)
            if len(d.get("cantrips_chosen", [])) < need_c:
                return f"Choose {need_c} cantrip(s) for your class."
            if not wd.is_preparing_caster(cn):
                need_s = wd.spells_known_count(cn, level)
                chosen_s = len([s for s in d.get("spells_chosen", []) if s not in d.get("cantrips_chosen", [])])
                if cn == "ranger" and level < 2:
                    pass  # rangers don't get spells at level 1
                elif chosen_s < need_s and need_s > 0:
                    return f"Choose {need_s} spell(s) known for your class."
        return ""

    # ── Step 1: Identity ──────────────────────────────────────────────────────

    def _step_identity(self):
        p = self._content
        _section_title(p, "Who are you?")
        ctk.CTkLabel(p, text="Let's start with the basics — your character's name and a few quick choices "
                     "about how the campaign tracks progress.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=600,
                     justify="left").pack(anchor="w", pady=(0, 20))

        # Name + player name
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=1)

        nf = ctk.CTkFrame(row, fg_color="transparent")
        nf.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ctk.CTkLabel(nf, text="Character Name *", text_color=ACCENT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        name_var = tk.StringVar(value=self._data.get("name", ""))
        name_entry = ctk.CTkEntry(nf, textvariable=name_var, height=38,
                                   fg_color=SURFACE, border_color=BORDER, text_color=TEXT,
                                   font=ctk.CTkFont(size=14), placeholder_text="e.g. Arannis Brightmantle")
        name_entry.pack(fill="x", pady=4)
        name_entry.focus()

        pf = ctk.CTkFrame(row, fg_color="transparent")
        pf.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(pf, text="Player Name (optional)", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(anchor="w")
        player_var = tk.StringVar(value=self._data.get("player_name", ""))
        ctk.CTkEntry(pf, textvariable=player_var, height=38,
                     fg_color=SURFACE, border_color=BORDER, text_color=TEXT,
                     font=ctk.CTkFont(size=13), placeholder_text="Your real name").pack(fill="x", pady=4)

        # Alignment
        ctk.CTkLabel(p, text="Alignment", text_color=ACCENT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(16, 4))
        ctk.CTkLabel(p, text="Alignment describes your character's moral and ethical outlook. "
                     "It's a guide for roleplay, not a cage — feel free to evolve.",
                     text_color=MUTED, font=ctk.CTkFont(size=11), wraplength=560,
                     justify="left").pack(anchor="w", pady=(0, 8))

        align_frame = ctk.CTkFrame(p, fg_color="transparent")
        align_frame.pack(anchor="w", pady=(0, 8))
        align_var = tk.StringVar(value=self._data.get("alignment", "True Neutral"))

        def _pick_align(lbl):
            align_var.set(lbl)
            for btn in align_btns:
                is_sel = btn.cget("text") == lbl
                btn.configure(fg_color=ACCENT if is_sel else SURFACE2,
                              text_color=TEXT if is_sel else MUTED)

        align_btns = []
        for i, (full, abbr) in enumerate(wd.ALIGNMENTS):
            btn = ctk.CTkButton(
                align_frame, text=full, width=130, height=36,
                fg_color=(ACCENT if full == align_var.get() else SURFACE2),
                hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                command=lambda f=full: _pick_align(f))
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=3)
            align_btns.append(btn)

        # XP Tracking
        ctk.CTkLabel(p, text="Experience Tracking", text_color=ACCENT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(16, 4))
        xp_frame = ctk.CTkFrame(p, fg_color="transparent")
        xp_frame.pack(fill="x", pady=(0, 4))

        xp_mode = tk.StringVar(value=self._data.get("xp_tracking", "milestone"))
        xp_val = tk.StringVar(value=str(self._data.get("xp", 0)))
        xp_entry_frame = ctk.CTkFrame(p, fg_color="transparent")

        def _set_xp_mode(m):
            xp_mode.set(m)
            if m == "xp":
                xp_entry_frame.pack(anchor="w", pady=2)
            else:
                xp_entry_frame.pack_forget()

        for mode, lbl, desc in [
            ("milestone", "Milestone",
             "Your DM decides when you level up — no tracking needed. Great for narrative campaigns."),
            ("xp", "Experience Points",
             "You earn XP from encounters and milestones, leveling up when you hit the threshold."),
        ]:
            card = ctk.CTkFrame(xp_frame, fg_color=SURFACE, corner_radius=8, border_width=1,
                                border_color=BORDER)
            card.pack(fill="x", pady=3)
            rb = ctk.CTkRadioButton(card, text=lbl, variable=xp_mode, value=mode,
                                     text_color=TEXT, fg_color=ACCENT,
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     command=lambda m=mode: _set_xp_mode(m))
            rb.pack(side="left", padx=14, pady=10)
            ctk.CTkLabel(card, text=desc, text_color=MUTED, font=ctk.CTkFont(size=11),
                         wraplength=480, justify="left").pack(side="left", padx=8, pady=10)

        ctk.CTkLabel(xp_entry_frame, text="Starting XP:", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        ctk.CTkEntry(xp_entry_frame, textvariable=xp_val, width=100, height=32,
                     fg_color=SURFACE, border_color=BORDER, text_color=TEXT,
                     font=ctk.CTkFont(size=13)).pack(side="left")
        if xp_mode.get() == "xp":
            xp_entry_frame.pack(anchor="w", pady=2)

        def collect():
            self._data["name"] = name_var.get().strip()
            self._data["player_name"] = player_var.get().strip()
            self._data["alignment"] = align_var.get()
            self._data["xp_tracking"] = xp_mode.get()
            try:
                self._data["xp"] = int(xp_val.get()) if xp_mode.get() == "xp" else 0
            except ValueError:
                self._data["xp"] = 0

        self._collector = collect

    # ── Step 2: Race ─────────────────────────────────────────────────────────

    def _step_race(self):
        p = self._content
        _section_title(p, "Choose Your Race")
        ctk.CTkLabel(p, text="Your race shapes your character's appearance, background history, and some "
                     "natural abilities. It also adds bonuses to certain ability scores.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=600,
                     justify="left").pack(anchor="w", pady=(0, 16))

        outer = ctk.CTkFrame(p, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=2)

        # Left: searchable list
        list_frame = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_frame.grid_rowconfigure(1, weight=1)

        search_var = tk.StringVar()
        ctk.CTkEntry(list_frame, textvariable=search_var, placeholder_text="Search races…",
                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT,
                     height=34).pack(fill="x", padx=10, pady=8)

        race_listbox = ctk.CTkScrollableFrame(list_frame, fg_color="transparent",
                                               scrollbar_button_color=ACCENT, height=380)
        race_listbox.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # Right: description
        desc_frame = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10)
        desc_frame.grid(row=0, column=1, sticky="nsew")
        desc_frame.grid_rowconfigure(1, weight=1)

        desc_title = ctk.CTkLabel(desc_frame, text="Select a race to see details",
                                   text_color=MUTED, font=ctk.CTkFont(size=14, weight="bold"),
                                   wraplength=380)
        desc_title.pack(anchor="w", padx=16, pady=(14, 4))

        bonus_lbl = ctk.CTkLabel(desc_frame, text="", text_color=GOLD,
                                  font=ctk.CTkFont(size=11))
        bonus_lbl.pack(anchor="w", padx=16)

        desc_scroll = ctk.CTkScrollableFrame(desc_frame, fg_color="transparent",
                                              scrollbar_button_color=ACCENT, height=300)
        desc_scroll.pack(fill="both", expand=True, padx=8, pady=4)
        desc_text = ctk.CTkLabel(desc_scroll, text="", text_color=MUTED,
                                  font=ctk.CTkFont(size=11), wraplength=380, justify="left")
        desc_text.pack(anchor="w", padx=8, pady=4)

        # Subrace section
        sub_frame = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=8, border_width=1,
                                  border_color=BORDER)
        subrace_var = tk.StringVar(value=self._data.get("subrace", ""))
        sub_label = ctk.CTkLabel(sub_frame, text="", text_color=ACCENT,
                                  font=ctk.CTkFont(size=12, weight="bold"))
        sub_menu = ctk.CTkOptionMenu(sub_frame, values=["—"], variable=subrace_var,
                                     fg_color=SURFACE2, button_color=ACCENT,
                                     button_hover_color=ACCENT_H, text_color=TEXT,
                                     dropdown_fg_color=SURFACE, dropdown_text_color=TEXT)

        race_var = tk.StringVar(value=self._data.get("race", ""))
        _btn_map: dict[str, ctk.CTkButton] = {}

        def _pick_race(name: str, opt: dict):
            race_var.set(name)
            for n, b in _btn_map.items():
                b.configure(fg_color=(ACCENT if n == name else "transparent"),
                            text_color=(TEXT if n == name else MUTED))
            desc_title.configure(text=name)
            bonuses = wd.RACIAL_BONUSES.get(name, {})
            if bonuses:
                bstr = "  ".join(f"+{v} {k.upper()}" for k, v in bonuses.items())
                bonus_lbl.configure(text=f"ASI: {bstr}")
            else:
                bonus_lbl.configure(text="")
            body = opt.get("body_md", "") or ""
            # strip markdown to plain text for label
            import re
            plain = re.sub(r"\*+([^*]+)\*+", r"\1", body)
            plain = re.sub(r"#+\s*", "", plain)
            desc_text.configure(text=plain[:800] + ("…" if len(plain) > 800 else ""))
            # Subraces: look for category=subrace, parent=name in DB
            subraces = [r["name"] for r in self._races
                        if r.get("category", "") == "subrace"
                        and (r.get("parent", "") or "").lower() == name.lower()]
            if subraces:
                sub_label.configure(text=f"Subrace of {name}")
                opts = ["(none)"] + subraces
                sub_menu.configure(values=opts)
                if subrace_var.get() not in subraces:
                    subrace_var.set("(none)")
                sub_label.pack(anchor="w", padx=14, pady=(10, 2))
                sub_menu.pack(anchor="w", padx=14, pady=(0, 10))
                sub_frame.pack(fill="x", pady=(8, 0))
            else:
                sub_frame.pack_forget()
                subrace_var.set("")

        def _rebuild_list(*_):
            q = search_var.get().strip().lower()
            for w in race_listbox.winfo_children():
                w.destroy()
            _btn_map.clear()
            shown = [r for r in self._races
                     if r.get("category", "") == "race"
                     and (not q or q in (r.get("name", "") or "").lower())]
            for opt in shown:
                nm = opt["name"]
                btn = ctk.CTkButton(
                    race_listbox, text=nm, anchor="w", height=32,
                    fg_color=(ACCENT if nm == race_var.get() else "transparent"),
                    hover_color=SURFACE2, text_color=(TEXT if nm == race_var.get() else MUTED),
                    font=ctk.CTkFont(size=13), corner_radius=4,
                    command=lambda n=nm, o=opt: _pick_race(n, o))
                btn.pack(fill="x", padx=4, pady=1)
                _btn_map[nm] = btn

        search_var.trace_add("write", _rebuild_list)
        _rebuild_list()

        # Restore selection if returning to this step
        if race_var.get():
            for opt in self._races:
                if opt["name"] == race_var.get():
                    _pick_race(opt["name"], opt)
                    break

        def collect():
            self._data["race"] = race_var.get()
            sr = subrace_var.get()
            self._data["subrace"] = sr if sr and sr != "(none)" else ""

        self._collector = collect

    # ── Step 3: Class & Level ─────────────────────────────────────────────────

    def _step_class(self):
        p = self._content
        _section_title(p, "Choose Your Class & Level")
        ctk.CTkLabel(p, text="Your class is your character's primary calling — it determines your combat "
                     "style, special abilities, and how you grow. Set your starting level if joining "
                     "a campaign that's already in progress.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=600,
                     justify="left").pack(anchor="w", pady=(0, 16))

        outer = ctk.CTkFrame(p, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=2)

        list_frame = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        class_listbox = ctk.CTkScrollableFrame(list_frame, fg_color="transparent",
                                                scrollbar_button_color=ACCENT, height=380)
        class_listbox.pack(fill="both", expand=True, padx=4, pady=8)

        right = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew")

        class_title = ctk.CTkLabel(right, text="Select a class to see details",
                                    text_color=MUTED, font=ctk.CTkFont(size=14, weight="bold"),
                                    wraplength=380)
        class_title.pack(anchor="w", padx=16, pady=(14, 4))

        class_desc = ctk.CTkScrollableFrame(right, fg_color="transparent",
                                             scrollbar_button_color=ACCENT, height=220)
        class_desc.pack(fill="both", expand=False, padx=8, pady=4)
        class_desc_lbl = ctk.CTkLabel(class_desc, text="", text_color=MUTED,
                                       font=ctk.CTkFont(size=11), wraplength=380, justify="left")
        class_desc_lbl.pack(anchor="w", padx=8, pady=4)

        # Level + subclass section (below the two columns)
        cfg_frame = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=10, border_width=1,
                                  border_color=BORDER)

        class_var = tk.StringVar(value=self._data.get("class_name", ""))
        level_var = tk.IntVar(value=self._data.get("level", 1))
        subclass_var = tk.StringVar(value=self._data.get("subclass", ""))
        _class_btns: dict[str, ctk.CTkButton] = {}

        subclass_row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        subclass_lbl_w = ctk.CTkLabel(subclass_row, text="Subclass", text_color=ACCENT,
                                       font=ctk.CTkFont(size=12, weight="bold"))
        subclass_hint = ctk.CTkLabel(subclass_row, text="", text_color=MUTED,
                                      font=ctk.CTkFont(size=11))
        subclass_menu = ctk.CTkOptionMenu(subclass_row, variable=subclass_var,
                                          values=["—"],
                                          fg_color=SURFACE2, button_color=ACCENT,
                                          button_hover_color=ACCENT_H, text_color=TEXT,
                                          dropdown_fg_color=SURFACE, dropdown_text_color=TEXT)

        def _update_subclass_row():
            cn = class_var.get().lower()
            lv = level_var.get()
            sc_lv = lr.subclass_level(cn)
            if lv >= sc_lv and cn:
                subs = [r["name"] for r in self.db.list_char_options(category="subclass")
                        if (r.get("parent") or "").lower() == cn]
                if not subs:
                    subs = ["(custom)"]
                else:
                    subs = ["(none yet)"] + subs
                subclass_menu.configure(values=subs)
                if subclass_var.get() not in subs:
                    subclass_var.set(subs[0])
                subclass_hint.configure(text=f"Subclasses unlock at level {sc_lv} for {class_var.get()}.")
                subclass_lbl_w.pack(anchor="w", padx=14, pady=(10, 0))
                subclass_hint.pack(anchor="w", padx=14)
                subclass_menu.pack(anchor="w", padx=14, pady=(4, 10))
                subclass_row.pack(fill="x")
            else:
                if sc_lv > 1:
                    subclass_hint.configure(text=f"Subclass unlocks at level {sc_lv}.")
                subclass_row.pack_forget()

        def _pick_class(cn: str, opt: dict):
            class_var.set(cn)
            for nm, b in _class_btns.items():
                b.configure(fg_color=(ACCENT if nm == cn else "transparent"),
                            text_color=(TEXT if nm == cn else MUTED))
            class_title.configure(text=cn)
            import re
            body = opt.get("body_md", "") or ""
            plain = re.sub(r"\*+([^*]+)\*+", r"\1", body)
            plain = re.sub(r"#+\s*", "", plain)
            class_desc_lbl.configure(text=plain[:700] + ("…" if len(plain) > 700 else ""))
            cfg_frame.pack(fill="x", pady=(12, 0))
            _update_subclass_row()

        # Class list (from DB + fallback to CLASS_NAMES)
        db_classes = self.db.list_char_options(category="class")
        class_opts = db_classes if db_classes else [{"name": n, "body_md": ""} for n in lr.CLASS_NAMES]

        for opt in class_opts:
            nm = opt["name"]
            btn = ctk.CTkButton(
                class_listbox, text=nm, anchor="w", height=34,
                fg_color=(ACCENT if nm == class_var.get() else "transparent"),
                hover_color=SURFACE2, text_color=(TEXT if nm == class_var.get() else MUTED),
                font=ctk.CTkFont(size=13), corner_radius=4,
                command=lambda n=nm, o=opt: _pick_class(n, o))
            btn.pack(fill="x", padx=4, pady=1)
            _class_btns[nm] = btn

        # Level picker inside cfg_frame
        lvl_row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        lvl_row.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(lvl_row, text="Starting Level", text_color=ACCENT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkLabel(lvl_row, text="(1 for a brand-new character)", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=12)

        lvl_ctrl = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        lvl_ctrl.pack(anchor="w", padx=14, pady=(0, 4))
        lvl_display = ctk.CTkLabel(lvl_ctrl, text=str(level_var.get()), text_color=TEXT,
                                    font=ctk.CTkFont(size=22, weight="bold"), width=48)

        def _set_level(delta: int):
            nv = max(1, min(20, level_var.get() + delta))
            level_var.set(nv)
            lvl_display.configure(text=str(nv))
            _update_subclass_row()

        ctk.CTkButton(lvl_ctrl, text="−", width=36, height=36, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=16),
                      command=lambda: _set_level(-1)).pack(side="left", padx=(0, 6))
        lvl_display.pack(side="left", padx=4)
        ctk.CTkButton(lvl_ctrl, text="+", width=36, height=36, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=16),
                      command=lambda: _set_level(1)).pack(side="left", padx=(6, 0))

        subclass_row.pack_forget()

        # Restore if returning to step
        if class_var.get():
            for opt in class_opts:
                if opt["name"] == class_var.get():
                    _pick_class(opt["name"], opt)
                    break

        def collect():
            self._data["class_name"] = class_var.get()
            self._data["level"] = level_var.get()
            sc = subclass_var.get()
            self._data["subclass"] = "" if sc in ("—", "(none yet)", "(custom)") else sc

        self._collector = collect

    # ── Step 4: Ability Scores ────────────────────────────────────────────────

    def _step_scores(self):
        p = self._content
        _section_title(p, "Set Your Ability Scores")
        ctk.CTkLabel(p, text="Your six ability scores define your character's physical and mental "
                     "attributes. Choose a method below. Racial bonuses are previewed and applied automatically.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=620,
                     justify="left").pack(anchor="w", pady=(0, 16))

        method_var = tk.StringVar(value=self._data.get("score_method", "standard_array"))

        methods = [
            ("standard_array", "Standard Array", "★ Recommended for beginners",
             "You're dealt six pre-set scores — 15, 14, 13, 12, 10, and 8 — and assign each one "
             "to the ability that matters most for your character. No math required, just drag and drop "
             "your strengths where they belong. Fast, fair, and balanced for any class."),
            ("point_buy", "Point Buy", "Best for precise control",
             "You start every ability at 8 and spend a budget of 27 points to raise them. "
             "Raising a score from 8 to 9 costs 1 point; from 14 to 15 costs 2 points. "
             "No score can go above 15 before racial bonuses. Perfect if you want exactly the "
             "numbers your build needs without relying on dice luck."),
            ("manual", "Manual / Roll", "Bring your own dice",
             "Enter numbers your DM had you roll at the table, or click 🎲 Roll to simulate "
             "rolling 4 six-sided dice and dropping the lowest (the classic method). "
             "This can give high scores, low scores, or both — true to tabletop drama."),
        ]

        method_frame = ctk.CTkFrame(p, fg_color="transparent")
        method_frame.pack(fill="x", pady=(0, 16))

        scores_body = ctk.CTkFrame(p, fg_color="transparent")
        scores_body.pack(fill="x")

        def _pick_method(m):
            method_var.set(m)
            self._data["score_method"] = m
            for btn, mid in method_btns:
                is_sel = mid == m
                btn.configure(border_color=(ACCENT if is_sel else BORDER),
                              border_width=(2 if is_sel else 1))
            self._data["score_method"] = m
            _rebuild_body()

        method_btns = []
        for col, (mid, title, tag, desc) in enumerate(methods):
            card = ctk.CTkFrame(method_frame, fg_color=SURFACE, corner_radius=10,
                                border_width=2 if method_var.get() == mid else 1,
                                border_color=ACCENT if method_var.get() == mid else BORDER)
            card.grid(row=0, column=col, padx=6, sticky="nsew")
            method_frame.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(card, text=title, text_color=TEXT,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(12, 0))
            ctk.CTkLabel(card, text=tag, text_color=GOLD,
                         font=ctk.CTkFont(size=10)).pack(anchor="w", padx=12)
            ctk.CTkLabel(card, text=desc, text_color=MUTED, font=ctk.CTkFont(size=10),
                         wraplength=190, justify="left").pack(anchor="w", padx=12, pady=(4, 8))
            ctk.CTkButton(card, text="Use this method", height=30, fg_color=SURFACE2,
                          hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=11),
                          command=lambda m=mid: _pick_method(m)).pack(fill="x", padx=12, pady=(0, 12))
            method_btns.append((card, mid))

        # Score variable state (shared across method switches)
        score_vars: dict[str, tk.IntVar] = {
            a: tk.IntVar(value=self._data["scores"].get(a, 10)) for a, _ in _ABILITIES
        }
        # Standard Array: which value is assigned to each ability
        sa_vars: dict[str, tk.StringVar] = {
            a: tk.StringVar(value="—") for a, _ in _ABILITIES
        }

        # Initialise SA vars from current scores if they match the array
        cur = sorted([self._data["scores"].get(a, 10) for a, _ in _ABILITIES], reverse=True)
        if cur == sorted(wd.STANDARD_ARRAY, reverse=True):
            used: list[int] = []
            for a, _ in _ABILITIES:
                sv = self._data["scores"].get(a, 10)
                if sv in wd.STANDARD_ARRAY and sv not in used:
                    sa_vars[a].set(str(sv))
                    used.append(sv)

        def _rebuild_body():
            for w in scores_body.winfo_children():
                w.destroy()
            m = method_var.get()
            if m == "standard_array":
                _build_sa(scores_body)
            elif m == "point_buy":
                _build_pb(scores_body)
            else:
                _build_manual(scores_body)
            # Also update the collector to read from the current widgets
            _rebind_collector()

        def _sa_remaining() -> list[int]:
            assigned = []
            for a, _ in _ABILITIES:
                try:
                    v = int(sa_vars[a].get())
                    assigned.append(v)
                except (ValueError, tk.TclError):
                    pass
            rem = list(wd.STANDARD_ARRAY)
            for v in assigned:
                if v in rem:
                    rem.remove(v)
            return rem

        def _build_sa(parent):
            ctk.CTkLabel(parent, text="Assign each value to one ability (each can only be used once).",
                         text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 8))
            remaining_lbl = ctk.CTkLabel(parent, text="", text_color=GOLD,
                                          font=ctk.CTkFont(size=12, weight="bold"))
            remaining_lbl.pack(anchor="w", pady=(0, 8))

            menus: dict[str, ctk.CTkOptionMenu] = {}

            def _update_menus(*_):
                rem = _sa_remaining()
                rem_str = "  ".join(str(v) for v in sorted(rem, reverse=True))
                remaining_lbl.configure(
                    text=f"Unassigned: {rem_str}" if rem else "✓ All values assigned!")
                for a, _ in _ABILITIES:
                    cur_val = sa_vars[a].get()
                    try:
                        cv = int(cur_val)
                        available = [str(cv)] + [str(v) for v in sorted(rem, reverse=True)]
                    except (ValueError, tk.TclError):
                        available = ["—"] + [str(v) for v in sorted(rem, reverse=True)]
                    menus[a].configure(values=available)

            grid = ctk.CTkFrame(parent, fg_color="transparent")
            grid.pack(fill="x")
            for i, (a, label) in enumerate(_ABILITIES):
                row = ctk.CTkFrame(grid, fg_color=SURFACE, corner_radius=8)
                row.grid(row=i // 2, column=i % 2, padx=6, pady=4, sticky="ew")
                grid.grid_columnconfigure(i % 2, weight=1)
                ctk.CTkLabel(row, text=label, text_color=TEXT,
                             font=ctk.CTkFont(size=13, weight="bold"), width=44).pack(side="left", padx=12, pady=10)
                sa_vars[a].trace_add("write", _update_menus)
                menu = ctk.CTkOptionMenu(row, variable=sa_vars[a],
                                         values=["—"] + [str(v) for v in sorted(wd.STANDARD_ARRAY, reverse=True)],
                                         fg_color=SURFACE2, button_color=ACCENT,
                                         button_hover_color=ACCENT_H, text_color=TEXT,
                                         dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
                                         width=100)
                menu.pack(side="right", padx=12, pady=10)
                menus[a] = menu
            _update_menus()

        def _build_pb(parent):
            budget_lbl = ctk.CTkLabel(parent, text="", text_color=ACCENT,
                                       font=ctk.CTkFont(size=13, weight="bold"))
            budget_lbl.pack(anchor="w", pady=(0, 8))

            def _spent():
                return sum(wd.POINT_BUY_COST.get(score_vars[a].get(), 0) for a, _ in _ABILITIES)

            def _update_budget():
                s = _spent()
                rem = wd.POINT_BUY_BUDGET - s
                if rem < 0:
                    budget_lbl.configure(text=f"Points remaining: {rem} ⚠ overspent!", text_color=DANGER)
                elif rem == 0:
                    budget_lbl.configure(text="Points remaining: 0 ✓", text_color=GOOD)
                else:
                    budget_lbl.configure(text=f"Points remaining: {rem}", text_color=ACCENT)
                for a, _ in _ABILITIES:
                    _update_pb_row(a)

            pb_minus: dict[str, ctk.CTkButton] = {}
            pb_plus:  dict[str, ctk.CTkButton] = {}
            pb_lbl:   dict[str, ctk.CTkLabel]  = {}
            pb_cost:  dict[str, ctk.CTkLabel]  = {}

            def _update_pb_row(a):
                sv = score_vars[a].get()
                pb_lbl[a].configure(text=f"{sv}  (mod {_mod(sv):+})")
                cost = wd.POINT_BUY_COST.get(sv, 0)
                pb_cost[a].configure(text=f"cost: {cost}")
                pb_minus[a].configure(state="normal" if sv > wd.PB_MIN else "disabled")
                spent = _spent()
                pb_plus[a].configure(
                    state="normal" if sv < wd.PB_MAX
                          and wd.POINT_BUY_COST.get(sv + 1, 99) <= wd.POINT_BUY_BUDGET - spent + cost
                    else "disabled")

            def _pb_change(a, delta):
                nv = max(wd.PB_MIN, min(wd.PB_MAX, score_vars[a].get() + delta))
                score_vars[a].set(nv)
                _update_budget()

            grid = ctk.CTkFrame(parent, fg_color="transparent")
            grid.pack(fill="x")
            for i, (a, label) in enumerate(_ABILITIES):
                row = ctk.CTkFrame(grid, fg_color=SURFACE, corner_radius=8)
                row.grid(row=i // 2, column=i % 2, padx=6, pady=4, sticky="ew")
                grid.grid_columnconfigure(i % 2, weight=1)
                ctk.CTkLabel(row, text=label, text_color=TEXT,
                             font=ctk.CTkFont(size=13, weight="bold"), width=44).pack(side="left", padx=10)
                pb_minus[a] = ctk.CTkButton(row, text="−", width=30, height=30,
                                             fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT,
                                             font=ctk.CTkFont(size=14),
                                             command=lambda x=a: _pb_change(x, -1))
                pb_minus[a].pack(side="left", padx=4, pady=8)
                pb_lbl[a] = ctk.CTkLabel(row, text="", text_color=TEXT,
                                          font=ctk.CTkFont(size=13), width=100)
                pb_lbl[a].pack(side="left", padx=4)
                pb_plus[a] = ctk.CTkButton(row, text="+", width=30, height=30,
                                            fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT,
                                            font=ctk.CTkFont(size=14),
                                            command=lambda x=a: _pb_change(x, 1))
                pb_plus[a].pack(side="left", padx=4)
                pb_cost[a] = ctk.CTkLabel(row, text="", text_color=MUTED,
                                           font=ctk.CTkFont(size=10))
                pb_cost[a].pack(side="left", padx=8)
            _update_budget()

        def _build_manual(parent):
            ctk.CTkLabel(parent,
                         text="Enter your rolled scores, or click 🎲 to roll 4d6 and drop the lowest.",
                         text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 12))
            grid = ctk.CTkFrame(parent, fg_color="transparent")
            grid.pack(fill="x")
            entries: dict[str, ctk.CTkEntry] = {}
            for i, (a, label) in enumerate(_ABILITIES):
                row = ctk.CTkFrame(grid, fg_color=SURFACE, corner_radius=8)
                row.grid(row=i // 2, column=i % 2, padx=6, pady=4, sticky="ew")
                grid.grid_columnconfigure(i % 2, weight=1)
                ctk.CTkLabel(row, text=label, text_color=TEXT,
                             font=ctk.CTkFont(size=13, weight="bold"), width=44).pack(side="left", padx=10)
                ev = tk.StringVar(value=str(score_vars[a].get()))
                entry = ctk.CTkEntry(row, textvariable=ev, width=60, height=34,
                                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT,
                                     font=ctk.CTkFont(size=14), justify="center")
                entry.pack(side="left", padx=8, pady=8)
                entries[a] = entry

                def _sync_entry(a=a, ev=ev):
                    try:
                        score_vars[a].set(max(1, min(30, int(ev.get()))))
                    except ValueError:
                        pass
                ev.trace_add("write", lambda *_, a=a, ev=ev: _sync_entry(a, ev))

                def _roll(a=a, ev=ev):
                    dice = sorted([random.randint(1, 6) for _ in range(4)])
                    total = sum(dice[1:])
                    ev.set(str(total))
                    score_vars[a].set(total)

                ctk.CTkButton(row, text="🎲 Roll", width=72, height=30, fg_color=SURFACE2,
                              hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=11),
                              command=_roll).pack(side="left", padx=4)
                mod_lbl = ctk.CTkLabel(row, text=f"mod {_mod(score_vars[a].get()):+}",
                                        text_color=MUTED, font=ctk.CTkFont(size=11), width=60)
                mod_lbl.pack(side="left", padx=4)

                def _upd_mod(a=a, ml=mod_lbl):
                    ml.configure(text=f"mod {_mod(score_vars[a].get()):+}")
                score_vars[a].trace_add("write", lambda *_, a=a, ml=mod_lbl: _upd_mod(a, ml))

            ctk.CTkButton(parent, text="🎲  Roll All Six", width=140, height=34,
                          fg_color=ACCENT, hover_color=ACCENT_H, text_color=TEXT,
                          font=ctk.CTkFont(size=12),
                          command=lambda: [_do_roll(a, e) for a, e in
                                           [(a, entries[a]) for a, _ in _ABILITIES]]
                          ).pack(anchor="w", pady=(12, 0))

            def _do_roll(a, entry):
                dice = sorted([random.randint(1, 6) for _ in range(4)])
                total = sum(dice[1:])
                entry.delete(0, "end")
                entry.insert(0, str(total))
                score_vars[a].set(total)

        # Racial bonus preview (persistent below body)
        racial_frame = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=8, border_width=1,
                                     border_color=BORDER)
        racial_frame.pack(fill="x", pady=(12, 0))
        race = self._data.get("race", "")
        bonuses = wd.RACIAL_BONUSES.get(race, {})
        if bonuses:
            bstr = "  ".join(f"+{v} {k.upper()}" for k, v in bonuses.items())
            ctk.CTkLabel(racial_frame,
                         text=f"Racial bonuses from {race} ({bstr}) will be added to your final scores.",
                         text_color=GOLD, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=14, pady=10)
        else:
            ctk.CTkLabel(racial_frame,
                         text=f"Race selected: {race or 'none'}. Custom racial bonuses — adjust scores on the sheet.",
                         text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=14, pady=10)

        def _rebind_collector():
            def collect():
                m = method_var.get()
                self._data["score_method"] = m
                raw: dict[str, int] = {}
                if m == "standard_array":
                    for a, _ in _ABILITIES:
                        try:
                            raw[a] = int(sa_vars[a].get())
                        except (ValueError, tk.TclError):
                            raw[a] = 10
                else:
                    raw = {a: score_vars[a].get() for a, _ in _ABILITIES}
                bonuses = wd.RACIAL_BONUSES.get(self._data.get("race", ""), {})
                self._data["scores"] = {
                    a: min(30, raw.get(a, 10) + bonuses.get(a, 0)) for a, _ in _ABILITIES
                }
            self._collector = collect

        _rebuild_body()
        _rebind_collector()

    # ── Step 5: Background & Skills ───────────────────────────────────────────

    def _step_background(self):
        p = self._content
        _section_title(p, "Background & Skill Proficiencies")
        ctk.CTkLabel(p,
                     text="Your background tells the story of who you were before adventuring. "
                     "It grants skill proficiencies, languages, and tools. Below you'll also "
                     "choose your class skill proficiencies.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=620,
                     justify="left").pack(anchor="w", pady=(0, 16))

        outer = ctk.CTkFrame(p, fg_color="transparent")
        outer.pack(fill="x")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=2)

        bg_list_frame = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10)
        bg_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        bg_search = tk.StringVar()
        ctk.CTkEntry(bg_list_frame, textvariable=bg_search, placeholder_text="Search…",
                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT,
                     height=34).pack(fill="x", padx=10, pady=8)

        bg_scroll = ctk.CTkScrollableFrame(bg_list_frame, fg_color="transparent",
                                            scrollbar_button_color=ACCENT, height=340)
        bg_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        right = ctk.CTkFrame(outer, fg_color=SURFACE, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew")

        bg_title = ctk.CTkLabel(right, text="Select a background", text_color=MUTED,
                                 font=ctk.CTkFont(size=14, weight="bold"))
        bg_title.pack(anchor="w", padx=16, pady=(14, 4))
        bg_skills_lbl = ctk.CTkLabel(right, text="", text_color=GOLD,
                                      font=ctk.CTkFont(size=11))
        bg_skills_lbl.pack(anchor="w", padx=16)
        bg_tools_lbl = ctk.CTkLabel(right, text="", text_color=GOOD,
                                     font=ctk.CTkFont(size=11))
        bg_tools_lbl.pack(anchor="w", padx=16, pady=(2, 0))
        bg_lang_lbl = ctk.CTkLabel(right, text="", text_color=ACCENT,
                                    font=ctk.CTkFont(size=11))
        bg_lang_lbl.pack(anchor="w", padx=16, pady=(2, 8))

        bg_var = tk.StringVar(value=self._data.get("background", ""))
        bg_btns: dict[str, ctk.CTkButton] = {}

        def _pick_bg(nm: str):
            bg_var.set(nm)
            for n, b in bg_btns.items():
                b.configure(fg_color=(ACCENT if n == nm else "transparent"),
                            text_color=(TEXT if n == nm else MUTED))
            bg_title.configure(text=nm)
            skills = wd.BACKGROUND_SKILLS.get(nm, [])
            bg_skills_lbl.configure(
                text=("Skills: " + ", ".join(skills)) if skills else "Skills: (varies)")
            tools = wd.BACKGROUND_TOOLS.get(nm, [])
            bg_tools_lbl.configure(
                text=("Tools: " + ", ".join(tools)) if tools else "")
            langs = wd.BACKGROUND_LANGUAGES.get(nm, 0)
            bg_lang_lbl.configure(
                text=(f"Languages: +{langs} of your choice") if langs else "")

        def _rebuild_bg(*_):
            q = bg_search.get().strip().lower()
            for w in bg_scroll.winfo_children():
                w.destroy()
            bg_btns.clear()
            shown = [r for r in self._backgrounds
                     if not q or q in (r.get("name") or "").lower()]
            for opt in shown:
                nm = opt["name"]
                btn = ctk.CTkButton(
                    bg_scroll, text=nm, anchor="w", height=30,
                    fg_color=(ACCENT if nm == bg_var.get() else "transparent"),
                    hover_color=SURFACE2, text_color=(TEXT if nm == bg_var.get() else MUTED),
                    font=ctk.CTkFont(size=12), corner_radius=4,
                    command=lambda n=nm: _pick_bg(n))
                btn.pack(fill="x", padx=4, pady=1)
                bg_btns[nm] = btn

        bg_search.trace_add("write", _rebuild_bg)
        _rebuild_bg()
        if bg_var.get():
            _pick_bg(bg_var.get())

        # Class skill picker
        ctk.CTkLabel(p, text="Class Skill Proficiencies", text_color=ACCENT,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(20, 4))

        cn = self._data.get("class_name", "").lower()
        spec = wd.CLASS_SKILL_CHOICES.get(cn, {"count": 0, "from": []})
        count = spec["count"]
        allowed = spec["from"]

        ctk.CTkLabel(p, text=f"Choose {count} skill(s) from the list below "
                     f"(from your {self._data.get('class_name', 'class')} class).",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 8))

        skill_vars: dict[str, tk.BooleanVar] = {}
        selected_cls = set(self._data.get("class_skills", []))

        skill_grid = ctk.CTkFrame(p, fg_color="transparent")
        skill_grid.pack(fill="x")

        skill_count_lbl = ctk.CTkLabel(p, text=f"Selected: 0 / {count}",
                                        text_color=MUTED, font=ctk.CTkFont(size=11))
        skill_count_lbl.pack(anchor="w", pady=(4, 0))

        def _update_count():
            sel = sum(1 for v in skill_vars.values() if v.get())
            skill_count_lbl.configure(
                text=f"Selected: {sel} / {count}",
                text_color=GOOD if sel == count else (DANGER if sel > count else MUTED))

        for i, skill in enumerate(allowed):
            var = tk.BooleanVar(value=skill in selected_cls)
            skill_vars[skill] = var

            def _on_toggle(s=skill, v=var):
                sel = sum(1 for x in skill_vars.values() if x.get())
                if v.get() and sel > count:
                    v.set(False)
                _update_count()

            cb = ctk.CTkCheckBox(skill_grid, text=skill, variable=var,
                                  text_color=TEXT, fg_color=ACCENT,
                                  hover_color=ACCENT_H, border_color=BORDER,
                                  font=ctk.CTkFont(size=12), command=_on_toggle)
            cb.grid(row=i // 3, column=i % 3, padx=8, pady=3, sticky="w")
            skill_grid.grid_columnconfigure(i % 3, weight=1)

        _update_count()

        def collect():
            self._data["background"] = bg_var.get()
            self._data["class_skills"] = [s for s, v in skill_vars.items() if v.get()]
            # Background-granted skills stored separately
            bg = bg_var.get()
            self._data["background_skills"] = wd.BACKGROUND_SKILLS.get(bg, [])

        self._collector = collect

    # ── Step 6: Equipment ────────────────────────────────────────────────────

    def _step_equipment(self):
        p = self._content
        cn = self._data.get("class_name", "").lower()
        _section_title(p, "Starting Equipment")
        ctk.CTkLabel(p,
                     text="Choose a starting equipment package or take gold instead and "
                     "buy your own gear at the start of the campaign.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=600,
                     justify="left").pack(anchor="w", pady=(0, 16))

        packages = wd.STARTING_EQUIPMENT.get(cn, {})
        gold = wd.STARTING_GOLD.get(cn, 100)
        choice_var = tk.StringVar(value=self._data.get("equipment_choice", "A"))

        def _pick(val):
            choice_var.set(val)
            for v, card in cards.items():
                sel = v == val
                card.configure(border_color=(ACCENT if sel else BORDER),
                               border_width=(2 if sel else 1))

        cards: dict[str, ctk.CTkFrame] = {}

        for pkg, items in packages.items():
            card = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=10, border_width=1,
                                border_color=BORDER)
            card.pack(fill="x", pady=6)
            cards[pkg] = card
            ctk.CTkButton(card, text=f"Package {pkg}", height=34, anchor="w",
                          fg_color=SURFACE2, hover_color=ACCENT_H, text_color=TEXT,
                          font=ctk.CTkFont(size=13, weight="bold"),
                          command=lambda v=pkg: _pick(v)).pack(anchor="w", padx=14, pady=(12, 4))
            for item in items:
                ctk.CTkLabel(card, text=f"  •  {item}", text_color=MUTED,
                             font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", padx=24, pady=1)
            ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

        # Gold option
        gold_card = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=10, border_width=1,
                                  border_color=BORDER)
        gold_card.pack(fill="x", pady=6)
        cards["gold"] = gold_card
        ctk.CTkButton(gold_card, text="Take Starting Gold Instead", height=34, anchor="w",
                      fg_color=SURFACE2, hover_color=ACCENT_H, text_color=TEXT,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: _pick("gold")).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(gold_card, text=f"  •  {gold} gp to spend at a shop before your first adventure.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", padx=24, pady=(1, 12))

        # Restore selection
        _pick(choice_var.get() if choice_var.get() in cards else ("A" if "A" in cards else "gold"))

        def collect():
            self._data["equipment_choice"] = choice_var.get()

        self._collector = collect

    # ── Step 7: Spells (conditional) ─────────────────────────────────────────

    def _step_spells(self):
        p = self._content
        cn = self._data.get("class_name", "").lower()
        level = self._data.get("level", 1)
        _section_title(p, "Spells")

        need_c = wd.cantrips_known(cn, level)
        is_prep = wd.is_preparing_caster(cn)
        need_s = 0 if is_prep else wd.spells_known_count(cn, level)
        max_sl = wd.max_spell_level_for_class(cn, level)

        ctk.CTkLabel(p, text=f"As a level {level} {self._data.get('class_name', 'spellcaster')}, "
                     f"you get {need_c} cantrip(s)" +
                     (f" and prepare spells from your full list each day." if is_prep else
                      f" and know {need_s} spell(s) up to level {max_sl}." if need_s > 0 else "."),
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=600,
                     justify="left").pack(anchor="w", pady=(0, 12))

        if is_prep:
            card = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=10, border_width=1,
                                border_color=BORDER)
            card.pack(fill="x", pady=8)
            ctk.CTkLabel(card, text="You prepare spells fresh each day from your class spell list.",
                         text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(
                             anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(card, text="After the wizard creates your character, head to the Spellbook "
                         "tab to prepare your spells for the session. You'll always have access to your "
                         "full list — no need to pre-select them here.",
                         text_color=MUTED, font=ctk.CTkFont(size=11), wraplength=540,
                         justify="left").pack(anchor="w", padx=16, pady=(0, 14))

        # Spell lists from DB
        all_class_spells = self.db.list_spells(cls=self._data.get("class_name", ""))
        cantrips = [s for s in all_class_spells if s["level"] == 0]
        leveled = [s for s in all_class_spells if 1 <= s["level"] <= max(1, max_sl)]

        chosen_c = set(self._data.get("cantrips_chosen", []))
        chosen_s = set(self._data.get("spells_chosen", []))

        c_count_lbl = ctk.CTkLabel(p, text="", text_color=MUTED, font=ctk.CTkFont(size=11))
        s_count_lbl = ctk.CTkLabel(p, text="", text_color=MUTED, font=ctk.CTkFont(size=11))
        cantrip_vars: dict[str, tk.BooleanVar] = {}
        spell_vars:   dict[str, tk.BooleanVar] = {}

        def _upd_counts():
            cc = sum(1 for v in cantrip_vars.values() if v.get())
            c_count_lbl.configure(
                text=f"Cantrips: {cc} / {need_c}",
                text_color=GOOD if cc == need_c else MUTED)
            sc = sum(1 for v in spell_vars.values() if v.get())
            s_count_lbl.configure(
                text=f"Spells known: {sc} / {need_s}",
                text_color=GOOD if sc == need_s else MUTED)

        def _guard(d: dict[str, tk.BooleanVar], cap: int, v: tk.BooleanVar):
            sel = sum(1 for x in d.values() if x.get())
            if v.get() and sel > cap:
                v.set(False)
            _upd_counts()

        if cantrips and need_c > 0:
            ctk.CTkLabel(p, text="Cantrips", text_color=ACCENT,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(12, 4))
            c_count_lbl.pack(anchor="w", pady=(0, 6))
            cg = ctk.CTkFrame(p, fg_color="transparent")
            cg.pack(fill="x")
            for i, sp in enumerate(cantrips):
                nm = sp["name"]
                var = tk.BooleanVar(value=nm in chosen_c)
                cantrip_vars[nm] = var
                cb = ctk.CTkCheckBox(cg, text=nm, variable=var,
                                     text_color=TEXT, fg_color=ACCENT, hover_color=ACCENT_H,
                                     border_color=BORDER, font=ctk.CTkFont(size=12),
                                     command=lambda v=var: _guard(cantrip_vars, need_c, v))
                cb.grid(row=i // 3, column=i % 3, padx=8, pady=3, sticky="w")
                cg.grid_columnconfigure(i % 3, weight=1)

        if leveled and need_s > 0 and not is_prep:
            ctk.CTkLabel(p, text="Spells Known", text_color=ACCENT,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(16, 4))
            s_count_lbl.pack(anchor="w", pady=(0, 6))
            sg = ctk.CTkFrame(p, fg_color="transparent")
            sg.pack(fill="x")
            # Group by level
            by_level: dict[int, list] = {}
            for sp in leveled:
                by_level.setdefault(sp["level"], []).append(sp)
            r = 0
            for sl in sorted(by_level):
                ctk.CTkLabel(sg, text=f"Level {sl}",
                             text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).grid(
                                 row=r, column=0, columnspan=3, sticky="w", padx=8, pady=(8, 2))
                r += 1
                for sp in by_level[sl]:
                    nm = sp["name"]
                    var = tk.BooleanVar(value=nm in chosen_s)
                    spell_vars[nm] = var
                    cb = ctk.CTkCheckBox(sg, text=nm, variable=var,
                                         text_color=TEXT, fg_color=ACCENT, hover_color=ACCENT_H,
                                         border_color=BORDER, font=ctk.CTkFont(size=12),
                                         command=lambda v=var: _guard(spell_vars, need_s, v))
                    col = (r - 1) % 3  # won't work right, let's keep 3-col layout
                cb_idx = 0
                for sp in by_level[sl]:
                    nm = sp["name"]
                    sg.grid_columnconfigure(cb_idx % 3, weight=1)
                    cb_idx += 1
                    r_local = r + (cb_idx - 1) // 3
                    col = (cb_idx - 1) % 3
                    ctk.CTkCheckBox(sg, text=nm, variable=spell_vars.get(nm, tk.BooleanVar()),
                                    text_color=TEXT, fg_color=ACCENT, hover_color=ACCENT_H,
                                    border_color=BORDER, font=ctk.CTkFont(size=12),
                                    command=lambda v=spell_vars.get(nm): _guard(spell_vars, need_s, v)
                                    if v else None).grid(row=r_local, column=col,
                                                         padx=8, pady=2, sticky="w")
                r += (len(by_level[sl]) + 2) // 3

        _upd_counts()

        def collect():
            self._data["cantrips_chosen"] = [nm for nm, v in cantrip_vars.items() if v.get()]
            self._data["spells_chosen"] = [nm for nm, v in spell_vars.items() if v.get()]

        self._collector = collect

    # ── Step 8: Review ────────────────────────────────────────────────────────

    def _step_review(self):
        p = self._content
        _section_title(p, "Review Your Character")
        ctk.CTkLabel(p, text="Everything looks good? Click 'Create Character' to bring them to life.",
                     text_color=MUTED, font=ctk.CTkFont(size=12), wraplength=600,
                     justify="left").pack(anchor="w", pady=(0, 16))

        d = self._data
        cn = d.get("class_name", "").lower()
        level = d.get("level", 1)
        hd = lr.hit_die(cn)
        con_mod = (d["scores"]["con"] - 10) // 2
        hp = hd + con_mod  # level 1: max die + CON
        if level > 1:
            hp += sum(lr.hp_gain(cn, con_mod) for _ in range(level - 1))
        hp = max(level, hp)

        sections = [
            ("Identity", [
                ("Name", d.get("name", "")),
                ("Player", d.get("player_name", "") or "—"),
                ("Alignment", d.get("alignment", "")),
                ("XP Tracking", d.get("xp_tracking", "milestone").title()),
            ]),
            ("Race & Class", [
                ("Race", (d.get("race", "") + (f" ({d['subrace']})" if d.get("subrace") else ""))),
                ("Class", d.get("class_name", "")),
                ("Level", str(level)),
                ("Subclass", d.get("subclass", "") or "—"),
                ("Hit Points", f"{hp} (1×d{hd} max + {level-1}×avg" +
                 (f" + {con_mod * level:+} CON)" if con_mod else ")")),
            ]),
            ("Ability Scores", [
                (f"{label}  ({d['scores'].get(a, 10):>2}  {_mod(d['scores'].get(a,10)):+})", "")
                for a, label in _ABILITIES
            ]),
            ("Proficiencies", [
                ("Background", d.get("background", "")),
                ("Class skills", ", ".join(d.get("class_skills", [])) or "—"),
                ("BG skills", ", ".join(d.get("background_skills", [])) or "—"),
            ]),
            ("Equipment", [
                ("Choice", ("Package " + d.get("equipment_choice") if d.get("equipment_choice") != "gold"
                            else f"Starting gold ({wd.STARTING_GOLD.get(cn, 100)} gp)")),
            ]),
        ]
        if d.get("cantrips_chosen") or d.get("spells_chosen"):
            sections.append(("Spells", [
                ("Cantrips", ", ".join(d.get("cantrips_chosen", [])) or "—"),
                ("Spells known", ", ".join(d.get("spells_chosen", [])) or "—"),
            ]))

        for sec_title, rows in sections:
            sec = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=10, border_width=1,
                               border_color=BORDER)
            sec.pack(fill="x", pady=6)
            ctk.CTkLabel(sec, text=sec_title, text_color=ACCENT,
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=14, pady=(10, 4))
            for label, val in rows:
                row = ctk.CTkFrame(sec, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=2)
                ctk.CTkLabel(row, text=label, text_color=MUTED,
                             font=ctk.CTkFont(size=12), width=200, anchor="w").pack(side="left")
                if val:
                    ctk.CTkLabel(row, text=val, text_color=TEXT,
                                 font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=8)
            ctk.CTkFrame(sec, fg_color="transparent", height=6).pack()

        self._collector = None  # Review step has nothing to collect

    # ── Character creation ────────────────────────────────────────────────────

    def _create_character(self):
        d = self._data
        cn = d.get("class_name", "").lower()
        level = d.get("level", 1)
        sc = d["scores"]
        con_mod = (sc["con"] - 10) // 2

        # HP calculation
        hd = lr.hit_die(cn)
        hp = hd + con_mod  # level 1: max
        if level > 1:
            hp += sum(lr.hp_gain(cn, con_mod) for _ in range(level - 1))
        hp = max(level, hp)

        xp = d.get("xp", 0) if d.get("xp_tracking") == "xp" else 0

        # 1 — Create character row
        cid = self.db.create_character({
            "name": d["name"],
            "player_name": d.get("player_name", ""),
            "alignment": d.get("alignment", ""),
            "race": d.get("race", ""),
            "subrace": d.get("subrace", ""),
            "background": d.get("background", ""),
            "xp": xp,
            "str": sc["str"], "dex": sc["dex"], "con": sc["con"],
            "int": sc["int"], "wis": sc["wis"], "cha": sc["cha"],
            "hp_max": hp, "hp_current": hp,
            "ac": 10 + (sc["dex"] - 10) // 2,  # naked AC
            "speed": 30,
        })

        # 2 — Class
        self.db.create_character_class(cid, {
            "class": d.get("class_name", ""),
            "subclass": d.get("subclass", ""),
            "level": level,
        })

        # 3 — Saving throw proficiencies
        for ab in wd.CLASS_SAVING_THROWS.get(cn, []):
            self.db.create_character_save(cid, {"ability": ab.upper(), "proficient": 1})

        # 4 — Skill proficiencies (class + background)
        all_skills = list(dict.fromkeys(d.get("class_skills", []) + d.get("background_skills", [])))
        for sk in all_skills:
            self.db.create_character_skill(cid, {"skill": sk, "proficiency": "proficient"})

        # 5 — Other proficiencies (armor, weapons, tools, languages)
        for nm in wd.CLASS_ARMOR_PROFS.get(cn, []):
            self.db.create_character_proficiency(cid, {"kind": "armor", "name": nm})
        for nm in wd.CLASS_WEAPON_PROFS.get(cn, []):
            self.db.create_character_proficiency(cid, {"kind": "weapon", "name": nm})
        for nm in wd.CLASS_TOOL_PROFS.get(cn, []):
            self.db.create_character_proficiency(cid, {"kind": "tool", "name": nm})
        for nm in wd.BACKGROUND_TOOLS.get(d.get("background", ""), []):
            self.db.create_character_proficiency(cid, {"kind": "tool", "name": nm})
        # Default languages
        self.db.create_character_proficiency(cid, {"kind": "language", "name": "Common"})
        lang_count = wd.BACKGROUND_LANGUAGES.get(d.get("background", ""), 0)
        if lang_count:
            self.db.create_character_proficiency(
                cid, {"kind": "language", "name": f"+{lang_count} language(s) of your choice"})

        # 6 — Equipment
        eq_choice = d.get("equipment_choice", "")
        if eq_choice == "gold":
            gold = wd.STARTING_GOLD.get(cn, 100)
            self.db.create_character_inventory(cid, {"item_name": f"Starting Gold ({gold} gp)", "quantity": 1})
        else:
            items = wd.STARTING_EQUIPMENT.get(cn, {}).get(eq_choice, [])
            for item_str in items:
                nm = item_str.rstrip(" ×1234567890").strip()
                qty = 1
                if "×" in item_str:
                    try:
                        qty = int(item_str.rsplit("×", 1)[-1])
                        nm = item_str.rsplit("×", 1)[0].strip()
                    except ValueError:
                        pass
                self.db.create_character_inventory(cid, {"item_name": nm, "quantity": qty})

        # 7 — Spells
        for nm in d.get("cantrips_chosen", []):
            ref_id = self.db._lookup_ref_id("spells", nm)
            self.db.create_character_spell(cid, {
                "spell_name": nm, "spell_ref_id": ref_id,
                "known": 1, "prepared": 0})
        for nm in d.get("spells_chosen", []):
            ref_id = self.db._lookup_ref_id("spells", nm)
            self.db.create_character_spell(cid, {
                "spell_name": nm, "spell_ref_id": ref_id,
                "known": 1, "prepared": 1 if wd.is_preparing_caster(cn) else 0})

        # 8 — Spell slots (multiclass table at starting level)
        if wd.is_spellcaster(cn):
            class_list = [{"class": d.get("class_name", ""), "subclass": d.get("subclass", ""), "level": level}]
            cl = sr.caster_level(class_list)
            if cl > 0:
                slots = sr.MULTICLASS_SLOTS.get(cl, [0] * 9)
                for i, slot_count in enumerate(slots):
                    if slot_count > 0:
                        self.db.create_character_spell_slot(cid, {"level": i + 1, "used": 0})
            # Warlock pact slots
            pact = sr.pact_magic(class_list)
            if pact:
                self.db.create_character_spell_slot(cid, {"level": pact["level"], "used": 0})

        # 9 — Features from reference compendium
        for cat, source_type in [
            ("race", "Race"), ("class", "Class"),
            ("subclass", "Subclass"), ("background", "Background"),
        ]:
            if cat == "race":
                name_to_look = d.get("race", "")
            elif cat == "subclass":
                name_to_look = d.get("subclass", "")
            elif cat == "background":
                name_to_look = d.get("background", "")
            else:
                name_to_look = d.get("class_name", "")
            opt = ref.find_option(self.db, cat, name_to_look)
            if opt:
                self.db.create_character_feature(cid, ref.feature_from_option(opt, source_type))

        # Done — set as active character and navigate home
        if self.app:
            self.app.active_character_id = cid
        self._go_home()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mod(score: int) -> int:
    return (int(score) - 10) // 2


def _section_title(parent, text: str):
    ctk.CTkLabel(parent, text=text, text_color=TEXT,
                 font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(4, 4))
