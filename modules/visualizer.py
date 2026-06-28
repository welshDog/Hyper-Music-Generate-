"""
Module 3: Visualizer
Fast, audio-reactive visualizer drawn with Pillow + numpy (no matplotlib in the
frame loop). Each draw function returns a transparent RGBA layer that the render
engine composites over the procedural background.

Types (selectable via style["visualizer_type"]):
    bars     — vertical spectrum, optionally mirrored (style["mirror"])
    waveform — centred oscilloscope line
    radial   — circular spectrum
    particles— onset-triggered bursts

Glow/bloom is the big visual win: shapes are drawn once, blurred, and the crisp
copy is composited on top.

Public API:
    make_visualizer(style, audio_data) -> callable(frame_idx, t, pump) -> PIL.Image (RGBA)
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1080, 1920
FPS = 30


# ─────────────────────────────────────────────
#  COLOUR HELPERS
# ─────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _lerp(c1: tuple, c2: tuple, f: float) -> tuple:
    f = max(0.0, min(1.0, f))
    return tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


_GLOW_DOWNSCALE = 3   # blur on a 1/3-res copy — visually identical bloom, ~9x cheaper


def _apply_glow(sharp: Image.Image, radius: int) -> Image.Image:
    """Composite a blurred copy under the crisp layer for a neon bloom.

    The blur runs on a downscaled copy (GaussianBlur cost scales with pixel
    count), then upscales — the bloom is soft anyway so the result is identical
    to a full-res blur but far faster.
    """
    if radius <= 0:
        return sharp
    w, h = sharp.size
    small = sharp.resize((w // _GLOW_DOWNSCALE, h // _GLOW_DOWNSCALE), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(max(1, radius // _GLOW_DOWNSCALE)))
    glow = small.resize((w, h), Image.BILINEAR)
    out = Image.alpha_composite(glow, glow)   # double-up for a brighter bloom
    out = Image.alpha_composite(out, sharp)
    return out


# ─────────────────────────────────────────────
#  PUBLIC FACTORY
# ─────────────────────────────────────────────

def make_visualizer(style: dict, audio_data: dict):
    vtype = style.get("visualizer_type", "bars")
    bar_color = _hex_to_rgb(style.get("bar_color", "#00ffff"))
    accent = _hex_to_rgb(style.get("accent_color", "#ff00ff"))
    glow_radius = 14 if style.get("glow", True) else 0
    mirror = style.get("mirror", False)
    bar_count = int(style.get("bar_count", 64))

    frame_bars = audio_data["frame_bars"]
    n_frames = len(frame_bars)
    y = audio_data["y"]
    sr = audio_data["sr"]
    onset_times = audio_data.get("onset_times", [])

    print(f"    Visualizer: {vtype}{' (mirrored)' if mirror else ''} | glow={'on' if glow_radius else 'off'}")

    def _bars_for(frame_idx: int) -> np.ndarray:
        idx = min(frame_idx, n_frames - 1) if n_frames else 0
        bars = np.asarray(frame_bars[idx] if n_frames else [0.0] * bar_count)
        # collapse/expand to requested bar_count
        if len(bars) != bar_count and len(bars) > 0:
            bars = np.interp(
                np.linspace(0, len(bars) - 1, bar_count),
                np.arange(len(bars)), bars,
            )
        return bars

    def draw(frame_idx: int, t: float, pump: float) -> Image.Image:
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        if vtype == "waveform":
            _draw_waveform(d, y, sr, t, bar_color, accent, pump)
        elif vtype == "radial":
            _draw_radial(d, _bars_for(frame_idx), bar_color, accent, pump)
        elif vtype == "particles":
            _draw_particles(d, onset_times, t, bar_color, accent)
        else:
            _draw_bars(d, _bars_for(frame_idx), bar_color, accent, pump, mirror)
        return _apply_glow(layer, glow_radius)

    return draw


# ─────────────────────────────────────────────
#  DRAW PRIMITIVES
# ─────────────────────────────────────────────

def _draw_bars(d, bars, bar_color, accent, pump, mirror):
    n = len(bars)
    if n == 0:
        return
    gap = 6
    bar_w = (WIDTH - gap * (n + 1)) / n
    boost = 1.0 + 0.30 * pump
    max_h = HEIGHT * 0.34
    base_y = int(HEIGHT * 0.74)

    for i, v in enumerate(bars):
        h = max(4, int(v * max_h * boost))
        x0 = gap + i * (bar_w + gap)
        x1 = x0 + bar_w
        col = _lerp(bar_color, accent, i / max(1, n - 1)) + (255,)
        r = max(2, int(bar_w / 2))
        if mirror:
            cy = int(HEIGHT * 0.5)
            d.rounded_rectangle([x0, cy - h // 2, x1, cy + h // 2], radius=r, fill=col)
        else:
            d.rounded_rectangle([x0, base_y - h, x1, base_y], radius=r, fill=col)


def _draw_waveform(d, y, sr, t, bar_color, accent, pump):
    win = int(sr * 0.05)                      # 50 ms window
    start = int(t * sr)
    chunk = y[start:start + win]
    if len(chunk) < 2:
        return
    step = max(1, len(chunk) // WIDTH)
    chunk = chunk[::step][:WIDTH]
    cy = HEIGHT * 0.5
    amp = HEIGHT * 0.16 * (1.0 + 0.5 * pump)
    pts = [(int(i * WIDTH / len(chunk)), int(cy + s * amp)) for i, s in enumerate(chunk)]
    col = _lerp(bar_color, accent, 0.5) + (255,)
    d.line(pts, fill=col, width=6, joint="curve")


def _draw_radial(d, bars, bar_color, accent, pump):
    n = len(bars)
    if n == 0:
        return
    cx, cy = WIDTH // 2, HEIGHT // 2
    inner = 240
    boost = 1.0 + 0.45 * pump
    max_len = 360
    for i, v in enumerate(bars):
        ang = (i / n) * 2 * math.pi - math.pi / 2
        length = inner + v * max_len * boost
        x0 = cx + math.cos(ang) * inner
        y0 = cy + math.sin(ang) * inner
        x1 = cx + math.cos(ang) * length
        y1 = cy + math.sin(ang) * length
        col = _lerp(bar_color, accent, i / max(1, n - 1)) + (255,)
        d.line([x0, y0, x1, y1], fill=col, width=10)


def _draw_particles(d, onset_times, t, bar_color, accent):
    life = 0.7   # seconds a burst stays visible
    for oi, ot in enumerate(onset_times):
        age = t - ot
        if 0 <= age <= life:
            rng = np.random.default_rng(oi)          # deterministic per onset
            cx = rng.uniform(0.15, 0.85) * WIDTH
            cy = rng.uniform(0.25, 0.75) * HEIGHT
            prog = age / life
            radius = 20 + prog * 220
            alpha = int(255 * (1 - prog))
            col = _lerp(bar_color, accent, prog) + (alpha,)
            d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                      outline=col, width=6)
            for _ in range(6):
                px = cx + rng.uniform(-1, 1) * radius
                py = cy + rng.uniform(-1, 1) * radius
                d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=col)
