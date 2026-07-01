"""PHB lookup tables for the character creation wizard.

All pure data — no UI, no tkinter imports. Values come from the Player's
Handbook (5e, 2014 printing) unless noted.
"""

# ── Ability score building ─────────────────────────────────────────────────────

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# Point Buy: each score value maps to its cost (PHB p.13)
POINT_BUY_COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27
PB_MIN, PB_MAX = 8, 15

# ── Alignment ─────────────────────────────────────────────────────────────────

ALIGNMENTS = [
    ("Lawful Good",    "LG"),  ("Neutral Good",  "NG"),  ("Chaotic Good",    "CG"),
    ("Lawful Neutral", "LN"),  ("True Neutral",  "TN"),  ("Chaotic Neutral", "CN"),
    ("Lawful Evil",    "LE"),  ("Neutral Evil",  "NE"),  ("Chaotic Evil",    "CE"),
]

# ── Class proficiency data (PHB) ───────────────────────────────────────────────

CLASS_SAVING_THROWS = {
    "artificer": ["int", "con"],
    "barbarian": ["str", "con"],
    "bard":      ["dex", "cha"],
    "cleric":    ["wis", "cha"],
    "druid":     ["int", "wis"],
    "fighter":   ["str", "con"],
    "monk":      ["str", "dex"],
    "paladin":   ["wis", "cha"],
    "ranger":    ["str", "dex"],
    "rogue":     ["dex", "int"],
    "sorcerer":  ["con", "cha"],
    "warlock":   ["wis", "cha"],
    "wizard":    ["int", "wis"],
}

ALL_SKILLS = [
    "Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception",
    "History", "Insight", "Intimidation", "Investigation", "Medicine",
    "Nature", "Perception", "Performance", "Persuasion", "Religion",
    "Sleight of Hand", "Stealth", "Survival",
]

CLASS_SKILL_CHOICES = {
    "artificer": {"count": 2, "from": ["Arcana", "History", "Investigation", "Medicine", "Nature", "Perception", "Sleight of Hand"]},
    "barbarian": {"count": 2, "from": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]},
    "bard":      {"count": 3, "from": ALL_SKILLS},
    "cleric":    {"count": 2, "from": ["History", "Insight", "Medicine", "Persuasion", "Religion"]},
    "druid":     {"count": 2, "from": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"]},
    "fighter":   {"count": 2, "from": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"]},
    "monk":      {"count": 2, "from": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"]},
    "paladin":   {"count": 2, "from": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"]},
    "ranger":    {"count": 3, "from": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"]},
    "rogue":     {"count": 4, "from": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"]},
    "sorcerer":  {"count": 2, "from": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"]},
    "warlock":   {"count": 2, "from": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"]},
    "wizard":    {"count": 2, "from": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"]},
}

CLASS_ARMOR_PROFS = {
    "artificer": ["Light armor", "Medium armor", "Shields"],
    "barbarian": ["Light armor", "Medium armor", "Shields"],
    "bard":      ["Light armor"],
    "cleric":    ["Light armor", "Medium armor", "Shields"],
    "druid":     ["Light armor", "Medium armor", "Shields"],
    "fighter":   ["All armor", "Shields"],
    "monk":      [],
    "paladin":   ["All armor", "Shields"],
    "ranger":    ["Light armor", "Medium armor", "Shields"],
    "rogue":     ["Light armor"],
    "sorcerer":  [],
    "warlock":   ["Light armor"],
    "wizard":    [],
}

CLASS_WEAPON_PROFS = {
    "artificer": ["Simple weapons"],
    "barbarian": ["Simple weapons", "Martial weapons"],
    "bard":      ["Simple weapons", "Hand crossbows", "Longswords", "Rapiers", "Shortswords"],
    "cleric":    ["Simple weapons"],
    "druid":     ["Clubs", "Daggers", "Darts", "Javelins", "Maces", "Quarterstaffs", "Scimitars", "Sickles", "Slings", "Spears"],
    "fighter":   ["Simple weapons", "Martial weapons"],
    "monk":      ["Simple weapons", "Shortswords"],
    "paladin":   ["Simple weapons", "Martial weapons"],
    "ranger":    ["Simple weapons", "Martial weapons"],
    "rogue":     ["Simple weapons", "Hand crossbows", "Longswords", "Rapiers", "Shortswords"],
    "sorcerer":  ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"],
    "warlock":   ["Simple weapons"],
    "wizard":    ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"],
}

CLASS_TOOL_PROFS = {
    "artificer": ["Thieves' tools", "Tinker's tools"],
    "monk":      ["One Artisan's tool or Musical instrument"],
    "rogue":     ["Thieves' tools"],
}

# Starting gold (GP) when player skips equipment packages
STARTING_GOLD = {
    "artificer": 125, "barbarian": 75,  "bard": 125, "cleric": 125,
    "druid": 50,  "fighter": 175, "monk": 12,  "paladin": 175,
    "ranger": 125, "rogue": 100,  "sorcerer": 75, "warlock": 100, "wizard": 100,
}

# PHB starting equipment — two canonical packages per class
STARTING_EQUIPMENT = {
    "artificer": {
        "A": ["Studded leather armor", "Two simple weapons", "Thieves' tools", "Dungeoneer's Pack"],
        "B": ["Scale mail", "Two simple weapons", "Thieves' tools", "Dungeoneer's Pack"],
    },
    "barbarian": {
        "A": ["Greataxe", "Two handaxes", "Explorer's Pack", "Javelin ×4"],
        "B": ["Any martial melee weapon", "Any simple weapon", "Explorer's Pack", "Javelin ×4"],
    },
    "bard": {
        "A": ["Rapier", "Diplomat's Pack", "Lute", "Leather armor", "Dagger"],
        "B": ["Longsword", "Diplomat's Pack", "Lute", "Leather armor", "Dagger"],
    },
    "cleric": {
        "A": ["Mace", "Scale mail", "Light crossbow & 20 bolts", "Priest's Pack", "Shield", "Holy symbol"],
        "B": ["Mace", "Leather armor", "Light crossbow & 20 bolts", "Priest's Pack", "Shield", "Holy symbol"],
    },
    "druid": {
        "A": ["Wooden shield", "Scimitar", "Leather armor", "Explorer's Pack", "Druidic focus"],
        "B": ["Wooden shield", "Any simple weapon", "Leather armor", "Explorer's Pack", "Druidic focus"],
    },
    "fighter": {
        "A": ["Chain mail", "Martial weapon & shield", "Light crossbow & 20 bolts", "Dungeoneer's Pack"],
        "B": ["Leather armor", "Two martial weapons", "Light crossbow & 20 bolts", "Explorer's Pack"],
    },
    "monk": {
        "A": ["Shortsword", "Dungeoneer's Pack", "10 darts"],
        "B": ["Any simple weapon", "Explorer's Pack", "10 darts"],
    },
    "paladin": {
        "A": ["Martial weapon & shield", "Javelin ×5", "Priest's Pack", "Chain mail", "Holy symbol"],
        "B": ["Two martial weapons", "Javelin ×5", "Explorer's Pack", "Chain mail", "Holy symbol"],
    },
    "ranger": {
        "A": ["Scale mail", "Two shortswords", "Dungeoneer's Pack", "Longbow & 20 arrows"],
        "B": ["Leather armor", "Two shortswords", "Explorer's Pack", "Longbow & 20 arrows"],
    },
    "rogue": {
        "A": ["Rapier", "Shortbow & 20 arrows", "Burglar's Pack", "Leather armor", "Two daggers", "Thieves' tools"],
        "B": ["Shortsword", "Shortbow & 20 arrows", "Burglar's Pack", "Leather armor", "Two daggers", "Thieves' tools"],
    },
    "sorcerer": {
        "A": ["Light crossbow & 20 bolts", "Arcane focus", "Dungeoneer's Pack", "Two daggers"],
        "B": ["Any simple weapon", "Arcane focus", "Explorer's Pack", "Two daggers"],
    },
    "warlock": {
        "A": ["Light crossbow & 20 bolts", "Arcane focus", "Scholar's Pack", "Leather armor", "Any simple weapon", "Two daggers"],
        "B": ["Any simple weapon", "Arcane focus", "Dungeoneer's Pack", "Leather armor", "Two daggers"],
    },
    "wizard": {
        "A": ["Quarterstaff", "Arcane focus", "Scholar's Pack", "Spellbook"],
        "B": ["Dagger", "Arcane focus", "Explorer's Pack", "Spellbook"],
    },
}

# ── Racial ability score bonuses (PHB + Volo's, common races) ─────────────────

RACIAL_BONUSES: dict[str, dict[str, int]] = {
    # PHB
    "Dwarf":                {"con": 2},
    "Hill Dwarf":           {"con": 2, "wis": 1},
    "Mountain Dwarf":       {"con": 2, "str": 2},
    "Elf":                  {"dex": 2},
    "High Elf":             {"dex": 2, "int": 1},
    "Wood Elf":             {"dex": 2, "wis": 1},
    "Dark Elf":             {"dex": 2, "cha": 1},
    "Drow":                 {"dex": 2, "cha": 1},
    "Halfling":             {"dex": 2},
    "Lightfoot Halfling":   {"dex": 2, "cha": 1},
    "Stout Halfling":       {"dex": 2, "con": 1},
    "Human":                {"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1},
    "Variant Human":        {},
    "Dragonborn":           {"str": 2, "cha": 1},
    "Gnome":                {"int": 2},
    "Forest Gnome":         {"int": 2, "dex": 1},
    "Rock Gnome":           {"int": 2, "con": 1},
    "Half-Elf":             {"cha": 2},
    "Half-Orc":             {"str": 2, "con": 1},
    "Tiefling":             {"int": 1, "cha": 2},
    # Volo's Guide
    "Aasimar":              {"cha": 2},
    "Fallen Aasimar":       {"cha": 2, "str": 1},
    "Protector Aasimar":    {"cha": 2, "wis": 1},
    "Scourge Aasimar":      {"cha": 2, "con": 1},
    "Firbolg":              {"wis": 2, "str": 1},
    "Goliath":              {"str": 2, "con": 1},
    "Kenku":                {"dex": 2, "wis": 1},
    "Lizardfolk":           {"con": 2, "wis": 1},
    "Tabaxi":               {"dex": 2, "cha": 1},
    "Triton":               {"str": 1, "con": 1, "cha": 1},
    "Yuan-ti Pureblood":    {"cha": 2, "int": 1},
    # Mordenkainen's
    "Bugbear":              {"str": 2, "dex": 1},
    "Goblin":               {"dex": 2, "con": 1},
    "Hobgoblin":            {"int": 2, "con": 1},
    "Kobold":               {"dex": 2},
    "Orc":                  {"str": 2, "con": 1},
    # Misc
    "Tortle":               {"str": 2, "wis": 1},
    "Warforged":            {"con": 2},
    "Leonin":               {"str": 2, "con": 1},
    "Satyr":                {"cha": 2, "dex": 1},
}

# ── Background data (PHB + SCAG) ──────────────────────────────────────────────

BACKGROUND_SKILLS: dict[str, list[str]] = {
    "Acolyte":              ["Insight", "Religion"],
    "Charlatan":            ["Deception", "Sleight of Hand"],
    "Criminal":             ["Deception", "Stealth"],
    "Spy":                  ["Deception", "Stealth"],
    "Entertainer":          ["Acrobatics", "Performance"],
    "Gladiator":            ["Acrobatics", "Performance"],
    "Folk Hero":            ["Animal Handling", "Survival"],
    "Guild Artisan":        ["Insight", "Persuasion"],
    "Guild Merchant":       ["Insight", "Persuasion"],
    "Hermit":               ["Medicine", "Religion"],
    "Noble":                ["History", "Persuasion"],
    "Knight":               ["History", "Persuasion"],
    "Outlander":            ["Athletics", "Survival"],
    "Sage":                 ["Arcana", "History"],
    "Sailor":               ["Athletics", "Perception"],
    "Pirate":               ["Athletics", "Perception"],
    "Soldier":              ["Athletics", "Intimidation"],
    "Urchin":               ["Sleight of Hand", "Stealth"],
    # SCAG
    "City Watch":           ["Athletics", "Insight"],
    "Investigator":         ["Investigation", "Insight"],
    "Clan Crafter":         ["History", "Insight"],
    "Cloistered Scholar":   ["History", "Arcana"],
    "Courtier":             ["Insight", "Persuasion"],
    "Far Traveler":         ["Insight", "Perception"],
    "Inheritor":            ["Survival", "History"],
    "Knight of the Order":  ["Persuasion", "History"],
    "Mercenary Veteran":    ["Athletics", "Persuasion"],
    "Urban Bounty Hunter":  ["Deception", "Stealth"],
    "Uthgardt Tribe Member":["Athletics", "Survival"],
    "Waterdhavian Noble":   ["History", "Persuasion"],
}

BACKGROUND_TOOLS: dict[str, list[str]] = {
    "Charlatan":            ["Disguise kit", "Forgery kit"],
    "Criminal":             ["Thieves' tools"],
    "Spy":                  ["Thieves' tools"],
    "Entertainer":          ["Disguise kit", "One musical instrument"],
    "Gladiator":            ["Disguise kit", "One unusual weapon"],
    "Folk Hero":            ["One set of Artisan's tools", "Vehicles (land)"],
    "Guild Artisan":        ["One set of Artisan's tools"],
    "Guild Merchant":       ["One set of Artisan's tools"],
    "Hermit":               ["Herbalism kit"],
    "Sailor":               ["Navigator's tools", "Vehicles (water)"],
    "Pirate":               ["Navigator's tools", "Vehicles (water)"],
    "Soldier":              ["One gaming set", "Vehicles (land)"],
    "Urchin":               ["Disguise kit", "Thieves' tools"],
    "Mercenary Veteran":    ["One gaming set", "Vehicles (land)"],
    "Clan Crafter":         ["One set of Artisan's tools"],
}

# Extra languages granted (count = number of player-chosen languages)
BACKGROUND_LANGUAGES: dict[str, int] = {
    "Acolyte": 2, "Sage": 2, "Noble": 1, "Knight": 1, "Outlander": 1,
    "Guild Artisan": 1, "Guild Merchant": 1, "Far Traveler": 1,
    "Cloistered Scholar": 2, "Courtier": 2, "Inheritor": 1,
    "Waterdhavian Noble": 1, "City Watch": 2, "Investigator": 2,
    "Clan Crafter": 1, "Knight of the Order": 1, "Uthgardt Tribe Member": 1,
}

# ── Spellcasting ───────────────────────────────────────────────────────────────

_SPELLCASTER_CLASSES = {
    "artificer", "bard", "cleric", "druid", "paladin",
    "ranger", "sorcerer", "warlock", "wizard",
}

_PREPARING_CLASSES = {"wizard", "cleric", "druid", "paladin", "artificer"}


def is_spellcaster(class_name: str) -> bool:
    return (class_name or "").strip().lower() in _SPELLCASTER_CLASSES


def is_preparing_caster(class_name: str) -> bool:
    """True for classes that prepare spells from their full list (no fixed known set)."""
    return (class_name or "").strip().lower() in _PREPARING_CLASSES


# Cantrips known by class at each level
CANTRIPS_KNOWN: dict[str, dict[int, int]] = {
    "artificer": {1:2,2:2,3:2,4:2,5:2,6:2,7:2,8:2,9:2,10:3,11:3,12:3,13:3,14:4,15:4,16:4,17:4,18:4,19:4,20:4},
    "bard":      {1:2,2:2,3:2,4:3,5:3,6:3,7:3,8:3,9:3,10:4,11:4,12:4,13:4,14:4,15:4,16:4,17:4,18:4,19:4,20:4},
    "cleric":    {1:3,2:3,3:3,4:4,5:4,6:4,7:4,8:4,9:4,10:5,11:5,12:5,13:5,14:5,15:5,16:5,17:5,18:5,19:5,20:5},
    "druid":     {1:2,2:2,3:2,4:3,5:3,6:3,7:3,8:3,9:3,10:4,11:4,12:4,13:4,14:4,15:4,16:4,17:4,18:4,19:4,20:4},
    "sorcerer":  {1:4,2:4,3:4,4:5,5:5,6:5,7:5,8:5,9:5,10:6,11:6,12:6,13:6,14:6,15:6,16:6,17:6,18:6,19:6,20:6},
    "warlock":   {1:2,2:2,3:2,4:3,5:3,6:3,7:3,8:3,9:3,10:4,11:4,12:4,13:4,14:4,15:4,16:4,17:4,18:4,19:4,20:4},
    "wizard":    {1:3,2:3,3:3,4:4,5:4,6:4,7:4,8:4,9:4,10:5,11:5,12:5,13:5,14:5,15:5,16:5,17:5,18:5,19:5,20:5},
}

# Spells known (for know-list classes: bard, ranger, sorcerer, warlock)
SPELLS_KNOWN: dict[str, dict[int, int]] = {
    "bard":     {1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,9:12,10:14,11:15,12:15,13:16,14:18,15:19,16:19,17:20,18:22,19:22,20:22},
    "ranger":   {1:0,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6,10:6,11:7,12:7,13:8,14:8,15:9,16:9,17:10,18:10,19:11,20:11},
    "sorcerer": {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:12,13:13,14:13,15:14,16:14,17:15,18:15,19:15,20:15},
    "warlock":  {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:10,11:11,12:11,13:12,14:12,15:13,16:13,17:14,18:14,19:15,20:15},
}

# Wizard starts with 6 spells in their spellbook at level 1, +2 per additional level
WIZARD_SPELLBOOK_START = 6
WIZARD_SPELLBOOK_PER_LEVEL = 2


def cantrips_known(class_name: str, level: int) -> int:
    """Number of cantrips the class knows at this level."""
    tbl = CANTRIPS_KNOWN.get((class_name or "").lower(), {})
    return tbl.get(level, 0)


def spells_known_count(class_name: str, level: int) -> int:
    """Spells known for know-list classes; 0 for preparing classes."""
    cn = (class_name or "").lower()
    if cn == "wizard":
        # Spellbook: pick from all wizard spells; we handle this as known=True entries
        return WIZARD_SPELLBOOK_START + WIZARD_SPELLBOOK_PER_LEVEL * max(0, level - 1)
    tbl = SPELLS_KNOWN.get(cn, {})
    return tbl.get(level, 0)


def max_spell_level_for_class(class_name: str, level: int) -> int:
    """Highest spell level accessible at this class level (0 = cantrips only)."""
    from pages.spell_rules import caster_level, MULTICLASS_SLOTS
    cl = caster_level([(class_name, level, "")])
    if cl == 0:
        return 0
    slots = MULTICLASS_SLOTS.get(cl, [0] * 9)
    for sl in range(8, -1, -1):
        if slots[sl] > 0:
            return sl + 1
    return 0
