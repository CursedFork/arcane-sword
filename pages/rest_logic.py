"""Rest logic — shared by the Rest tab and the Character Sheet's quick-rest
buttons. Functions take (db, character_id) and persist immediately.

Long rest: HP to max (temp HP cleared), recover half your total hit dice,
restore all spell slots, reset death saves, and refresh both short- and
long-recharge resources.
Short rest: restore short-recharge resources; spend_hit_die() heals and uses a
hit die.
"""
from db import Database
from pages import levelup_rules as lr


def long_rest(db, cid: int) -> dict:
    c = db.get_character(cid)
    if not c:
        return {}
    total_hd = c.get("total_level", 0)
    recovered_hd = max(1, total_hd // 2) if total_hd else 0
    c["hp_current"] = c["hp_max"]
    c["hp_temp"] = 0
    c["hit_dice_used"] = max(0, int(c.get("hit_dice_used", 0)) - recovered_hd)
    c["death_save_success"] = 0
    c["death_save_fail"] = 0
    db.update_character(cid, c)

    slots_reset = 0
    for r in db.list_character_spell_slots(cid):
        if r.get("used"):
            db.update_character_spell_slot(r["id"], {"used": 0})
            slots_reset += 1
    res_reset = 0
    for r in db.list_character_resources(cid):  # long rest restores short + long
        if r.get("current") != r.get("maximum"):
            db.update_character_resource(r["id"], {"current": r.get("maximum", 0)})
            res_reset += 1
    return {"hp": c["hp_max"], "hit_dice_recovered": recovered_hd,
            "slots_reset": slots_reset, "resources_reset": res_reset}


def short_rest(db, cid: int) -> dict:
    res_reset = 0
    for r in db.list_character_resources(cid):
        if (r.get("recharge") or "").lower() == "short" and r.get("current") != r.get("maximum"):
            db.update_character_resource(r["id"], {"current": r.get("maximum", 0)})
            res_reset += 1
    return {"resources_reset": res_reset}


def hit_dice_status(db, cid: int) -> tuple[int, int]:
    """(remaining, total) hit dice."""
    c = db.get_character(cid)
    total = c.get("total_level", 0) if c else 0
    used = int(c.get("hit_dice_used", 0)) if c else 0
    return max(0, total - used), total


def spend_hit_die(db, cid: int, roll: int | None = None) -> dict:
    """Spend one hit die to heal (rolled or average of the character's largest
    hit die) + CON modifier. No-op if no hit dice remain."""
    c = db.get_character(cid)
    if not c:
        return {"spent": False}
    total, used = c.get("total_level", 0), int(c.get("hit_dice_used", 0))
    if used >= total:
        return {"spent": False, "reason": "no hit dice remaining"}
    dice = [lr.hit_die(k["class"]) for k in c["classes"]] or [8]
    die = max(dice)
    base = roll if roll else die // 2 + 1
    heal = max(1, int(base) + Database.ability_mod(c.get("con", 10)))
    c["hp_current"] = min(c["hp_max"], int(c.get("hp_current", 0)) + heal)
    c["hit_dice_used"] = used + 1
    db.update_character(cid, c)
    return {"spent": True, "healed": heal, "die": f"d{die}"}
