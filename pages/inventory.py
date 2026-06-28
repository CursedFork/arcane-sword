"""Inventory tab for the active character.

Reuses the Items reference (magic_items) for searching/adding and for showing a
matched item's description (MarkdownText). Lines persist immediately to
character_inventory. Enforces the 3-item attunement cap and shows an attuned
count + a rough carried-weight estimate where weight data is available.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from pages.md_widget import MarkdownText
from pages.ui_util import ScrollList, bind_row
from pages import weapon_rules, theme

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

ATTUNE_CAP = 3


def build_item_detail(parent, item: dict | None):
    for w in parent.winfo_children():
        w.destroy()
    if not item:
        ctk.CTkLabel(parent, text="Select an item to view it", text_color=MUTED,
                     font=ctk.CTkFont(size=13)).pack(expand=True)
        return
    ctk.CTkLabel(parent, text=item["name"], font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=TEXT, anchor="w").pack(fill="x", padx=16, pady=(16, 2))
    bits = [b for b in (item.get("item_type"), item.get("rarity")) if b]
    if item.get("requires_attunement"):
        req = item.get("attunement_requirement") or ""
        bits.append("requires attunement" + (f" ({req})" if req else ""))
    ctk.CTkLabel(parent, text=" · ".join(bits) or "—", text_color=MUTED,
                 font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=(0, 6))
    ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(0, 8))
    md = MarkdownText(parent, bg=SURFACE2)
    md.pack(fill="both", expand=True, padx=16, pady=(0, 16))
    body = item.get("description", "") or ""
    if item.get("mechanical_effect"):
        body += ("\n\n**Effect:** " + item["mechanical_effect"])
    md.set_markdown(body or "*(no description)*")


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


class InventoryPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._inv: list[dict] = []
        self._items_by_id: dict[int, dict] = {}
        self._items_by_name: dict[str, dict] = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, width=460, fg_color=SURFACE, corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_propagate(False)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        ctk.CTkLabel(hdr, text="Inventory", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="＋ Add Item", width=96, height=28, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._add_dialog).pack(side="right")

        self._summary = ctk.CTkLabel(left, text="", text_color=MUTED,
                                     font=ctk.CTkFont(size=11), anchor="w")
        self._summary.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 4))

        self._list = ScrollList(left, bg=SURFACE, accent=ACCENT)
        self._list.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 8))

        self._right = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        self._right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=1)
        build_item_detail(self._right, None)

    # ── data ────────────────────────────────────────────────────────────────
    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        if not self._items_by_id:
            for it in self.db.list_items():
                self._items_by_id[it["id"]] = it
                self._items_by_name[it["name"].lower()] = it
        if not self._char:
            self._list.clear(); self._list.finalize()
            self._summary.configure(text="")
            _empty(self._right, "Create or select a character on the Character Sheet tab.")
            return
        self._inv = self.db.list_character_inventory(self._cid)
        self._render_summary()
        self._render_list()

    def _ref_for(self, row) -> dict | None:
        if row.get("item_ref_id") and row["item_ref_id"] in self._items_by_id:
            return self._items_by_id[row["item_ref_id"]]
        return self._items_by_name.get((row.get("item_name") or "").lower())

    def _attuned_count(self) -> int:
        return sum(1 for r in self._inv if r.get("attuned"))

    def _row_weight(self, row):
        w = weapon_rules.find_weapon(row.get("item_name", ""))
        if w:
            return w["weight"]
        ref = self._ref_for(row)
        if ref:
            return weapon_rules.parse_weight(
                (ref.get("description") or "") + " " + (ref.get("mechanical_effect") or ""))
        return None

    def _total_weight(self):
        total = 0.0
        unknown = 0
        for r in self._inv:
            w = self._row_weight(r)
            if w is None:
                unknown += 1
            else:
                total += w * max(1, int(r.get("quantity", 1)))
        return total, unknown

    def _render_summary(self):
        att = self._attuned_count()
        weight, unknown = self._total_weight()
        wtxt = f"~{weight:g} lb" + (f" (+{unknown} w/o weight data)" if unknown else "")
        color = DANGER if att > ATTUNE_CAP else MUTED
        self._summary.configure(
            text=f"Attuned: {att}/{ATTUNE_CAP}     Carried: {wtxt}", text_color=color)

    # ── list ──────────────────────────────────────────────────────────────────
    def _render_list(self):
        self._list.clear()
        body = self._list.body
        if not self._inv:
            tk.Label(body, text="No items yet — use “＋ Add Item”.", bg=SURFACE, fg=MUTED,
                     font=("Segoe UI", 10)).pack(fill="x", padx=10, pady=12)
            self._list.finalize()
            return
        for r in self._inv:
            ref = self._ref_for(r)
            row = tk.Frame(body, bg=SURFACE2)
            row.pack(fill="x", padx=3, pady=1)

            name = tk.Label(row, text=r["item_name"], anchor="w", bg=SURFACE2,
                            fg=(TEXT if ref else MUTED), font=("Segoe UI", 11), cursor="hand2")
            name.pack(side="left", fill="x", expand=True, padx=(6, 2), pady=4)
            if ref:
                name.bind("<Button-1>", lambda e, it=ref: build_item_detail(self._right, it))

            tk.Button(row, text="✕", bd=0, bg=SURFACE2, fg=MUTED, font=("Segoe UI", 9),
                      activebackground=DANGER, cursor="hand2",
                      command=lambda rr=r: self._remove(rr)).pack(side="right", padx=(2, 6))
            # attuned (only meaningful for attunement items, but allow on any)
            att = bool(r.get("attuned"))
            tk.Button(row, text="Attuned" if att else "Attune", bd=0, padx=4,
                      bg=(GOLD if att else SURFACE), fg=(BG if att else MUTED),
                      font=("Segoe UI", 8), cursor="hand2",
                      command=lambda rr=r: self._toggle_attuned(rr)).pack(side="right", padx=2)
            eq = bool(r.get("equipped"))
            tk.Button(row, text="Equipped" if eq else "Equip", bd=0, padx=4,
                      bg=(GOOD if eq else SURFACE), fg=(BG if eq else MUTED),
                      font=("Segoe UI", 8), cursor="hand2",
                      command=lambda rr=r: self._toggle(rr, "equipped")).pack(side="right", padx=2)
            # quantity −/n/+
            tk.Button(row, text="+", bd=0, bg=SURFACE, fg=TEXT, font=("Segoe UI", 9),
                      cursor="hand2", command=lambda rr=r: self._set_qty(rr, +1)
                      ).pack(side="right", padx=(2, 4))
            tk.Label(row, text=f"×{r.get('quantity', 1)}", bg=SURFACE2, fg=TEXT,
                     font=("Segoe UI", 10), width=4).pack(side="right")
            tk.Button(row, text="−", bd=0, bg=SURFACE, fg=TEXT, font=("Segoe UI", 9),
                      cursor="hand2", command=lambda rr=r: self._set_qty(rr, -1)
                      ).pack(side="right", padx=4)
        self._list.finalize()

    # ── mutations ─────────────────────────────────────────────────────────────
    def _add_item(self, name, ref_id=None, qty=1, notes=""):
        if not (name or "").strip():
            return
        self.db.create_character_inventory(self._cid, {
            "item_name": name.strip(), "item_ref_id": ref_id,
            "quantity": max(1, int(qty)), "notes": notes})
        self.refresh()

    def _set_qty(self, row, delta):
        q = max(1, int(row.get("quantity", 1)) + delta)
        self.db.update_character_inventory(row["id"], {"quantity": q})
        self.refresh()

    def _toggle(self, row, field):
        self.db.update_character_inventory(row["id"], {field: 0 if row.get(field) else 1})
        self.refresh()

    def _toggle_attuned(self, row):
        # The attunement cap is a "training wheels" rules warning; with it off,
        # power users can exceed 3 deliberately.
        if (not row.get("attuned") and self._attuned_count() >= ATTUNE_CAP
                and theme.tw("warnings")):
            messagebox.showwarning(
                "Attunement limit",
                f"You can be attuned to at most {ATTUNE_CAP} items at once.\n"
                f"Un-attune something first.")
            return
        self.db.update_character_inventory(row["id"], {"attuned": 0 if row.get("attuned") else 1})
        self.refresh()

    def _remove(self, row):
        self.db.delete_character_inventory(row["id"])
        self.refresh()

    # ── add dialog (reference search + custom) ────────────────────────────────
    def _add_dialog(self):
        if not self._char:
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add Item")
        dlg.geometry("420x520")
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()

        custom = ctk.CTkFrame(dlg, fg_color="transparent")
        custom.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(custom, text="Custom item:", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left")
        cvar = tk.StringVar()
        ctk.CTkEntry(custom, textvariable=cvar, fg_color=SURFACE2, border_color=BORDER,
                     text_color=TEXT, height=28).pack(side="left", fill="x", expand=True, padx=6)

        def add_custom():
            if cvar.get().strip():
                self._add_item(cvar.get(), None, 1)
                dlg.destroy()
        ctk.CTkButton(custom, text="Add", width=56, height=28, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, command=add_custom).pack(side="left")

        ctk.CTkLabel(dlg, text="…or search the reference:", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(8, 2))
        svar = tk.StringVar()
        ctk.CTkEntry(dlg, textvariable=svar, placeholder_text="Search items…",
                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT, height=30
                     ).pack(fill="x", padx=12)
        results = ScrollList(dlg, bg=SURFACE, accent=ACCENT)
        results.pack(fill="both", expand=True, padx=10, pady=8)

        def search(*_):
            results.clear()
            q = svar.get().strip()
            rows = self.db.list_items(search=q)[:200] if q else self.db.list_items()[:200]
            for it in rows:
                r = tk.Frame(results.body, bg=SURFACE, cursor="hand2")
                r.pack(fill="x", padx=2, pady=1)
                tk.Label(r, text=it["name"], anchor="w", bg=SURFACE, fg=TEXT,
                         font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True, padx=6, pady=3)
                tk.Label(r, text=it.get("rarity", ""), bg=SURFACE, fg=MUTED,
                         font=("Segoe UI", 8)).pack(side="right", padx=6)
                bind_row(r, lambda i=it: (self._add_item(i["name"], i["id"], 1), dlg.destroy()),
                         SURFACE, SURFACE2)
            results.finalize()
        svar.trace_add("write", search)
        search()
