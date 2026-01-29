"""
Narrative Structure Analyzer: Add story-aware fields to scenes.

Implements deterministic narrative classification:
  - story_progress_tag: Where in story timeline (intro, setup, buildup, conflict, climax, resolution, epilogue)
  - scene_category_secondary: Narrative flavor (romance, suspense, emotional_conflict, etc.)
  - narrative_function: What the scene does (introduce_character, develop_relationship, escalate_conflict, etc.)
  - scene_priority_formal: Explainable formula-based priority scoring

All rule-based, no ML models needed.
"""

import os
import json
import sys

MOVIE_NAME = "Alanati ramachandrudu - trailer"
OUTPUT_JSON_DIR = "output_json"


# ============================================================================
# NARRATIVE STRUCTURE RULES
# ============================================================================

def compute_story_progress_tag(scene_index, total_scenes, climax_flag):
    """
    Determine story position tag based on scene index and story markers.
    
    Args:
        scene_index: 0-based index of scene
        total_scenes: Total number of scenes in movie
        climax_flag: Boolean from climax_point_flag
    
    Returns:
        str: One of [intro, setup, buildup, conflict, revelation, climax, resolution, epilogue]
    """
    position = (scene_index + 1) / total_scenes  # 1-based normalized position
    
    # If explicitly marked as climax, honor that
    if climax_flag:
        return "climax"
    
    # Otherwise, use position-based heuristic
    if position < 0.15:
        return "intro"
    elif position < 0.30:
        return "setup"
    elif position < 0.55:
        return "buildup"
    elif position < 0.70:
        return "conflict"
    elif position < 0.90:
        return "resolution"
    else:
        return "epilogue"


def classify_scene_category_secondary(scene):
    """
    Classify narrative flavor based on dialogue, emotion, style, location, time.
    
    Examples:
      - emotional dialogue + high arousal + night → emotional_conflict
      - questions/confrontations → suspense
      - single speaker + emotional → character_introspection
      - crowd activity + interaction → social_commentary
    
    Returns:
        str: Category (or "neutral" if no strong signal)
    """
    dialogue = scene.get("dialogue_text", [])
    emotions = scene.get("emotions", [])
    arousal = scene.get("emotion_arousal_score", 0)
    cinematic_style = scene.get("cinematic_style", "")
    location = scene.get("location", "")
    time_of_day = scene.get("time_of_day", "")
    objects = scene.get("objects", [])
    background_activity = scene.get("background_activity", [])
    
    # Extract signals
    dialogue_text = " ".join([d.get("line", "").lower() for d in dialogue])
    has_questions = "?" in dialogue_text
    has_emotional_words = any(w in dialogue_text for w in ["love", "miss", "heart", "feel", "emotions", "care"])
    is_single_speaker = len(dialogue) <= 2
    has_high_arousal = arousal >= 0.22
    has_crowd_activity = "crowd" in background_activity
    
    # === CLASSIFICATION LOGIC ===
    
    # Emotional conflict: emotional dialogue + high arousal + night or dark
    if has_emotional_words and has_high_arousal and (time_of_day == "night" or cinematic_style == "contemplative"):
        return "emotional_conflict"
    
    # Character introspection: single speaker + emotional words
    if is_single_speaker and has_emotional_words and len(dialogue) > 0:
        return "character_introspection"
    
    # Suspense: many questions or confrontational tone
    if has_questions and (has_high_arousal or "conflict" in dialogue_text or "why" in dialogue_text):
        return "suspense"
    
    # Revelation: dialogue reveals new information (many keywords)
    keywords = scene.get("keywords_auto_generated", [])
    if len(dialogue) > 3 and len(keywords) >= 3:
        return "revelation"
    
    # Social commentary: crowd activity + multiple objects + diverse activity
    if has_crowd_activity and len(objects) > 3:
        return "social_commentary"
    
    # Romance: emotional words + positive tone
    if has_emotional_words and arousal < 0.20:  # calm emotion = romantic
        return "romance"
    
    # Default
    return "neutral"


def infer_narrative_function(scene, scene_index, all_scenes):
    """
    Determine what narrative role this scene plays.
    
    Values:
      - introduce_character: New character appears
      - develop_relationship: Character interaction
      - escalate_conflict: Tension increases
      - reveal_information: New plot information
      - emotional_turn: Emotional state change
      - setup_future_event: Sets up later action
    
    Args:
        scene: Current scene dict
        scene_index: Index in scene list
        all_scenes: All scenes for context
    
    Returns:
        str: Narrative function
    """
    characters = scene.get("characters", [])
    dialogue = scene.get("dialogue_text", [])
    priority = scene.get("scene_priority", 0)
    arousal = scene.get("emotion_arousal_score", 0)
    keywords = scene.get("keywords_auto_generated", [])
    
    # Get previous scene for comparison
    prev_scene = all_scenes[scene_index - 1] if scene_index > 0 else None
    prev_characters = set(prev_scene.get("characters", [])) if prev_scene else set()
    
    # === LOGIC ===
    
    # New character introduction
    new_characters = set(characters) - prev_characters
    if new_characters:
        return "introduce_character"
    
    # High priority + new keywords = revelation
    if priority > 0.55 and len(keywords) >= 4:
        return "reveal_information"
    
    # Emotional dialogue + single speaker = emotional turn
    emotional_words = ["love", "miss", "heart", "feel", "care", "emotion"]
    dialogue_text = " ".join([d.get("line", "").lower() for d in dialogue])
    if any(w in dialogue_text for w in emotional_words) and len(characters) <= 1:
        return "emotional_turn"
    
    # Multiple characters + dialogue = relationship development
    if len(characters) > 1 and len(dialogue) > 2:
        return "develop_relationship"
    
    # High arousal + high priority = escalate conflict
    if arousal > 0.20 and priority > 0.50:
        return "escalate_conflict"
    
    # Short scene + low dialogue = setup for next
    if len(dialogue) <= 2 and scene.get("duration", 0) < 20:
        return "setup_future_event"
    
    # Default
    return "develop_relationship"


def compute_scene_priority_formal(scene):
    """
    Compute scene priority using explicit formula for reproducibility.
    
    Formula:
    scene_priority = 0.4 * norm(dialogue_speed) + 0.3 * norm(motion) + 0.3 * norm(arousal)
    
    Normalization: min-max scaling to [0, 1] range
    
    Args:
        scene: Scene dict
    
    Returns:
        float: Priority score 0.0-1.0
    """
    # Get raw values
    dialogue_wpm = scene.get("dialogue_speed_wpm", 0)
    motion = scene.get("motion_intensity_score", 0)
    arousal = scene.get("emotion_arousal_score", 0)
    
    # Define normalization ranges (empirical from data)
    # Dialogue: 0-200 WPM
    norm_dialogue = min(dialogue_wpm / 200.0, 1.0)
    
    # Motion: 0-50 intensity
    norm_motion = min(motion / 50.0, 1.0)
    
    # Arousal: 0-1 scale (already normalized)
    norm_arousal = min(arousal, 1.0)
    
    # Weighted sum
    priority = (0.4 * norm_dialogue) + (0.3 * norm_motion) + (0.3 * norm_arousal)
    
    # Clamp to [0, 1]
    priority = min(max(priority, 0.0), 1.0)
    
    return round(priority, 3)


def add_narrative_structure(complete_schema_file):
    """
    Load complete schema and add all narrative structure fields.
    
    Adds:
      - story_progress_tag
      - scene_category_secondary
      - narrative_function
      - Updates scene_priority with formal calculation
    """
    if not os.path.exists(complete_schema_file):
        print(f"[WARN] File not found: {complete_schema_file}")
        return
    
    with open(complete_schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    scenes = schema.get("scenes", [])
    total_scenes = len(scenes)
    
    print(f"[NARRATIVE STRUCTURE] Processing {total_scenes} scenes")
    
    # === FIRST PASS: Compute all narrative fields ===
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", "")
        climax_flag = scene.get("climax_point_flag", False)
        
        # 1. Story progress tag
        story_tag = compute_story_progress_tag(idx, total_scenes, climax_flag)
        scene["story_progress_tag"] = story_tag
        
        # 2. Scene category secondary
        category = classify_scene_category_secondary(scene)
        scene["scene_category_secondary"] = category
        
        # 3. Narrative function (needs context)
        # Will compute in second pass
        scene["_narrative_function_pending"] = True
        
        # 4. Update scene priority with formal calculation
        formal_priority = compute_scene_priority_formal(scene)
        scene["scene_priority"] = formal_priority
    
    # === SECOND PASS: Compute narrative function (needs all scenes) ===
    for idx, scene in enumerate(scenes):
        if scene.get("_narrative_function_pending"):
            func = infer_narrative_function(scene, idx, scenes)
            scene["narrative_function"] = func
            del scene["_narrative_function_pending"]
    
    # === OUTPUT ===
    merged_count = 0
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        story_tag = scene.get("story_progress_tag", "unknown")
        category = scene.get("scene_category_secondary", "neutral")
        func = scene.get("narrative_function", "develop_relationship")
        priority = scene.get("scene_priority", 0)
        
        print(f"  [{scene_id}] {story_tag:12} | {category:20} | {func:20} | priority={priority:.3f}")
        merged_count += 1
    
    # Save updated schema
    with open(complete_schema_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Narrative structure fields added → {complete_schema_file}")


def main():
    """Pipeline entry point."""
    target_movie = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME") or MOVIE_NAME
    complete_schema_file = f"{OUTPUT_JSON_DIR}/{target_movie}_complete_schema.json"
    add_narrative_structure(complete_schema_file)


if __name__ == "__main__":
    main()
