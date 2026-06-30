"""Theming + app settings for Arcane Sword.

A single source of truth for the colour palette and the "training wheels"
toggles. Pages keep their familiar module-level colour names (BG, SURFACE, …);
`apply_all()` rewrites those names across every page module when the theme
changes, and the App rebuilds its UI so the new colours take effect live.

Each theme also has a full-window backdrop image: a user PNG dropped in
assets/themes/<slug>.png if present, otherwise an auto-generated gradient
derived from the palette (cached under %APPDATA%/ArcaneSword/backdrops/).
"""
import json
import os
import sys
import re
from pathlib import Path

COLOR_KEYS = ["BG", "SURFACE", "SURFACE2", "BORDER", "ACCENT", "ACCENT_H",
              "TEXT", "MUTED", "DANGER", "GOOD", "GOLD"]

# ── Built-in themes ──────────────────────────────────────────────────────────────
# Palettes are hand-tuned to the backdrop art in assets/themes/<slug>.(jpg|png).
# More will be added as new art is generated.
THEMES: dict[str, dict] = {
    "Mystic Blue": {  # deep cobalt night sky + cyan arcane glyphs
        "BG": "#0a0e1a", "SURFACE": "#121a2e", "SURFACE2": "#1a2542", "BORDER": "#29385f",
        "ACCENT": "#4a86e0", "ACCENT_H": "#6fa6f2", "TEXT": "#dde7f7", "MUTED": "#8294b8",
        "DANGER": "#e05a52", "GOOD": "#52be80", "GOLD": "#e0b84a",
    },
    "Martial Red": {  # blood-crimson battlefield + bronze weapons
        "BG": "#140707", "SURFACE": "#1f0d0d", "SURFACE2": "#2c1313", "BORDER": "#48201d",
        "ACCENT": "#c0392b", "ACCENT_H": "#e25140", "TEXT": "#f1ddda", "MUTED": "#b18a86",
        "DANGER": "#ff5b4d", "GOOD": "#8fbf52", "GOLD": "#cf9b54",
    },
    "Artificer Bronze": {  # dark workshop brown + copper/amber gears
        "BG": "#120c06", "SURFACE": "#1d150b", "SURFACE2": "#281d0f", "BORDER": "#3f2e17",
        "ACCENT": "#c0832e", "ACCENT_H": "#e0a64a", "TEXT": "#f0e4cf", "MUTED": "#a8906c",
        "DANGER": "#d0473a", "GOOD": "#8bbf52", "GOLD": "#e6c258",
    },

    "Barbarian Blood Red": {  # brutal crimson stone + warrior weapons
        "BG": "#0f0505", "SURFACE": "#1a0808", "SURFACE2": "#240d0d", "BORDER": "#3d1515",
        "ACCENT": "#c23020", "ACCENT_H": "#e04030", "TEXT": "#f0ddd8", "MUTED": "#a07070",
        "DANGER": "#ff3333", "GOOD": "#7abf52", "GOLD": "#c8904a",
    },
    "Bard Purple": {  # rich violet velvet + gold filigree instruments
        "BG": "#0c0610", "SURFACE": "#160d20", "SURFACE2": "#1e122c", "BORDER": "#341a4a",
        "ACCENT": "#c060d0", "ACCENT_H": "#d880e8", "TEXT": "#f0e8f5", "MUTED": "#9a7eab",
        "DANGER": "#e05060", "GOOD": "#60bf80", "GOLD": "#d4a040",
    },
    "Fighter Steel": {  # dark slate + cool blue-grey armour and heraldry
        "BG": "#0a0c10", "SURFACE": "#131720", "SURFACE2": "#1c2030", "BORDER": "#2c3448",
        "ACCENT": "#7090b8", "ACCENT_H": "#90aed8", "TEXT": "#dce4f0", "MUTED": "#7a8899",
        "DANGER": "#c05040", "GOOD": "#60b870", "GOLD": "#c0a050",
    },
    "Monk Yellow": {  # warm sepia-gold + eastern scrolls and yin-yang
        "BG": "#0e0a04", "SURFACE": "#1a1208", "SURFACE2": "#241a0c", "BORDER": "#3a2a12",
        "ACCENT": "#c89030", "ACCENT_H": "#e0aa48", "TEXT": "#f0e8d0", "MUTED": "#a08858",
        "DANGER": "#d04030", "GOOD": "#7ab840", "GOLD": "#e0b030",
    },
    "Wizard Sapphire": {  # deep navy + arcane gold runes and spellbooks
        "BG": "#05060f", "SURFACE": "#0c0e1e", "SURFACE2": "#121628", "BORDER": "#1e2444",
        "ACCENT": "#3060d8", "ACCENT_H": "#5080f0", "TEXT": "#d8e4f8", "MUTED": "#6878a8",
        "DANGER": "#e05050", "GOOD": "#50b878", "GOLD": "#d0a030",
    },

    # ── Simple colour-only themes, one per ability score ─────────────────────
    "STR Red": {
        "BG": "#120c0c", "SURFACE": "#1c1313", "SURFACE2": "#271a1a", "BORDER": "#3a2626",
        "ACCENT": "#e0473a", "ACCENT_H": "#f26a5c", "TEXT": "#f0e3e1", "MUTED": "#a08e8e",
        "DANGER": "#c0392b", "GOOD": "#6fbf6a", "GOLD": "#e0b84a",
    },
    "DEX Green": {
        "BG": "#0c120d", "SURFACE": "#131e16", "SURFACE2": "#1a291f", "BORDER": "#26392d",
        "ACCENT": "#46c46a", "ACCENT_H": "#6fe08f", "TEXT": "#e3f0e6", "MUTED": "#8ea596",
        "DANGER": "#e0573f", "GOOD": "#6fe08f", "GOLD": "#e0c64a",
    },
    "CON Orange": {
        "BG": "#130d07", "SURFACE": "#1e150c", "SURFACE2": "#291e10", "BORDER": "#3d2c18",
        "ACCENT": "#e8893a", "ACCENT_H": "#f7a557", "TEXT": "#f0e6da", "MUTED": "#a8917c",
        "DANGER": "#d9453a", "GOOD": "#8bbf52", "GOLD": "#e6b84a",
    },
    "INT Blue": {
        "BG": "#0b0f15", "SURFACE": "#141b26", "SURFACE2": "#1c2636", "BORDER": "#2a3850",
        "ACCENT": "#4a86e0", "ACCENT_H": "#6fa6f2", "TEXT": "#e0eaf5", "MUTED": "#8a99ad",
        "DANGER": "#e0573f", "GOOD": "#52be80", "GOLD": "#e0b84a",
    },
    "WIS Purple": {
        "BG": "#0f0c16", "SURFACE": "#181324", "SURFACE2": "#211a30", "BORDER": "#322748",
        "ACCENT": "#9a6fd8", "ACCENT_H": "#b48ce8", "TEXT": "#e7e0f2", "MUTED": "#978aad",
        "DANGER": "#e0573f", "GOOD": "#52be80", "GOLD": "#e0b84a",
    },
    "CHA Pink": {
        "BG": "#140a10", "SURFACE": "#1f121a", "SURFACE2": "#2b1925", "BORDER": "#422638",
        "ACCENT": "#e060a0", "ACCENT_H": "#f582ba", "TEXT": "#f0e0ea", "MUTED": "#ad8a9d",
        "DANGER": "#e0573f", "GOOD": "#52be80", "GOLD": "#e0b84a",
    },
}

DEFAULT_THEME = "Mystic Blue"

# How big a margin reveals the backdrop art around the floating panels.
PANEL_INSETS = {"Subtle": 12, "Balanced": 30, "Bold": 60}
DEFAULT_INSET = "Balanced"

TRAINING_WHEELS = ["hints", "tooltips", "warnings", "simple_mode"]
_TW_LABELS = {
    "hints": "Derivation hints",
    "tooltips": "Tooltips & guidance",
    "warnings": "Rules warnings",
    "simple_mode": "Simple mode",
}

# ── In-memory state (persisted to settings.json) ─────────────────────────────────
_active = DEFAULT_THEME
_inset = DEFAULT_INSET
_tw = {"hints": True, "tooltips": True, "warnings": True, "simple_mode": False}


def _appdata_dir() -> Path:
    d = Path(os.environ.get("APPDATA", Path.home())) / "ArcaneSword"
    d.mkdir(parents=True, exist_ok=True)
    return d


def settings_path() -> Path:
    return _appdata_dir() / "settings.json"


def load() -> None:
    """Load the saved theme + training-wheels flags (best effort)."""
    global _active, _inset
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
        if data.get("theme") in THEMES:
            _active = data["theme"]
        if data.get("panel_inset") in PANEL_INSETS:
            _inset = data["panel_inset"]
        for k in TRAINING_WHEELS:
            if k in data.get("training_wheels", {}):
                _tw[k] = bool(data["training_wheels"][k])
    except Exception:
        pass


def save() -> None:
    try:
        settings_path().write_text(json.dumps(
            {"theme": _active, "panel_inset": _inset, "training_wheels": _tw},
            indent=2), encoding="utf-8")
    except Exception:
        pass


def panel_inset_name() -> str:
    return _inset


def panel_inset() -> int:
    return PANEL_INSETS.get(_inset, PANEL_INSETS[DEFAULT_INSET])


def set_panel_inset(name: str) -> None:
    global _inset
    if name in PANEL_INSETS:
        _inset = name
        save()


# ── Theme accessors ──────────────────────────────────────────────────────────────
def theme_names() -> list[str]:
    return list(THEMES.keys())


def active_theme() -> str:
    return _active


def palette(name: str | None = None) -> dict:
    return THEMES[name or _active]


def set_active(name: str) -> None:
    global _active
    if name in THEMES:
        _active = name
        save()


def tw(flag: str) -> bool:
    return bool(_tw.get(flag, False))


def tw_label(flag: str) -> str:
    return _TW_LABELS.get(flag, flag)


def set_tw(flag: str, value: bool) -> None:
    if flag in _tw:
        _tw[flag] = bool(value)
        save()


def apply_all() -> None:
    """Rewrite the COLOR_KEYS module globals on every page module (and main) to
    the active palette. Call before building/rebuilding the UI."""
    pal = palette()
    for name, mod in list(sys.modules.items()):
        if not mod:
            continue
        if name == "main" or name == "__main__" or name.startswith("pages."):
            for k in COLOR_KEYS:
                if hasattr(mod, k):
                    setattr(mod, k, pal[k])


# ── Backdrop image (full-window) ─────────────────────────────────────────────────
def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _user_image_path(name: str) -> Path | None:
    base = Path(__file__).resolve().parent.parent / "assets" / "themes"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = base / f"{_slug(name)}{ext}"
        if p.exists():
            return p
    return None


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def backdrop_source(name: str | None = None):
    """Return a PIL.Image for the theme's backdrop: the user's art if present,
    else an auto-generated gradient cached under %APPDATA%. Returns None if
    Pillow is unavailable."""
    name = name or _active
    try:
        from PIL import Image
    except Exception:
        return None
    user = _user_image_path(name)
    if user:
        try:
            return Image.open(user).convert("RGB")
        except Exception:
            pass
    # Generated gradient backdrop, cached.
    cache = _appdata_dir() / "backdrops"
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{_slug(name)}.png"
    if path.exists():
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            pass
    img = _make_gradient(name)
    try:
        img.save(path)
    except Exception:
        pass
    return img


def _make_gradient(name: str):
    """A subtle diagonal gradient (BG -> accent-tinted dark) with a vignette."""
    from PIL import Image
    pal = palette(name)
    # Small source — it's a soft gradient upscaled to the window at display time.
    w, h = 240, 150
    bg = _hex(pal["BG"])
    ac = _hex(pal["ACCENT"])
    far = tuple(int(b * 0.55 + a * 0.18) for b, a in zip(bg, ac))  # darkened accent corner
    img = Image.new("RGB", (w, h))
    px = img.load()
    maxd = w + h
    for y in range(h):
        for x in range(w):
            t = (x + y) / maxd
            px[x, y] = (int(bg[0] + (far[0] - bg[0]) * t),
                        int(bg[1] + (far[1] - bg[1]) * t),
                        int(bg[2] + (far[2] - bg[2]) * t))
    return img
