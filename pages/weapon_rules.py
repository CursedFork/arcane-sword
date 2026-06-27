"""Weapon rules — pure helpers (no UI) for deriving attack/damage from a
character's equipped weapons. The reference compendium stores weapon text but
not structured damage/properties, so the standard PHB weapons live here as
reliable data. Unknown items simply don't produce a derived attack (the user
can add a manual one).
"""
import re

# name -> properties. damage = base die; type = damage type; category drives
# proficiency ("simple"/"martial"); flags: finesse, ranged, thrown, versatile.
WEAPONS: dict[str, dict] = {}


def _w(name, damage, dtype, category, weight, *, finesse=False, ranged=False,
       thrown=False, versatile=None):
    WEAPONS[name.lower()] = {
        "name": name, "damage": damage, "type": dtype, "category": category,
        "weight": weight, "finesse": finesse, "ranged": ranged,
        "thrown": thrown, "versatile": versatile,
    }


# ── Simple melee ────────────────────────────────────────────────────────────
_w("Club", "1d4", "bludgeoning", "simple", 2)
_w("Dagger", "1d4", "piercing", "simple", 1, finesse=True, thrown=True)
_w("Greatclub", "1d8", "bludgeoning", "simple", 10)
_w("Handaxe", "1d6", "slashing", "simple", 2, thrown=True)
_w("Javelin", "1d6", "piercing", "simple", 2, thrown=True)
_w("Light Hammer", "1d4", "bludgeoning", "simple", 2, thrown=True)
_w("Mace", "1d6", "bludgeoning", "simple", 4)
_w("Quarterstaff", "1d6", "bludgeoning", "simple", 4, versatile="1d8")
_w("Sickle", "1d4", "slashing", "simple", 2)
_w("Spear", "1d6", "piercing", "simple", 3, thrown=True, versatile="1d8")
# ── Simple ranged ───────────────────────────────────────────────────────────
_w("Light Crossbow", "1d8", "piercing", "simple", 5, ranged=True)
_w("Dart", "1d4", "piercing", "simple", 0.25, finesse=True, thrown=True, ranged=True)
_w("Shortbow", "1d6", "piercing", "simple", 2, ranged=True)
_w("Sling", "1d4", "bludgeoning", "simple", 0, ranged=True)
# ── Martial melee ───────────────────────────────────────────────────────────
_w("Battleaxe", "1d8", "slashing", "martial", 4, versatile="1d10")
_w("Flail", "1d8", "bludgeoning", "martial", 2)
_w("Glaive", "1d10", "slashing", "martial", 6, versatile=None)
_w("Greataxe", "1d12", "slashing", "martial", 7)
_w("Greatsword", "2d6", "slashing", "martial", 6)
_w("Halberd", "1d10", "slashing", "martial", 6)
_w("Lance", "1d12", "piercing", "martial", 6)
_w("Longsword", "1d8", "slashing", "martial", 3, versatile="1d10")
_w("Maul", "2d6", "bludgeoning", "martial", 10)
_w("Morningstar", "1d8", "piercing", "martial", 4)
_w("Rapier", "1d8", "piercing", "martial", 2, finesse=True)
_w("Scimitar", "1d6", "slashing", "martial", 3, finesse=True)
_w("Shortsword", "1d6", "piercing", "martial", 2, finesse=True)
_w("Trident", "1d6", "piercing", "martial", 4, thrown=True, versatile="1d8")
_w("War Pick", "1d8", "piercing", "martial", 2)
_w("Warhammer", "1d8", "bludgeoning", "martial", 2, versatile="1d10")
_w("Whip", "1d4", "slashing", "martial", 3, finesse=True)
# ── Martial ranged ──────────────────────────────────────────────────────────
_w("Hand Crossbow", "1d6", "piercing", "martial", 3, ranged=True)
_w("Heavy Crossbow", "1d10", "piercing", "martial", 18, ranged=True)
_w("Longbow", "1d8", "piercing", "martial", 2, ranged=True)


def mod(score) -> int:
    try:
        return (int(score) - 10) // 2
    except (TypeError, ValueError):
        return 0


def _sing(s: str) -> str:
    s = s.strip().lower()
    return s[:-1] if s.endswith("s") else s


def find_weapon(name: str) -> dict | None:
    """Match an item name to a known weapon (case/plural-insensitive)."""
    if not name:
        return None
    key = name.strip().lower()
    if key in WEAPONS:
        return WEAPONS[key]
    sk = _sing(key)
    for k, w in WEAPONS.items():
        if _sing(k) == sk:
            return w
    return None


def is_proficient(weapon: dict, profs: list[str]) -> bool:
    """Whether the character is proficient with this weapon, given their weapon
    proficiency strings (names like 'Daggers' or categories like 'Martial
    Weapons' / 'Simple Weapons' / 'All weapons')."""
    cat = weapon["category"]
    wname = _sing(weapon["name"])
    for p in (x.strip().lower() for x in profs if x and x.strip()):
        if "all weapons" in p or p == "weapons":
            return True
        if cat in p and "weapon" in p:
            return True
        ps = _sing(p)
        if ps == wname or wname in ps.split() or ps in wname:
            return True
    return False


def weapon_attack(weapon: dict, abilities: dict, prof_bonus: int,
                  weapon_profs: list[str]) -> dict:
    """Derive an attack line: ability used, attack bonus, damage string."""
    sm, dm = mod(abilities.get("str", 10)), mod(abilities.get("dex", 10))
    ranged = weapon.get("ranged") and not weapon.get("thrown")
    if ranged:
        ability = "dex"
    elif weapon.get("finesse"):
        ability = "dex" if dm >= sm else "str"
    else:
        ability = "str"
    amod = dm if ability == "dex" else sm
    prof = is_proficient(weapon, weapon_profs)
    bonus = amod + (prof_bonus if prof else 0)
    dice = weapon["damage"]
    dmg = dice if amod == 0 else f"{dice} {amod:+d}"
    return {
        "name": weapon["name"], "ability": ability, "bonus": bonus,
        "proficient": prof, "damage": f"{dmg} {weapon['type']}".strip(),
        "damage_dice": dice, "damage_mod": amod, "damage_type": weapon["type"],
        "versatile": weapon.get("versatile"),
    }


_WEIGHT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound)", re.I)


def parse_weight(text: str):
    """Pull a 'N lb' weight out of free reference text, if present."""
    if not text:
        return None
    m = _WEIGHT_RE.search(text)
    return float(m.group(1)) if m else None
