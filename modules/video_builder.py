"""
Module 5: Video Builder
Final step - stitches all layers together into a TikTok-ready MP4.
"""

import os
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip


def build_video(
    overlay_path: str,
    audio_path: str,
    style: dict,
    output_dir: str = "output"
) -> str:
    """
    Combine visualizer video + original audio into final TikTok-ready MP4.
    
    Returns:
        Path to the final output video
    """
    output_path = os.path.join(output_dir, "tiktok_ready.mp4")
    
    print(f"    Combining video + audio...")
    
    video = VideoFileClip(overlay_path)
    audio = AudioFileClip(audio_path)
    
    # Match video duration to audio
    if video.duration < audio.duration:
        video = video.loop(duration=audio.duration)
    else:
        video = video.subclip(0, audio.duration)
    
    final = video.set_audio(audio)
    
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="output/temp_audio.m4a",
        remove_temp=True,
        logger=None
    )
    
    print(f"    ✅ Final video: {output_path}")
    return output_path
