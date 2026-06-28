"""
Module 2: Background Generator
Procedural, CPU-only animated backgrounds (plasma / flow-field / gradient-mesh),
beat-reactive. No GPU, no API, no cost.

The real diffusion path (_generate_with_diffusers) is preserved behind the
`huggingface.enabled` config flag for a future GPU/API upgrade — off by default.

Public API:
    make_background(style, audio_data) -> callable(t, pump) -> np.ndarray (H, W, 3) uint8
    generate_art(audio_data, style)    -> str   (legacy single-still helper, still used as fallback)
"""

import os
import numpy as np
from PIL import Image

WIDTH, HEIGHT = 1080, 1920

# Backgrounds are expensive at full res, so we render the soft procedural field
# at a downscale and let PIL upscale it. Looks identical, ~36x fewer pixels.
_BG_SCALE = 6
_BW, _BH = WIDTH // _BG_SCALE, HEIGHT // _BG_SCALE


# ─────────────────────────────────────────────
#  COLOUR HELPERS
# ─────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> np.ndarray:
    h = hex_color.lstrip("#")
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], dtype=np.float64)


def _palette(style: dict) -> tuple:
    """Three anchor colours pulled from the style preset."""
    bg = _hex_to_rgb(style.get("bg_color", "#0a0a0a"))
    bar = _hex_to_rgb(style.get("bar_color", "#00ffff"))
    accent = _hex_to_rgb(style.get("accent_color", "#ff00ff"))
    return bg, bar, accent


# Precompute the low-res coordinate grid once (shared by all generators).
_yy, _xx = np.mgrid[0:_BH, 0:_BW].astype(np.float64)
_nx = _xx / _BW          # 0..1
_ny = _yy / _BH          # 0..1
_cx, _cy = _nx - 0.5, _ny - 0.5
_radius = np.sqrt(_cx ** 2 + _cy ** 2)


def _colourise(field: np.ndarray, bg, bar, accent) -> np.ndarray:
    """Map a 0..1 scalar field through bg -> bar -> accent gradient."""
    field = np.clip(field, 0.0, 1.0)[..., None]
    lo = field * 2.0                 # 0..1 over first half
    hi = (field - 0.5) * 2.0         # 0..1 over second half
    first = bg * (1 - np.clip(lo, 0, 1)) + bar * np.clip(lo, 0, 1)
    second = bar * (1 - np.clip(hi, 0, 1)) + accent * np.clip(hi, 0, 1)
    mix = np.where(field < 0.5, first, second)
    return mix


def _finish(rgb_small: np.ndarray, pump: float) -> np.ndarray:
    """Brightness pulse on the beat, then upscale to full 1080x1920."""
    rgb_small = rgb_small * (1.0 + 0.18 * pump)
    rgb_small = np.clip(rgb_small, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_small, "RGB").resize((WIDTH, HEIGHT), Image.BILINEAR)
    return np.asarray(img)


# ─────────────────────────────────────────────
#  PROCEDURAL GENERATORS  (return callable(t, pump) -> ndarray)
# ─────────────────────────────────────────────

def _plasma(style: dict):
    bg, bar, accent = _palette(style)

    def frame(t: float, pump: float = 0.0) -> np.ndarray:
        v = (
            np.sin(_nx * 6.0 + t * 0.6)
            + np.sin(_ny * 5.0 - t * 0.4)
            + np.sin((_nx + _ny) * 4.0 + t * 0.5)
            + np.sin(_radius * 12.0 - t * 0.8)
        )
        field = (v + 4.0) / 8.0
        return _finish(_colourise(field, bg, bar, accent), pump)

    return frame


def _flow(style: dict):
    bg, bar, accent = _palette(style)

    def frame(t: float, pump: float = 0.0) -> np.ndarray:
        angle = np.sin(_nx * 3.0 + t * 0.3) + np.cos(_ny * 3.0 - t * 0.25)
        v = np.sin(angle * 2.0 + _radius * 8.0 + t * 0.5)
        field = (v + 1.0) / 2.0
        # vertical falloff keeps the top airy, bottom rich
        field = field * (0.55 + 0.45 * _ny)
        return _finish(_colourise(field, bg, bar, accent), pump)

    return frame


def _mesh(style: dict):
    bg, bar, accent = _palette(style)

    def frame(t: float, pump: float = 0.0) -> np.ndarray:
        # three drifting radial blobs
        b1 = ((_nx - (0.5 + 0.3 * np.sin(t * 0.4))) ** 2 +
              (_ny - (0.35 + 0.15 * np.cos(t * 0.3))) ** 2)
        b2 = ((_nx - (0.3 + 0.25 * np.cos(t * 0.35))) ** 2 +
              (_ny - (0.7 + 0.15 * np.sin(t * 0.5))) ** 2)
        field = np.exp(-b1 * 9.0) + 0.7 * np.exp(-b2 * 11.0)
        return _finish(_colourise(field, bg, bar, accent), pump)

    return frame


def _static(style: dict):
    """Cheapest option — a fixed vertical gradient, no animation."""
    bg, bar, _ = _palette(style)
    base = (bg[None, None, :] * (1 - _ny[..., None] * 0.6) +
            bar[None, None, :] * (_ny[..., None] * 0.25))

    def frame(t: float, pump: float = 0.0) -> np.ndarray:
        return _finish(base.copy(), pump)

    return frame


_GENERATORS = {
    "plasma": _plasma,
    "flow": _flow,
    "mesh": _mesh,
    "gradient": _static,
    "static": _static,
}


def make_background(style: dict, audio_data: dict):
    """
    Build an animated background renderer for the whole song.

    Returns a callable(t, pump) -> np.ndarray(1080, 1920, 3) uint8.
    `pump` (0..1) is the beat envelope supplied by the render engine.
    """
    bg_type = style.get("bg_type", "plasma")
    gen = _GENERATORS.get(bg_type, _plasma)
    print(f"    Background: {bg_type} (procedural, CPU)")
    return gen(style)


# ─────────────────────────────────────────────
#  LEGACY / OPTIONAL PATHS
# ─────────────────────────────────────────────

def generate_art(audio_data: dict, style: dict, output_dir: str = "output") -> str:
    """
    Legacy single-still helper (kept for backwards compat / quick previews).
    Honours huggingface.enabled if a diffusion model is wired; otherwise saves
    one procedural frame as background.png.
    """
    os.makedirs(output_dir, exist_ok=True)
    art_path = os.path.join(output_dir, "background.png")

    hf = style.get("_huggingface", {})
    if hf.get("enabled"):
        vibe = audio_data.get("vibe", "mid-energy")
        prompt = f"{style.get('prompt_prefix', 'abstract music visualizer')}, {vibe} energy, ultra detailed, 4k, vertical 9:16 format"
        try:
            _generate_with_diffusers(prompt, art_path, hf)
            print(f"    ✅ AI background saved: {art_path}")
            return art_path
        except Exception as e:  # noqa: BLE001
            print(f"    ⚠️  Diffusers failed ({e}); falling back to procedural.")

    frame = make_background(style, audio_data)(0.0, 0.0)
    Image.fromarray(frame, "RGB").save(art_path)
    print(f"    ✅ Background saved: {art_path}")
    return art_path


def _generate_with_diffusers(prompt: str, output_path: str, hf: dict):
    """Generate art using a HuggingFace diffusers pipeline (GPU/API path, opt-in)."""
    from diffusers import DiffusionPipeline
    import torch

    model_id = hf.get("model", "black-forest-labs/FLUX.1-schnell")
    pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

    image = pipe(
        prompt=prompt,
        width=WIDTH,
        height=HEIGHT,
        num_inference_steps=hf.get("steps", 4),
        guidance_scale=hf.get("guidance_scale", 0.0),
    ).images[0]
    image.save(output_path)
