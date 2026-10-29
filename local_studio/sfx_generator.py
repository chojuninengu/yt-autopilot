import math
import wave
from pathlib import Path
import numpy as np

SFX_DIR = Path(__file__).resolve().parent / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)

def generate_whoosh(path: Path, duration: float = 0.5, sr: int = 44100):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Bandpass swept noise
    noise = np.random.uniform(-1, 1, len(t))
    sweep = np.sin(np.pi * t / duration) ** 2
    f_mod = 300 + 1200 * np.sin(np.pi * t / duration)
    phase = 2 * np.pi * np.cumsum(f_mod) / sr
    audio = 0.6 * noise * sweep + 0.4 * np.sin(phase) * sweep
    audio = (audio / np.max(np.abs(audio) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def generate_punch(path: Path, duration: float = 0.6, sr: int = 44100):
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = 180 * np.exp(-14 * t) + 45
    phase = 2 * np.pi * np.cumsum(freq) / sr
    sine = np.sin(phase)
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-30 * t)
    envelope = np.exp(-6 * t)
    audio = (0.75 * sine + 0.45 * noise) * envelope
    audio = (audio / np.max(np.abs(audio) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def generate_ground_slam(path: Path, duration: float = 1.2, sr: int = 44100):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Deep earthquake sub-bass 80Hz -> 25Hz with rumbling noise
    freq = 90 * np.exp(-5 * t) + 25
    phase = 2 * np.pi * np.cumsum(freq) / sr
    sub = np.sin(phase) * np.exp(-2.5 * t)
    rumble = np.random.uniform(-1, 1, len(t)) * np.exp(-4 * t)
    audio = 0.8 * sub + 0.5 * rumble
    audio = (audio / np.max(np.abs(audio) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def generate_laser(path: Path, duration: float = 0.4, sr: int = 44100):
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = 2200 * np.exp(-18 * t) + 200
    phase = 2 * np.pi * np.cumsum(freq) / sr
    audio = np.sin(phase) * np.exp(-5 * t)
    audio = (audio / np.max(np.abs(audio) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def ensure_sfx_library() -> dict:
    """Ensures all standard action sound effects exist and returns their filepaths."""
    effects = {
        "whoosh": SFX_DIR / "whoosh.wav",
        "punch": SFX_DIR / "punch.wav",
        "ground_slam": SFX_DIR / "ground_slam.wav",
        "laser": SFX_DIR / "laser.wav"
    }
    if not effects["whoosh"].exists():
        generate_whoosh(effects["whoosh"])
    if not effects["punch"].exists():
        generate_punch(effects["punch"])
    if not effects["ground_slam"].exists():
        generate_ground_slam(effects["ground_slam"])
    if not effects["laser"].exists():
        generate_laser(effects["laser"])
    return effects

if __name__ == "__main__":
    ensure_sfx_library()
    print("All SFX generated in", SFX_DIR)
