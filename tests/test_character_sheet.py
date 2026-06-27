"""Headless render test for the Character Sheet tab.

Builds the real App against a throwaway database (temp APPDATA), imports the
sample character, renders the sheet, and checks the derived values + that edits
persist through the Database. Never touches real user data.

Run:  python tests/test_character_sheet.py
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="arcane_sword_sheet_test_")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402
import main  # noqa: E402


def main_test() -> int:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = main.App()

    # Import the bundled sample character.
    template = (ROOT / "data" / "characters_template.csv").read_text(encoding="utf-8")
    res = app.db.import_csv("characters_template.csv", template)
    assert res["inserted"] == 1, res

    # Render the Character Sheet tab.
    app.show_page("character_sheet")
    app.update_idletasks()
    sheet = app._pages["character_sheet"]

    # Picker resolved the active character and shared it onto the app.
    assert app.active_character_id is not None
    assert sheet._cid == app.active_character_id
    assert sheet._char["name"] == "Lyra Moonwhisper"

    def mod(code): return sheet._mod_lbls[code].cget("text")
    def save(code): return sheet._save_lbls[code].cget("text")
    def skill(name): return sheet._skill_lbls[name].cget("text")

    # ── Ability modifiers (live labels) ──────────────────────────────────────
    assert mod("int") == "+4", mod("int")   # 18 -> +4
    assert mod("dex") == "+3", mod("dex")   # 16 -> +3
    assert mod("str") == "-1", mod("str")   # 8  -> -1

    # ── Proficiency bonus (derived from total level 7) ───────────────────────
    assert sheet._prof_lbl.cget("text") == "+3", sheet._prof_lbl.cget("text")

    # ── Initiative = DEX mod + initiative_misc ───────────────────────────────
    assert sheet._init_lbl.cget("text") == "+3", sheet._init_lbl.cget("text")

    # ── Saving throws (INT & WIS proficient) ─────────────────────────────────
    assert save("int") == "+7", save("int")   # 4 + 3
    assert save("wis") == "+4", save("wis")   # 1 + 3
    assert save("str") == "-1", save("str")   # -1, not proficient
    assert sheet._save_dots["int"].cget("text") == "●"
    assert sheet._save_dots["str"].cget("text") == "○"

    # ── Skills (proficient / expertise / none) ───────────────────────────────
    assert skill("Investigation") == "+10", skill("Investigation")  # expertise: 4 + 2*3
    assert skill("Arcana") == "+7", skill("Arcana")                 # proficient: 4 + 3
    assert skill("Stealth") == "+3", skill("Stealth")               # none: dex 3
    assert sheet._skill_dots["Investigation"].cget("text") == "★"
    assert sheet._skill_dots["Arcana"].cget("text") == "●"

    # ── Passive senses (template provides overrides) ─────────────────────────
    assert sheet._passive_lbls["Perception"].cget("text") == "11"
    assert sheet._passive_lbls["Insight"].cget("text") == "13"
    assert sheet._passive_lbls["Investigation"].cget("text") == "18"

    # ── Live recompute when an ability changes (no rebuild) ───────────────────
    sheet._char["int"] = 20
    sheet._recompute()
    assert mod("int") == "+5", mod("int")
    assert save("int") == "+8", save("int")
    assert skill("Investigation") == "+11", skill("Investigation")
    sheet._char["int"] = 18  # restore

    # ── Skill cycle persists through the Database ─────────────────────────────
    cid = sheet._cid
    before = {s["skill"] for s in app.db.list_character_skills(cid)}
    assert "Stealth" not in before
    sheet._cycle_skill("Stealth")  # none -> proficient
    after = {s["skill"]: s["proficiency"] for s in app.db.list_character_skills(cid)}
    assert after.get("Stealth") == "proficient", after
    assert skill("Stealth") == "+6", skill("Stealth")  # dex 3 + prof 3

    # ── Saving-throw toggle persists ─────────────────────────────────────────
    sheet._toggle_save("con")  # add CON proficiency
    con_saves = {_s["ability"].lower()[:3] for _s in app.db.list_character_saves(cid)
                 if _s["proficient"]}
    assert "con" in con_saves, con_saves
    assert save("con") == "+5", save("con")  # con mod 2 + prof 3

    # ── HP damage absorbs temp first, then current; persists ─────────────────
    sheet._char["hp_temp"] = 5
    sheet._char["hp_current"] = 44
    app.db.update_character(cid, sheet._char)
    # Simulate a 12-damage hit (5 temp absorbed, 7 to current).
    val = 12
    tmp = sheet._char["hp_temp"]; absorbed = min(tmp, val)
    sheet._char["hp_temp"] = tmp - absorbed
    sheet._char["hp_current"] = max(0, sheet._char["hp_current"] - (val - absorbed))
    app.db.update_character(cid, sheet._char)
    reloaded = app.db.get_character(cid)
    assert reloaded["hp_temp"] == 0 and reloaded["hp_current"] == 37, \
        (reloaded["hp_temp"], reloaded["hp_current"])

    # ── New character via the picker action; delete via DB (delete() prompts) ─
    sheet._new_character()
    assert app.db.get_character(sheet._cid)["name"] == "New Character"
    app.db.delete_character(sheet._cid)
    sheet.refresh()
    assert len(app.db.list_characters()) == 1

    print("integrity_check:", app.db.conn.execute("PRAGMA integrity_check").fetchone()[0])
    print("\nCHARACTER SHEET RENDER TEST PASSED")
    app.update_idletasks()
    app.destroy()
    return 0


if __name__ == "__main__":
    try:
        rc = main_test()
    finally:
        import shutil
        shutil.rmtree(os.environ["APPDATA"], ignore_errors=True)
    sys.exit(rc)
