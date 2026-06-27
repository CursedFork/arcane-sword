# Arcane Sword — Scaffold Report

First increment: recycle Arcane Shield's infrastructure into a runnable
player-facing shell with working reference browsers and placeholder character
tabs. **No** Arcane Shield source file or database was modified.

- **Source app:** `C:\Users\Andrew\arcane-shield-py` (GitHub: CursedFork/arcane-shield)
- **Target app:** `C:\Users\Andrew\arcane-sword`
- **Stack (unchanged):** Python 3.10+, customtkinter ≥ 5.2.2, Pillow ≥ 10.0.0, stdlib `sqlite3` + `csv`. Launch via `run.bat` / `python main.py`.

---

## Files copied VERBATIM

| File | Notes |
| --- | --- |
| `dice.py` | Dice roller — identical. |
| `pages/md_widget.py` | `MarkdownText` renderer — identical. |
| `pages/ui_util.py` | `ScrollList`, `bind_row`, `descendants` — identical. |
| `pages/__init__.py` | Empty package marker — identical. |
| `requirements.txt` | Identical (`customtkinter>=5.2.2`, `Pillow>=10.0.0`). |
| `run.bat` | Identical (`pip install … && pythonw main.py`). |
| `icon.ico` | Same icon reused (per instructions). |
| `pages/spells.py` | Reference browser — copied as-is. |
| `pages/character_options.py` | Reference browser — copied as-is. |
| `pages/conditions.py` | Reference browser — copied as-is. |
| `pages/skills.py` | Reference browser — copied as-is. |
| `pages/languages.py` | Reference browser — copied as-is. |
| `pages/items.py` | Reference browser — copied as-is. |

The six reference pages were copied **unchanged**; they depend only on the
shared utilities, the page-local color constants, and `Database` methods that
are preserved in Sword's `db.py`. Their filters (spell level/school/class, feat
source/boon/prerequisite, item type/rarity/attunement/tag, language category,
etc.) all keep working. The DM-only **+ New / Clear / Export** buttons were left
in place (read-only spirit, as specified).

The dark theme color constants are kept identical across the app:
`BG #0f0f13`, `SURFACE #1a1a24`, `SURFACE2 #22222f`, `BORDER #2e2e3e`,
`ACCENT #7c5cbf`, `ACCENT_H #9472d8`, `TEXT #e2e0f0`, `MUTED #8a8aa0`,
`DANGER #c0392b`.

---

## Files ADAPTED (copied then modified)

### `db.py`
Kept Arcane Shield's whole database **infrastructure** unchanged in spirit:
`_db_path()`, `_backup_dir()`, `_is_healthy()`, `_make_backup()`,
`_auto_recover()`, `_connect()` (self-heal + rotating backups), the CSV
import/export framework (`import_csv` / `export_csv` / `_detect_table`), and the
versioned `_migrate` scaffold (`PRAGMA user_version`). Changes for Sword:

- `_db_path()` now points at `%APPDATA%\ArcaneSword\arcane-sword.db`.
- Backup/quarantine filenames re-prefixed `arcane-sword_*`.
- `_migrate` creates **only the reference tables**: `spells`,
  `character_options`, `conditions`, `skills`, `languages`, `magic_items`.
  (Character tables come in the next prompt.)
- Kept Arcane Shield's **seed logic** for `conditions` / `skills` / `languages`
  as a fallback if a bundled CSV is missing/empty.
- Added `_load_bundled_reference()` + `_reference_dir()`: on first launch each
  reference table, if empty, is populated from `data/reference/*.csv`
  (`;`-joined tag columns are re-encoded to the JSON the schema stores).
- `Database` retains only the methods the reference pages use
  (spells / conditions / character_options / skills / languages / magic_items),
  plus `clear_table`, `export_csv`, `import_csv`. Bestiary/players/DM-shield/etc.
  methods and tables were dropped (DM-only, not needed by the player app).
- `export_csv` / `import_csv` / `_detect_table` trimmed to the six reference
  tables and extended to cover `conditions` / `skills` / `languages` (which
  Arcane Shield's exporter did not handle).

### `main.py`
Kept the `App` window, sidebar framework, page routing (`show_page` + stored
per-button defaults via `_nav_defaults`), and the icon + AppUserModelID setup.
Changes for Sword:

- Window title → **"Arcane Sword"**; sidebar header → "🗡 ARCANE SWORD" /
  "Player Companion".
- AppUserModelID → **`arcane.sword.player`** (was `arcane.shield.dm`).
- Navigation replaced with Arcane Sword's player tabs:
  - **Top:** 🗡 Character Sheet *(placeholder)*
  - **Content:** ✨ Spells · 🧙 Character Options · 🜸 Conditions · 🎯 Skills ·
    🗣 Languages · ✦ Items *(the six working reference browsers)*, then
    ⚡ Actions · 🎒 Inventory · 📕 Spellbook · 🌟 Features & Traits · ⬆ Level-Up ·
    🌙 Rest · ✎ Campaign Notes *(placeholders)*
  - **Bottom:** ⬆ Import Character *(placeholder)*
- Default landing page is **Spells** (a working reference browser).

---

## Files CREATED (new to Arcane Sword)

| File | Purpose |
| --- | --- |
| `pages/placeholder.py` | `PlaceholderPage` — a "Coming soon" frame matching the page contract (`refresh()`), so stubs swap for real pages later without touching routing. |
| `.gitignore` | Standard Python ignore set (source app had none). Ignores `__pycache__`, local `*.db*`, editor dirs. |
| `README.md` | Player-companion overview + getting-started (mirrors Shield's style). |
| `SCAFFOLD_REPORT.md` | This file. |
| `data/reference/*.csv` | Bundled offline compendium (see below). |

---

## Bundled reference data

Exported to `data/reference/` (column orders match Arcane Shield's `export_csv`;
`conditions`/`skills`/`languages` use their natural table column order since
Shield's exporter didn't cover them):

| CSV | Table | Rows loaded |
| --- | --- | ---: |
| `spells.csv` | `spells` | **554** |
| `character_options.csv` | `character_options` | **572** |
| `magic_items.csv` | `magic_items` | **521** |
| `conditions.csv` | `conditions` | **15** |
| `skills.csv` | `skills` | **18** |
| `languages.csv` | `languages` | **18** |

**Total: 1,698 reference rows**, all verified loaded into a fresh
`%APPDATA%\ArcaneSword\arcane-sword.db` on first launch (`integrity_check: ok`).

### ⚠️ Source-of-data note (important)
The task said to read Arcane Shield's **live** DB
(`%APPDATA%\ArcaneShield\arcane-shield.db`) read-only. At scaffold time that
live DB was **mid-operation**: its uncommitted WAL held an in-progress bulk
operation that had cleared most reference tables (a read-only view showed only
`languages` populated). Reading it directly would have bundled a near-empty,
inconsistent compendium.

To get the **full, self-consistent** compendium the task's BUNDLE section
requires ("so players have the full compendium offline"), the data was instead
exported from Arcane Shield's **own most-recent healthy backup snapshot**,
`%APPDATA%\ArcaneShield\backups\arcane-shield_20260627_083238.db` — a snapshot
Arcane Shield itself wrote, opened **read-only** (`mode=ro`), which passed
`integrity_check: ok`. **Arcane Shield's database and source were never
modified.** (`bestiary` and `mechanics` exist in Shield but are DM-only and were
intentionally not bundled.)

---

## Left as STUBS / deferred to later prompts

- **Character tables & features** — not created yet. Placeholder tabs:
  Character Sheet, Actions, Inventory, Spellbook, Features & Traits, Level-Up,
  Rest, Campaign Notes, Import Character (all render a "Coming soon" card).
- **Read-only enforcement** — reference pages still expose Shield's DM-only
  **+ New / Clear / Export** buttons (left in per instructions; can be hidden in
  a later pass).
- **GitHub remote** — `CursedFork/arcane-sword` does **not** exist; the repo was
  initialized **locally only** (not created on GitHub, per instructions).

---

## Verification

- `python db.py` smoke test: migrate + bundled load succeeds; all six reference
  tables populated; `PRAGMA integrity_check` → **ok**; `user_version` = 1.
- Full GUI built headless: all **15** pages (6 reference browsers + 9
  placeholders) construct and `refresh()` without error; window opens and closes
  cleanly.
- App launches to the sidebar with **Spells** showing populated data.
