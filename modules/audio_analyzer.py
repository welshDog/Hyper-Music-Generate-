"""
Module 1: Audio Analyzer - FULL M1 BUILD
Extracts BPM, beat timestamps, onset strength, energy per frame,
spectral data, waveform preview, and per-frame bar data for the visualizer.
"""

import librosa
import numpy as np
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def analyze_audio(audio_path: str, output_dir: str = "output") -> dict:
    """
    Full audio analysis pipeline.

    Returns dict with:
        y, sr, bpm, beat_times, onset_times, duration,
        rms_frames, spectral_centroid, mel_spec_db,
        frame_bars, hop_length, fps, vibe, waveform_preview_path
    """
    print(f"    Loading: {audio_path}")
    os.makedirs(output_dir, exist_ok=True)

    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # --- BPM & Beat Tracking ---
    bpm, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(np.asarray(bpm).reshape(-1)[0])  # newer librosa returns an array
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # --- Onset Detection (note starts, hits) ---
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()

    # --- RMS Energy per frame ---
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

    # --- Spectral Features ---
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    spectral_rolloff  = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)[0]
    zero_crossing     = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]

    # --- Mel Spectrogram (128 bands) ---
    mel_spec    = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, hop_length=hop_length)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    # --- Per-frame bar data for visualizer (64 bars, normalised 0-1) ---
    fps = 30
    frame_count = int(duration * fps)
    frame_bars  = _build_frame_bars(y, sr, fps, frame_count, n_bars=64)

    # --- Vibe Detection ---
    vibe = _detect_vibe(
        float(bpm),
        float(np.mean(rms)),
        float(np.mean(spectral_centroid))
    )

    # --- Waveform Preview Image ---
    waveform_path = _save_waveform_preview(y, sr, beat_times, output_dir)

    # --- Save analysis JSON (handy for debugging) ---
    analysis_summary = {
        "file": audio_path,
        "bpm": float(bpm),
        "duration": float(duration),
        "beat_count": len(beat_times),
        "onset_count": len(onset_times),
        "vibe": vibe,
        "sample_rate": int(sr),
        "fps": fps,
        "frame_count": frame_count,
    }
    summary_path = os.path.join(output_dir, "audio_analysis.json")
    with open(summary_path, "w") as f:
        json.dump(analysis_summary, f, indent=2)

    print(f"    ✅ BPM: {bpm:.1f} | Duration: {duration:.1f}s | Beats: {len(beat_times)} | Vibe: {vibe}")
    print(f"    📊 Waveform preview → {waveform_path}")
    print(f"    📄 Analysis JSON   → {summary_path}")

    return {
        "y":                   y,
        "sr":                  int(sr),
        "bpm":                 float(bpm),
        "beat_times":          beat_times,
        "onset_times":         onset_times,
        "duration":            float(duration),
        "rms":                 rms,
        "spectral_centroid":   spectral_centroid,
        "spectral_rolloff":    spectral_rolloff,
        "zero_crossing":       zero_crossing,
        "mel_spec_db":         mel_spec_db,
        "frame_bars":          frame_bars,
        "hop_length":          hop_length,
        "fps":                 fps,
        "vibe":                vibe,
        "waveform_preview":    waveform_path,
        "summary_path":        summary_path,
    }


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _build_frame_bars(y: np.ndarray, sr: int, fps: int, frame_count: int, n_bars: int = 64) -> list:
    """
    For every video frame, compute n_bars FFT frequency magnitudes (0-1).
    Returns a list of lists: frame_bars[frame_idx] = [bar0, bar1, ... bar63]
    """
    samples_per_frame = sr // fps
    bars_per_frame = []

    for i in range(frame_count):
        start = i * samples_per_frame
        end   = start + samples_per_frame * 4  # 4-frame window for smoother look
        chunk = y[start:end] if end < len(y) else y[start:]

        if len(chunk) < 64:
            bars_per_frame.append([0.0] * n_bars)
            continue

        fft  = np.abs(np.fft.rfft(chunk, n=n_bars * 2))[:n_bars]
        peak = np.max(fft)
        norm = (fft / peak).tolist() if peak > 0 else [0.0] * n_bars
        bars_per_frame.append(norm)

    return bars_per_frame


def _detect_vibe(bpm: float, energy: float, brightness: float) -> str:
    """Classify the song vibe from audio features."""
    if bpm > 150:
        return "high-energy"
    elif bpm > 125 and energy > 0.05:
        return "upbeat"
    elif bpm > 100:
        return "mid-energy"
    elif bpm < 75:
        return "chill"
    elif brightness > 4000:
        return "bright-electronic"
    else:
        return "mid-energy"


def _save_waveform_preview(y: np.ndarray, sr: int, beat_times: list, output_dir: str) -> str:
    """Save a waveform image with beat markers overlaid."""
    output_path = os.path.join(output_dir, "waveform_preview.png")
    duration    = librosa.get_duration(y=y, sr=sr)
    times       = np.linspace(0, duration, len(y))

    fig, ax = plt.subplots(figsize=(14, 4), facecolor="#0a0a0a")
    ax.set_facecolor("#0a0a0a")

    # Waveform
    ax.plot(times, y, color="#00ffff", linewidth=0.4, alpha=0.85)

    # Beat markers
    for bt in beat_times:
        ax.axvline(x=bt, color="#ff00ff", linewidth=0.8, alpha=0.6)

    ax.set_xlim(0, duration)
    ax.set_ylim(-1, 1)
    ax.set_xlabel("Time (s)", color="#aaaaaa", fontsize=9)
    ax.set_ylabel("Amplitude", color="#aaaaaa", fontsize=9)
    ax.tick_params(colors="#555555")
    ax.spines[:].set_color("#222222")
    ax.set_title("🎵 Waveform + Beat Markers", color="#00ffff", fontsize=11, pad=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight", facecolor="#0a0a0a")
    plt.close()

    return output_path
