"""Level-up rules — pure helpers (no UI) for the 5e leveling flow: hit dice,
multiclass prerequisites, subclass timing, ASI levels, and HP gain.
"""

HIT_DICE = {
    "barbarian": 12,
    "fighter": 10, "paladin": 10, "ranger": 10,
    "artificer": 8, "bard": 8, "cleric": 8, "druid": 8, "monk": 8,
    "rogue": 8, "warlock": 8,
    "sorcerer": 6, "wizard": 6,
}

# Multiclass ability prerequisites (PHB). "all" must all be met; "any" needs one.
MULTICLASS_PREREQS = {
    "barbarian": {"all": [("str", 13)]},
    "bard": {"all": [("cha", 13)]},
    "cleric": {"all": [("wis", 13)]},
    "druid": {"all": [("wis", 13)]},
    "fighter": {"any": [("str", 13), ("dex", 13)]},
    "monk": {"all": [("dex", 13), ("wis", 13)]},
    "paladin": {"all": [("str", 13), ("cha", 13)]},
    "ranger": {"all": [("dex", 13), ("wis", 13)]},
    "rogue": {"all": [("dex", 13)]},
    "sorcerer": {"all": [("cha", 13)]},
    "warlock": {"all": [("cha", 13)]},
    "wizard": {"all": [("int", 13)]},
    "artificer": {"all": [("int", 13)]},
}

# Level at which a class chooses its subclass.
SUBCLASS_LEVEL = {
    "cleric": 1, "sorcerer": 1, "warlock": 1,
    "wizard": 2, "druid": 2,
}
DEFAULT_SUBCLASS_LEVEL = 3

# ASI levels by class (extra ones for Fighter and Rogue).
_BASE_ASI = {4, 8, 12, 16, 19}
_EXTRA_ASI = {"fighter": {6, 14}, "rogue": {10}}

CLASS_NAMES = ["Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
               "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]

_ABBR = {"str": "Strength", "dex": "Dexterity", "con": "Constitution",
         "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}


def hit_die(class_name: str) -> int:
    return HIT_DICE.get((class_name or "").strip().lower(), 8)


def avg_hp(class_name: str) -> int:
    """The fixed 'take the average' HP value for a class hit die (d8 -> 5)."""
    return hit_die(class_name) // 2 + 1


def asi_levels(class_name: str) -> set:
    return _BASE_ASI | _EXTRA_ASI.get((class_name or "").strip().lower(), set())


def is_asi_level(class_name: str, new_class_level: int) -> bool:
    return new_class_level in asi_levels(class_name)


def subclass_level(class_name: str) -> int:
    return SUBCLASS_LEVEL.get((class_name or "").strip().lower(), DEFAULT_SUBCLASS_LEVEL)


def needs_subclass(class_name: str, new_class_level: int, has_subclass: bool) -> bool:
    return (not has_subclass) and new_class_level >= subclass_level(class_name)


def prereq_met(class_name: str, abilities: dict) -> tuple[bool, str]:
    """Whether a character meets the multiclass prerequisites for a class.
    Returns (ok, human-readable requirement description)."""
    spec = MULTICLASS_PREREQS.get((class_name or "").strip().lower())
    if not spec:
        return True, ""
    def score(a):
        try:
            return int(abilities.get(a, 0) or 0)
        except (TypeError, ValueError):
            return 0
    if "all" in spec:
        ok = all(score(a) >= n for a, n in spec["all"])
        desc = " and ".join(f"{_ABBR[a]} {n}" for a, n in spec["all"])
        return ok, desc
    ok = any(score(a) >= n for a, n in spec["any"])
    desc = " or ".join(f"{_ABBR[a]} {n}" for a, n in spec["any"])
    return ok, desc


def hp_gain(class_name: str, con_mod: int, method: str = "average",
            roll: int | None = None) -> int:
    """HP gained for one level: (rolled or average die) + CON modifier, min 1."""
    if method == "roll" and roll is not None:
        base = int(roll)
    else:
        base = avg_hp(class_name)
    return max(1, base + int(con_mod))
