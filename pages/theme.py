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

# ── Built-in themes (colour-only until you add art) ──────────────────────────────
THEMES: dict[str, dict] = {
    "Arcane Violet": {
        "BG": "#0f0f13", "SURFACE": "#1a1a24", "SURFACE2": "#22222f", "BORDER": "#2e2e3e",
        "ACCENT": "#7c5cbf", "ACCENT_H": "#9472d8", "TEXT": "#e2e0f0", "MUTED": "#8a8aa0",
        "DANGER": "#c0392b", "GOOD": "#52be80", "GOLD": "#e0b040",
    },
    "Crimson Forge": {
        "BG": "#140d0d", "SURFACE": "#211414", "SURFACE2": "#2b1a1a", "BORDER": "#3d2626",
        "ACCENT": "#c0392b", "ACCENT_H": "#e0573f", "TEXT": "#f0e2e0", "MUTED": "#a98e8e",
        "DANGER": "#e74c3c", "GOOD": "#8bbf52", "GOLD": "#e0a840",
    },
    "Verdant Grove": {
        "BG": "#0c130d", "SURFACE": "#15201a", "SURFACE2": "#1c2b22", "BORDER": "#2a3d30",
        "ACCENT": "#4caf6a", "ACCENT_H": "#6fd88f", "TEXT": "#e2f0e6", "MUTED": "#8aa392",
        "DANGER": "#c0392b", "GOOD": "#6fd88f", "GOLD": "#e0c040",
    },
    "Frostbound": {
        "BG": "#0b0f16", "SURFACE": "#141a24", "SURFACE2": "#1a2230", "BORDER": "#263040",
        "ACCENT": "#4aa6d8", "ACCENT_H": "#6fc4ee", "TEXT": "#e0eaf2", "MUTED": "#8a96a8",
        "DANGER": "#c0392b", "GOOD": "#52be80", "GOLD": "#e0b040",
    },
    "Gilded Tome": {
        "BG": "#15110a", "SURFACE": "#211a10", "SURFACE2": "#2b2216", "BORDER": "#3d3322",
        "ACCENT": "#c79a3a", "ACCENT_H": "#e0b850", "TEXT": "#f0e8d8", "MUTED": "#a89a80",
        "DANGER": "#c0392b", "GOOD": "#8bbf52", "GOLD": "#e0b840",
    },
}

DEFAULT_THEME = "Arcane Violet"
TRAINING_WHEELS = ["hints", "tooltips", "warnings", "simple_mode"]
_TW_LABELS = {
    "hints": "Derivation hints",
    "tooltips": "Tooltips & guidance",
    "warnings": "Rules warnings",
    "simple_mode": "Simple mode",
}

# ── In-memory state (persisted to settings.json) ─────────────────────────────────
_active = DEFAULT_THEME
_tw = {"hints": True, "tooltips": True, "warnings": True, "simple_mode": False}


def _appdata_dir() -> Path:
    d = Path(os.environ.get("APPDATA", Path.home())) / "ArcaneSword"
    d.mkdir(parents=True, exist_ok=True)
    return d


def settings_path() -> Path:
    return _appdata_dir() / "settings.json"


def load() -> None:
    """Load the saved theme + training-wheels flags (best effort)."""
    global _active
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
        if data.get("theme") in THEMES:
            _active = data["theme"]
        for k in TRAINING_WHEELS:
            if k in data.get("training_wheels", {}):
                _tw[k] = bool(data["training_wheels"][k])
    except Exception:
        pass


def save() -> None:
    try:
        settings_path().write_text(json.dumps(
            {"theme": _active, "training_wheels": _tw}, indent=2), encoding="utf-8")
    except Exception:
        pass


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
