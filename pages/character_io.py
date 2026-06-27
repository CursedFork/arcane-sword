"""Import / Manage Characters tab.

- Export the active character to a single CSV (the characters import format) or
  to a lossless JSON (character + all child rows).
- Import from a characters CSV (one or many characters) or a JSON export.
- Delete the active character, or reset ALL character data (compendium kept).
"""
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk

BG       = "#0f0f13"
SURFACE  = "#1a1a24"
SURFACE2 = "#22222f"
BORDER   = "#2e2e3e"
ACCENT   = "#7c5cbf"
ACCENT_H = "#9472d8"
TEXT     = "#e2e0f0"
MUTED    = "#8a8aa0"
DANGER   = "#c0392b"


class CharacterIOPage(ctk.CTkFrame):
    def __init__(self, parent, db, app=None):
        super().__init__(parent, fg_color=BG)
        self.db = db
        self.app = app
        self._cid = None
        self._char = None
        self._wrap = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=ACCENT)
        self._wrap.pack(fill="both", expand=True, padx=40, pady=24)

    def refresh(self):
        self._cid = getattr(self.app, "active_character_id", None) if self.app else None
        self._char = self.db.get_character(self._cid) if self._cid else None
        for w in self._wrap.winfo_children():
            w.destroy()
        self._render()

    def _card(self, title, color=ACCENT):
        card = ctk.CTkFrame(self._wrap, fg_color=SURFACE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=8)
        ctk.CTkLabel(card, text=title, text_color=color,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=18, pady=(14, 2))
        return card

    def _render(self):
        ctk.CTkLabel(self._wrap, text="Import / Manage Characters", text_color=TEXT,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 4))
        who = self._char["name"] if self._char else "none selected"
        ctk.CTkLabel(self._wrap, text=f"Active character: {who}", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 8))

        # Export
        exp = self._card("Export Active Character")
        ctk.CTkLabel(exp, text="CSV uses the import format (re-importable). JSON is a "
                     "lossless backup of the character and all its data.",
                     text_color=MUTED, font=ctk.CTkFont(size=11), justify="left"
                     ).pack(anchor="w", padx=18, pady=(0, 8))
        ebtns = ctk.CTkFrame(exp, fg_color="transparent")
        ebtns.pack(anchor="w", padx=18, pady=(0, 16))
        ctk.CTkButton(ebtns, text="Export CSV", width=130, height=32, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, command=self._export_csv
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(ebtns, text="Export JSON", width=130, height=32, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, command=self._export_json
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(ebtns, text="Export ALL (CSV)", width=140, height=32, fg_color=SURFACE2,
                      hover_color=BORDER, text_color=TEXT, command=self._export_all_csv
                      ).pack(side="left")

        # Import
        imp = self._card("Import Character")
        ctk.CTkLabel(imp, text="Load a characters CSV (one or many characters) or a JSON "
                     "export. Imported characters are added; nothing is overwritten.",
                     text_color=MUTED, font=ctk.CTkFont(size=11), justify="left"
                     ).pack(anchor="w", padx=18, pady=(0, 8))
        ctk.CTkButton(imp, text="Import from file…", width=160, height=32, fg_color=ACCENT,
                      hover_color=ACCENT_H, text_color=TEXT, command=self._import_file
                      ).pack(anchor="w", padx=18, pady=(0, 16))

        # Danger zone
        dz = self._card("Danger Zone", color=DANGER)
        ctk.CTkButton(dz, text="Delete Active Character", width=200, height=32, fg_color=SURFACE2,
                      hover_color=DANGER, text_color=TEXT, command=self._delete_active
                      ).pack(anchor="w", padx=18, pady=(0, 8))
        ctk.CTkLabel(dz, text="Erase ALL character data (the bundled reference compendium is "
                     "kept). A backup snapshot is taken first.", text_color=MUTED,
                     font=ctk.CTkFont(size=11), justify="left").pack(anchor="w", padx=18)
        ctk.CTkButton(dz, text="Erase ALL Character Data", width=220, height=34, fg_color=DANGER,
                      hover_color="#e74c3c", text_color=TEXT, command=self._reset_all
                      ).pack(anchor="w", padx=18, pady=(6, 16))

    # ── export ────────────────────────────────────────────────────────────────
    def _export_csv(self):
        if not self._char:
            messagebox.showinfo("Export", "No active character."); return
        path = filedialog.asksaveasfilename(
            title="Export Character CSV", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"{self._safe(self._char['name'])}.csv")
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write(self.db.export_character_csv(self._cid))
            messagebox.showinfo("Export", f"Saved CSV to:\n{path}")

    def _export_json(self):
        if not self._char:
            messagebox.showinfo("Export", "No active character."); return
        path = filedialog.asksaveasfilename(
            title="Export Character JSON", defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"{self._safe(self._char['name'])}.json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.db.export_character_json(self._cid))
            messagebox.showinfo("Export", f"Saved JSON to:\n{path}")

    def _export_all_csv(self):
        if self.db.character_count() == 0:
            messagebox.showinfo("Export", "No characters to export."); return
        path = filedialog.asksaveasfilename(
            title="Export ALL Characters (CSV)", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], initialfile="characters.csv")
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write(self.db.export_characters_csv())
            messagebox.showinfo("Export", f"Exported {self.db.character_count()} character(s) to:\n{path}")

    # ── import ────────────────────────────────────────────────────────────────
    def _import_file(self):
        path = filedialog.askopenfilename(
            title="Import Character", filetypes=[("Character files", "*.csv *.json"),
                                                 ("CSV", "*.csv"), ("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror("Import", f"Could not read file:\n{e}"); return

        is_json = path.lower().endswith(".json") or text.lstrip().startswith("{")
        try:
            if is_json:
                cid = self.db.import_character_json(text)
                if self.app is not None:
                    self.app.active_character_id = cid
                msg = "Imported 1 character from JSON."
            else:
                res = self.db.import_csv(os.path.basename(path), text)
                if res["table"] != "characters":
                    messagebox.showerror("Import",
                                         "That CSV doesn't look like a characters file."); return
                msg = (f"Imported {res['inserted']} character(s)"
                       + (f", skipped {res['skipped']}" if res['skipped'] else "")
                       + (f"\nErrors: {len(res['errors'])}" if res['errors'] else "") + ".")
        except Exception as e:
            messagebox.showerror("Import", f"Import failed:\n{e}"); return
        self.refresh()
        messagebox.showinfo("Import", msg)

    # ── danger zone ───────────────────────────────────────────────────────────
    def _delete_active(self):
        if not self._char:
            messagebox.showinfo("Delete", "No active character."); return
        if messagebox.askyesno("Delete Character",
                               f"Permanently delete '{self._char['name']}' and all its data?"):
            self.db.delete_character(self._cid)
            if self.app is not None:
                self.app.active_character_id = None
            self.refresh()

    def _reset_all(self):
        n = self.db.character_count()
        if n == 0:
            messagebox.showinfo("Reset", "There are no characters to erase."); return
        if not messagebox.askyesno(
                "Erase ALL Character Data",
                f"This permanently deletes ALL {n} character(s) and everything attached to "
                f"them.\nThe reference compendium is kept and a backup snapshot is taken first.\n\n"
                f"Are you sure?"):
            return
        if not messagebox.askyesno("Final confirmation", "Really erase everything? This cannot be undone."):
            return
        self.db.wipe_all_characters()
        if self.app is not None:
            self.app.active_character_id = None
        self.refresh()
        messagebox.showinfo("Reset", f"Erased {n} character(s).")

    @staticmethod
    def _safe(name):
        return "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in (name or "character")).strip()
