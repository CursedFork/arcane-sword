"""Spellcasting rules — pure helpers (no UI) for deriving slots and prepared
counts from a character's classes. Kept tkinter-free so it can be unit-tested.

Slot totals follow the 5e *multiclass spellcaster* table (PHB p.165): sum a
caster level from each class's contribution, then look up the row. Warlock
Pact Magic is tracked separately. Only `used` is persisted per level; totals
are always recomputed here.
"""

FULL_CASTERS = {"bard", "cleric", "druid", "sorcerer", "wizard"}
HALF_CASTERS = {"paladin", "ranger"}            # round levels DOWN when multiclassing
# Third-casters are subclasses of Fighter / Rogue.
THIRD_SUBCLASSES = {
    "fighter": "eldritch knight",
    "rogue": "arcane trickster",
}

# Spellcasting ability per class (for prepared-count + spell save/attack later).
CASTING_ABILITY = {
    "artificer": "int", "wizard": "int",
    "cleric": "wis", "druid": "wis", "ranger": "wis",
    "bard": "cha", "paladin": "cha", "sorcerer": "cha", "warlock": "cha",
}

# Classes that PREPARE a spell list (vs. knowing a fixed set). Value is the
# fraction of class level that counts toward the prepared maximum.
PREPARING_CLASSES = {
    "wizard": 1.0, "cleric": 1.0, "druid": 1.0,
    "paladin": 0.5, "artificer": 0.5,
}

# Multiclass spellcaster slots: caster level -> [L1..L9].
MULTICLASS_SLOTS = {
    1:  [2, 0, 0, 0, 0, 0, 0, 0, 0],
    2:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
    3:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
    4:  [4, 3, 0, 0, 0, 0, 0, 0, 0],
    5:  [4, 3, 2, 0, 0, 0, 0, 0, 0],
    6:  [4, 3, 3, 0, 0, 0, 0, 0, 0],
    7:  [4, 3, 3, 1, 0, 0, 0, 0, 0],
    8:  [4, 3, 3, 2, 0, 0, 0, 0, 0],
    9:  [4, 3, 3, 3, 1, 0, 0, 0, 0],
    10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
    11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
    12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
    13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
    14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
    15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
    16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
    17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
    19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
    20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
}


def ability_mod(score) -> int:
    try:
        return (int(score) - 10) // 2
    except (TypeError, ValueError):
        return 0


def _norm(c: dict) -> tuple[str, str, int]:
    name = (c.get("class") or "").strip().lower()
    sub = (c.get("subclass") or "").strip().lower()
    try:
        lvl = int(c.get("level") or 0)
    except (TypeError, ValueError):
        lvl = 0
    return name, sub, lvl


def caster_level(classes: list[dict]) -> int:
    """Combined caster level for the multiclass slot table (excludes Warlock)."""
    total = 0
    for c in classes:
        name, sub, lvl = _norm(c)
        if name in FULL_CASTERS:
            total += lvl
        elif name == "artificer":
            total += (lvl + 1) // 2          # Artificer rounds UP, even multiclassing
        elif name in HALF_CASTERS:
            total += lvl // 2                # Paladin/Ranger round down
        elif THIRD_SUBCLASSES.get(name) and THIRD_SUBCLASSES[name] in sub:
            total += lvl // 3                # Eldritch Knight / Arcane Trickster
    return total


def spell_slots(classes: list[dict]) -> dict[int, int]:
    """Map of spell level (1..9) -> total slots, from the multiclass table.
    Levels with zero slots are omitted."""
    cl = caster_level(classes)
    if cl <= 0:
        return {}
    arr = MULTICLASS_SLOTS[min(cl, 20)]
    return {i + 1: arr[i] for i in range(9) if arr[i] > 0}


def warlock_level(classes: list[dict]) -> int:
    return sum(lvl for name, _sub, lvl in map(_norm, classes) if name == "warlock")


def pact_magic(classes: list[dict]) -> dict | None:
    """Warlock Pact Magic: {'count': slots, 'level': slot spell-level} or None."""
    wl = warlock_level(classes)
    if wl <= 0:
        return None
    count = 1 if wl == 1 else 2 if wl <= 10 else 3 if wl <= 16 else 4
    level = min(5, (wl + 1) // 2)
    return {"count": count, "level": level}


def prepared_max(classes: list[dict], abilities: dict) -> int:
    """A reasonable 'spells you can prepare' maximum: for each preparing class,
    spellcasting-ability modifier + (full or half) class level, min 1 each."""
    total = 0
    for c in classes:
        name, _sub, lvl = _norm(c)
        if name not in PREPARING_CLASSES or lvl <= 0:
            continue
        frac = PREPARING_CLASSES[name]
        lvl_part = lvl if frac >= 1.0 else (
            (lvl + 1) // 2 if name == "artificer" else lvl // 2)
        mod = ability_mod(abilities.get(CASTING_ABILITY.get(name, ""), 10))
        total += max(1, mod + lvl_part)
    return max(0, total)
