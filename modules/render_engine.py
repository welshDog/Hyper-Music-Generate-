"""
Module: Render Engine — the compositing spine.

Builds every video frame in one fast Pillow/numpy pass, layering:

    background(t, pump)  →  visualizer(frame_idx, t, pump)  →  text/lyrics(t)

No matplotlib in the loop; reuses M1's precomputed `frame_bars`/`beat_times`.
A single beat-pump envelope drives background brightness, bar scaling and motion.

Public API:
    render_video(audio_data, style, title, artist, lyrics_file, output_dir, preview)
        -> path to the silent composited video (audio is muxed later by video_builder)
"""

import os
import bisect
import numpy as np
from PIL import Image
from moviepy.editor import VideoClip

from modules.art_generator import make_background
from modules.visualizer import make_visualizer
from modules.text_overlay import make_text_layer

WIDTH, HEIGHT = 1080, 1920
FPS = 30
_PUMP_DECAY = 0.18   # seconds for a beat kick to fall off


def _make_beat_pump(beat_times: list):
    beats = sorted(beat_times)

    def pump(t: float) -> float:
        if not beats:
            return 0.0
        i = bisect.bisect_right(beats, t) - 1
        if i < 0:
            return 0.0
        age = t - beats[i]
        return max(0.0, 1.0 - age / _PUMP_DECAY)

    return pump


def render_video(
    audio_data: dict,
    style: dict,
    title: str = "",
    artist: str = "",
    lyrics_file: str = "",
    output_dir: str = "output",
    preview: float = None,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "visualizer.mp4")

    duration = float(audio_data["duration"])
    if preview:
        duration = min(duration, float(preview))

    background = make_background(style, audio_data)
    visualizer = make_visualizer(style, audio_data)
    text_layer = make_text_layer(style, title, artist, lyrics_file, audio_data)
    pump_of = _make_beat_pump(audio_data.get("beat_times", []))

    print(f"    Compositing {int(duration * FPS)} frames @ {FPS}fps...")

    def make_frame(t: float) -> np.ndarray:
        pump = pump_of(t)
        frame_idx = int(t * FPS)

        base = Image.fromarray(background(t, pump), "RGB").convert("RGBA")
        base = Image.alpha_composite(base, visualizer(frame_idx, t, pump))
        base = Image.alpha_composite(base, text_layer(t))
        return np.asarray(base.convert("RGB"))

    clip = VideoClip(make_frame, duration=duration)
    clip.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="medium",
        threads=os.cpu_count() or 4,
        logger=None,
    )
    print(f"    ✅ Composited video: {output_path}")
    return output_path
