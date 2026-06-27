"""Tests for Features pull, Background, and the Level-Up flow (single-class and
multiclass), against a throwaway database.

Run:  python tests/test_leveling.py
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="arcane_sword_level_test_")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402
import main  # noqa: E402
from pages import levelup_rules as lr  # noqa: E402


def test_rules():
    assert lr.hit_die("Wizard") == 6 and lr.avg_hp("Wizard") == 4
    assert lr.hit_die("Barbarian") == 12 and lr.avg_hp("Barbarian") == 7
    assert lr.is_asi_level("Wizard", 4) and not lr.is_asi_level("Wizard", 5)
    assert lr.is_asi_level("Fighter", 6) and lr.is_asi_level("Rogue", 10)
    assert lr.needs_subclass("Cleric", 1, False)          # cleric picks at 1
    assert not lr.needs_subclass("Fighter", 1, False)     # fighter at 3
    assert lr.needs_subclass("Fighter", 3, False)
    assert lr.hp_gain("Fighter", 2, "average") == 8       # 6 + 2
    assert lr.hp_gain("Wizard", 3, "roll", 5) == 8        # 5 + 3

    ok, desc = lr.prereq_met("Paladin", {"str": 13, "cha": 13})
    assert ok and "Strength" in desc and "Charisma" in desc
    assert not lr.prereq_met("Paladin", {"str": 13, "cha": 10})[0]
    assert lr.prereq_met("Fighter", {"str": 8, "dex": 14})[0]   # OR
    assert not lr.prereq_met("Fighter", {"str": 8, "dex": 8})[0]
    print("  rules OK")


def test_flow():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = main.App()
    template = (ROOT / "data" / "characters_template.csv").read_text(encoding="utf-8")
    assert app.db.import_csv("characters_template.csv", template)["inserted"] == 1
    app.show_page("character_sheet")
    app.update_idletasks()
    cid = app.active_character_id

    # ── Features: pull from reference ────────────────────────────────────────
    app.show_page("features")
    app.update_idletasks()
    feats = app._pages["features"]
    before = len(app.db.list_character_features(cid))
    added = feats.pull_from_reference()
    assert added >= 1, "should pull at least one class/race/background feature"
    after = app.db.list_character_features(cid)
    assert len(after) == before + added
    # A Wizard class feature should now exist.
    assert any((f.get("source_type") or f.get("source_name") or "").lower() == "class"
               and f["name"].lower() == "wizard" for f in after), \
        [f["name"] for f in after]
    feats.refresh()  # render with pulled features
    print(f"  features pulled: {added}")

    # ── Background tab renders + persists ────────────────────────────────────
    app.show_page("background")
    app.update_idletasks()
    bg = app._pages["background"]
    bg._editor.delete("1.0", "end")
    bg._editor.insert("1.0", "## Bonds\nProtect the village.")
    bg._persist()
    assert "Protect the village" in app.db.get_character(cid)["background_info"]
    print("  background OK")

    # ── Single-class level up (Wizard 5 -> 6) ────────────────────────────────
    app.show_page("level_up")
    app.update_idletasks()
    lvl = app._pages["level_up"]
    hp0 = app.db.get_character(cid)["hp_max"]
    res = lvl.level_up("Wizard", hp_method="average")   # CON 14 (+2), d6 avg 4 -> +6
    assert res["level"] == 6, res
    assert res["hp_gain"] == 6, res
    after_c = app.db.get_character(cid)
    assert after_c["hp_max"] == hp0 + 6
    wiz = next(c for c in after_c["classes"] if c["class"] == "Wizard")
    assert wiz["level"] == 6
    assert after_c["total_level"] == 8                  # was 7 (Wiz5/Cleric2)
    assert after_c["proficiency_bonus"] == 3            # level 8 -> +3

    # ASI at a Wizard ASI level (level 8): +2 INT (18 -> 20, capped)
    lvl.level_up("Wizard", hp_method="average")          # 6->7
    res2 = lvl.level_up("Wizard", hp_method="average", asi={"int": 2})  # 7->8 (ASI)
    assert res2["level"] == 8
    assert app.db.get_character(cid)["int"] == 20, app.db.get_character(cid)["int"]

    # ── Multiclass: add Fighter (meets DEX 13? Lyra DEX 16) ───────────────────
    lvl.refresh()
    ok, _ = lvl.check_multiclass("Fighter")
    assert ok, "Lyra (DEX 16) meets Fighter's DEX-or-STR prereq"
    res3 = lvl.level_up("Fighter")                       # new class at level 1
    assert res3["level"] == 1
    classes = {c["class"]: c for c in app.db.get_character(cid)["classes"]}
    assert "Fighter" in classes and classes["Fighter"]["level"] == 1

    # Fighter to 3 -> subclass required; pick one and confirm it's stored.
    lvl.level_up("Fighter")                              # ->2
    subs = sorted({r["name"] for r in app.db.list_char_options(category="subclass")
                   if (r.get("parent") or "").lower() == "fighter"})
    res4 = lvl.level_up("Fighter", subclass=subs[0])     # ->3 with subclass
    assert res4["subclass"] == subs[0]
    fighter = next(c for c in app.db.get_character(cid)["classes"] if c["class"] == "Fighter")
    assert fighter["subclass"] == subs[0]
    # Subclass feature pulled.
    assert any(f["name"] == subs[0] for f in app.db.list_character_features(cid))

    # ── Reversibility: level down Fighter ────────────────────────────────────
    hp_before = app.db.get_character(cid)["hp_max"]
    lvl.level_down("Fighter")                            # 3 -> 2
    fighter = next(c for c in app.db.get_character(cid)["classes"] if c["class"] == "Fighter")
    assert fighter["level"] == 2
    assert app.db.get_character(cid)["hp_max"] < hp_before

    # Spell slots recompute from the new class mix automatically.
    from pages import spell_rules
    slots = spell_rules.spell_slots(app.db.get_character(cid)["classes"])
    assert slots, "a multiclass caster should still have slots"

    print("  leveling OK")
    print("integrity_check:", app.db.conn.execute("PRAGMA integrity_check").fetchone()[0])
    app.update_idletasks()
    app.destroy()


def main_test() -> int:
    test_rules()
    test_flow()
    print("\nLEVELING TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = main_test()
    finally:
        import shutil
        shutil.rmtree(os.environ["APPDATA"], ignore_errors=True)
    sys.exit(rc)
