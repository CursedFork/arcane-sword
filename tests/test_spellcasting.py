"""Tests for the spellcasting tabs: pure slot/prepared rules + headless render
of the Available and Spellbook pages against a throwaway database.

Run:  python tests/test_spellcasting.py
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="arcane_sword_spell_test_")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk  # noqa: E402
import main  # noqa: E402
from pages import spell_rules as sr  # noqa: E402
from pages.spellcasting import PACT_SLOT_LEVEL_KEY  # noqa: E402


def _cl(*items):
    return [{"class": c, "subclass": s, "level": l} for c, s, l in items]


def test_rules():
    lyra = _cl(("Wizard", "Evocation", 5), ("Cleric", "Life Domain", 2))
    assert sr.caster_level(lyra) == 7
    assert sr.spell_slots(lyra) == {1: 4, 2: 3, 3: 3, 4: 1}, sr.spell_slots(lyra)
    assert sr.pact_magic(lyra) is None
    assert sr.prepared_max(lyra, {"int": 18, "wis": 12, "cha": 10}) == 12

    assert sr.spell_slots(_cl(("Wizard", "", 5))) == {1: 4, 2: 3, 3: 2}
    assert sr.spell_slots(_cl(("Paladin", "", 5))) == {1: 3}           # half, rounded down
    assert sr.spell_slots(_cl(("Artificer", "", 5))) == {1: 4, 2: 2}   # rounds up -> CL3
    assert sr.spell_slots(_cl(("Fighter", "Eldritch Knight", 3))) == {1: 2}
    assert sr.spell_slots(_cl(("Fighter", "Champion", 5))) == {}       # non-caster

    w5 = _cl(("Warlock", "", 5))
    assert sr.spell_slots(w5) == {}                                    # Warlock not in table
    assert sr.pact_magic(w5) == {"count": 2, "level": 3}
    assert sr.pact_magic(_cl(("Warlock", "", 1))) == {"count": 1, "level": 1}
    assert sr.pact_magic(_cl(("Warlock", "", 17))) == {"count": 4, "level": 5}
    print("  rules OK")


def test_pages():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = main.App()

    template = (ROOT / "data" / "characters_template.csv").read_text(encoding="utf-8")
    assert app.db.import_csv("characters_template.csv", template)["inserted"] == 1

    # Character Sheet sets the shared active id; spell tabs read it.
    app.show_page("character_sheet")
    app.update_idletasks()
    cid = app.active_character_id
    assert cid is not None

    # ── Available tab ────────────────────────────────────────────────────────
    app.show_page("spells_avail")
    app.update_idletasks()
    avail = app._pages["spells_avail"]
    names = [s["name"] for s in avail._spells]
    assert names, "expected spells available to Wizard/Cleric"
    assert "Fireball" in names, "Fireball (Wizard) should be available"
    # The template already knows/prepares some spells; Fireball is indexed.
    assert "fireball" in avail._index

    # Add a brand-new spell via the row action ("Light" — not in the template).
    target = next(s for s in avail._spells if s["name"] == "Light")
    assert "light" not in avail._index
    avail._set_flag(target, "known")
    after = {cs["spell_name"].lower(): cs for cs in app.db.list_character_spells(cid)}
    assert "light" in after and after["light"]["known"] == 1
    # ref-id matched to the compendium so full text is available
    assert after["light"]["spell_ref_id"], "new spell should match the reference table"

    # ── Spellbook tab ────────────────────────────────────────────────────────
    app.show_page("spellbook")
    app.update_idletasks()
    book = app._pages["spellbook"]

    prepared, max_prep = book._prepared_counts()
    # Template prepares Shield, Magic Missile, Fireball, Cure Wounds (all L>0).
    assert prepared == 4, prepared
    assert max_prep == 12, max_prep

    # Slot tracker: expend two L1 slots, persists `used` only.
    book._spend_slot(1, +1)
    book._spend_slot(1, +1)
    used = {r["level"]: r["used"] for r in app.db.list_character_spell_slots(cid)}
    assert used.get(1) == 2, used
    book._spend_slot(1, -1)            # restore one
    used = {r["level"]: r["used"] for r in app.db.list_character_spell_slots(cid)}
    assert used.get(1) == 1, used
    # Can't exceed total (4 at L1) or go below 0.
    for _ in range(10):
        book._spend_slot(1, +1)
    used = {r["level"]: r["used"] for r in app.db.list_character_spell_slots(cid)}
    assert used[1] == 4, used

    # Toggle prepared off for Fireball -> prepared count drops to 3.
    fb = next(cs for cs in app.db.list_character_spells(cid)
              if cs["spell_name"] == "Fireball")
    book._toggle(fb, "prepared")
    prepared2, _ = book._prepared_counts()
    assert prepared2 == 3, prepared2

    # Prepared-max override persists and wins over the derived value.
    book._char["prepared_max_override"] = 5
    app.db.update_character(cid, book._char)
    book.refresh()
    assert book._prepared_counts()[1] == 5

    # Remove a spell.
    light = next(cs for cs in app.db.list_character_spells(cid)
                 if cs["spell_name"] == "Light")
    book._remove(light)
    assert "light" not in {cs["spell_name"].lower()
                           for cs in app.db.list_character_spells(cid)}

    # ── Warlock pact slots render + persist ──────────────────────────────────
    wcid = app.db.create_character({"name": "Hexblade", "cha": 16})
    app.db.create_character_class(wcid, {"class": "Warlock", "subclass": "Hexblade", "level": 5})
    app.active_character_id = wcid
    book.refresh()
    book._spend_slot(PACT_SLOT_LEVEL_KEY, +1)
    pact_used = {r["level"]: r["used"] for r in app.db.list_character_spell_slots(wcid)}
    assert pact_used.get(PACT_SLOT_LEVEL_KEY) == 1, pact_used

    print("  pages OK")
    print("integrity_check:", app.db.conn.execute("PRAGMA integrity_check").fetchone()[0])
    print("user_version:", app.db.conn.execute("PRAGMA user_version").fetchone()[0])
    app.update_idletasks()
    app.destroy()


def main_test() -> int:
    test_rules()
    test_pages()
    print("\nSPELLCASTING TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        rc = main_test()
    finally:
        import shutil
        shutil.rmtree(os.environ["APPDATA"], ignore_errors=True)
    sys.exit(rc)
