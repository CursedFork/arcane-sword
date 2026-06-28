# Arcane Sword 🗡

**Arcane Sword** is the *player companion* to
[Arcane Shield](https://github.com/CursedFork/arcane-shield) — a desktop D&D 5e
**character builder and play companion**, sharing Arcane Shield's look, feel, and
reference compendium.

Where Arcane Shield is the **DM's** reference and screen, Arcane Sword puts the
same offline 5e compendium — spells, character options, conditions, skills,
languages, and magic items — into the **player's** hands, and adds everything you
need to build, level, and run a character: a full character sheet, spellbook and
slots, inventory, actions, features, leveling (with multiclassing), rests, and
per-character campaign notes.

Everything runs **fully offline** against a local SQLite database. No account, no
internet, no DM required.

## Features

### Build & run a character
- **Character Sheet** — abilities with live modifiers, saving throws, all 18
  skills (proficiency / expertise), AC, initiative, speed, hit dice, an HP bar
  with Damage / Heal / Temp and death saves, passive senses (with overrides),
  conditions (with rules pop-ups), and defenses. A character **picker** at the
  top switches who every tab is showing.
- **Level-Up** — level an existing class or **multiclass** (with the standard
  ability prerequisites enforced). Walks you through subclass selection at the
  right level, **ASI-or-Feat** at ASI levels, HP (roll or average), and pulls the
  relevant class/subclass features. Proficiency bonus, spell slots, and prepared
  counts all recompute automatically. Level-ups are reversible.
- **Spells — Available** — the spells your class(es) can use, filtered by
  level / school, with one-click **Know** / **Prepare**.
- **Spellbook** — your spells grouped by level (cantrips first), prepared and
  always-prepared toggles, a **Prepared X / max** counter, and a **spell-slot
  tracker** (multiclass caster table + Warlock Pact Magic) — expend and restore
  slots.
- **Actions** — derived attacks for your equipped weapons (to-hit and damage,
  STR/DEX with finesse), plus spells grouped by casting time and custom actions.
- **Inventory** — add gear from the compendium or as custom items; quantities,
  equip/attune toggles (3-item attunement cap), carried-weight estimate.
- **Features & Traits** — grouped by source (Race / Class / Subclass /
  Background / Feat), Markdown-rendered. **Pull from reference** auto-populates
  them from the compendium for your race/classes/subclasses/background.
- **Background** — write personality, ideals, bonds, flaws, and backstory in
  Markdown with a live preview, alongside your background's feature.
- **Rest** — **long rest** (HP to max, recover half your hit dice, reset all
  spell slots and resources) and **short rest** (spend hit dice, restore
  short-recharge resources).
- **Campaign Notes** — per-character titled notes with Markdown bodies,
  newest-first and searchable.

### Reference compendium (bundled, offline)
- **Spells**, **Character Options** (races / classes / subclasses / backgrounds /
  feats), **Conditions**, **Skills**, **Languages**, and **Items** — searchable
  with the same filters as Arcane Shield.

### Import / manage characters
- **Export** the active character to a single **CSV** (re-importable) or a
  lossless **JSON** backup (character + everything attached). Export **all**
  characters to one CSV.
- **Import** a characters CSV (one *or many* characters in one file) or a JSON
  export.
- **Delete** a character, or **Erase ALL character data** (the reference
  compendium is kept; a backup snapshot is taken first).

## Stack

- Python 3.10+
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) ≥ 5.2.2
- [Pillow](https://python-pillow.org/) ≥ 10.0.0
- `sqlite3` and `csv` from the standard library

## Getting started

```bat
:: From the project folder
run.bat
```

`run.bat` installs the requirements (quietly) and launches the app. Or run it
manually:

```bat
pip install -r requirements.txt
python main.py
```

On first launch the app:

1. Creates its database at `%APPDATA%\ArcaneSword\arcane-sword.db`.
2. Loads the bundled compendium from `data/reference/*.csv` into the reference
   tables (only if they're empty).
3. Writes a rotating backup snapshot.

Then click **+ New** on the Character Sheet to start a character, or import one
(below).

## Desktop launcher (no console window)

To open Arcane Sword from your Desktop with a single click — and **without** a
command-prompt window — create a shortcut once:

```powershell
powershell -ExecutionPolicy Bypass -File install-desktop-shortcut.ps1
```

This puts an **"Arcane Sword"** shortcut on your Desktop that launches the app
through `pythonw.exe` (the windowed Python interpreter), so no console appears —
the app window just opens. Re-run the script any time (for example after dropping
in a new `icon.ico` logo) to refresh the shortcut.

> First-time setup only: make sure the dependencies are installed once with
> `pip install -r requirements.txt` (or a single `run.bat`). After that, use the
> Desktop shortcut for everyday launching.

## Importing a character

A character is one row in a CSV using the columns documented in
[`data/characters_template.csv`](data/characters_template.csv). Multi-value
fields are semicolon-separated; a few use compact encodings:

| Field | Example |
| --- | --- |
| `classes` | `Wizard(Evocation):5;Cleric(Life Domain):2` |
| `skill_proficiencies` | `Arcana;*Investigation` (`*` = expertise) |
| `saving_throws` | `INT;WIS` |
| `inventory` | `Longsword:1;Healing Potion:3` |
| `spells_known` / `spells_prepared` | `Fire Bolt;Shield;Fireball` |
| `features` | `Source\|Name\|Description;;Source\|Name\|Description` |

To import: open **Import / Manage** (bottom of the sidebar) → **Import from
file…**, and pick a CSV or a JSON export. CSV files may contain **multiple**
characters (one per row). Inventory items and spells are matched to the
compendium by name so their full text is always available.

You can edit `data/characters_template.csv`, drop in your own rows, and import it
to bulk-create characters.

## Themes & training wheels

Open the **⚙ Settings** tab to:

- **Pick a theme** — the whole app recolours instantly and your choice is
  remembered. Each theme paints a full-window backdrop from custom art. The
  built-in set (more added over time):
  - **Mystic Blue** — deep cobalt night sky and arcane glyphs.
  - **Martial Red** — blood-crimson battlefield and bronze weapons.
  - **Artificer Bronze** — dark workshop browns and copper gears.
  - **Add your own:** drop an image into `assets/themes/` named after the theme,
    lower-case and hyphenated (e.g. `mystic-blue.jpg`; `.jpg`/`.png`/`.webp` all
    work), and add a matching palette entry in `pages/theme.py`. If a theme has
    no art, a soft gradient is generated from its palette.
- **Toggle "training wheels"** — beginner-friendly helpers you can switch off as
  you get comfortable:
  - *Derivation hints* — show how totals are built (saves, passive senses, …).
  - *Tooltips & guidance* — short tips on tabs and fields.
  - *Rules warnings* — confirmations for multiclass prerequisites, the 3-item
    attunement cap, over-preparing, etc.
  - *Simple mode* — hide advanced controls (multiclass, custom actions).

Settings are saved to `%APPDATA%\ArcaneSword\settings.json`.

## Data & backups

- **Database:** `%APPDATA%\ArcaneSword\arcane-sword.db`
- **Backups:** `%APPDATA%\ArcaneSword\backups\` (most recent 7 kept automatically;
  a snapshot is taken on every clean launch and before any destructive reset)
- **Bundled reference data:** `data/reference/*.csv` in this repo — checked-in
  CSVs of the full compendium (spells, character options, magic items,
  conditions, skills, languages).

**Self-healing:** if the live database is ever corrupted, Arcane Sword
quarantines it and automatically restores the newest healthy backup on the next
launch.

### How the reference data is bundled

The compendium ships as plain CSV under `data/reference/` and is loaded into the
local database on first launch (and only when a table is empty, so your edits are
never overwritten). The CSVs were exported, read-only, from Arcane Shield's own
compendium; Arcane Sword never touches Arcane Shield's database.

## Tests

Headless tests cover the data layer, each tab, the rules (spell slots,
leveling/multiclass, weapon attacks), and a full end-to-end smoke test
(create → level up → multiclass → spells → inventory → rest → export/import →
relaunch persistence → reset):

```bat
for %f in (tests\test_*.py) do python %f
```

## Relationship to Arcane Shield

Arcane Sword deliberately reuses Arcane Shield's infrastructure — the dice
roller, the Markdown renderer, the fast list widgets, the dark theme, and the
self-healing database layer — so the two apps stay in sync. The shared reference
browsers are the same pages, presented to the player. Arcane Sword **never**
writes to Arcane Shield's database; it ships its own snapshot of the compendium
and keeps its own database under `%APPDATA%\ArcaneSword`.
