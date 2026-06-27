"""Background tab — edit the character's background_info (Markdown: personality
traits, ideals, bonds, flaws, backstory) with a live preview, alongside the
chosen background's feature from the reference compendium.
"""
import tkinter as tk
import customtkinter as ctk

from pages.md_widget import MarkdownText
from pages import reference_lookup as ref

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"

_TEMPLATE = ("## Personality Traits\n\n\n## Ideals\n\n\n## Bonds\n\n\n"
             "## Flaws\n\n\n## Backstory\n\n")


class BackgroundPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._debounce_id = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1, uniform="bg")
        self.grid_columnconfigure(1, weight=1, uniform="bg")
        self.grid_rowconfigure(0, weight=1)

        # Left: editor
        left = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(left, text="Character Background", text_color=TEXT,
                     font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, sticky="w",
                                                                    padx=14, pady=(12, 0))
        ctk.CTkLabel(left, text="Personality, ideals, bonds, flaws, backstory (Markdown).",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).grid(row=1, column=0, sticky="w",
                                                                       padx=14, pady=(0, 6))
        self._editor = ctk.CTkTextbox(left, fg_color=SURFACE2, border_color=BORDER,
                                      text_color=TEXT, wrap="word", font=ctk.CTkFont(size=13))
        self._editor.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self._editor.bind("<KeyRelease>", lambda e: self._on_key())
        self._editor.bind("<FocusOut>", lambda e: self._persist())
        btns = ctk.CTkFrame(left, fg_color="transparent")
        btns.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        ctk.CTkButton(btns, text="Insert template", height=26, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=MUTED, font=ctk.CTkFont(size=11),
                      command=self._insert_template).pack(side="left")
        ctk.CTkButton(btns, text="Save", height=26, width=70, fg_color=ACCENT,
                      hover_color="#9472d8", text_color=TEXT, font=ctk.CTkFont(size=11),
                      command=self._persist).pack(side="right")

        # Right: preview + reference background feature
        right = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right.grid_rowconfigure(1, weight=1)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(right, text="Preview", text_color=MUTED,
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w",
                                                                    padx=14, pady=(12, 2))
        self._preview = MarkdownText(right, bg=SURFACE2)
        self._preview.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self._bg_label = ctk.CTkLabel(right, text="Background Feature", text_color=ACCENT,
                                      font=ctk.CTkFont(size=12, weight="bold"))
        self._bg_label.grid(row=2, column=0, sticky="w", padx=14, pady=(4, 2))
        self._bg_ref = MarkdownText(right, bg=SURFACE2)
        self._bg_ref.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        self._editor.delete("1.0", "end")
        if not self._char:
            self._editor.configure(state="disabled")
            self._preview.set_markdown("*No character selected.*")
            self._bg_ref.set_markdown("")
            self._bg_label.configure(text="Background Feature")
            return
        self._editor.configure(state="normal")
        self._editor.insert("1.0", self._char.get("background_info", "") or "")
        self._update_preview()
        self._load_reference()

    def _load_reference(self):
        bg = (self._char.get("background") or "").strip()
        self._bg_label.configure(text=f"Background Feature — {bg}" if bg else "Background Feature")
        opt = ref.find_option(self.db, "background", bg) if bg else None
        self._bg_ref.set_markdown(opt.get("body_md", "") if opt
                                  else "*No matching background in the reference compendium.*")

    def _on_key(self):
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(180, self._update_preview)

    def _update_preview(self):
        self._preview.set_markdown(self._editor.get("1.0", "end").strip() or "*(empty)*")

    def _insert_template(self):
        if self._char and not self._editor.get("1.0", "end").strip():
            self._editor.insert("1.0", _TEMPLATE)
            self._update_preview()
            self._persist()

    def _persist(self):
        if not self._char:
            return
        self._char["background_info"] = self._editor.get("1.0", "end").strip()
        self.db.update_character(self._cid, self._char)
