"""
Scene Classification & Enrichment Module

Populates missing critical fields:
- scene_type: Classification of scene (dialogue, action, montage, exposition, etc.)
- character details: Ensures characters are properly populated
- scene metadata validation

Run after all other enrichments to fill gaps.
"""

import json
import os
import sys
from typing import List, Dict, Any


MOVIE_NAME = "Alanati ramachandrudu - trailer"
OUTPUT_JSON_DIR = "output_json"


def classify_scene_type(scene: Dict[str, Any]) -> str:
    """
    Classify scene type based on content analysis.
    
    Returns one of:
    - "dialogue" - primarily conversation/dialogue
    - "action" - physical activity/movement
    - "montage" - sequence of short moments
    - "exposition" - information/explanation
    - "emotional" - emotional scene
    - "transition" - connecting scene
    - "climax" - intense/confrontational
    - "quiet" - minimal dialogue/activity
    """
    dialogue = scene.get("dialogue_text", [])
    actions = scene.get("actions", [])
    location = scene.get("location", "")
    motion_intensity = scene.get("motion_intensity_score", 0)
    arousal = scene.get("emotion_arousal_score", 0)
    duration = scene.get("duration", 0)
    characters = scene.get("characters", [])
    background_activity = scene.get("background_activity", [])
    
    # Signals for classification
    dialogue_lines = len(dialogue)
    action_count = len(actions)
    bg_activity_count = len(background_activity)
    char_count = len(characters)
    
    # Check for climax marker
    if scene.get("climax_point_flag", False):
        return "climax"
    
    # High motion, low dialogue = action
    if motion_intensity > 40 and dialogue_lines < 5:
        return "action"
    
    # Short scenes with many moments = montage
    if duration < 10 and (action_count > 2 or bg_activity_count > 3):
        return "montage"
    
    # High arousal + dialogue = emotional or confrontation
    if arousal >= 0.3:
        if dialogue_lines > 8:
            return "emotional"
        else:
            return "climax"
    
    # Lots of dialogue, no action = dialogue scene
    if dialogue_lines >= 5 and action_count == 0 and motion_intensity < 20:
        return "dialogue"
    
    # Low dialogue, no action = quiet scene
    if dialogue_lines < 2 and action_count == 0 and motion_intensity < 15:
        return "quiet"
    
    # Mixed dialogue and activity = scene (generic)
    if dialogue_lines > 0 and (action_count > 0 or bg_activity_count > 0):
        return "exposition"
    
    # Low duration, connecting feel = transition
    if duration < 5:
        return "transition"
    
    # Default
    return "scene"


def extract_character_names_from_dialogue(dialogue: List[Dict]) -> List[str]:
    """
    Extract character names from dialogue speakers.
    """
    speakers = set()
    for d in dialogue:
        speaker = d.get("speaker", "").strip()
        if speaker and speaker.lower() != "unknown" and speaker:
            speakers.add(speaker)
    
    return sorted(list(speakers))


def enrich_scene_metadata(scene: Dict[str, Any], scene_index: int, total_scenes: int) -> Dict[str, Any]:
    """
    Populate missing critical fields in scene.
    """
    # 1. Leave scene_type empty (requires manual definition or proper classification)
    # if not scene.get("scene_type") or scene.get("scene_type") == "":
    #     scene["scene_type"] = classify_scene_type(scene)
    
    # 2. Extract characters from dialogue if not present
    if not scene.get("characters") or len(scene.get("characters", [])) == 0:
        dialogue = scene.get("dialogue_text", [])
        if dialogue:
            extracted_chars = extract_character_names_from_dialogue(dialogue)
            if extracted_chars:
                scene["characters"] = extracted_chars
    
    # 3. Ensure narrative_function is set
    if not scene.get("narrative_function") or scene.get("narrative_function") == "":
        scene["narrative_function"] = _determine_narrative_function(scene)
    
    # 4. Ensure story_progress_tag consistency
    if not scene.get("story_progress_tag") or scene.get("story_progress_tag") == "":
        scene["story_progress_tag"] = _compute_story_progress(scene_index, total_scenes, scene)
    
    # 5. Add scene_complexity score
    complexity = _compute_scene_complexity(scene)
    scene["scene_complexity_score"] = complexity
    
    # 6. Add character_count for easy filtering
    scene["character_count"] = len(scene.get("characters", []))
    
    # 7. Add dialogue_intensity
    dialogue_count = len(scene.get("dialogue_text", []))
    if dialogue_count == 0:
        scene["dialogue_intensity"] = "none"
    elif dialogue_count < 3:
        scene["dialogue_intensity"] = "minimal"
    elif dialogue_count < 8:
        scene["dialogue_intensity"] = "moderate"
    else:
        scene["dialogue_intensity"] = "heavy"
    
    return scene


def _determine_narrative_function(scene: Dict[str, Any]) -> str:
    """Determine what narrative role the scene plays."""
    # If already set, keep it
    if scene.get("narrative_function") and scene.get("narrative_function") != "":
        return scene.get("narrative_function")
    
    # Infer from scene content
    scene_type = scene.get("scene_type", "")
    dialogue = scene.get("dialogue_text", [])
    arousal = scene.get("emotion_arousal_score", 0)
    
    if scene.get("climax_point_flag", False):
        return "escalate_conflict"
    
    if arousal >= 0.4:
        if len(dialogue) > 8:
            return "develop_relationship"
        return "escalate_conflict"
    
    if scene_type == "exposition":
        return "reveal_information"
    
    if len(dialogue) < 2:
        return "provide_context"
    
    return "develop_relationship"


def _compute_story_progress(scene_index: int, total_scenes: int, scene: Dict) -> str:
    """Compute story progress tag."""
    if scene.get("story_progress_tag") and scene.get("story_progress_tag") != "":
        return scene.get("story_progress_tag")
    
    position = (scene_index + 1) / total_scenes
    
    if scene.get("climax_point_flag", False):
        return "climax"
    
    if position < 0.20:
        return "intro"
    elif position < 0.35:
        return "setup"
    elif position < 0.60:
        return "buildup"
    elif position < 0.75:
        return "conflict"
    elif position < 0.90:
        return "resolution"
    else:
        return "epilogue"


def _compute_scene_complexity(scene: Dict[str, Any]) -> float:
    """
    Calculate scene complexity (0.0 to 1.0).
    
    Factors:
    - Number of characters
    - Dialogue intensity
    - Motion intensity
    - Arousal level
    - Scene duration
    """
    char_count = len(scene.get("characters", []))
    dialogue_count = len(scene.get("dialogue_text", []))
    motion = scene.get("motion_intensity_score", 0) / 100.0
    arousal = min(scene.get("emotion_arousal_score", 0), 1.0)
    duration = min(scene.get("duration", 0) / 60.0, 1.0)  # Normalize to ~60s max
    
    # Weighted complexity score
    complexity = (
        (min(char_count / 5, 1.0) * 0.25) +      # More characters = more complex
        (min(dialogue_count / 20, 1.0) * 0.25) +  # More dialogue = more complex
        (motion * 0.15) +                          # Motion adds complexity
        (arousal * 0.20) +                         # Emotional intensity
        (duration * 0.15)                          # Longer scenes tend more complex
    )
    
    return round(min(complexity, 1.0), 3)


def enrich_json_file(json_path: str) -> None:
    """
    Load JSON, enrich all scenes with missing data, save back.
    """
    print(f"\n[ENRICHER] Loading: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    scenes = data.get("scenes", [])
    total = len(scenes)
    print(f"[ENRICHER] Processing {total} scenes...\n")
    
    # Track changes
    changes = {
        "characters_extracted": 0,
        "complexity_computed": 0,
        "fields_completed": 0
    }
    
    # Process each scene
    for idx, scene in enumerate(scenes):
        old_chars = len(scene.get("characters", []))
        
        # Enrich
        scene = enrich_scene_metadata(scene, idx, total)
        scenes[idx] = scene
        
        # Track changes
        new_chars = len(scene.get("characters", []))
        
        if old_chars == 0 and new_chars > 0:
            changes["characters_extracted"] += 1
        
        if "scene_complexity_score" in scene:
            changes["complexity_computed"] += 1
        
        # Print progress
        if (idx + 1) % 50 == 0:
            print(f"  [{idx+1}/{total}] Processed")
    
    # Save back
    print(f"\n[ENRICHER] Saving enriched data to {json_path}...")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Summary
    print(f"\n[SUMMARY] Enrichment Complete:")
    print(f"  characters extracted: {changes['characters_extracted']}/{total}")
    print(f"  complexity computed: {changes['complexity_computed']}/{total}")
    print(f"  Total fields enriched: {sum(changes.values())}")


def main():
    """Entry point for enrichment."""
    json_file = None
    
    # Prefer TARGET_MOVIE (set by run_pipeline.py) over sys.argv
    target_movie = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME") or MOVIE_NAME
    
    # Only use sys.argv if it's a file path (not a command-line flag)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        json_file = sys.argv[1]
    else:
        json_file = f"{OUTPUT_JSON_DIR}/{target_movie}_complete_schema.json"
    
    if not os.path.exists(json_file):
        print(f"[ERROR] File not found: {json_file}")
        return
    
    enrich_json_file(json_file)


if __name__ == "__main__":
    main()
