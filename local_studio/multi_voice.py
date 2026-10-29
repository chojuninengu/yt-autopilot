import os
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pydub import AudioSegment
import edge_tts
from .sfx_generator import ensure_sfx_library

async def _synthesize_line(text: str, voice: str, output_path: Path):
    communicate = edge_tts.Communicate(text, voice, rate="+8%")
    await communicate.save(str(output_path))

def render_battle_audio(battle_plan: Dict[str, Any], work_dir: Path) -> Tuple[List[Dict[str, Any]], Path, Path]:
    """Synthesizes dialogue lines with distinct character voices, overlays SFX, and creates color-coded subtitles.
    Returns: (scene_audio_meta, master_audio_path, srt_path)
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    sfx_lib = ensure_sfx_library()

    char1 = battle_plan.get("character_1", {"name": "Character 1", "voice": "en-US-ChristopherNeural", "color": "&H00D7FF"})
    char2 = battle_plan.get("character_2", {"name": "Character 2", "voice": "en-US-GuyNeural", "color": "&HFFFFFF"})

    scenes = battle_plan.get("scenes", [])
    scene_audio_meta = []
    combined_audio = AudioSegment.silent(duration=300)  # 300ms initial breath

    srt_entries = []
    current_ms = 300

    print(f"[MultiVoice] Synthesizing battle dialogue ({char1['name']} vs {char2['name']})...")

    for i, scene in enumerate(scenes):
        idx = scene.get("scene_number", i + 1)
        speaker_id = scene.get("speaker", 1)
        speaker = char1 if speaker_id == 1 else char2
        voice = speaker.get("voice", "en-US-ChristopherNeural")
        dialogue = scene.get("dialogue", "")
        sfx_key = scene.get("sfx", "")

        raw_speech_file = work_dir / f"speech_{idx:02d}.mp3"
        mixed_scene_file = work_dir / f"scene_audio_{idx:02d}.mp3"

        # 1. Synthesize character voice
        asyncio.run(_synthesize_line(dialogue, voice, raw_speech_file))

        speech_seg = AudioSegment.from_file(raw_speech_file)

        # 2. Overlay SFX if specified
        if sfx_key and sfx_key in sfx_lib and sfx_lib[sfx_key].exists():
            sfx_seg = AudioSegment.from_file(sfx_lib[sfx_key])
            # Volume boost for heavy impacts
            if sfx_key in ["punch", "ground_slam"]:
                sfx_seg = sfx_seg + 2
            else:
                sfx_seg = sfx_seg - 3
            # Overlay at the start or mid-speech
            mixed_seg = speech_seg.overlay(sfx_seg, position=0)
        else:
            mixed_seg = speech_seg

        # Add brief 400ms pause after turn for dramatic tension
        mixed_seg = mixed_seg + AudioSegment.silent(duration=400)
        mixed_seg.export(mixed_scene_file, format="mp3")

        seg_duration_ms = len(mixed_seg)
        start_ms = current_ms
        end_ms = current_ms + seg_duration_ms - 200

        # Subtitle entry formatted with character name prefix
        def fmt_time(ms):
            s = ms // 1000
            m = s // 60
            h = m // 60
            ms_rem = ms % 1000
            return f"{h:02d}:{m%60:02d}:{s%60:02d},{ms_rem:03d}"

        srt_entries.append(
            f"{i+1}\n{fmt_time(start_ms)} --> {fmt_time(end_ms)}\n"
            f"{speaker['name'].upper()}: {dialogue}\n"
        )

        combined_audio = combined_audio + mixed_seg
        scene_audio_meta.append({
            "scene_number": idx,
            "speaker": speaker["name"],
            "duration": seg_duration_ms / 1000.0,
            "audio_path": mixed_scene_file,
            "shake": scene.get("shake", False)
        })
        current_ms += seg_duration_ms

    master_audio_path = work_dir / "battle_master.mp3"
    combined_audio.export(master_audio_path, format="mp3")

    srt_path = work_dir / "battle_subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    print(f"[MultiVoice] Master battle soundtrack ready: {current_ms/1000:.2f}s with {len(scenes)} character turns.")
    return scene_audio_meta, master_audio_path, srt_path
