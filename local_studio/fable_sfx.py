import wave
from pathlib import Path
import numpy as np

SFX_DIR = Path(__file__).resolve().parent / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)

def generate_digging(path: Path, duration: float = 1.0, sr: int = 44100):
    """Synthesizes metal shovel digging into rocky dry soil."""
    t = np.linspace(0, duration, int(sr * duration), False)
    # Shovel scrape + earth thud
    scrape_noise = np.random.uniform(-1, 1, len(t))
    # Filter envelope for two distinct shovel scoops
    env1 = np.exp(-12 * (t % 0.5)) * (t < 0.9)
    scrape = scrape_noise * env1
    clink = np.sin(2 * np.pi * 1800 * t) * np.exp(-35 * (t % 0.5))
    audio = 0.7 * scrape + 0.3 * clink
    audio = (audio / (np.max(np.abs(audio)) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def generate_gushing(path: Path, duration: float = 1.8, sr: int = 44100):
    """Synthesizes sudden geyser of liquid (oil/water fountain) bursting from ground."""
    t = np.linspace(0, duration, int(sr * duration), False)
    # White noise through lowpass resonance + bubbling frequency modulation
    noise = np.random.uniform(-1, 1, len(t))
    surge = np.clip(t / 0.3, 0, 1) * np.exp(-1.2 * t)
    rumble = np.sin(2 * np.pi * 60 * t) * surge
    audio = 0.65 * noise * surge + 0.5 * rumble
    audio = (audio / (np.max(np.abs(audio)) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def generate_tear_drop(path: Path, duration: float = 0.5, sr: int = 44100):
    """Synthesizes tear drops hitting dry ground."""
    t = np.linspace(0, duration, int(sr * duration), False)
    # Water droplet pitch sweep 800Hz -> 400Hz
    freq = 800 - 400 * (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    audio = np.sin(phase) * np.exp(-15 * t)
    audio = (audio / (np.max(np.abs(audio)) + 1e-6) * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def ensure_fable_sfx() -> dict:
    """Ensures all fable sound effects are generated and ready."""
    sfx = {
        "digging": SFX_DIR / "digging.wav",
        "gushing": SFX_DIR / "gushing.wav",
        "tears": SFX_DIR / "tears.wav"
    }
    if not sfx["digging"].exists():
        generate_digging(sfx["digging"])
    if not sfx["gushing"].exists():
        generate_gushing(sfx["gushing"])
    if not sfx["tears"].exists():
        generate_tear_drop(sfx["tears"])
    return sfx

if __name__ == "__main__":
    ensure_fable_sfx()
    print("Fable SFX ready in", SFX_DIR)
