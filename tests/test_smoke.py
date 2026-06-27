"""Full smoke test for Arcane Sword v1.

Creates a character from CSV, levels it up (including a multiclass), picks a
spell, manages inventory, rests, exercises CSV + JSON export/import, confirms
the data survives a simulated relaunch (a fresh DB connection on the same file),
and that the global reset keeps the reference compendium.

Run:  python tests/test_smoke.py
"""
import os
import sys
import tempfile
from pathlib import Path

APPDATA = tempfile.mkdtemp(prefix="arcane_sword_smoke_")
os.environ["APPDATA"] = APPDATA
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402
import db as db_module  # noqa: E402
import main  # noqa: E402
from pages import rest_logic, spell_rules  # noqa: E402


def run() -> int:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = main.App()

    # 1) Create a character from CSV.
    template = (ROOT / "data" / "characters_template.csv").read_text(encoding="utf-8")
    assert app.db.import_csv("characters_template.csv", template)["inserted"] == 1
    app.show_page("character_sheet")
    app.update_idletasks()
    cid = app.active_character_id
    assert cid and app.db.get_character(cid)["total_level"] == 7

    # 2) Level up (single-class) and multiclass.
    lvl = app._pages["level_up"]
    lvl.refresh()
    lvl.level_up("Wizard", hp_method="average")          # Wizard 5 -> 6
    assert lvl.check_multiclass("Fighter")[0]
    lvl.level_up("Fighter")                              # add Fighter 1
    c = app.db.get_character(cid)
    assert c["total_level"] == 9
    assert {k["class"] for k in c["classes"]} == {"Wizard", "Cleric", "Fighter"}
    assert c["proficiency_bonus"] == 4                  # level 9 -> +4

    # 3) Pick a spell via the Available tab.
    av = app._pages["spells_avail"]
    av.refresh()
    target = next(s for s in av._spells if s["name"] == "Light")
    av._set_flag(target, "known")
    assert any(cs["spell_name"] == "Light" for cs in app.db.list_character_spells(cid))
    # Slots are derived from the new class mix.
    assert spell_rules.spell_slots(c["classes"]), "should have spell slots"

    # 4) Manage inventory.
    invp = app._pages["inventory"]
    invp.refresh()
    invp._add_item("Bag of Holding", None, 1)
    bag = next(r for r in invp._inv if r["item_name"] == "Bag of Holding")
    invp._toggle(bag, "equipped")
    assert next(r for r in invp._inv if r["id"] == bag["id"])["equipped"] == 1

    # 5) Rest: spend a hit die on a short rest, then a long rest restores HP.
    app.db.update_character(cid, {**app.db.get_character(cid), "hp_current": 1})
    sd = rest_logic.spend_hit_die(app.db, cid)
    assert sd["spent"] and app.db.get_character(cid)["hp_current"] > 1
    lr_res = rest_logic.long_rest(app.db, cid)
    full = app.db.get_character(cid)
    assert full["hp_current"] == full["hp_max"] == lr_res["hp"]
    assert full["hit_dice_used"] < full["total_level"]   # recovered some hit dice

    # 6) Export CSV + JSON; re-import for round-trips.
    csv_text = app.db.export_character_csv(cid)
    assert "Lyra Moonwhisper" in csv_text
    res = app.db.import_csv("lyra.csv", csv_text)
    assert res["table"] == "characters" and res["inserted"] == 1, res

    json_text = app.db.export_character_json(cid)
    clone_id = app.db.import_character_json(json_text)
    clone = app.db.get_character(clone_id)
    orig = app.db.get_character(cid)
    assert clone["name"] == orig["name"]
    assert clone["total_level"] == orig["total_level"]
    assert len(clone["spells"]) == len(orig["spells"])
    assert len(clone["inventory"]) == len(orig["inventory"])
    assert len(app.db.list_characters()) == 3            # original + CSV + JSON clones

    # Snapshot values to verify after "relaunch".
    snap = {"hp_max": orig["hp_max"], "total_level": orig["total_level"],
            "spells": len(orig["spells"]), "inventory": len(orig["inventory"]),
            "characters": len(app.db.list_characters())}

    # Self-heal/backup system is active: a backup snapshot exists.
    backups = list((Path(APPDATA) / "ArcaneSword" / "backups").glob("arcane-sword_*.db"))
    assert backups, "expected a rotating backup snapshot"

    app.update_idletasks()
    app.destroy()

    # 7) Simulated relaunch: a brand-new DB connection on the same file.
    db2 = db_module.Database()
    assert db2.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert len(db2.list_characters()) == snap["characters"], "characters did not persist"
    reloaded = db2.get_character(cid)
    assert reloaded["hp_max"] == snap["hp_max"]
    assert reloaded["total_level"] == snap["total_level"]
    assert len(reloaded["spells"]) == snap["spells"]
    assert len(reloaded["inventory"]) == snap["inventory"]
    assert any(cs["spell_name"] == "Light" for cs in reloaded["spells"])
    print("  persistence across relaunch OK")

    # 8) Global reset keeps the compendium.
    spells_before = db2.conn.execute("SELECT COUNT(*) FROM spells").fetchone()[0]
    erased = db2.wipe_all_characters()
    assert erased == snap["characters"]
    assert db2.character_count() == 0
    assert db2.conn.execute("SELECT COUNT(*) FROM spells").fetchone()[0] == spells_before, \
        "reference compendium must be kept after reset"
    print(f"  reset erased {erased} character(s); compendium intact ({spells_before} spells)")

    print("\nFULL SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = run()
    finally:
        import shutil
        shutil.rmtree(APPDATA, ignore_errors=True)
    sys.exit(rc)
