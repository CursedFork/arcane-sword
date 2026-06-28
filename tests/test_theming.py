"""Tests for the theme engine + training-wheels toggles.

Run:  python tests/test_theming.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="arcane_sword_theme_test_")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402
import main  # noqa: E402
from pages import theme  # noqa: E402
import pages.inventory as invmod  # noqa: E402


def test_engine():
    assert theme.active_theme() == theme.DEFAULT_THEME
    assert len(theme.theme_names()) >= 3
    # backdrop comes from the bundled art (or degrades to None without Pillow)
    src = theme.backdrop_source("Martial Red")
    assert src is None or src.size[0] > 0
    print("  engine basics OK")


def test_live_switch_and_persist():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = main.App()

    assert main.BG == theme.palette(theme.DEFAULT_THEME)["BG"]
    app.apply_theme("Martial Red")
    assert main.BG == theme.palette("Martial Red")["BG"], main.BG
    assert invmod.ACCENT == theme.palette("Martial Red")["ACCENT"]  # page module recoloured

    # Persisted to settings.json
    saved = json.loads(Path(theme.settings_path()).read_text(encoding="utf-8"))
    assert saved["theme"] == "Martial Red", saved

    # Switching works and the UI rebuilds without error.
    app.apply_theme("Artificer Bronze")
    app.show_page("settings")
    app.update_idletasks()
    assert main.BG == theme.palette("Artificer Bronze")["BG"]
    print("  live switch + persist OK")

    # ── Training wheels: rules warnings gate the attunement cap ──────────────
    template = (ROOT / "data" / "characters_template.csv").read_text(encoding="utf-8")
    app.db.import_csv("characters_template.csv", template)
    app.show_page("character_sheet"); app.update_idletasks()
    cid = app.active_character_id
    app.show_page("inventory"); app.update_idletasks()
    inv = app._pages["inventory"]
    items = inv._inv
    assert len(items) >= 4, "template should give >=4 items"

    theme.set_tw("warnings", True)
    for r in items[:3]:
        fresh = next(x for x in inv._inv if x["id"] == r["id"])
        if not fresh.get("attuned"):
            inv._toggle_attuned(fresh)
    assert inv._attuned_count() == 3
    fourth = next(r for r in inv._inv if not r.get("attuned"))
    inv._toggle_attuned(fourth)            # warnings ON -> blocked at the cap
    assert inv._attuned_count() == 3, "cap should hold while warnings are on"

    theme.set_tw("warnings", False)
    fourth = next(r for r in inv._inv if not r.get("attuned"))
    inv._toggle_attuned(fourth)            # warnings OFF -> allowed past the cap
    assert inv._attuned_count() == 4, "cap is bypassable with warnings off"
    print("  training-wheels (warnings) OK")

    # ── Simple mode: Level-Up still renders with multiclass hidden ───────────
    theme.set_tw("simple_mode", True)
    app.apply_settings()
    app.show_page("level_up"); app.update_idletasks()
    assert theme.tw("simple_mode")
    print("  training-wheels (simple mode) OK")

    print("integrity_check:", app.db.conn.execute("PRAGMA integrity_check").fetchone()[0])
    app.update_idletasks()
    app.destroy()


def main_test() -> int:
    test_engine()
    test_live_switch_and_persist()
    print("\nTHEMING + TRAINING-WHEELS TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = main_test()
    finally:
        import shutil
        shutil.rmtree(os.environ["APPDATA"], ignore_errors=True)
    sys.exit(rc)
