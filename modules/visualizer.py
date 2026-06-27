"""
Module 3: Visualizer
Creates animated audio-reactive visualizer frames synced to the beat.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from moviepy.editor import VideoClip
from PIL import Image


def create_visualizer(audio_path: str, audio_data: dict, style: dict, output_dir: str = "output") -> str:
    """
    Create an animated visualizer video (no audio, just visuals).
    
    Returns:
        Path to the visualizer video file
    """
    visualizer_type = style.get("visualizer_type", "bars")
    output_path = os.path.join(output_dir, "visualizer.mp4")
    
    print(f"    Type: {visualizer_type} | FPS: 30")
    
    if visualizer_type == "bars":
        _create_bar_visualizer(audio_data, style, output_path)
    elif visualizer_type == "waveform":
        _create_waveform_visualizer(audio_data, style, output_path)
    else:
        _create_bar_visualizer(audio_data, style, output_path)
    
    print(f"    ✅ Visualizer saved: {output_path}")
    return output_path


def _create_bar_visualizer(audio_data: dict, style: dict, output_path: str):
    """Create a bar chart style audio visualizer."""
    import librosa
    
    y = audio_data["y"]
    sr = audio_data["sr"]
    duration = audio_data["duration"]
    fps = 30
    bar_count = style.get("bar_count", 64)
    bar_color = style.get("bar_color", "#00ffff")
    bg_color = style.get("bg_color", "#0a0a0a")
    
    hop_length = int(sr / fps)
    
    def make_frame(t):
        frame_idx = int(t * fps)
        start_sample = frame_idx * hop_length
        end_sample = start_sample + hop_length * 4
        
        chunk = y[start_sample:end_sample] if end_sample < len(y) else y[start_sample:]
        if len(chunk) == 0:
            chunk = np.zeros(hop_length)
        
        # FFT for frequency bars
        fft = np.abs(np.fft.rfft(chunk, n=bar_count * 2))[:bar_count]
        fft = fft / (np.max(fft) + 1e-8)  # Normalise
        
        fig, ax = plt.subplots(figsize=(10.8, 19.2), dpi=10)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        x = np.arange(bar_count)
        ax.bar(x, fft, color=bar_color, width=0.8)
        ax.set_xlim(-1, bar_count)
        ax.set_ylim(0, 1.2)
        ax.axis("off")
        plt.tight_layout(pad=0)
        
        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        plt.close(fig)
        return frame
    
    clip = VideoClip(make_frame, duration=duration)
    clip.write_videofile(output_path, fps=fps, codec="libx264", logger=None)


def _create_waveform_visualizer(audio_data: dict, style: dict, output_path: str):
    """Create a waveform style visualizer."""
    # TODO: Implement waveform visualizer
    # For now, falls back to bar visualizer
    _create_bar_visualizer(audio_data, style, output_path)
