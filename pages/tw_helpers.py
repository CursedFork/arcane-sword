"""Tiny helpers for the training-wheels toggles, so pages can add guidance
tips / derivation hints without each re-implementing the gating + styling.
Pages are rebuilt when a toggle changes, so these reflect the current flags.
"""
import customtkinter as ctk
from pages import theme


def tip(parent, text: str, **pack_kw):
    """A guidance banner, shown only when 'Tooltips & guidance' is on."""
    if not theme.tw("tooltips"):
        return None
    pal = theme.palette()
    lbl = ctk.CTkLabel(parent, text="💡  " + text, text_color=pal["MUTED"],
                       font=ctk.CTkFont(size=11), anchor="w", justify="left",
                       wraplength=pack_kw.pop("wraplength", 720))
    lbl.pack(fill="x", padx=pack_kw.pop("padx", 14), pady=pack_kw.pop("pady", (6, 2)),
             **pack_kw)
    return lbl


def hint(parent, text: str, **pack_kw):
    """A derivation hint (how a value is computed), shown only when
    'Derivation hints' is on."""
    if not theme.tw("hints"):
        return None
    pal = theme.palette()
    lbl = ctk.CTkLabel(parent, text="ƒ  " + text, text_color=pal["ACCENT"],
                       font=ctk.CTkFont(size=10), anchor="w", justify="left",
                       wraplength=pack_kw.pop("wraplength", 460))
    lbl.pack(fill="x", padx=pack_kw.pop("padx", 12), pady=pack_kw.pop("pady", (0, 4)),
             **pack_kw)
    return lbl
