"""Smoke test: import a sample character via import_csv, read it back with
get_character(). Runs against a throwaway database in a temp APPDATA so it never
touches the user's real Arcane Sword (or Arcane Shield) data.

Run:  python tests/test_character_import.py
"""
import os
import sys
import tempfile
from pathlib import Path

# Point the DB at a temp dir BEFORE importing db (db._db_path reads %APPDATA%).
_TMP = tempfile.mkdtemp(prefix="arcane_sword_test_")
os.environ["APPDATA"] = _TMP

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import db  # noqa: E402


def main() -> int:
    database = db.Database()

    # Use the shipped template as the sample import (also validates the template).
    template = ROOT / "data" / "characters_template.csv"
    text = template.read_text(encoding="utf-8")

    # Detection should resolve to the characters table from the header alone.
    assert db._detect_table(set(text.splitlines()[0].split(",")), "characters_template.csv") == "characters"

    result = database.import_csv("characters_template.csv", text)
    print("import result:", result)
    assert result["table"] == "characters", result
    assert result["inserted"] == 1, result
    assert not result["errors"], result["errors"]

    chars = database.list_characters()
    assert len(chars) == 1, chars
    cid = chars[0]["id"]
    assert chars[0]["total_level"] == 7, chars[0]["total_level"]
    assert chars[0]["class_summary"], chars[0]["class_summary"]

    c = database.get_character(cid)
    assert c is not None

    # ── Core fields ──────────────────────────────────────────────────────────
    assert c["name"] == "Lyra Moonwhisper", c["name"]
    assert c["player_name"] == "Andrew"
    assert c["race"] == "Elf" and c["subrace"] == "High Elf"
    assert c["int"] == 18 and c["dex"] == 16 and c["str"] == 8
    assert c["hp_max"] == 44 and c["hp_current"] == 44
    assert c["ac"] == 13 and c["speed"] == 30
    assert c["inspiration"] == 1 and c["xp"] == 14000

    # ── Derived helpers ──────────────────────────────────────────────────────
    assert db.Database.ability_mod(18) == 4
    assert db.Database.ability_mod(8) == -1
    assert database.total_level(cid) == 7
    assert database.derived_proficiency_bonus(cid) == 3  # level 7 -> +3
    assert c["proficiency_bonus"] == 3

    # ── Multiclass ───────────────────────────────────────────────────────────
    classes = {row["class"]: row for row in c["classes"]}
    assert classes["Wizard"]["level"] == 5
    assert classes["Wizard"]["subclass"] == "Evocation", classes["Wizard"]
    assert classes["Cleric"]["level"] == 2
    assert classes["Cleric"]["subclass"] == "Life Domain"

    # ── Skills (expertise vs proficient) ─────────────────────────────────────
    skills = {row["skill"]: row["proficiency"] for row in c["skills"]}
    assert skills["Investigation"] == "expertise", skills
    assert skills["Arcana"] == "proficient", skills

    # ── Saves ────────────────────────────────────────────────────────────────
    saves = {row["ability"] for row in c["saves"] if row["proficient"]}
    assert saves == {"INT", "WIS"}, saves

    # ── Proficiencies by kind ────────────────────────────────────────────────
    profs: dict[str, list] = {}
    for row in c["proficiencies"]:
        profs.setdefault(row["kind"], []).append(row["name"])
    assert "Elvish" in profs["language"], profs
    assert "Daggers" in profs["weapon"], profs
    assert "Light Armor" in profs["armor"], profs
    assert "Calligrapher's Supplies" in profs["tool"], profs

    # ── Defenses (JSON) + conditions ─────────────────────────────────────────
    assert c["defenses"]["resist"] == ["Fire"], c["defenses"]
    assert c["defenses"]["vuln"] == ["Cold"], c["defenses"]
    assert c["conditions"] == [], c["conditions"]

    # ── Inventory (ref-id matched where possible) ────────────────────────────
    inv = {row["item_name"]: row for row in c["inventory"]}
    assert inv["Potion of Healing"]["quantity"] == 3, inv
    assert inv["Spellbook"]["quantity"] == 1

    # ── Spells (known / prepared, ref-id matched) ────────────────────────────
    spells = {row["spell_name"]: row for row in c["spells"]}
    assert spells["Fireball"]["known"] == 1 and spells["Fireball"]["prepared"] == 1, spells["Fireball"]
    assert spells["Counterspell"]["known"] == 1 and spells["Counterspell"]["prepared"] == 0
    matched = [s for s in c["spells"] if s["spell_ref_id"]]
    assert matched, "expected at least one spell matched to the reference compendium"
    print(f"  spells matched to compendium: {len(matched)}/{len(c['spells'])}")
    inv_matched = [i for i in c["inventory"] if i["item_ref_id"]]
    print(f"  inventory matched to compendium: {len(inv_matched)}/{len(c['inventory'])}")

    # ── Features + notes + background_info ────────────────────────────────────
    feats = {row["name"]: row for row in c["features"]}
    assert feats["Arcane Recovery"]["source_name"] == "Class", feats["Arcane Recovery"]
    assert "Darkvision" in feats
    assert len(c["notes"]) == 1 and "Waterdeep" in c["notes"][0]["body_md"]
    assert "Personality" in c["background_info"]

    # ── Cascade delete ───────────────────────────────────────────────────────
    database.delete_character(cid)
    assert database.get_character(cid) is None
    assert database.conn.execute("SELECT COUNT(*) FROM character_classes").fetchone()[0] == 0, \
        "child rows should be cascade-deleted"

    print("integrity_check:", database.conn.execute("PRAGMA integrity_check").fetchone()[0])
    print("user_version:", database.conn.execute("PRAGMA user_version").fetchone()[0])
    print("\nALL CHARACTER-IMPORT TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    finally:
        # Best-effort cleanup of the throwaway DB.
        import shutil
        shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(rc)
