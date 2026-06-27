"""Helpers to match a character's race/class/subclass/background/feat to the
character_options reference rows, and to turn a reference row into a
character_features dict. Shared by the Features and Level-Up tabs.
"""


def find_option(db, category: str, name: str, parent: str | None = None) -> dict | None:
    if not (name or "").strip():
        return None
    rows = db.list_char_options(category=category)
    nm = name.strip().lower()
    cands = [r for r in rows if (r.get("name") or "").strip().lower() == nm]
    if parent:
        p = parent.strip().lower()
        pc = [r for r in cands if (r.get("parent") or "").strip().lower() == p]
        if pc:
            cands = pc
    if cands:
        return cands[0]
    # Loose fallback: a row whose name contains the query (or vice versa).
    for r in rows:
        rn = (r.get("name") or "").strip().lower()
        if rn and (nm in rn or rn in nm):
            if not parent or (r.get("parent") or "").strip().lower() == parent.strip().lower():
                return r
    return None


def find_race_option(db, race: str, subrace: str = "") -> dict | None:
    """Races are named like 'Elf', 'Aasimar, Fallen', etc. Try sensible combos."""
    race = (race or "").strip()
    subrace = (subrace or "").strip()
    candidates = []
    if subrace:
        candidates += [f"{race}, {subrace}", f"{subrace} {race}", f"{race} ({subrace})", subrace]
    if race:
        candidates.append(race)
    for c in candidates:
        opt = find_option(db, "race", c)
        if opt:
            return opt
    return None


def feature_from_option(opt: dict, source_type: str) -> dict:
    return {
        "source_type": source_type,
        "source_name": opt.get("name", ""),
        "name": opt.get("name", ""),
        "description": opt.get("body_md", "") or "",
    }
