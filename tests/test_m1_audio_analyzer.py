"""
M1 Test Script - Audio Analyzer
Run: python tests/test_m1_audio_analyzer.py

Drops a test tone if no real song is available,
then runs the full analyze_audio() pipeline and prints a report.
"""

import sys
import os
import numpy as np
import soundfile as sf

# Allow running from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.audio_analyzer import analyze_audio


def generate_test_tone(path: str, duration: float = 10.0, sr: int = 22050):
    """Generate a simple 440Hz sine wave test tone with a beat-like pulse."""
    t       = np.linspace(0, duration, int(sr * duration))
    # Base tone
    tone    = 0.4 * np.sin(2 * np.pi * 440 * t)
    # Add a 120bpm pulse every 0.5s
    pulse   = np.zeros_like(t)
    bpm     = 120
    beat_s  = 60.0 / bpm
    for i in range(int(duration / beat_s)):
        idx = int(i * beat_s * sr)
        pulse[idx:idx + 1000] += 0.6 * np.sin(2 * np.pi * 80 * t[:1000])
    audio = np.clip(tone + pulse, -1.0, 1.0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, audio, sr)
    print(f"🎵 Generated test tone → {path}")
    return path


def run_test(audio_path: str = None):
    # If no song provided, generate a test tone
    if not audio_path or not os.path.exists(audio_path):
        audio_path = generate_test_tone("input/test_tone.wav")

    print("\n" + "═" * 50)
    print("  🥇 M1 Audio Analyzer Test")
    print("═" * 50)

    data = analyze_audio(audio_path, output_dir="output")

    print("\n📋 Analysis Report:")
    print(f"  🎵 BPM          : {data['bpm']:.2f}")
    print(f"  ⏱  Duration     : {data['duration']:.2f}s")
    print(f"  🎯 Beats        : {len(data['beat_times'])}")
    print(f"  💥 Onsets       : {len(data['onset_times'])}")
    print(f"  🎨 Vibe         : {data['vibe']}")
    print(f"  📊 Sample Rate  : {data['sr']} Hz")
    print(f"  🎬 Frame Count  : {len(data['frame_bars'])} @ {data['fps']}fps")
    print(f"  📈 Bars/frame   : {len(data['frame_bars'][0])} bars")
    print(f"  🖼  Waveform     : {data['waveform_preview']}")
    print(f"  📄 JSON Summary : {data['summary_path']}")

    # Sanity checks
    assert data['bpm'] > 0,                 "BPM should be > 0"
    assert data['duration'] > 0,            "Duration should be > 0"
    assert len(data['frame_bars']) > 0,     "Should have frame bar data"
    assert len(data['frame_bars'][0]) == 64, "Should have 64 bars per frame"
    assert os.path.exists(data['waveform_preview']), "Waveform image should exist"

    print("\n✅ All checks passed! M1 is GO! 🚀")
    print("═" * 50 + "\n")


if __name__ == "__main__":
    # Pass your own song path as arg, or it auto-generates a test tone
    song = sys.argv[1] if len(sys.argv) > 1 else None
    run_test(song)
