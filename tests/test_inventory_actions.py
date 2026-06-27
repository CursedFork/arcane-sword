"""Tests for the Inventory and Actions tabs: weapon rules + headless render and
mutation against a throwaway database.

Run:  python tests/test_inventory_actions.py
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="arcane_sword_inv_test_")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402
import main  # noqa: E402
from pages import weapon_rules as wr  # noqa: E402


def test_weapon_rules():
    ls = wr.find_weapon("Longsword")
    assert ls and ls["damage"] == "1d8"
    assert wr.find_weapon("longswords")["name"] == "Longsword"   # plural/case
    assert wr.find_weapon("Potion of Healing") is None

    abil = {"str": 16, "dex": 12}      # str +3, dex +1
    a = wr.weapon_attack(ls, abil, 3, ["Martial Weapons"])
    assert a["proficient"] and a["ability"] == "str" and a["bonus"] == 6  # +3 +3
    assert a["damage"] == "1d8 +3 slashing", a["damage"]

    rapier = wr.find_weapon("Rapier")  # finesse -> better of str/dex
    a2 = wr.weapon_attack(rapier, {"str": 10, "dex": 18}, 2, ["Rapier"])
    assert a2["ability"] == "dex" and a2["bonus"] == 6, a2          # +4 +2

    bow = wr.find_weapon("Longbow")    # ranged -> dex; not proficient here
    a3 = wr.weapon_attack(bow, {"str": 14, "dex": 16}, 3, ["Simple Weapons"])
    assert a3["ability"] == "dex" and a3["proficient"] is False and a3["bonus"] == 3

    assert wr.is_proficient(ls, ["All weapons"]) is True
    assert wr.parse_weight("A heavy chest. Weight: 25 lb.") == 25.0
    print("  weapon rules OK")


def test_pages():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = main.App()
    template = (ROOT / "data" / "characters_template.csv").read_text(encoding="utf-8")
    assert app.db.import_csv("characters_template.csv", template)["inserted"] == 1
    app.show_page("character_sheet")
    app.update_idletasks()
    cid = app.active_character_id

    # ── Inventory ────────────────────────────────────────────────────────────
    app.show_page("inventory")
    app.update_idletasks()
    inv = app._pages["inventory"]
    names = {r["item_name"] for r in inv._inv}
    assert {"Quarterstaff", "Spellbook", "Potion of Healing"} <= names, names

    # Add a custom item.
    inv._add_item("Mysterious Orb", None, 2)
    assert any(r["item_name"] == "Mysterious Orb" and r["quantity"] == 2 for r in inv._inv)

    # Quantity +/-
    orb = next(r for r in inv._inv if r["item_name"] == "Mysterious Orb")
    inv._set_qty(orb, +1)
    orb = next(r for r in inv._inv if r["item_name"] == "Mysterious Orb")
    assert orb["quantity"] == 3

    # Equip the quarterstaff (used by Actions).
    qs = next(r for r in inv._inv if r["item_name"] == "Quarterstaff")
    inv._toggle(qs, "equipped")
    assert next(r for r in inv._inv if r["item_name"] == "Quarterstaff")["equipped"] == 1

    # Attunement cap: attune 3 items, the 4th is refused.
    attunable = [r for r in inv._inv][:3]
    for r in attunable:
        fresh = next(x for x in inv._inv if x["id"] == r["id"])
        if not fresh.get("attuned"):
            inv._toggle_attuned(fresh)
    assert inv._attuned_count() == 3, inv._attuned_count()
    fourth = next((r for r in inv._inv if not r.get("attuned")), None)
    assert fourth is not None
    inv._toggle_attuned(fourth)  # should warn + refuse (no dialog in headless = no-op path)
    assert inv._attuned_count() == 3, "attunement cap must hold at 3"

    # Weight estimate includes the known quarterstaff weight (4 lb).
    weight, unknown = inv._total_weight()
    assert weight >= 4.0, (weight, unknown)
    print("  inventory OK (attuned cap holds, weight estimated)")

    # ── Actions ──────────────────────────────────────────────────────────────
    app.show_page("actions")
    app.update_idletasks()
    act = app._pages["actions"]

    attacks = {a["name"]: a for a in act._weapon_attacks()}
    assert "Quarterstaff" in attacks, attacks
    qa = attacks["Quarterstaff"]
    # Lyra STR 8 (-1), proficient with Quarterstaffs, prof +3 -> +2 to hit; 1d6 -1 bludgeoning
    assert qa["ability"] == "str" and qa["proficient"] and qa["bonus"] == 2, qa
    assert qa["damage"] == "1d6 -1 bludgeoning", qa["damage"]

    # Spell actions grouped by casting time — Fire Bolt is an Action cantrip.
    spell_groups = act._spell_actions()
    assert "Fire Bolt" in spell_groups["Action"], spell_groups["Action"]

    # Custom attack + custom action persist as character_features.
    app.db.create_character_feature(cid, {"source_type": "attack", "name": "Eldritch Blast",
                                          "description": "+7||1d10 force"})
    app.db.create_character_feature(cid, {"source_type": "bonus", "name": "Misty Step Dash",
                                          "description": "teleport 30 ft"})
    act.refresh()
    assert any(m["name"] == "Eldritch Blast" for m in act._manual_attacks())
    assert any(f["name"] == "Misty Step Dash" for f in act._feature_actions()["Bonus Action"])

    print("  actions OK")
    print("integrity_check:", app.db.conn.execute("PRAGMA integrity_check").fetchone()[0])
    app.update_idletasks()
    app.destroy()


def main_test() -> int:
    test_weapon_rules()
    test_pages()
    print("\nINVENTORY + ACTIONS TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = main_test()
    finally:
        import shutil
        shutil.rmtree(os.environ["APPDATA"], ignore_errors=True)
    sys.exit(rc)
