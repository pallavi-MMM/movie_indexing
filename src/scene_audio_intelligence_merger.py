"""
Audio Intelligence Merger: Integrate audio signals into final complete schema.

Adds 7 fields to each scene:
  - background_music_mood
  - sfx_presence
  - sfx_details
  - audio_peaks_detected
  - sound_design_notes
  - narration_present
  - narration_text
"""

import os
import json
import sys

MOVIE_NAME = "Alanati ramachandrudu - trailer"
OUTPUT_JSON_DIR = "output_json"


def merge_audio_intelligence(movie_name=None):
    """
    Load audio intelligence and merge into complete schema.
    """
    # Determine target movie from parameter or globals
    target_movie = movie_name or globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME") or MOVIE_NAME
    
    # Load audio intelligence
    audio_intel_file = f"outputs/scene_audio/{target_movie}/{target_movie}_audio_intelligence.json"
    
    if not os.path.exists(audio_intel_file):
        print(f"[WARN] Audio intelligence file not found: {audio_intel_file}")
        return
    
    with open(audio_intel_file, "r", encoding="utf-8") as f:
        audio_data = json.load(f)
    
    audio_intel = audio_data.get("audio_intelligence", {})
    
    # Load complete schema
    complete_schema_file = f"{OUTPUT_JSON_DIR}/{target_movie}_complete_schema.json"
    
    if not os.path.exists(complete_schema_file):
        print(f"[WARN] Complete schema not found: {complete_schema_file}")
        return
    
    with open(complete_schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    print(f"[AUDIO INTELLIGENCE MERGE] Merging into {complete_schema_file}")
    
    # Merge audio intelligence into each scene
    scenes = schema.get("scenes", [])
    merged_count = 0
    
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        
        if scene_id not in audio_intel:
            print(f"  [WARN] No audio intelligence for {scene_id}")
            continue
        
        audio_intel_scene = audio_intel[scene_id]
        
        # Add all 7 audio intelligence fields
        scene["background_music_mood"] = audio_intel_scene.get("background_music_mood", "unknown")
        scene["sfx_presence"] = audio_intel_scene.get("sfx_presence", False)
        scene["sfx_details"] = audio_intel_scene.get("sfx_details", [])
        scene["audio_peaks_detected"] = audio_intel_scene.get("audio_peaks_detected", False)
        scene["sound_design_notes"] = audio_intel_scene.get("sound_design_notes", "")
        scene["narration_present"] = audio_intel_scene.get("narration_present", False)
        scene["narration_text"] = audio_intel_scene.get("narration_text", "")
        
        merged_count += 1
        print(f"  [{scene_id}] Merged audio intelligence: "
              f"mood={scene['background_music_mood']}, "
              f"sfx={scene['sfx_presence']}, "
              f"narration={scene['narration_present']}")
    
    # Save merged schema
    with open(complete_schema_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Audio intelligence merged → {complete_schema_file}")


def main():
    """Pipeline entry point."""
    movie_name = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME")
    merge_audio_intelligence(movie_name)


if __name__ == "__main__":
    main()
