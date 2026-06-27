"""
Module 2: AI Art Generator
Generates background artwork using HuggingFace models based on the song vibe.
"""

import os
from PIL import Image


def generate_art(audio_data: dict, style: dict, output_dir: str = "output") -> str:
    """
    Generate AI background art for the video.
    
    Returns:
        Path to the generated background image
    """
    vibe = audio_data.get("vibe", "mid-energy")
    prompt_prefix = style.get("prompt_prefix", "abstract music visualizer")
    
    prompt = f"{prompt_prefix}, {vibe} energy, ultra detailed, 4k, vertical 9:16 format"
    print(f"    Prompt: {prompt[:60]}...")
    
    art_path = os.path.join(output_dir, "background.png")
    
    # TODO: Uncomment when running with GPU / HuggingFace token set
    # _generate_with_diffusers(prompt, art_path, style)
    
    # Fallback: generate a solid colour background
    _generate_fallback_bg(style, art_path)
    
    print(f"    ✅ Background saved: {art_path}")
    return art_path


def _generate_with_diffusers(prompt: str, output_path: str, style: dict):
    """Generate art using HuggingFace diffusers pipeline."""
    from diffusers import DiffusionPipeline
    import torch
    
    model_id = "black-forest-labs/FLUX.1-schnell"
    pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    
    image = pipe(
        prompt=prompt,
        width=1080,
        height=1920,
        num_inference_steps=4,
        guidance_scale=0.0
    ).images[0]
    
    image.save(output_path)


def _generate_fallback_bg(style: dict, output_path: str):
    """Create a gradient fallback background if no GPU available."""
    import numpy as np
    
    width, height = 1080, 1920
    bg_color = style.get("bg_color", "#0a0a0a")
    
    # Convert hex to RGB
    r = int(bg_color[1:3], 16)
    g = int(bg_color[3:5], 16)
    b = int(bg_color[5:7], 16)
    
    # Simple gradient from top to bottom
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        factor = i / height
        img_array[i] = [int(r * (1 - factor * 0.5)),
                        int(g * (1 - factor * 0.5)),
                        int(b * (1 - factor * 0.3))]
    
    Image.fromarray(img_array).save(output_path)
