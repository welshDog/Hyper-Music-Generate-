"""
Module 4: Text Overlay
Animated title card + karaoke-style lyric sync, drawn with Pillow and returned as
a transparent RGBA layer for the render engine to composite on top.

Fonts never crash: style font -> bundled TTF -> matplotlib's DejaVuSans (always
present, since matplotlib is a dependency) -> PIL default.

Public API:
    make_text_layer(style, title, artist, lyrics_file, audio_data)
        -> callable(t) -> PIL.Image (RGBA)
"""

import os
import re
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920


# ─────────────────────────────────────────────
#  FONTS  (bulletproof fallback chain, cached)
# ─────────────────────────────────────────────

def _dejavu_path() -> str:
    """A guaranteed-present bold TTF, located via matplotlib's font manager."""
    try:
        from matplotlib import font_manager
        return font_manager.findfont(font_manager.FontProperties(weight="bold"))
    except Exception:  # noqa: BLE001
        return ""


@lru_cache(maxsize=32)
def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in (font_path, _dejavu_path()):
        if candidate and os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except (IOError, OSError):
                continue
    return ImageFont.load_default()


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


_MARGIN = 80  # keep text this many px clear of each frame edge


def _fit_font(font_path: str, text: str, max_size: int,
              max_width: int = WIDTH - 2 * _MARGIN, min_size: int = 26):
    """Largest font (≤ max_size) at which `text` fits within max_width."""
    size = max_size
    while size > min_size:
        font = _load_font(font_path, size)
        try:
            w = font.getlength(text)
        except AttributeError:               # very old Pillow
            w = font.getbbox(text)[2]
        if w <= max_width:
            return font
        size -= 4
    return _load_font(font_path, min_size)


def _draw_centered(draw, text, y, font, fill, shadow=(0, 0, 0, 180)):
    w = _text_w(draw, text, font)
    x = (WIDTH - w) // 2
    draw.text((x + 3, y + 3), text, font=font, fill=shadow)   # soft drop shadow
    draw.text((x, y), text, font=font, fill=fill)


# ─────────────────────────────────────────────
#  LYRICS PARSING
# ─────────────────────────────────────────────

_LRC_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")


def _parse_lyrics(lyrics_file: str, beat_times: list, duration: float) -> list:
    """Return a sorted list of (start_time, line). Supports .lrc and plain .txt."""
    if not lyrics_file or not os.path.exists(lyrics_file):
        return []

    with open(lyrics_file, "r", encoding="utf-8") as f:
        raw = f.read()

    timed = []
    for m in _LRC_RE.finditer(raw):
        mins, secs, line = m.group(1), m.group(2), m.group(3).strip()
        if line:
            timed.append((int(mins) * 60 + float(secs), line))
    if timed:
        return sorted(timed)

    # Plain text: distribute non-empty lines across the song's beats.
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return []
    anchors = beat_times if len(beat_times) >= len(lines) else \
        [duration * i / len(lines) for i in range(len(lines))]
    step = max(1, len(anchors) // len(lines))
    return [(anchors[min(i * step, len(anchors) - 1)], ln) for i, ln in enumerate(lines)]


def _current_line(lyrics: list, t: float) -> int:
    idx = -1
    for i, (start, _) in enumerate(lyrics):
        if t >= start:
            idx = i
        else:
            break
    return idx


# ─────────────────────────────────────────────
#  PUBLIC FACTORY
# ─────────────────────────────────────────────

def make_text_layer(style: dict, title: str, artist: str, lyrics_file: str, audio_data: dict):
    font_path = style.get("font", "")
    accent = style.get("accent_color", "#f9ca24")
    duration = audio_data.get("duration", 0.0)
    beat_times = audio_data.get("beat_times", [])

    # Title is constant per render, so size it to fit once; artist is short.
    title_font = _fit_font(font_path, title, 78) if title else _load_font(font_path, 78)
    artist_font = _load_font(font_path, 46)

    lyrics = _parse_lyrics(lyrics_file, beat_times, duration)
    if lyrics:
        print(f"    Lyrics: {len(lyrics)} lines (karaoke sync on)")

    # Title card timing: slide/fade in 0-1s, hold to 3.5s, fade out by 5s.
    def _title_alpha(t: float) -> float:
        if t < 1.0:
            return t
        if t < 3.5:
            return 1.0
        if t < 5.0:
            return 1.0 - (t - 3.5) / 1.5
        return 0.0

    def draw(t: float) -> Image.Image:
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        # --- Title card ---
        a = _title_alpha(t)
        if a > 0 and title:
            slide = int((1 - min(1.0, t)) * 40)        # gentle slide-down on entry
            alpha = int(255 * a)
            _draw_centered(d, title, 150 + slide, title_font, _rgba(accent, alpha))
            if artist:
                _draw_centered(d, f"— {artist} —", 250 + slide, artist_font,
                               (230, 230, 230, alpha))

        # --- Karaoke lyrics (fit each line to the frame width) ---
        if lyrics:
            i = _current_line(lyrics, t)
            if i >= 0:
                cy = int(HEIGHT * 0.82)
                _draw_centered(d, lyrics[i][1], cy,
                               _fit_font(font_path, lyrics[i][1], 64),
                               _rgba(accent, 255))
                if i + 1 < len(lyrics):
                    _draw_centered(d, lyrics[i + 1][1], cy + 90,
                                   _fit_font(font_path, lyrics[i + 1][1], 40),
                                   (200, 200, 200, 120))
        return layer

    return draw


def _rgba(hex_color: str, alpha: int) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


# ─────────────────────────────────────────────
#  LEGACY SHIM (old pipeline entrypoint — now a no-op passthrough)
# ─────────────────────────────────────────────

def add_text_overlay(visualizer_path: str, *args, **kwargs) -> str:
    """Deprecated: text is composited live by render_engine. Kept for safety."""
    return visualizer_path
