# Arcane Sword 🗡

**Arcane Sword** is the *player companion* to [Arcane Shield](https://github.com/CursedFork/arcane-shield) — a desktop D&D 5e character builder for players, sharing Arcane Shield's look, feel, and reference compendium.

Where Arcane Shield is the **DM's** reference and screen, Arcane Sword puts the same offline 5e compendium — spells, character options, conditions, skills, languages, and magic items — into the **player's** hands, alongside the tools you need to build and run a character.

> **Scaffold status:** this is the first increment. The reference browsers are
> fully working and bundled with the complete compendium. The character-building
> tabs (Character Sheet, Actions, Inventory, Spellbook, Features & Traits,
> Level-Up, Rest, Campaign Notes, Import Character) are labeled **placeholders**
> for now — later increments fill them in.

## Features (this build)

- **Spells** — searchable spellbook with level / school / class filters
- **Character Options** — races, classes, subclasses, backgrounds, and feats with source/boon/prerequisite filters
- **Conditions** — the standard 5e conditions reference
- **Skills** — the 18 skills with governing abilities and usage notes
- **Languages** — standard, exotic, and secret languages
- **Items** — the magic-item compendium with type / rarity / attunement / tag filters

All reference data ships **offline** in `data/reference/` and loads into a local
SQLite database on first launch — no internet connection required.

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
2. Loads the bundled compendium from `data/reference/*.csv` into the reference tables.
3. Writes a rotating backup snapshot (self-healing recovery is built in, mirroring Arcane Shield).

## Data & backups

- **Database:** `%APPDATA%\ArcaneSword\arcane-sword.db`
- **Backups:** `%APPDATA%\ArcaneSword\backups\` (most recent 7 kept automatically)
- **Bundled reference data:** `data/reference/` in this repo — checked-in CSVs
  exported from Arcane Shield's compendium.

If the live database is ever corrupted, Arcane Sword quarantines it and restores
the newest healthy backup automatically on the next launch.

## Relationship to Arcane Shield

Arcane Sword deliberately reuses Arcane Shield's infrastructure verbatim — the
dice roller, the Markdown renderer, the fast list widgets, the dark theme, and
the database layer — so the two apps stay in sync. The shared reference browsers
are the same pages, presented to the player in a read-only spirit. Arcane Sword
**never** writes to Arcane Shield's database; it ships its own snapshot of the
compendium and keeps its own database under `%APPDATA%\ArcaneSword`.
