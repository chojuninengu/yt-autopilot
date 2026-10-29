import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pydub import AudioSegment
import edge_tts
from .fable_sfx import ensure_fable_sfx
from .sfx_generator import ensure_sfx_library

async def _synthesize_voice(text: str, voice: str, rate: str, pitch: str, output_path: Path):
    clean_text = text.replace("...", ". ").strip()
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
            await communicate.save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 500:
                return
        except Exception as e:
            if attempt == 2:
                communicate = edge_tts.Communicate(clean_text, "en-US-GuyNeural")
                await communicate.save(str(output_path))
            await asyncio.sleep(1)

def render_fable_audio(fable_plan: Dict[str, Any], work_dir: Path) -> Tuple[List[Dict[str, Any]], Path, Path]:
    """Synthesizes high-emotion acting voices for both characters, overlays story SFX, and generates centered viral captions."""
    work_dir.mkdir(parents=True, exist_ok=True)
    fable_sfx = ensure_fable_sfx()
    action_sfx = ensure_sfx_library()
    all_sfx = {**action_sfx, **fable_sfx}

    char1 = fable_plan.get("character_1", {"name": "Watermelon", "voice": "en-US-GuyNeural"})
    char2 = fable_plan.get("character_2", {"name": "Banana", "voice": "en-US-ChristopherNeural"})

    scenes = fable_plan.get("scenes", [])
    scene_audio_meta = []
    combined_audio = AudioSegment.silent(duration=200)

    srt_entries = []
    current_ms = 200

    print(f"[FableAudio] Directing voice acting for {char1['name']} & {char2['name']}...")

    for i, scene in enumerate(scenes):
        idx = scene.get("scene_number", i + 1)
        speaker_id = scene.get("speaker", 1)
        speaker = char1 if speaker_id == 1 else char2
        dialogue = scene.get("dialogue", "")
        emotion = scene.get("emotion", "neutral")
        sfx_key = scene.get("sfx", "")
        highlight_word = scene.get("highlight_word", "")

        raw_audio_file = work_dir / f"fable_voice_{idx:02d}.mp3"
        mixed_file = work_dir / f"fable_scene_{idx:02d}.mp3"

        # Emotional pitch and speed tuning
        if emotion == "crying":
            rate = "-4%"
            pitch = "+5Hz"
        elif emotion == "arrogant":
            rate = "+6%"
            pitch = "-2Hz"
        elif emotion == "shocked_triumph":
            rate = "+8%"
            pitch = "+8Hz"
        elif emotion == "cold_rejection":
            rate = "-6%"
            pitch = "-4Hz"
        else:
            rate = "+0%"
            pitch = "+0Hz"

        asyncio.run(_synthesize_voice(dialogue, speaker.get("voice", "en-US-ChristopherNeural"), rate, pitch, raw_audio_file))
        speech_seg = AudioSegment.from_file(raw_audio_file)

        # Overlay SFX
        if sfx_key and sfx_key in all_sfx and all_sfx[sfx_key].exists():
            sfx_seg = AudioSegment.from_file(all_sfx[sfx_key])
            if sfx_key in ["gushing", "ground_slam"]:
                sfx_seg = sfx_seg + 3
            else:
                sfx_seg = sfx_seg - 2
            mixed_seg = speech_seg.overlay(sfx_seg, position=0)
        else:
            mixed_seg = speech_seg

        # Dramatic pause between beats
        pause_len = 600 if idx in [2, 3, 6] else 400
        mixed_seg = mixed_seg + AudioSegment.silent(duration=pause_len)
        mixed_seg.export(mixed_file, format="mp3")

        seg_duration_ms = len(mixed_seg)
        start_ms = current_ms
        end_ms = current_ms + seg_duration_ms - 200

        def fmt_time(ms):
            s = ms // 1000
            m = s // 60
            h = m // 60
            ms_rem = ms % 1000
            return f"{h:02d}:{m%60:02d}:{s%60:02d},{ms_rem:03d}"

        # Subtitle caption: punchy line with highlight word
        display_caption = dialogue.strip()
        if highlight_word and highlight_word.upper() in display_caption.upper():
            display_caption = display_caption.upper()

        srt_entries.append(
            f"{i+1}\n{fmt_time(start_ms)} --> {fmt_time(end_ms)}\n"
            f"{display_caption}\n"
        )

        combined_audio = combined_audio + mixed_seg
        scene_audio_meta.append({
            "scene_number": idx,
            "speaker": speaker["name"],
            "duration": seg_duration_ms / 1000.0,
            "audio_path": mixed_file,
            "shake": scene.get("shake", False),
            "highlight": highlight_word
        })
        current_ms += seg_duration_ms

    master_audio_path = work_dir / "fable_soundtrack.mp3"
    combined_audio.export(master_audio_path, format="mp3")

    srt_path = work_dir / "fable_captions.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    print(f"[FableAudio] Fable soundtrack ready: {current_ms/1000:.2f}s with {len(scenes)} narrative beats.")
    return scene_audio_meta, master_audio_path, srt_path
