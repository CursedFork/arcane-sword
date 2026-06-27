"""Campaign Notes tab — per-character notes (character_notes): quick-add titled
notes with Markdown bodies, newest-first, searchable, full CRUD. Mirrors Arcane
Shield's Notes tab, scoped to the active character.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from pages.md_widget import MarkdownText
from pages.ui_util import ScrollList, bind_row

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
ACCENT_H = "#9472d8"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"
DANGER   = "#c0392b"


class CampaignNotesPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._notes: list[dict] = []
        self._selected = None
        self._debounce_id = None
        self._build()

    def _debounce(self, fn, ms=160):
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(ms, fn)

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, width=320, fg_color=SURFACE, corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_propagate(False)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        ctk.CTkLabel(hdr, text="Campaign Notes", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="+ New", width=64, height=28, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=self._new).pack(side="right")

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._debounce(self._render_list))
        ctk.CTkEntry(left, textvariable=self._search_var, placeholder_text="Search notes…",
                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT, height=30
                     ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

        self._list = ScrollList(left, bg=SURFACE, accent=ACCENT)
        self._list.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 8))

        self._right = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        self._right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self._right.grid_columnconfigure(0, weight=1)
        self._right.grid_rowconfigure(0, weight=1)
        self._placeholder()

    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        if not self._char:
            self._list.clear(); self._list.finalize()
            self._placeholder("Create or select a character on the Character Sheet tab.")
            return
        self._render_list()

    # ── list ──────────────────────────────────────────────────────────────────
    def _render_list(self):
        q = self._search_var.get().strip().lower()
        self._notes = self.db.list_character_notes(self._cid)  # newest-first
        if q:
            self._notes = [n for n in self._notes
                           if q in (n.get("title") or "").lower()
                           or q in (n.get("body_md") or "").lower()]
        self._list.clear()
        body = self._list.body
        if not self._notes:
            tk.Label(body, text="No notes yet — “+ New”.", bg=SURFACE, fg=MUTED,
                     font=("Segoe UI", 10)).pack(fill="x", padx=10, pady=12)
            self._list.finalize()
            return
        for n in self._notes:
            row = tk.Frame(body, bg=SURFACE, cursor="hand2")
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=(n.get("title") or "(untitled)"), anchor="w", bg=SURFACE,
                     fg=TEXT, font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True,
                                                          padx=6, pady=3)
            tk.Label(row, text=(n.get("created_at") or "")[:10], bg=SURFACE, fg=MUTED,
                     font=("Segoe UI", 8)).pack(side="right", padx=6)
            bind_row(row, lambda nn=n: self._select(nn), SURFACE, SURFACE2)
        self._list.finalize()

    # ── detail / edit ─────────────────────────────────────────────────────────
    def _placeholder(self, msg="Select a note, or “+ New”."):
        for w in self._right.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._right, text=msg, text_color=MUTED,
                     font=ctk.CTkFont(size=13)).pack(expand=True)

    def _select(self, note):
        self._selected = note
        self._edit(note)

    def _new(self):
        if not self._char:
            return
        self._edit(None)

    def _edit(self, note):
        for w in self._right.winfo_children():
            w.destroy()
        is_new = note is None

        hdr = ctk.CTkFrame(self._right, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(16, 6))
        title_var = tk.StringVar(value=(note.get("title") if note else ""))
        ctk.CTkEntry(hdr, textvariable=title_var, placeholder_text="Title",
                     fg_color=SURFACE2, border_color=BORDER, text_color=TEXT,
                     font=ctk.CTkFont(size=15, weight="bold"), height=32
                     ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(hdr, text="Save", width=64, height=30, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, font=ctk.CTkFont(size=12),
                      command=lambda: self._save(note, title_var, editor)).pack(side="left", padx=(6, 0))
        if not is_new:
            ctk.CTkButton(hdr, text="Delete", width=64, height=30, fg_color=DANGER,
                          hover_color="#e74c3c", text_color=TEXT, font=ctk.CTkFont(size=12),
                          command=lambda: self._delete(note)).pack(side="left", padx=(6, 0))

        tabs = ctk.CTkFrame(self._right, fg_color="transparent")
        tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tabs.grid_columnconfigure((0, 1), weight=1, uniform="n")
        tabs.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(tabs, text="Markdown", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkLabel(tabs, text="Preview", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="w", padx=4)
        editor = ctk.CTkTextbox(tabs, fg_color=SURFACE2, border_color=BORDER, text_color=TEXT,
                                wrap="word", font=ctk.CTkFont(size=13))
        editor.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        if note:
            editor.insert("1.0", note.get("body_md", "") or "")
        preview = MarkdownText(tabs, bg=SURFACE2)
        preview.grid(row=1, column=1, sticky="nsew", padx=(4, 0))

        def update_preview(_=None):
            preview.set_markdown(editor.get("1.0", "end").strip() or "*(empty)*")
        editor.bind("<KeyRelease>", lambda e: self._debounce(update_preview, 180))
        update_preview()

    def _save(self, note, title_var, editor):
        title = title_var.get().strip()
        body = editor.get("1.0", "end").strip()
        if not title and not body:
            messagebox.showerror("Validation", "Add a title or some text."); return
        if note:
            self.db.update_character_note(note["id"], {"title": title, "body_md": body})
        else:
            self.db.create_character_note(self._cid, {"title": title, "body_md": body})
        self.refresh()

    def _delete(self, note):
        if messagebox.askyesno("Delete Note", f"Delete '{note.get('title') or 'note'}'?"):
            self.db.delete_character_note(note["id"])
            self._selected = None
            self.refresh()
            self._placeholder()
