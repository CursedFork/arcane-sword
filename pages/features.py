"""Features & Traits tab — character_features grouped by source (Race / Class /
Subclass / Background / Feat / Other), each rendered as Markdown.

"Pull from reference" auto-populates features from the character_options
compendium for the character's race/classes/subclasses/background. The user can
also add, edit, or remove features manually. Action-type features (managed on
the Actions tab) are excluded here.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from pages.md_widget import MarkdownText
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

GROUPS = ["Race", "Class", "Subclass", "Background", "Feat", "Other"]
ACTION_TYPES = {"attack", "action", "bonus", "reaction"}


def _group_of(f: dict) -> str | None:
    st = (f.get("source_type") or "").strip()
    if st.lower() in ACTION_TYPES:
        return None  # belongs to the Actions tab
    for g in GROUPS:
        if st.lower() == g.lower():
            return g
    sn = (f.get("source_name") or "").strip()
    for g in GROUPS:
        if sn.lower() == g.lower():
            return g
    return "Other"


class FeaturesPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._build()

    def _build(self):
        bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkLabel(bar, text="Features & Traits", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=16)
        ctk.CTkButton(bar, text="＋ Add Feature", width=120, height=30, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=lambda: self._edit_dialog(None)).pack(side="right", padx=(4, 16), pady=10)
        ctk.CTkButton(bar, text="⟲ Pull from reference", width=160, height=30, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._pull_clicked).pack(side="right", padx=4, pady=10)

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

    # ── pull from reference ───────────────────────────────────────────────────
    def pull_from_reference(self) -> int:
        """Add features from the compendium for the character's race/classes/
        subclasses/background. Skips ones already present. Returns count added."""
        existing = {((f.get("source_type") or "").lower(), (f.get("name") or "").lower())
                    for f in self.db.list_character_features(self._cid)}
        also = {((f.get("source_name") or "").lower(), (f.get("name") or "").lower())
                for f in self.db.list_character_features(self._cid)}
        added = 0

        def add(opt, kind):
            nonlocal added
            if not opt:
                return
            key = (kind.lower(), (opt.get("name") or "").lower())
            if key in existing or key in also:
                return
            self.db.create_character_feature(self._cid, ref.feature_from_option(opt, kind))
            existing.add(key)
            added += 1

        c = self._char
        add(ref.find_race_option(self.db, c.get("race", ""), c.get("subrace", "")), "Race")
        for cls in c["classes"]:
            add(ref.find_option(self.db, "class", cls.get("class", "")), "Class")
            if cls.get("subclass"):
                add(ref.find_option(self.db, "subclass", cls["subclass"],
                                    parent=cls.get("class")), "Subclass")
        add(ref.find_option(self.db, "background", c.get("background", "")), "Background")
        return added

    def _pull_clicked(self):
        n = self.pull_from_reference()
        self.refresh()
        messagebox.showinfo("Pull from reference",
                            f"Added {n} feature(s) from the compendium." if n
                            else "Nothing new to add — everything is already present "
                                 "(or no matching reference entries were found).")

    # ── render ────────────────────────────────────────────────────────────────
    def _render(self):
        feats = [f for f in self.db.list_character_features(self._cid) if _group_of(f)]
        if not feats:
            ctk.CTkLabel(self._scroll, text="No features yet — use “Pull from reference” "
                         "or “＋ Add Feature”.", text_color=MUTED,
                         font=ctk.CTkFont(size=12)).pack(pady=20)
            return
        by_group: dict[str, list] = {}
        for f in feats:
            by_group.setdefault(_group_of(f), []).append(f)
        for g in GROUPS:
            items = by_group.get(g)
            if not items:
                continue
            ctk.CTkLabel(self._scroll, text=g, text_color=ACCENT,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=4, pady=(12, 2))
            for f in items:
                self._feature_card(f)

    def _feature_card(self, f):
        card = ctk.CTkFrame(self._scroll, fg_color=SURFACE, corner_radius=8,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=4, pady=3)
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(head, text=f.get("name", ""), text_color=TEXT,
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
                     ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(head, text="✕", width=24, height=24, fg_color="transparent",
                      hover_color=DANGER, text_color=MUTED, font=ctk.CTkFont(size=11),
                      command=lambda: self._remove(f)).pack(side="right")
        ctk.CTkButton(head, text="Edit", width=48, height=24, fg_color="transparent",
                      hover_color=BORDER, text_color=MUTED, font=ctk.CTkFont(size=11),
                      command=lambda: self._edit_dialog(f)).pack(side="right", padx=2)
        body = (f.get("description") or "").strip()
        if body:
            md = MarkdownText(card, bg=SURFACE2, height=min(260, 40 + body.count("\n") * 18))
            md.pack(fill="x", padx=10, pady=(4, 10))
            md.set_markdown(body)
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    # ── mutations ─────────────────────────────────────────────────────────────
    def _remove(self, f):
        self.db.delete_character_feature(f["id"])
        self.refresh()

    def _edit_dialog(self, f):
        if not self._char:
            return
        is_new = f is None
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add Feature" if is_new else "Edit Feature")
        dlg.geometry("460x420")
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="Source", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(12, 0))
        st_var = tk.StringVar(value=(_group_of(f) if f else "Other") or "Other")
        ctk.CTkOptionMenu(dlg, variable=st_var, values=GROUPS, fg_color=SURFACE2,
                          button_color=ACCENT, button_hover_color=ACCENT_H,
                          text_color=TEXT).pack(fill="x", padx=16)
        ctk.CTkLabel(dlg, text="Name", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
        name_var = tk.StringVar(value=(f.get("name") if f else ""))
        ctk.CTkEntry(dlg, textvariable=name_var, fg_color=SURFACE2, border_color=BORDER,
                     text_color=TEXT, height=28).pack(fill="x", padx=16)
        ctk.CTkLabel(dlg, text="Description (Markdown)", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16, pady=(10, 0))
        body = ctk.CTkTextbox(dlg, height=180, fg_color=SURFACE2, border_color=BORDER,
                              text_color=TEXT, wrap="word")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        if f:
            body.insert("1.0", f.get("description", "") or "")

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Validation", "Name is required."); return
            data = {"source_type": st_var.get(), "source_name": st_var.get(),
                    "name": name, "description": body.get("1.0", "end").strip()}
            if is_new:
                self.db.create_character_feature(self._cid, data)
            else:
                self.db.update_character_feature(f["id"], data)
            dlg.destroy()
            self.refresh()
        ctk.CTkButton(dlg, text="Save", fg_color=ACCENT, hover_color=ACCENT_H, text_color=TEXT,
                      height=34, command=save).pack(fill="x", padx=16, pady=(0, 14))
