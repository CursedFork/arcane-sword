"""Actions tab for the active character (derived, read-mostly).

- Attacks: one row per equipped weapon, with attack bonus (ability mod +
  proficiency when proficient) and damage (weapon die + ability mod), choosing
  STR/DEX (finesse picks the better). Weapon data comes from weapon_rules.
- Other actions: the character's spells grouped by casting time (Action / Bonus
  Action / Reaction) and any features that read as actions. The user can add
  custom attacks and custom actions.

Custom attacks/actions are stored as character_features rows (source_type
'attack' / 'action' / 'bonus' / 'reaction') so no extra table is needed.
"""
import tkinter as tk
import customtkinter as ctk

from pages import weapon_rules

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
ACCENT_H = "#9472d8"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"
DANGER   = "#c0392b"
GOLD     = "#e0b040"

TIMINGS = ["Action", "Bonus Action", "Reaction"]
_ST_FROM_TIMING = {"Action": "action", "Bonus Action": "bonus", "Reaction": "reaction"}


def classify_timing(text: str) -> str | None:
    t = (text or "").lower()
    if "bonus action" in t:
        return "Bonus Action"
    if "reaction" in t:
        return "Reaction"
    if "action" in t:
        return "Action"
    return None


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


class ActionsPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._spell_by_id: dict[int, dict] = {}
        self._spell_by_name: dict[str, dict] = {}
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=ACCENT)
        self._scroll.pack(fill="both", expand=True, padx=12, pady=12)

    # ── data ────────────────────────────────────────────────────────────────
    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        for w in self._scroll.winfo_children():
            w.destroy()
        if not self._char:
            _empty(self, "Create or select a character on the Character Sheet tab.")
            for w in self._scroll.winfo_children():
                w.destroy()
            return
        if not self._spell_by_id:
            for sp in self.db.list_spells():
                self._spell_by_id[sp["id"]] = sp
                self._spell_by_name[sp["name"].lower()] = sp
        self._render()

    def _spell_ref(self, cs):
        if cs.get("spell_ref_id") and cs["spell_ref_id"] in self._spell_by_id:
            return self._spell_by_id[cs["spell_ref_id"]]
        return self._spell_by_name.get((cs.get("spell_name") or "").lower(), {})

    def _abilities(self):
        return {k: self._char[k] for k in ("str", "dex", "con", "int", "wis", "cha")}

    # ── derivations (also used by tests) ──────────────────────────────────────
    def _weapon_attacks(self) -> list[dict]:
        profs = [p["name"] for p in self._char["proficiencies"] if p["kind"] == "weapon"]
        pb = self.db.proficiency_bonus(self._cid)
        abil = self._abilities()
        out = []
        for inv in self.db.list_character_inventory(self._cid):
            if not inv.get("equipped"):
                continue
            w = weapon_rules.find_weapon(inv.get("item_name", ""))
            if w:
                out.append(weapon_rules.weapon_attack(w, abil, pb, profs))
        return out

    def _manual_attacks(self) -> list[dict]:
        out = []
        for f in self.db.list_character_features(self._cid):
            if (f.get("source_type") or "").lower() == "attack":
                parts = (f.get("description") or "").split("||")
                out.append({"id": f["id"], "name": f["name"],
                            "to_hit": parts[0] if parts else "",
                            "damage": parts[1] if len(parts) > 1 else ""})
        return out

    def _spell_actions(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {"Action": [], "Bonus Action": [], "Reaction": [], "Other": []}
        for cs in self.db.list_character_spells(self._cid):
            ref = self._spell_ref(cs)
            timing = classify_timing(ref.get("casting_time", "")) or "Other"
            groups[timing].append(cs["spell_name"])
        return groups

    def _feature_actions(self) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = {"Action": [], "Bonus Action": [], "Reaction": []}
        for f in self.db.list_character_features(self._cid):
            st = (f.get("source_type") or "").lower()
            if st == "attack":
                continue
            if st == "action":
                timing = "Action"
            elif st in ("bonus", "bonus action"):
                timing = "Bonus Action"
            elif st == "reaction":
                timing = "Reaction"
            else:
                timing = classify_timing(f.get("description", ""))
                if not timing:
                    continue
            groups[timing].append(f)
        return groups

    # ── render ────────────────────────────────────────────────────────────────
    def _section(self, title, accent=ACCENT):
        ctk.CTkLabel(self._scroll, text=title, text_color=accent,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=4, pady=(12, 2))

    def _render(self):
        # Attacks
        bar = ctk.CTkFrame(self._scroll, fg_color="transparent")
        bar.pack(fill="x", padx=4, pady=(2, 0))
        ctk.CTkLabel(bar, text="Attacks", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(bar, text="＋ Custom attack", width=120, height=26, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=11),
                      command=self._add_attack_dialog).pack(side="right")

        attacks = self._weapon_attacks()
        manual = self._manual_attacks()
        if not attacks and not manual:
            ctk.CTkLabel(self._scroll, text="No attacks — equip a weapon or add a custom attack.",
                         text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=8, pady=4)
        for a in attacks:
            self._attack_row(a["name"], f"{a['bonus']:+d}", a["damage"],
                             note=("" if a["proficient"] else "not proficient"))
        for m in manual:
            self._attack_row(m["name"], m["to_hit"] or "—", m["damage"] or "—",
                             remove=lambda mid=m["id"]: self._remove_feature(mid))

        # Other actions
        bar2 = ctk.CTkFrame(self._scroll, fg_color="transparent")
        bar2.pack(fill="x", padx=4, pady=(16, 0))
        ctk.CTkLabel(bar2, text="Other Actions", text_color=ACCENT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(bar2, text="＋ Custom action", width=120, height=26, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=11),
                      command=self._add_action_dialog).pack(side="right")

        spells = self._spell_actions()
        feats = self._feature_actions()
        any_row = False
        for timing in TIMINGS:
            items = []
            for f in feats.get(timing, []):
                items.append(("feature", f))
            for nm in spells.get(timing, []):
                items.append(("spell", nm))
            if not items:
                continue
            any_row = True
            ctk.CTkLabel(self._scroll, text=timing, text_color=GOLD,
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=8, pady=(8, 1))
            for kind, obj in items:
                if kind == "spell":
                    self._action_row("✦ " + obj, "spell")
                else:
                    self._action_row("◆ " + obj["name"], (obj.get("source_name") or "feature"),
                                     remove=(lambda fid=obj["id"]: self._remove_feature(fid))
                                     if (obj.get("source_type") or "").lower() in _ST_FROM_TIMING.values()
                                     else None)
        # Spells with non-action casting times (rituals, minutes) for reference.
        other = spells.get("Other", [])
        if other:
            any_row = True
            ctk.CTkLabel(self._scroll, text="Longer casting (minutes/ritual)", text_color=MUTED,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=8, pady=(8, 1))
            for nm in other:
                self._action_row("✦ " + nm, "spell")
        if not any_row:
            ctk.CTkLabel(self._scroll, text="No other actions yet.", text_color=MUTED,
                         font=ctk.CTkFont(size=11)).pack(anchor="w", padx=8, pady=4)

    def _attack_row(self, name, to_hit, damage, note="", remove=None):
        row = ctk.CTkFrame(self._scroll, fg_color=SURFACE2, corner_radius=6)
        row.pack(fill="x", padx=4, pady=1)
        ctk.CTkLabel(row, text=name, text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(side="left", padx=8, fill="x", expand=True)
        if remove:
            ctk.CTkButton(row, text="✕", width=24, height=24, fg_color="transparent",
                          hover_color=DANGER, text_color=MUTED, font=ctk.CTkFont(size=11),
                          command=remove).pack(side="right", padx=(0, 4))
        if note:
            ctk.CTkLabel(row, text=note, text_color=MUTED,
                         font=ctk.CTkFont(size=9)).pack(side="right", padx=6)
        ctk.CTkLabel(row, text=damage, text_color=TEXT, font=ctk.CTkFont(size=11),
                     width=130, anchor="e").pack(side="right", padx=6)
        ctk.CTkLabel(row, text=f"to hit {to_hit}", text_color=GOLD,
                     font=ctk.CTkFont(size=11, weight="bold"), width=90,
                     anchor="e").pack(side="right", padx=6)

    def _action_row(self, label, tag, remove=None):
        row = ctk.CTkFrame(self._scroll, fg_color=SURFACE2, corner_radius=6)
        row.pack(fill="x", padx=10, pady=1)
        ctk.CTkLabel(row, text=label, text_color=TEXT, font=ctk.CTkFont(size=12),
                     anchor="w").pack(side="left", padx=8, fill="x", expand=True, pady=2)
        if remove:
            ctk.CTkButton(row, text="✕", width=24, height=24, fg_color="transparent",
                          hover_color=DANGER, text_color=MUTED, font=ctk.CTkFont(size=11),
                          command=remove).pack(side="right", padx=(0, 4))
        ctk.CTkLabel(row, text=tag, text_color=MUTED,
                     font=ctk.CTkFont(size=9)).pack(side="right", padx=8)

    # ── mutations ─────────────────────────────────────────────────────────────
    def _remove_feature(self, fid):
        self.db.delete_character_feature(fid)
        self.refresh()

    def _add_attack_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Custom Attack")
        dlg.geometry("340x230")
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()
        nvar, tvar, dvar = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for label, var in [("Name", nvar), ("To hit (e.g. +6)", tvar),
                           ("Damage (e.g. 1d8+3 fire)", dvar)]:
            ctk.CTkLabel(dlg, text=label, text_color=MUTED,
                         font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
            ctk.CTkEntry(dlg, textvariable=var, fg_color=SURFACE2, border_color=BORDER,
                         text_color=TEXT, height=28).pack(fill="x", padx=16)

        def save():
            if nvar.get().strip():
                self.db.create_character_feature(self._cid, {
                    "source_type": "attack", "name": nvar.get().strip(),
                    "description": f"{tvar.get().strip()}||{dvar.get().strip()}"})
                dlg.destroy()
                self.refresh()
        ctk.CTkButton(dlg, text="Add", fg_color=ACCENT, hover_color=ACCENT_H, text_color=TEXT,
                      height=32, command=save).pack(fill="x", padx=16, pady=14)

    def _add_action_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Custom Action")
        dlg.geometry("360x300")
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()
        nvar = tk.StringVar()
        tvar = tk.StringVar(value="Action")
        ctk.CTkLabel(dlg, text="Name", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
        ctk.CTkEntry(dlg, textvariable=nvar, fg_color=SURFACE2, border_color=BORDER,
                     text_color=TEXT, height=28).pack(fill="x", padx=16)
        ctk.CTkLabel(dlg, text="Timing", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
        ctk.CTkOptionMenu(dlg, variable=tvar, values=TIMINGS, fg_color=SURFACE2,
                          button_color=ACCENT, button_hover_color=ACCENT_H,
                          text_color=TEXT).pack(fill="x", padx=16)
        ctk.CTkLabel(dlg, text="Description", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
        body = ctk.CTkTextbox(dlg, height=80, fg_color=SURFACE2, border_color=BORDER,
                              text_color=TEXT, wrap="word")
        body.pack(fill="x", padx=16)

        def save():
            if nvar.get().strip():
                self.db.create_character_feature(self._cid, {
                    "source_type": _ST_FROM_TIMING[tvar.get()], "name": nvar.get().strip(),
                    "description": body.get("1.0", "end").strip()})
                dlg.destroy()
                self.refresh()
        ctk.CTkButton(dlg, text="Add", fg_color=ACCENT, hover_color=ACCENT_H, text_color=TEXT,
                      height=32, command=save).pack(fill="x", padx=16, pady=12)
