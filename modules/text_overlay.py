"""
Module 4: Text Overlay
Adds title, artist name, and optional lyrics to the video.
"""

import os
from PIL import Image, ImageDraw, ImageFont


def add_text_overlay(
    visualizer_path: str,
    art_path: str,
    title: str,
    artist: str,
    lyrics_file: str = "",
    style: dict = None,
    output_dir: str = "output"
) -> str:
    """
    Composite the visualizer over the background art and add text overlays.
    
    Returns:
        Path to composited video with overlays
    """
    # TODO: Full implementation in M3
    # For now, returns the visualizer path as a passthrough
    print(f"    Title: {title} | Artist: {artist}")
    print(f"    ⚠️  Text overlay module - coming in M3!")
    return visualizer_path


def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font, falling back to default if not found."""
    try:
        return ImageFont.truetype(font_path, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def _add_title_card(frame: Image.Image, title: str, artist: str, style: dict) -> Image.Image:
    """Add title and artist text to a frame."""
    draw = ImageDraw.Draw(frame)
    
    font_path = style.get("font", "assets/fonts/bold.ttf") if style else ""
    accent_color = style.get("accent_color", "#ffffff") if style else "#ffffff"
    
    title_font = _load_font(font_path, 80)
    artist_font = _load_font(font_path, 50)
    
    # Title at top
    draw.text((54, 120), title, font=title_font, fill=accent_color)
    # Artist below
    draw.text((54, 220), artist, font=artist_font, fill="#cccccc")
    
    return frame
