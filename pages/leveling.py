"""Level-Up tab — level an existing class or add a new one (multiclass), with
the standard 5e choices: subclass at the right level, ASI-or-Feat at ASI
levels, HP (roll or average), and auto-pulled class/subclass features. Slots,
prepared counts, and proficiency bonus are all derived, so they update on their
own once the class level changes.

`level_up()` is callable headless (the dialog just gathers the same args), and
`level_down()` makes a level-up practically reversible.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from db import Database
from pages import levelup_rules as lr
from pages import reference_lookup as ref

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
ABILITIES = [("str", "STR"), ("dex", "DEX"), ("con", "CON"),
             ("int", "INT"), ("wis", "WIS"), ("cha", "CHA")]


class LevelUpPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=ACCENT)
        self._scroll.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        for w in self._scroll.winfo_children():
            w.destroy()
        if not self._char:
            ctk.CTkLabel(self._scroll, text="No character selected — create or select one "
                         "on the Character Sheet tab.", text_color=MUTED,
                         font=ctk.CTkFont(size=13)).pack(pady=40)
            return
        self._render()

    # ── helpers (also used by tests) ──────────────────────────────────────────
    def _abilities(self):
        return {k: self._char[k] for k in ("str", "dex", "con", "int", "wis", "cha")}

    def check_multiclass(self, class_name) -> tuple[bool, str]:
        return lr.prereq_met(class_name, self._abilities())

    def _class_row(self, class_name):
        for c in self.db.list_character_classes(self._cid):
            if (c.get("class") or "").strip().lower() == class_name.strip().lower():
                return c
        return None

    def _add_feature_once(self, kind, opt):
        if not opt:
            return
        nm = (opt.get("name") or "").lower()
        for f in self.db.list_character_features(self._cid):
            if (f.get("name") or "").lower() == nm and \
               (f.get("source_type") or f.get("source_name") or "").lower() == kind.lower():
                return
        self.db.create_character_feature(self._cid, ref.feature_from_option(opt, kind))

    # ── the engine ────────────────────────────────────────────────────────────
    def level_up(self, class_name, *, subclass=None, hp_method="average",
                 hp_roll=None, asi=None, feat=None) -> dict:
        """Apply one level of `class_name`. Persists every step. Returns a summary."""
        self._char = self.db.get_character(self._cid)
        row = self._class_row(class_name)
        if row:
            new_level = int(row["level"]) + 1
            self.db.update_character_class(row["id"], {"level": new_level})
            row_id = row["id"]
            cur_subclass = row.get("subclass") or ""
        else:
            new_level = 1
            row_id = self.db.create_character_class(
                self._cid, {"class": class_name, "subclass": subclass or "", "level": 1})
            cur_subclass = subclass or ""
            subclass = None  # consumed at creation

        if subclass:
            self.db.update_character_class(row_id, {"subclass": subclass})
            cur_subclass = subclass

        # Pull class + subclass features from the compendium (deduped).
        self._add_feature_once("Class", ref.find_option(self.db, "class", class_name))
        if cur_subclass:
            self._add_feature_once(
                "Subclass", ref.find_option(self.db, "subclass", cur_subclass, parent=class_name))

        # Ability Score Improvement.
        if asi:
            ch = self.db.get_character(self._cid)
            for ab, amt in asi.items():
                ch[ab] = min(20, int(ch.get(ab, 10)) + int(amt))
            self.db.update_character(self._cid, ch)

        # Feat.
        if feat:
            fopt = ref.find_option(self.db, "feat", feat)
            self.db.create_character_feature(self._cid, {
                "source_type": "Feat", "source_name": "Feat", "name": feat,
                "description": (fopt.get("body_md", "") if fopt else "")})

        # Hit points.
        ch = self.db.get_character(self._cid)
        con_mod = Database.ability_mod(ch.get("con", 10))
        gain = lr.hp_gain(class_name, con_mod, hp_method, hp_roll)
        ch["hp_max"] = int(ch.get("hp_max", 0)) + gain
        ch["hp_current"] = min(ch["hp_max"], int(ch.get("hp_current", 0)) + gain)
        self.db.update_character(self._cid, ch)

        self._char = self.db.get_character(self._cid)
        return {"class": class_name, "level": new_level, "hp_gain": gain,
                "subclass": cur_subclass, "total_level": self._char["total_level"],
                "proficiency_bonus": self._char["proficiency_bonus"]}

    def level_down(self, class_name) -> bool:
        """Remove one level of `class_name` (delete the class if it hits 0).
        Approximately reverses the HP gain. Returns True if something changed."""
        row = self._class_row(class_name)
        if not row:
            return False
        lvl = int(row["level"])
        if lvl <= 1:
            self.db.delete_character_class(row["id"])
        else:
            self.db.update_character_class(row["id"], {"level": lvl - 1})
        ch = self.db.get_character(self._cid)
        dec = max(1, lr.avg_hp(class_name) + Database.ability_mod(ch.get("con", 10)))
        ch["hp_max"] = max(1, int(ch.get("hp_max", 1)) - dec)
        ch["hp_current"] = min(ch["hp_max"], int(ch.get("hp_current", 0)))
        self.db.update_character(self._cid, ch)
        self._char = self.db.get_character(self._cid)
        return True

    # ── render ────────────────────────────────────────────────────────────────
    def _render(self):
        c = self._char
        head = ctk.CTkFrame(self._scroll, fg_color=SURFACE, corner_radius=8)
        head.pack(fill="x", padx=4, pady=(2, 8))
        ctk.CTkLabel(head, text=c["name"], text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(head, text=f"Total Level {c['total_level']}   ·   "
                     f"Proficiency +{c['proficiency_bonus']}   ·   "
                     f"HP {c['hp_current']}/{c['hp_max']}",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(side="right", padx=14)

        ctk.CTkLabel(self._scroll, text="Current Classes", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=4, pady=(8, 2))
        classes = self.db.list_character_classes(self._cid)
        if not classes:
            ctk.CTkLabel(self._scroll, text="No classes yet — add one below.", text_color=MUTED,
                         font=ctk.CTkFont(size=12)).pack(anchor="w", padx=8, pady=2)
        for cls in classes:
            self._class_row_widget(cls)

        # Add multiclass
        ctk.CTkLabel(self._scroll, text="Add a Class (multiclass)", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=4, pady=(16, 2))
        add = ctk.CTkFrame(self._scroll, fg_color=SURFACE2, corner_radius=8)
        add.pack(fill="x", padx=4, pady=2)
        self._new_class_var = tk.StringVar(value=lr.CLASS_NAMES[0])
        ctk.CTkOptionMenu(add, variable=self._new_class_var, values=lr.CLASS_NAMES,
                          fg_color=SURFACE, button_color=ACCENT, button_hover_color=ACCENT_H,
                          text_color=TEXT, width=160).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(add, text="Add Class", width=100, height=30, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT,
                      command=self._add_class_clicked).pack(side="left", padx=4)
        self._mc_note = ctk.CTkLabel(add, text="", text_color=MUTED, font=ctk.CTkFont(size=11))
        self._mc_note.pack(side="left", padx=10)

    def _class_row_widget(self, cls):
        row = ctk.CTkFrame(self._scroll, fg_color=SURFACE2, corner_radius=8)
        row.pack(fill="x", padx=4, pady=2)
        label = cls["class"] + (f" ({cls['subclass']})" if cls.get("subclass") else "")
        ctk.CTkLabel(row, text=label, text_color=TEXT,
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
                     ).pack(side="left", padx=12, fill="x", expand=True, pady=10)
        ctk.CTkLabel(row, text=f"Level {cls['level']}", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=8)
        ctk.CTkButton(row, text="Level Up", width=90, height=30, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT,
                      command=lambda c=cls: self._level_dialog(c["class"], is_new=False)
                      ).pack(side="right", padx=(4, 10))
        ctk.CTkButton(row, text="▼", width=34, height=30, fg_color=SURFACE,
                      hover_color=DANGER, text_color=MUTED,
                      command=lambda c=cls: self._level_down_clicked(c["class"])
                      ).pack(side="right", padx=2)

    # ── UI actions ────────────────────────────────────────────────────────────
    def _level_down_clicked(self, class_name):
        if messagebox.askyesno("Level Down",
                               f"Remove one level of {class_name}? (approx. reverses HP)"):
            self.level_down(class_name)
            self.refresh()

    def _add_class_clicked(self):
        class_name = self._new_class_var.get()
        ok, desc = self.check_multiclass(class_name)
        if not ok:
            if not messagebox.askyesno(
                    "Multiclass prerequisite",
                    f"You don't meet the prerequisite for {class_name} ({desc}).\n\n"
                    f"Add the class anyway?"):
                return
        self._level_dialog(class_name, is_new=True)

    # ── leveling dialog ───────────────────────────────────────────────────────
    def _level_dialog(self, class_name, is_new):
        row = self._class_row(class_name)
        new_level = 1 if (is_new and not row) else int(row["level"]) + 1
        has_subclass = bool(row and row.get("subclass"))

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"{'Add' if is_new else 'Level Up'} — {class_name}")
        dlg.geometry("420x560")
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=f"{class_name} → Level {new_level}", text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(14, 6))

        # HP
        ctk.CTkLabel(dlg, text=f"Hit Points (d{lr.hit_die(class_name)}, "
                     f"average {lr.avg_hp(class_name)})", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(6, 0))
        hp_method = tk.StringVar(value="average")
        roll_var = tk.StringVar()
        hpf = ctk.CTkFrame(dlg, fg_color="transparent")
        hpf.pack(fill="x", padx=16)
        ctk.CTkRadioButton(hpf, text="Average", variable=hp_method, value="average",
                           text_color=TEXT, fg_color=ACCENT).pack(side="left")
        ctk.CTkRadioButton(hpf, text="Roll:", variable=hp_method, value="roll",
                           text_color=TEXT, fg_color=ACCENT).pack(side="left", padx=(12, 2))
        ctk.CTkEntry(hpf, textvariable=roll_var, width=56, height=26, fg_color=SURFACE2,
                     border_color=BORDER, text_color=TEXT).pack(side="left")

        # Subclass
        sub_var = tk.StringVar(value="")
        if lr.needs_subclass(class_name, new_level, has_subclass):
            subs = sorted({r["name"] for r in self.db.list_char_options(category="subclass")
                           if (r.get("parent") or "").strip().lower() == class_name.lower()})
            if subs:
                ctk.CTkLabel(dlg, text="Choose Subclass", text_color=MUTED,
                             font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
                sub_var.set(subs[0])
                ctk.CTkComboBox(dlg, variable=sub_var, values=subs, fg_color=SURFACE2,
                                border_color=BORDER, button_color=ACCENT, text_color=TEXT,
                                dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT
                                ).pack(fill="x", padx=16)

        # ASI / Feat
        asi_mode = tk.StringVar(value="asi")
        a1 = tk.StringVar(value="str"); a2 = tk.StringVar(value="con")
        asi_amt = tk.StringVar(value="+1 / +1")
        feat_var = tk.StringVar(value="")
        if lr.is_asi_level(class_name, new_level):
            ctk.CTkLabel(dlg, text="Ability Score Improvement or Feat", text_color=MUTED,
                         font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
            ctk.CTkRadioButton(dlg, text="Ability Score Improvement", variable=asi_mode,
                               value="asi", text_color=TEXT, fg_color=ACCENT).pack(anchor="w", padx=16)
            af = ctk.CTkFrame(dlg, fg_color="transparent")
            af.pack(fill="x", padx=28)
            ctk.CTkOptionMenu(af, variable=asi_amt, values=["+1 / +1", "+2 to one"],
                              width=110, fg_color=SURFACE2, button_color=ACCENT,
                              text_color=TEXT).pack(side="left", padx=(0, 6))
            ctk.CTkOptionMenu(af, variable=a1, values=[a for a, _ in ABILITIES], width=70,
                              fg_color=SURFACE2, button_color=ACCENT, text_color=TEXT).pack(side="left")
            ctk.CTkOptionMenu(af, variable=a2, values=[a for a, _ in ABILITIES], width=70,
                              fg_color=SURFACE2, button_color=ACCENT, text_color=TEXT).pack(side="left", padx=4)
            ctk.CTkRadioButton(dlg, text="Take a Feat", variable=asi_mode, value="feat",
                               text_color=TEXT, fg_color=ACCENT).pack(anchor="w", padx=16, pady=(6, 0))
            feats = sorted({r["name"] for r in self.db.list_char_options(category="feat")})
            feat_var.set(feats[0] if feats else "")
            ctk.CTkComboBox(dlg, variable=feat_var, values=feats, fg_color=SURFACE2,
                            border_color=BORDER, button_color=ACCENT, text_color=TEXT,
                            dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT).pack(fill="x", padx=16, pady=(0, 4))

        def apply():
            kwargs = {"hp_method": hp_method.get()}
            if hp_method.get() == "roll":
                try:
                    kwargs["hp_roll"] = int(roll_var.get())
                except ValueError:
                    messagebox.showerror("HP", "Enter a number to roll."); return
            if sub_var.get():
                kwargs["subclass"] = sub_var.get()
            if lr.is_asi_level(class_name, new_level):
                if asi_mode.get() == "asi":
                    if asi_amt.get() == "+2 to one":
                        kwargs["asi"] = {a1.get(): 2}
                    else:
                        d = {}
                        d[a1.get()] = d.get(a1.get(), 0) + 1
                        d[a2.get()] = d.get(a2.get(), 0) + 1
                        kwargs["asi"] = d
                elif feat_var.get():
                    kwargs["feat"] = feat_var.get()
            self.level_up(class_name, **kwargs)
            dlg.destroy()
            self.refresh()

        ctk.CTkButton(dlg, text=f"Apply — Level {new_level}", fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, height=36,
                      command=apply).pack(side="bottom", fill="x", padx=16, pady=14)
