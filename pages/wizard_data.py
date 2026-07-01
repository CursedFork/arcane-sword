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


# ── Level milestone data ───────────────────────────────────────────────────────
# Key features per class per level. Not exhaustive — focused on the milestones
# that matter most when choosing a starting level.

PROF_BONUS = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

CLASS_LEVEL_FEATURES: dict[str, dict[int, list[str]]] = {
    "artificer": {
        1:  ["Magical Tinkering", "Spellcasting — INT, prepare spells from your list"],
        2:  ["Infuse Item — enchant 2 items per day with magical properties"],
        3:  ["Artificer Specialist — choose your subclass path"],
        4:  ["Ability Score Improvement"],
        5:  ["Extra Attack", "Artificer Specialist feature"],
        6:  ["Tool Expertise — double proficiency on tool checks"],
        7:  ["Flash of Genius — add INT mod to a saving throw (reaction)"],
        8:  ["Ability Score Improvement", "Artificer Specialist feature"],
        9:  ["Artificer Specialist feature"],
        10: ["Magic Item Adept — attune to 4 items"],
        11: ["Spell-Storing Item — store a 1st or 2nd level spell in an item"],
        12: ["Ability Score Improvement"],
        13: ["Artificer Specialist feature"],
        14: ["Magic Item Savant — attune to 5 items, ignore class requirements"],
        15: ["Artificer Specialist feature"],
        16: ["Ability Score Improvement"],
        18: ["Magic Item Master — attune to 6 items"],
        19: ["Ability Score Improvement"],
        20: ["Soul of Artifice — +1 to all saves per attuned item; save vs. 0 HP"],
    },
    "barbarian": {
        1:  ["Rage — deal extra damage, resist physical hits (2/long rest)", "Unarmored Defense — AC = 10 + DEX + CON (no armour needed)"],
        2:  ["Reckless Attack — attack with advantage, but enemies get it too", "Danger Sense — advantage on DEX saves vs. visible threats"],
        3:  ["Primal Path — choose your subclass; Rage uses increase to 3"],
        4:  ["Ability Score Improvement"],
        5:  ["Extra Attack — attack twice per Attack action", "Fast Movement — +10 ft speed when not wearing heavy armor"],
        6:  ["Primal Path feature", "Rage uses: 4, damage bonus: +3"],
        7:  ["Feral Instinct — advantage on initiative; can rage if surprised"],
        8:  ["Ability Score Improvement"],
        9:  ["Brutal Critical — roll one extra damage die on a critical hit"],
        10: ["Primal Path feature", "Rage damage bonus: +3"],
        11: ["Relentless Rage — drop to 1 HP instead of 0 (DC 10 CON save)"],
        12: ["Ability Score Improvement", "Rage uses: 5"],
        13: ["Brutal Critical — two extra damage dice on a crit"],
        14: ["Primal Path feature"],
        15: ["Persistent Rage — rage no longer ends from inactivity"],
        16: ["Ability Score Improvement", "Rage uses: 6", "Rage damage bonus: +4"],
        17: ["Brutal Critical — three extra damage dice on a crit"],
        18: ["Indomitable Might — STR checks are minimum your STR score"],
        19: ["Ability Score Improvement"],
        20: ["Primal Champion — +4 STR and +4 CON; unlimited rages"],
    },
    "bard": {
        1:  ["Spellcasting — CHA-based; know spells from the bard list", "Bardic Inspiration — give an ally a d6 to add to a roll (CHA mod/rest)"],
        2:  ["Jack of All Trades — add half proficiency to any unproficient check", "Song of Rest — allies regain d6 HP on a short rest"],
        3:  ["Bard College — choose your subclass", "Expertise — double proficiency in 2 skills"],
        4:  ["Ability Score Improvement"],
        5:  ["Bardic Inspiration die improves to d8", "Font of Inspiration — regain Bardic dice on a short rest"],
        6:  ["Countercharm — use music to end fear or charm on nearby allies", "Bard College feature"],
        8:  ["Ability Score Improvement"],
        9:  ["Song of Rest improves to d8"],
        10: ["Bardic Inspiration die improves to d10", "Expertise — double proficiency in 2 more skills", "Magical Secrets — learn 2 spells from any class list"],
        12: ["Ability Score Improvement"],
        13: ["Song of Rest improves to d10"],
        14: ["Magical Secrets — learn 2 more spells from any class", "Bard College feature"],
        15: ["Bardic Inspiration die improves to d12"],
        16: ["Ability Score Improvement"],
        17: ["Song of Rest improves to d12"],
        18: ["Magical Secrets — learn 2 more spells from any class"],
        19: ["Ability Score Improvement"],
        20: ["Superior Inspiration — regain 1 Bardic die on initiative if you have none"],
    },
    "cleric": {
        1:  ["Divine Domain — choose your subclass immediately", "Spellcasting — WIS-based; prepare spells from your domain + cleric list"],
        2:  ["Channel Divinity (1/rest) — potent divine powers from your domain", "Divine Domain feature"],
        3:  ["Unlock 2nd-level spell slots"],
        4:  ["Ability Score Improvement"],
        5:  ["Destroy Undead CR ½ — banish weak undead outright", "Unlock 3rd-level spell slots"],
        6:  ["Channel Divinity (2/rest)", "Divine Domain feature"],
        7:  ["Unlock 4th-level spell slots"],
        8:  ["Ability Score Improvement", "Divine Domain feature", "Destroy Undead CR 1"],
        9:  ["Unlock 5th-level spell slots"],
        10: ["Divine Intervention — call on your deity for a miracle (1/week)"],
        11: ["Destroy Undead CR 2", "Unlock 6th-level spell slots"],
        12: ["Ability Score Improvement"],
        13: ["Unlock 7th-level spell slots"],
        14: ["Destroy Undead CR 3"],
        15: ["Unlock 8th-level spell slots"],
        16: ["Ability Score Improvement"],
        17: ["Destroy Undead CR 4", "Divine Domain feature", "Unlock 9th-level spell slots"],
        18: ["Channel Divinity (3/rest)"],
        19: ["Ability Score Improvement"],
        20: ["Divine Intervention — guaranteed success once per week"],
    },
    "druid": {
        1:  ["Druidic — secret language known only to druids", "Spellcasting — WIS-based; prepare spells from the druid list"],
        2:  ["Wild Shape — transform into beasts (CR ¼, 2/rest)", "Druid Circle — choose your subclass"],
        3:  ["Unlock 2nd-level spell slots"],
        4:  ["Ability Score Improvement", "Wild Shape improves to CR ½ (swim speed)"],
        5:  ["Unlock 3rd-level spell slots"],
        6:  ["Druid Circle feature"],
        7:  ["Unlock 4th-level spell slots"],
        8:  ["Ability Score Improvement", "Wild Shape improves to CR 1 (fly speed)", "Unlock 5th-level spell slots"],
        10: ["Druid Circle feature", "Unlock 6th-level spell slots"],
        12: ["Ability Score Improvement", "Unlock 7th-level spell slots"],
        14: ["Druid Circle feature", "Unlock 8th-level spell slots"],
        16: ["Ability Score Improvement", "Unlock 9th-level spell slots"],
        18: ["Timeless Body — age 10× slower", "Beast Spells — cast spells while in Wild Shape"],
        19: ["Ability Score Improvement"],
        20: ["Archdruid — unlimited Wild Shape uses"],
    },
    "fighter": {
        1:  ["Fighting Style — choose a combat speciality (Archery, Defense, Dueling…)", "Second Wind — heal yourself as a bonus action (1/short rest)"],
        2:  ["Action Surge — take an extra full action on your turn (1/short rest)"],
        3:  ["Martial Archetype — choose your subclass"],
        4:  ["Ability Score Improvement"],
        5:  ["Extra Attack — attack twice per Attack action"],
        6:  ["Ability Score Improvement"],
        7:  ["Martial Archetype feature"],
        8:  ["Ability Score Improvement"],
        9:  ["Indomitable — reroll a failed saving throw (1/long rest)"],
        10: ["Martial Archetype feature"],
        11: ["Extra Attack — now attack three times per Attack action"],
        12: ["Ability Score Improvement"],
        13: ["Indomitable (2/long rest)"],
        14: ["Ability Score Improvement"],
        15: ["Martial Archetype feature"],
        16: ["Ability Score Improvement"],
        17: ["Action Surge (2/short rest)", "Indomitable (3/long rest)"],
        18: ["Martial Archetype feature"],
        19: ["Ability Score Improvement"],
        20: ["Extra Attack — now attack four times per Attack action"],
    },
    "monk": {
        1:  ["Unarmored Defense — AC = 10 + DEX + WIS (no armour)", "Martial Arts — unarmed strikes use DEX or STR; deal d4 damage"],
        2:  ["Ki (2 points) — fuel Flurry of Blows, Patient Defense, and Step of the Wind", "Unarmored Movement — +10 ft speed while unarmoured"],
        3:  ["Monastic Tradition — choose your subclass", "Deflect Missiles — reduce ranged damage with your reaction"],
        4:  ["Ability Score Improvement", "Slow Fall — halve fall damage (reaction)"],
        5:  ["Extra Attack", "Stunning Strike — spend 1 ki to stun a target on a hit", "Martial Arts die improves to d6"],
        6:  ["Ki-Empowered Strikes — unarmed strikes count as magical", "Monastic Tradition feature", "Unarmored Movement +15 ft"],
        7:  ["Evasion — take no damage on successful DEX saves", "Stillness of Mind — end charmed or frightened as an action"],
        8:  ["Ability Score Improvement"],
        9:  ["Unarmored Movement — run on walls and across liquids"],
        10: ["Purity of Body — immune to disease and poison", "Martial Arts die improves to d8"],
        11: ["Monastic Tradition feature"],
        12: ["Ability Score Improvement"],
        13: ["Tongue of the Sun and Moon — understand and be understood by all creatures"],
        14: ["Diamond Soul — proficiency in all saving throws"],
        15: ["Timeless Body — age 10× slower", "Martial Arts die improves to d10"],
        16: ["Ability Score Improvement"],
        17: ["Monastic Tradition feature"],
        18: ["Empty Body — spend 4 ki to become invisible and resist all but force damage"],
        19: ["Ability Score Improvement"],
        20: ["Perfect Self — restore 4 ki on initiative if you have none", "Martial Arts die improves to d12"],
    },
    "paladin": {
        1:  ["Divine Sense — detect celestials, fiends, and undead nearby", "Lay on Hands — pool of healing HP equal to 5 × your level"],
        2:  ["Fighting Style", "Spellcasting — CHA-based", "Divine Smite — spend a spell slot after hitting to deal radiant burst damage"],
        3:  ["Sacred Oath — choose your subclass", "Divine Health — immune to disease", "Channel Divinity (1/rest)"],
        4:  ["Ability Score Improvement"],
        5:  ["Extra Attack", "Unlock 3rd-level spell slots"],
        6:  ["Aura of Protection — you and nearby allies add CHA modifier to all saving throws (10 ft)"],
        7:  ["Sacred Oath feature"],
        8:  ["Ability Score Improvement"],
        9:  ["Unlock 5th-level spell slots"],
        10: ["Aura of Courage — you and nearby allies can't be frightened (10 ft)"],
        11: ["Improved Divine Smite — all melee hits deal an extra +1d8 radiant damage"],
        12: ["Ability Score Improvement"],
        13: ["Unlock 7th-level spell slots"],
        14: ["Cleansing Touch — end a spell on yourself or a willing ally (CHA mod/long rest)"],
        15: ["Sacred Oath feature"],
        16: ["Ability Score Improvement"],
        17: ["Unlock 9th-level spell slots"],
        18: ["Aura of Protection and Courage expand to 30 ft"],
        19: ["Ability Score Improvement"],
        20: ["Sacred Oath capstone — a powerful unique ability from your oath"],
    },
    "ranger": {
        1:  ["Favored Foe — mark an enemy for bonus damage (replaces Favored Enemy)", "Natural Explorer / Deft Explorer — expertise in nature and travel"],
        2:  ["Fighting Style", "Spellcasting — WIS-based; know spells from the ranger list"],
        3:  ["Primal Awareness / Primeval Awareness", "Ranger Conclave — choose your subclass"],
        4:  ["Ability Score Improvement"],
        5:  ["Extra Attack"],
        6:  ["Favored Foe improvement"],
        7:  ["Ranger Conclave feature"],
        8:  ["Ability Score Improvement", "Land's Stride — move through difficult terrain and plants without penalty"],
        9:  ["Unlock 5th-level spell slots"],
        10: ["Nature's Veil — become invisible briefly (WIS mod/long rest)"],
        11: ["Ranger Conclave feature"],
        12: ["Ability Score Improvement"],
        13: ["Unlock 7th-level spell slots"],
        14: ["Vanish — Hide as a bonus action; can't be tracked unless you choose to be"],
        15: ["Ranger Conclave feature"],
        16: ["Ability Score Improvement"],
        17: ["Unlock 9th-level spell slots"],
        18: ["Feral Senses — detect invisible creatures within 30 ft"],
        19: ["Ability Score Improvement"],
        20: ["Foe Slayer — add WIS modifier to attack or damage rolls vs. a favored enemy once per turn"],
    },
    "rogue": {
        1:  ["Expertise — double proficiency bonus in 2 skills", "Sneak Attack — deal extra d6 damage when you have advantage or an ally nearby", "Thieves' Cant — secret rogue language and signals"],
        2:  ["Cunning Action — Dash, Disengage, or Hide as a bonus action every turn"],
        3:  ["Roguish Archetype — choose your subclass", "Sneak Attack improves to 2d6"],
        4:  ["Ability Score Improvement"],
        5:  ["Uncanny Dodge — halve damage from one attack per round (reaction)", "Sneak Attack: 3d6"],
        6:  ["Expertise — double proficiency in 2 more skills"],
        7:  ["Evasion — take no damage on successful DEX saves; half on failures", "Sneak Attack: 4d6"],
        8:  ["Ability Score Improvement"],
        9:  ["Roguish Archetype feature", "Sneak Attack: 5d6"],
        10: ["Ability Score Improvement", "Sneak Attack: 6d6"],
        11: ["Reliable Talent — treat any roll below 10 as a 10 on proficient checks"],
        12: ["Ability Score Improvement"],
        13: ["Roguish Archetype feature", "Sneak Attack: 7d6"],
        14: ["Blindsense — detect invisible creatures within 10 ft if you can hear"],
        15: ["Slippery Mind — gain WIS saving throw proficiency", "Sneak Attack: 8d6"],
        16: ["Ability Score Improvement"],
        17: ["Roguish Archetype feature", "Sneak Attack: 9d6"],
        18: ["Elusive — attackers never gain advantage on attacks against you"],
        19: ["Ability Score Improvement", "Sneak Attack: 10d6"],
        20: ["Stroke of Luck — once per long rest, turn a miss into a hit or a failed check into a success"],
    },
    "sorcerer": {
        1:  ["Sorcerous Origin — choose your subclass (the source of your magic)", "Spellcasting — CHA-based; know spells (4 cantrips, 2 spells)"],
        2:  ["Font of Magic — 2 sorcery points; convert between slots and points"],
        3:  ["Metamagic — choose 2 ways to twist your spells (Subtle, Twinned, Quickened…)"],
        4:  ["Ability Score Improvement"],
        5:  ["Unlock 3rd-level spell slots"],
        6:  ["Sorcerous Origin feature"],
        7:  ["Unlock 4th-level spell slots"],
        8:  ["Ability Score Improvement"],
        9:  ["Unlock 5th-level spell slots"],
        10: ["Metamagic — learn a 3rd option"],
        11: ["Unlock 6th-level spell slots"],
        12: ["Ability Score Improvement"],
        13: ["Unlock 7th-level spell slots"],
        14: ["Sorcerous Origin feature"],
        15: ["Unlock 8th-level spell slots"],
        16: ["Ability Score Improvement"],
        17: ["Unlock 9th-level spell slots", "Metamagic — learn a 4th option"],
        18: ["Sorcerous Origin feature"],
        19: ["Ability Score Improvement"],
        20: ["Sorcerous Restoration — regain 4 sorcery points on a short rest"],
    },
    "warlock": {
        1:  ["Otherworldly Patron — choose your subclass (the entity that grants your power)", "Pact Magic — CHA-based; spell slots recharge on a short rest"],
        2:  ["Eldritch Invocations — choose 2 permanent magical enhancements"],
        3:  ["Pact Boon — Bond of the Blade (weapon), Tome (spells), or Chain (familiar)", "Unlock 2nd-level pact slots"],
        4:  ["Ability Score Improvement"],
        5:  ["Unlock 3rd-level pact slots", "Eldritch Invocations: 3 known"],
        6:  ["Otherworldly Patron feature"],
        7:  ["Unlock 4th-level pact slots", "Eldritch Invocations: 4 known"],
        8:  ["Ability Score Improvement"],
        9:  ["Unlock 5th-level pact slots (max level for Warlocks)", "Eldritch Invocations: 5 known"],
        10: ["Otherworldly Patron feature"],
        11: ["Mystic Arcanum — cast one 6th-level spell per long rest (beyond normal slots)"],
        12: ["Ability Score Improvement"],
        13: ["Mystic Arcanum — 7th-level spell"],
        14: ["Otherworldly Patron feature"],
        15: ["Mystic Arcanum — 8th-level spell"],
        16: ["Ability Score Improvement"],
        17: ["Mystic Arcanum — 9th-level spell"],
        18: ["Eldritch Invocations: 8 known"],
        19: ["Ability Score Improvement"],
        20: ["Eldritch Master — spend 1 minute to recover all pact magic slots (1/long rest)"],
    },
    "wizard": {
        1:  ["Spellcasting — INT-based; spellbook with 6 spells + 2 per level up", "Arcane Recovery — regain spell slots on a short rest (up to half your level)"],
        2:  ["Arcane Tradition — choose your subclass (School of Evocation, Abjuration…)"],
        3:  ["Unlock 2nd-level spell slots"],
        4:  ["Ability Score Improvement"],
        5:  ["Unlock 3rd-level spell slots"],
        6:  ["Arcane Tradition feature"],
        7:  ["Unlock 4th-level spell slots"],
        8:  ["Ability Score Improvement"],
        9:  ["Unlock 5th-level spell slots"],
        10: ["Arcane Tradition feature"],
        11: ["Unlock 6th-level spell slots"],
        12: ["Ability Score Improvement"],
        13: ["Unlock 7th-level spell slots"],
        14: ["Arcane Tradition feature"],
        15: ["Unlock 8th-level spell slots"],
        16: ["Ability Score Improvement"],
        17: ["Unlock 9th-level spell slots — the most powerful magic in existence"],
        18: ["Spell Mastery — cast one 1st-level and one 2nd-level spell at will without slots"],
        19: ["Ability Score Improvement"],
        20: ["Signature Spells — two 3rd-level spells you can cast for free on a short rest"],
    },
}


def level_milestones(class_name: str, max_level: int) -> list[tuple[int, list[str]]]:
    """Return (level, [feature strings]) for levels 1..max_level for the given class."""
    cn = (class_name or "").lower()
    feats = CLASS_LEVEL_FEATURES.get(cn, {})
    result = []
    for lv in range(1, max_level + 1):
        entries = list(feats.get(lv, []))
        result.append((lv, entries))
    return result
