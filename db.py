"""Database layer — all SQLite access for Arcane Sword.

This mirrors Arcane Shield's database infrastructure (self-healing connection,
rotating backups, CSV import/export framework, versioned migrations) so the two
apps stay in sync. For this scaffold it manages only the *reference* tables that
the player browses; character tables arrive in a later increment.
"""
import sqlite3
import json
import os
import re
import csv
import io
from pathlib import Path


def _db_path() -> Path:
    data_dir = Path(os.environ.get("APPDATA", Path.home())) / "ArcaneSword"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "arcane-sword.db"


def _backup_dir() -> Path:
    d = _db_path().parent / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _reference_dir() -> Path:
    """Bundled reference CSVs shipped with the repo (data/reference/)."""
    return Path(__file__).resolve().parent / "data" / "reference"


def _is_healthy(path: Path) -> bool:
    """True if the SQLite file opens and passes a quick integrity check."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        c = sqlite3.connect(path)
        try:
            ok = c.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        finally:
            c.close()
        return ok
    except Exception:
        return False


def _make_backup(conn: sqlite3.Connection, keep: int = 7) -> None:
    """Write a consistent snapshot to backups/ (uses the SQLite backup API so
    WAL contents are included), then prune to the most recent `keep`."""
    import time
    try:
        dst = _backup_dir() / f"arcane-sword_{time.strftime('%Y%m%d_%H%M%S')}.db"
        bck = sqlite3.connect(dst)
        with bck:
            conn.backup(bck)
        bck.close()
        backups = sorted(_backup_dir().glob("arcane-sword_*.db"))
        for old in backups[:-keep]:
            try:
                old.unlink()
            except Exception:
                pass
    except Exception:
        pass


def _auto_recover(path: Path) -> bool:
    """If the live DB is corrupt, move it aside and restore the newest healthy
    backup. Returns True if a restore happened."""
    if _is_healthy(path):
        return False
    # Newest-first list of restore candidates: rotating backups, then any
    # legacy .backup_* snapshots next to the DB.
    candidates = sorted(_backup_dir().glob("arcane-sword_*.db"), reverse=True)
    candidates += sorted(path.parent.glob("arcane-sword.db.backup_*"), reverse=True)
    good = next((b for b in candidates if _is_healthy(b)), None)
    if good is None:
        return False
    import time, shutil
    quarantine = path.parent / f"corrupt_{time.strftime('%Y%m%d_%H%M%S')}"
    quarantine.mkdir(exist_ok=True)
    for ext in ("", "-wal", "-shm"):
        f = Path(str(path) + ext)
        if f.exists():
            try:
                shutil.move(str(f), str(quarantine / f.name))
            except Exception:
                pass
    shutil.copy2(good, path)
    return True


def _connect() -> sqlite3.Connection:
    path = _db_path()
    _auto_recover(path)  # repair a corrupt DB from the latest good backup first
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    # ── Reference tables only (character tables land in a later increment) ──────
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS spells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 0,
            school TEXT NOT NULL DEFAULT '',
            casting_time TEXT NOT NULL DEFAULT '',
            range TEXT NOT NULL DEFAULT '',
            components TEXT NOT NULL DEFAULT '',
            duration TEXT NOT NULL DEFAULT '',
            concentration INTEGER NOT NULL DEFAULT 0,
            ritual INTEGER NOT NULL DEFAULT 0,
            classes TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            source TEXT,
            tags TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS character_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            parent TEXT NOT NULL DEFAULT '',
            body_md TEXT NOT NULL DEFAULT '',
            source TEXT,
            tags TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            ability TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'Standard',
            script TEXT NOT NULL DEFAULT '',
            typical_speakers TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS magic_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT '',
            rarity TEXT NOT NULL DEFAULT 'Common',
            requires_attunement INTEGER NOT NULL DEFAULT 0,
            attunement_requirement TEXT,
            description TEXT NOT NULL DEFAULT '',
            mechanical_effect TEXT NOT NULL DEFAULT '',
            charges INTEGER,
            source_campaign TEXT,
            tags TEXT NOT NULL DEFAULT '[]'
        );
    """)

    # Versioned one-time data migrations (PRAGMA user_version is the schema rev).
    try:
        ver = conn.execute("PRAGMA user_version").fetchone()[0]
        # (No data migrations yet — bump to 1 to anchor the scaffold revision.)
        if ver < 1:
            pass
        conn.execute("PRAGMA user_version = 1")
    except Exception:
        pass

    # ── Load the bundled compendium first (full reference data shipped in repo) ──
    # Each reference table is populated from data/reference/*.csv if it is empty.
    _load_bundled_reference(conn)

    # ── Seed fallbacks for the rules-text tables, in case a bundled CSV is
    # missing/empty (kept from Arcane Shield so the app is never empty).
    try:
        if conn.execute("SELECT COUNT(*) FROM conditions").fetchone()[0] == 0:
            for i, (nm, desc) in enumerate(_CONDITION_SEED):
                conn.execute(
                    "INSERT OR IGNORE INTO conditions (name,description,sort_order) VALUES (?,?,?)",
                    (nm, desc, i))
    except Exception:
        pass
    try:
        if conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 0:
            for i, (nm, ab, desc) in enumerate(_SKILL_SEED):
                conn.execute(
                    "INSERT OR IGNORE INTO skills (name,ability,description,sort_order) VALUES (?,?,?,?)",
                    (nm, ab, desc, i))
    except Exception:
        pass
    try:
        if conn.execute("SELECT COUNT(*) FROM languages").fetchone()[0] == 0:
            for i, (nm, cat, scr, spk, desc) in enumerate(_LANGUAGE_SEED):
                conn.execute(
                    "INSERT OR IGNORE INTO languages "
                    "(name,category,script,typical_speakers,description,sort_order) "
                    "VALUES (?,?,?,?,?,?)", (nm, cat, scr, spk, desc, i))
    except Exception:
        pass
    conn.commit()


# Column orders for the bundled reference CSVs — match Arcane Shield's
# export_csv output (tags are stored as ";"-joined strings in the CSV).
_REFERENCE_SPECS: list[tuple[str, str, list[str], set[str]]] = [
    ("spells.csv", "spells",
     ["name", "level", "school", "casting_time", "range", "components", "duration",
      "concentration", "ritual", "classes", "description", "source", "tags"], {"tags"}),
    ("character_options.csv", "character_options",
     ["category", "name", "parent", "body_md", "source", "tags"], {"tags"}),
    ("magic_items.csv", "magic_items",
     ["name", "item_type", "rarity", "requires_attunement", "attunement_requirement",
      "description", "mechanical_effect", "charges", "source_campaign", "tags"], {"tags"}),
    ("conditions.csv", "conditions", ["name", "description", "sort_order"], set()),
    ("skills.csv", "skills", ["name", "ability", "description", "sort_order"], set()),
    ("languages.csv", "languages",
     ["name", "category", "script", "typical_speakers", "description", "sort_order"], set()),
]

_INT_COLS = {"level", "concentration", "ritual", "requires_attunement", "charges", "sort_order"}


def _load_bundled_reference(conn: sqlite3.Connection) -> None:
    """Populate each reference table from its bundled CSV when the table is
    empty. A ";"-joined tag column is re-encoded as the JSON the schema stores."""
    ref_dir = _reference_dir()
    for fname, table, cols, jtags in _REFERENCE_SPECS:
        path = ref_dir / fname
        if not path.exists():
            continue
        try:
            if conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] != 0:
                continue  # already populated — never overwrite
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                placeholders = ",".join("?" for _ in cols)
                sql = f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
                rows = []
                for row in reader:
                    vals = []
                    for c in cols:
                        v = row.get(c)
                        if c in jtags:
                            parts = [p.strip() for p in (v or "").split(";") if p.strip()]
                            vals.append(json.dumps(parts))
                        elif c in _INT_COLS:
                            vals.append(_int(v, 0 if c != "charges" else None))
                        else:
                            vals.append(v if v not in (None, "") else "")
                    rows.append(vals)
                if rows:
                    conn.executemany(sql, rows)
        except Exception:
            pass
    conn.commit()


# Standard 5e languages (PHB). (name, category, script, typical_speakers, description)
_LANGUAGE_SEED = [
    ("Common", "Standard", "Common", "Humans, most civilized folk",
     "The trade tongue of most of the multiverse; nearly everyone speaks it."),
    ("Dwarvish", "Standard", "Dwarvish", "Dwarves",
     "Full of hard consonants and guttural sounds; carries into runic writing."),
    ("Elvish", "Standard", "Elvish", "Elves",
     "Fluid, with subtle intonations and intricate grammar; a beautiful script."),
    ("Giant", "Standard", "Dwarvish", "Giants, ogres",
     "The language of giantkind, descended from the Ordning's ancient tongue."),
    ("Gnomish", "Standard", "Dwarvish", "Gnomes",
     "Known for its technical treatises and catalogs of knowledge."),
    ("Goblin", "Standard", "Dwarvish", "Goblinoids (goblins, hobgoblins, bugbears)",
     "A harsh tongue spoken across goblinoid warbands."),
    ("Halfling", "Standard", "Common", "Halflings",
     "Rarely written; halflings pass it along orally and keep few secrets in it."),
    ("Orc", "Standard", "Dwarvish", "Orcs",
     "A grating language with hard consonants, borrowing the Dwarvish script."),
    ("Abyssal", "Exotic", "Infernal", "Demons, chaotic-evil outsiders",
     "The chaotic, vile speech of the demons of the Abyss."),
    ("Celestial", "Exotic", "Celestial", "Celestials (angels, devas)",
     "The melodic language of the upper planes."),
    ("Draconic", "Exotic", "Draconic", "Dragons, dragonborn, kobolds",
     "Thought to be one of the oldest languages; used in much arcane writing."),
    ("Deep Speech", "Exotic", "—", "Aberrations (mind flayers, beholders)",
     "An alien tongue of aberrations; impossible for most to speak without practice."),
    ("Infernal", "Exotic", "Infernal", "Devils, lawful-evil outsiders",
     "The precise, contractual language of the Nine Hells."),
    ("Primordial", "Exotic", "Dwarvish", "Elementals",
     "The elemental tongue, with dialects Aquan, Auran, Ignan, and Terran."),
    ("Sylvan", "Exotic", "Elvish", "Fey creatures",
     "The language of the Feywild and its fey inhabitants."),
    ("Undercommon", "Exotic", "Elvish", "Underdark traders (drow, etc.)",
     "The trade language of the Underdark."),
    ("Druidic", "Secret", "Druidic", "Druids only",
     "The secret language of druids; outsiders cannot learn it. Can leave hidden messages."),
    ("Thieves' Cant", "Secret", "—", "Rogues",
     "A secret mix of dialect, jargon, and code that lets rogues hide messages in conversation."),
]


# Standard 5e conditions — concise, paraphrased mechanical summaries.
_CONDITION_SEED = [
    ("Blinded", "- Can't see; automatically fails any check requiring sight.\n"
                "- Attack rolls against the creature have **advantage**; its own attack rolls have **disadvantage**."),
    ("Charmed", "- Can't attack the charmer or target them with harmful effects.\n"
                "- The charmer has **advantage** on social ability checks to interact with the creature."),
    ("Deafened", "- Can't hear; automatically fails any check requiring hearing."),
    ("Exhaustion", "Measured in 6 levels (cumulative):\n"
                   "1. Disadvantage on ability checks\n2. Speed halved\n"
                   "3. Disadvantage on attack rolls & saving throws\n4. Hit point maximum halved\n"
                   "5. Speed reduced to 0\n6. Death.\nA long rest removes one level (with food & drink)."),
    ("Frightened", "- Disadvantage on ability checks and attack rolls while the source of fear is in line of sight.\n"
                   "- Can't willingly move closer to the source."),
    ("Grappled", "- Speed becomes 0; can't benefit from bonuses to speed.\n"
                 "- Ends if the grappler is incapacitated or the creature is removed from reach."),
    ("Incapacitated", "- Can't take actions or reactions."),
    ("Invisible", "- Impossible to see without special senses; counts as heavily obscured.\n"
                  "- Attack rolls against the creature have **disadvantage**; its own attack rolls have **advantage**."),
    ("Paralyzed", "- Incapacitated; can't move or speak.\n"
                  "- Automatically fails STR and DEX saves.\n"
                  "- Attacks against it have advantage; any hit from within 5 ft. is a **critical hit**."),
    ("Petrified", "- Transformed to solid substance; incapacitated, can't move or speak, unaware.\n"
                  "- Weight x10, stops aging; attacks have advantage; fails STR & DEX saves.\n"
                  "- Resistance to all damage; immune to poison and disease."),
    ("Poisoned", "- Disadvantage on attack rolls and ability checks."),
    ("Prone", "- Can only crawl unless it stands up (costs half its movement).\n"
              "- Disadvantage on attack rolls.\n"
              "- Attacks within 5 ft. have advantage; ranged attacks against it have disadvantage."),
    ("Restrained", "- Speed becomes 0.\n"
                   "- Attacks against it have advantage; its own attacks have disadvantage.\n"
                   "- Disadvantage on DEX saving throws."),
    ("Stunned", "- Incapacitated, can't move, can speak only falteringly.\n"
                "- Automatically fails STR and DEX saves; attacks against it have advantage."),
    ("Unconscious", "- Incapacitated, can't move or speak, unaware; drops what it's holding and falls prone.\n"
                    "- Fails STR & DEX saves; attacks have advantage; hits within 5 ft. are **critical hits**."),
]


# The 18 standard skills: (name, governing ability, short usage summary).
_SKILL_SEED = [
    ("Acrobatics", "Dexterity", "Keep your balance on tricky terrain, tumble, or slip free of a grapple."),
    ("Animal Handling", "Wisdom", "Calm or control an animal, read its intentions, or handle a mount in a crisis."),
    ("Arcana", "Intelligence", "Recall lore about spells, magic items, eldritch symbols, and the planes."),
    ("Athletics", "Strength", "Climb, jump, swim, grapple, shove, or muscle past physical obstacles."),
    ("Deception", "Charisma", "Convincingly hide the truth in word or deed; mislead, bluff, or disguise intent."),
    ("History", "Intelligence", "Recall lore about events, ancient kingdoms, wars, and legendary figures."),
    ("Insight", "Wisdom", "Read a creature's true intentions — detect a lie or predict a next move."),
    ("Intimidation", "Charisma", "Influence through overt threats, hostile actions, or sheer menace."),
    ("Investigation", "Intelligence", "Deduce from clues, search for hidden details, infer how something works."),
    ("Medicine", "Wisdom", "Stabilize a dying creature or diagnose an illness."),
    ("Nature", "Intelligence", "Recall lore about terrain, plants, animals, weather, and natural cycles."),
    ("Perception", "Wisdom", "Spot, hear, or otherwise notice the presence of something."),
    ("Performance", "Charisma", "Delight an audience with music, dance, acting, or storytelling."),
    ("Persuasion", "Charisma", "Influence with tact, social grace, and good faith."),
    ("Religion", "Intelligence", "Recall lore about deities, rites, prayers, and holy symbols."),
    ("Sleight of Hand", "Dexterity", "Pick pockets, plant an item, conceal an object, or perform legerdemain."),
    ("Stealth", "Dexterity", "Hide, move silently, and slip past notice."),
    ("Survival", "Wisdom", "Track, hunt, navigate the wilds, forecast weather, and avoid natural hazards."),
]


def _rows(rs) -> list[dict]:
    return [dict(r) for r in rs]


def _tags_in(row: dict) -> dict:
    if "tags" in row:
        row["tags"] = json.loads(row["tags"] or "[]")
    return row


def _feat_has_prereq(body_md: str) -> bool:
    """True if a feat's body lists a real prerequisite (not 'None')."""
    m = re.search(r"(?i)prerequisite:\**\s*([^\n]*)", body_md or "")
    if not m:
        return False
    val = m.group(1).strip().strip("*").strip()
    return bool(val) and val.lower() not in ("none", "-", "—", "n/a")


def _tag_list(tags) -> list[str]:
    if isinstance(tags, list):
        return tags
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(";") if t.strip()]
    return []


class Database:
    def __init__(self):
        self.conn = _connect()
        _migrate(self.conn)
        self._bulk = False  # when True, create_* defer committing (see import_csv)
        # Snapshot a healthy DB on every clean launch so auto-recovery always
        # has a recent good copy to fall back on.
        _make_backup(self.conn)

    def _autocommit(self):
        """Commit unless a bulk operation is batching writes into one transaction."""
        if not self._bulk:
            self.conn.commit()

    # ── Spells ─────────────────────────────────────────────────────────────────

    def list_spells(self, search="", level="", school="", cls="") -> list[dict]:
        q = "SELECT * FROM spells WHERE 1=1"; p: list = []
        if search:
            q += " AND (name LIKE ? OR description LIKE ?)"; p += [f"%{search}%", f"%{search}%"]
        if level != "" and level is not None:
            q += " AND level=?"; p.append(int(level))
        if school:
            q += " AND school=?"; p.append(school)
        q += " ORDER BY level, name"
        rows = [_tags_in(r) for r in _rows(self.conn.execute(q, p).fetchall())]
        if cls:
            low = cls.lower()
            rows = [r for r in rows if low in (r.get("classes", "") or "").lower()]
        return rows

    def create_spell(self, d: dict) -> int:
        tags = json.dumps(_tag_list(d.get("tags", [])))
        cur = self.conn.execute(
            "INSERT INTO spells (name,level,school,casting_time,range,components,duration,"
            "concentration,ritual,classes,description,source,tags) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d["name"], int(d.get("level", 0) or 0), d.get("school", ""),
             d.get("casting_time", ""), d.get("range", ""), d.get("components", ""),
             d.get("duration", ""), 1 if d.get("concentration") else 0,
             1 if d.get("ritual") else 0, d.get("classes", ""), d.get("description", ""),
             d.get("source") or None, tags)
        )
        self._autocommit()
        return cur.lastrowid

    def update_spell(self, id: int, d: dict) -> None:
        tags = json.dumps(_tag_list(d.get("tags", [])))
        self.conn.execute(
            "UPDATE spells SET name=?,level=?,school=?,casting_time=?,range=?,components=?,"
            "duration=?,concentration=?,ritual=?,classes=?,description=?,source=?,tags=? WHERE id=?",
            (d["name"], int(d.get("level", 0) or 0), d.get("school", ""),
             d.get("casting_time", ""), d.get("range", ""), d.get("components", ""),
             d.get("duration", ""), 1 if d.get("concentration") else 0,
             1 if d.get("ritual") else 0, d.get("classes", ""), d.get("description", ""),
             d.get("source") or None, tags, id)
        )
        self.conn.commit()

    def delete_spell(self, id: int) -> None:
        self.conn.execute("DELETE FROM spells WHERE id=?", (id,)); self.conn.commit()

    def spell_schools(self) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT school FROM spells WHERE school!='' ORDER BY school"
        ).fetchall()]

    def spell_levels(self) -> list[int]:
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT level FROM spells ORDER BY level"
        ).fetchall()]

    def spell_classes(self) -> list[str]:
        out: set[str] = set()
        for r in self.conn.execute("SELECT classes FROM spells WHERE classes!=''").fetchall():
            for c in re.split(r"[;,]", r[0]):
                c = c.strip()
                if c:
                    out.add(c)
        return sorted(out, key=str.lower)

    # ── Conditions ─────────────────────────────────────────────────────────────

    def list_conditions(self, search="") -> list[dict]:
        q = "SELECT * FROM conditions WHERE 1=1"; p: list = []
        if search:
            q += " AND (name LIKE ? OR description LIKE ?)"; p += [f"%{search}%", f"%{search}%"]
        q += " ORDER BY sort_order, name"
        return _rows(self.conn.execute(q, p).fetchall())

    def condition_names(self) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT name FROM conditions ORDER BY sort_order, name"
        ).fetchall()]

    def create_condition(self, d: dict) -> int:
        order = self.conn.execute(
            "SELECT COALESCE(MAX(sort_order),0)+1 FROM conditions").fetchone()[0]
        cur = self.conn.execute(
            "INSERT INTO conditions (name,description,sort_order) VALUES (?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET description=excluded.description",
            (d["name"], d.get("description", ""), d.get("sort_order", order))
        )
        self._autocommit()
        return cur.lastrowid

    def update_condition(self, id: int, d: dict) -> None:
        self.conn.execute(
            "UPDATE conditions SET name=?,description=? WHERE id=?",
            (d["name"], d.get("description", ""), id)
        )
        self.conn.commit()

    def delete_condition(self, id: int) -> None:
        self.conn.execute("DELETE FROM conditions WHERE id=?", (id,)); self.conn.commit()

    # ── Character Options (races / classes / subclasses / backgrounds / feats) ──

    def list_char_options(self, category="", search="", source="",
                          boon=None, prereq=None) -> list[dict]:
        q = "SELECT * FROM character_options WHERE 1=1"; p: list = []
        if category:
            q += " AND category=?"; p.append(category)
        if search:
            q += " AND (name LIKE ? OR body_md LIKE ?)"; p += [f"%{search}%", f"%{search}%"]
        if source:
            q += " AND LOWER(COALESCE(source,''))=?"; p.append(source.lower())
        if boon is True:
            q += " AND LOWER(name) LIKE '%boon%'"
        elif boon is False:
            q += " AND LOWER(name) NOT LIKE '%boon%'"
        q += " ORDER BY name"
        rows = [_tags_in(r) for r in _rows(self.conn.execute(q, p).fetchall())]
        if prereq is not None:
            rows = [r for r in rows if _feat_has_prereq(r.get("body_md", "")) == prereq]
        return rows

    def char_feat_sources(self) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT source FROM character_options "
            "WHERE category='feat' AND source IS NOT NULL AND source!='' ORDER BY source"
        ).fetchall()]

    def create_char_option(self, d: dict) -> int:
        tags = json.dumps(_tag_list(d.get("tags", [])))
        cur = self.conn.execute(
            "INSERT INTO character_options (category,name,parent,body_md,source,tags) "
            "VALUES (?,?,?,?,?,?)",
            (d["category"], d["name"], d.get("parent", ""), d.get("body_md", ""),
             d.get("source") or None, tags)
        )
        self._autocommit()
        return cur.lastrowid

    def update_char_option(self, id: int, d: dict) -> None:
        tags = json.dumps(_tag_list(d.get("tags", [])))
        self.conn.execute(
            "UPDATE character_options SET category=?,name=?,parent=?,body_md=?,source=?,tags=? WHERE id=?",
            (d["category"], d["name"], d.get("parent", ""), d.get("body_md", ""),
             d.get("source") or None, tags, id)
        )
        self.conn.commit()

    def delete_char_option(self, id: int) -> None:
        self.conn.execute("DELETE FROM character_options WHERE id=?", (id,)); self.conn.commit()

    def clear_char_category(self, category: str) -> int:
        cur = self.conn.execute("DELETE FROM character_options WHERE category=?", (category,))
        self.conn.commit()
        return cur.rowcount

    # ── Skill Checks (18 standard skills reference) ─────────────────────────────

    def list_skills(self, search="") -> list[dict]:
        q = "SELECT * FROM skills WHERE 1=1"; p: list = []
        if search:
            q += " AND (name LIKE ? OR ability LIKE ? OR description LIKE ?)"
            p += [f"%{search}%", f"%{search}%", f"%{search}%"]
        q += " ORDER BY sort_order, name"
        return _rows(self.conn.execute(q, p).fetchall())

    def create_skill(self, d: dict) -> int:
        order = self.conn.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM skills").fetchone()[0]
        cur = self.conn.execute(
            "INSERT INTO skills (name,ability,description,sort_order) VALUES (?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET ability=excluded.ability, description=excluded.description",
            (d["name"], d.get("ability", ""), d.get("description", ""), d.get("sort_order", order))
        )
        self._autocommit()
        return cur.lastrowid

    def update_skill(self, id: int, d: dict) -> None:
        self.conn.execute(
            "UPDATE skills SET name=?,ability=?,description=? WHERE id=?",
            (d["name"], d.get("ability", ""), d.get("description", ""), id)
        )
        self.conn.commit()

    def delete_skill(self, id: int) -> None:
        self.conn.execute("DELETE FROM skills WHERE id=?", (id,)); self.conn.commit()

    # ── Languages ──────────────────────────────────────────────────────────────

    def list_languages(self, search="", category="") -> list[dict]:
        q = "SELECT * FROM languages WHERE 1=1"; p: list = []
        if search:
            q += " AND (name LIKE ? OR typical_speakers LIKE ? OR description LIKE ?)"
            p += [f"%{search}%", f"%{search}%", f"%{search}%"]
        if category:
            q += " AND category=?"; p.append(category)
        q += " ORDER BY category, sort_order, name"
        return _rows(self.conn.execute(q, p).fetchall())

    def language_categories(self) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT category FROM languages WHERE category!='' ORDER BY category"
        ).fetchall()]

    def create_language(self, d: dict) -> int:
        order = self.conn.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM languages").fetchone()[0]
        cur = self.conn.execute(
            "INSERT INTO languages (name,category,script,typical_speakers,description,sort_order) "
            "VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET category=excluded.category, script=excluded.script, "
            "typical_speakers=excluded.typical_speakers, description=excluded.description",
            (d["name"], d.get("category", "Standard"), d.get("script", ""),
             d.get("typical_speakers", ""), d.get("description", ""), d.get("sort_order", order))
        )
        self._autocommit()
        return cur.lastrowid

    def update_language(self, id: int, d: dict) -> None:
        self.conn.execute(
            "UPDATE languages SET name=?,category=?,script=?,typical_speakers=?,description=? WHERE id=?",
            (d["name"], d.get("category", "Standard"), d.get("script", ""),
             d.get("typical_speakers", ""), d.get("description", ""), id)
        )
        self.conn.commit()

    def delete_language(self, id: int) -> None:
        self.conn.execute("DELETE FROM languages WHERE id=?", (id,)); self.conn.commit()

    # ── Magic Items ────────────────────────────────────────────────────────────

    def list_items(self, search="", item_type="", rarity="",
                   attunement="", tag="") -> list[dict]:
        q = "SELECT * FROM magic_items WHERE 1=1"
        p: list = []
        if search:
            q += " AND (name LIKE ? OR description LIKE ?)"; p += [f"%{search}%", f"%{search}%"]
        if item_type:
            q += " AND item_type=?"; p.append(item_type)
        if rarity:
            q += " AND rarity=?"; p.append(rarity)
        if attunement == "yes":
            q += " AND requires_attunement=1"
        elif attunement == "no":
            q += " AND requires_attunement=0"
        q += " ORDER BY name"
        rows = [_tags_in(r) for r in _rows(self.conn.execute(q, p).fetchall())]
        if tag:
            rows = [r for r in rows if tag in r.get("tags", [])]
        return rows

    def create_item(self, d: dict) -> int:
        tags = json.dumps(_tag_list(d.get("tags", [])))
        cur = self.conn.execute(
            "INSERT INTO magic_items (name,item_type,rarity,requires_attunement,attunement_requirement,"
            "description,mechanical_effect,charges,source_campaign,tags) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (d["name"], d.get("item_type",""), d.get("rarity","Common"),
             1 if d.get("requires_attunement") else 0, d.get("attunement_requirement") or None,
             d.get("description",""), d.get("mechanical_effect",""),
             d.get("charges") or None, d.get("source_campaign") or None, tags)
        )
        self._autocommit()
        return cur.lastrowid

    def update_item(self, id: int, d: dict) -> None:
        tags = json.dumps(_tag_list(d.get("tags", [])))
        self.conn.execute(
            "UPDATE magic_items SET name=?,item_type=?,rarity=?,requires_attunement=?,"
            "attunement_requirement=?,description=?,mechanical_effect=?,charges=?,source_campaign=?,tags=? WHERE id=?",
            (d["name"], d.get("item_type",""), d.get("rarity","Common"),
             1 if d.get("requires_attunement") else 0, d.get("attunement_requirement") or None,
             d.get("description",""), d.get("mechanical_effect",""),
             d.get("charges") or None, d.get("source_campaign") or None, tags, id)
        )
        self.conn.commit()

    def delete_item(self, id: int) -> None:
        self.conn.execute("DELETE FROM magic_items WHERE id=?", (id,)); self.conn.commit()

    def item_types(self) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT item_type FROM magic_items WHERE item_type!='' ORDER BY item_type"
        ).fetchall()]

    def _distinct_tags(self, table: str) -> list[str]:
        """Collect the unique set of tags across every row of a tagged table."""
        out: set[str] = set()
        for r in self.conn.execute(f"SELECT tags FROM {table}").fetchall():
            try:
                for t in json.loads(r[0] or "[]"):
                    if t:
                        out.add(t)
            except Exception:
                pass
        return sorted(out, key=str.lower)

    def item_tags(self) -> list[str]:
        return self._distinct_tags("magic_items")

    # ── Bulk clear ─────────────────────────────────────────────────────────────

    CLEARABLE_TABLES = {
        "spells":            "Spells",
        "magic_items":       "Magic Items",
        "character_options": "Character Options",
    }

    def clear_table(self, table: str) -> int:
        """Delete all rows from a clearable table. Returns number of rows deleted."""
        if table not in self.CLEARABLE_TABLES:
            raise ValueError(f"Table '{table}' is not clearable.")
        cur = self.conn.execute(f"DELETE FROM {table}")
        self.conn.commit()
        return cur.rowcount

    # Every reference table (character tables arrive in a later increment).
    DATA_TABLES = [
        "spells", "character_options", "conditions", "skills", "languages", "magic_items",
    ]

    def total_row_count(self) -> int:
        """Total rows across all data tables."""
        total = 0
        for t in self.DATA_TABLES:
            try:
                total += self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass
        return total

    # ── CSV Export ─────────────────────────────────────────────────────────────

    def export_csv(self, table: str) -> str:
        out = io.StringIO()
        w = csv.writer(out)

        if table == "spells":
            cols = ["name","level","school","casting_time","range","components",
                    "duration","concentration","ritual","classes","description","source","tags"]
            w.writerow(cols)
            for r in self.conn.execute(
                    "SELECT name,level,school,casting_time,range,components,duration,"
                    "concentration,ritual,classes,description,source,tags FROM spells").fetchall():
                row = list(r)
                row[-1] = ";".join(json.loads(row[-1] or "[]"))
                w.writerow(row)

        elif table == "character_options":
            w.writerow(["category","name","parent","body_md","source","tags"])
            for r in self.conn.execute(
                    "SELECT category,name,parent,body_md,source,tags FROM character_options").fetchall():
                row = list(r)
                row[-1] = ";".join(json.loads(row[-1] or "[]"))
                w.writerow(row)

        elif table == "magic_items":
            w.writerow(["name","item_type","rarity","requires_attunement","attunement_requirement","description","mechanical_effect","charges","source_campaign","tags"])
            for r in self.conn.execute("SELECT name,item_type,rarity,requires_attunement,attunement_requirement,description,mechanical_effect,charges,source_campaign,tags FROM magic_items").fetchall():
                row = list(r)
                row[-1] = ";".join(json.loads(row[-1] or "[]"))
                w.writerow(row)

        elif table == "conditions":
            w.writerow(["name","description","sort_order"])
            for r in self.conn.execute("SELECT name,description,sort_order FROM conditions").fetchall():
                w.writerow(list(r))

        elif table == "skills":
            w.writerow(["name","ability","description","sort_order"])
            for r in self.conn.execute("SELECT name,ability,description,sort_order FROM skills").fetchall():
                w.writerow(list(r))

        elif table == "languages":
            w.writerow(["name","category","script","typical_speakers","description","sort_order"])
            for r in self.conn.execute("SELECT name,category,script,typical_speakers,description,sort_order FROM languages").fetchall():
                w.writerow(list(r))

        return out.getvalue()

    # ── CSV Import ─────────────────────────────────────────────────────────────

    def import_csv(self, filename: str, text: str) -> dict:
        """Auto-detect table from headers/filename and import rows."""
        try:
            reader = csv.DictReader(io.StringIO(text))
            headers = set(reader.fieldnames or [])
        except Exception as e:
            return {"table": "unknown", "inserted": 0, "skipped": 0, "errors": [str(e)]}

        table = _detect_table(headers, filename)
        if not table:
            return {"table": "unknown", "inserted": 0, "skipped": 0,
                    "errors": [f"Cannot detect table from headers: {headers}"]}

        inserted = 0; skipped = 0; errors: list[str] = []
        reader = csv.DictReader(io.StringIO(text))
        self._bulk = True  # batch the whole file into ONE transaction (avoids per-row fsync)
        for i, row in enumerate(reader, start=2):
            try:
                row = {k: (v.strip() if v else v) for k, v in row.items()}
                if table == "magic_items":
                    if not row.get("name"): skipped += 1; continue
                    self.create_item({
                        "name": row["name"],
                        "item_type": row.get("item_type",""),
                        "rarity": row.get("rarity","Common"),
                        "requires_attunement": row.get("requires_attunement","").lower() in ("1","true","yes"),
                        "attunement_requirement": row.get("attunement_requirement"),
                        "description": row.get("description",""),
                        "mechanical_effect": row.get("mechanical_effect",""),
                        "charges": _int(row.get("charges"), None),
                        "source_campaign": row.get("source_campaign"),
                        "tags": _tag_list(row.get("tags","")),
                    })
                elif table == "character_options":
                    if not row.get("name") or not row.get("category"): skipped += 1; continue
                    self.create_char_option({
                        "category": row["category"].strip().lower(),
                        "name": row["name"],
                        "parent": row.get("parent",""),
                        "body_md": row.get("body_md",""),
                        "source": row.get("source"),
                        "tags": _tag_list(row.get("tags","")),
                    })
                elif table == "spells":
                    if not row.get("name"): skipped += 1; continue
                    self.create_spell({
                        "name": row["name"],
                        "level": _int(row.get("level"), 0),
                        "school": row.get("school",""),
                        "casting_time": row.get("casting_time",""),
                        "range": row.get("range",""),
                        "components": row.get("components",""),
                        "duration": row.get("duration",""),
                        "concentration": str(row.get("concentration","")).lower() in ("1","true","yes"),
                        "ritual": str(row.get("ritual","")).lower() in ("1","true","yes"),
                        "classes": row.get("classes",""),
                        "description": row.get("description",""),
                        "source": row.get("source"),
                        "tags": _tag_list(row.get("tags","")),
                    })
                elif table == "conditions":
                    if not row.get("name"): skipped += 1; continue
                    self.create_condition({
                        "name": row["name"],
                        "description": row.get("description",""),
                        "sort_order": _int(row.get("sort_order"), 0),
                    })
                elif table == "skills":
                    if not row.get("name"): skipped += 1; continue
                    self.create_skill({
                        "name": row["name"],
                        "ability": row.get("ability",""),
                        "description": row.get("description",""),
                        "sort_order": _int(row.get("sort_order"), 0),
                    })
                elif table == "languages":
                    if not row.get("name"): skipped += 1; continue
                    self.create_language({
                        "name": row["name"],
                        "category": row.get("category","Standard"),
                        "script": row.get("script",""),
                        "typical_speakers": row.get("typical_speakers",""),
                        "description": row.get("description",""),
                        "sort_order": _int(row.get("sort_order"), 0),
                    })
                inserted += 1
            except Exception as e:
                errors.append(f"Row {i}: {e}")
        try:
            self.conn.commit()  # single commit for the whole file
        finally:
            self._bulk = False
        return {"table": table, "inserted": inserted, "skipped": skipped, "errors": errors}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _int(v, default):
    try:
        return int(v) if v not in (None, "", "None") else default
    except (ValueError, TypeError):
        return default


def _detect_table(headers: set, filename: str) -> str | None:
    h = {c.lower() for c in headers}

    # Header-based detection (most reliable)
    if "category" in h and "name" in h and ("parent" in h or "body_md" in h):
        return "character_options"
    if "item_type" in h and "rarity" in h:
        return "magic_items"
    if "school" in h and ("level" in h or "casting_time" in h):
        return "spells"
    if "ability" in h and "name" in h:
        return "skills"
    if "typical_speakers" in h or "script" in h:
        return "languages"
    if "name" in h and "description" in h and "sort_order" in h:
        return "conditions"

    # Filename fallback
    fn = filename.lower()
    if "spell" in fn:
        return "spells"
    if any(x in fn for x in ("magic", "item")):
        return "magic_items"
    if any(x in fn for x in ("character_option", "char_opt", "feat", "race", "class", "background")):
        return "character_options"
    if "condition" in fn:
        return "conditions"
    if "skill" in fn:
        return "skills"
    if any(x in fn for x in ("language", "tongue")):
        return "languages"

    return None
