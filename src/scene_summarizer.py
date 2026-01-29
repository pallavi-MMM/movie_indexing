"""
Scene summarizer: Generate narrative scene summaries analyzing dialogue content and context.

Analyzes:
  - Actual dialogue text content (keywords, emotions, topics)
  - Character interactions and relationships
  - Scene context (location, time, lighting, mood)
  - Emotional intensity and tension
  - Actions and activities occurring

Generates narrative summaries that capture the essence of each scene.
  
Usage (standalone):
  python src/scene_summarizer.py <path_to_complete_schema.json>

Usage (pipeline):
  - Automatically runs as final step in run_pipeline.py
"""

import json
import sys
import os
import re


# Global movie name (set by pipeline if running as module)
MOVIE_NAME = "Alanati ramachandrudu - trailer"
OUTPUT_JSON_DIR = "output_json"


# Dialogue keywords for context extraction
EMOTIONAL_KEYWORDS = {
    "love": "love/romance",
    "miss": "longing",
    "die": "death/mortality",
    "kill": "violence",
    "help": "seeking aid",
    "sorry": "regret/apology",
    "pray": "spirituality/faith",
    "god": "spiritual reference",
    "fear": "fear/anxiety",
    "danger": "danger/threat",
    "hurt": "pain/injury",
    "sick": "illness",
    "hospital": "medical situation",
    "baby": "infant/family",
    "child": "child/family",
    "mother": "motherhood",
    "father": "fatherhood",
    "family": "family relationships",
    "friend": "friendship",
    "money": "financial concerns",
    "job": "work/employment",
    "school": "education",
    "happy": "joy/happiness",
    "cry": "emotional breakdown",
    "laugh": "humor/laughter",
    "angry": "anger",
    "fight": "conflict/confrontation",
    "escape": "fleeing/running away",
    "secret": "hidden truth",
    "truth": "truth/revelation",
    "lie": "deception",
    "confession": "confession/admission",
}

ACTION_VERBS = {
    "running": "chase/running",
    "fight": "physical conflict",
    "embrace": "physical affection",
    "kiss": "romantic contact",
    "argue": "verbal conflict",
    "yell": "shouting",
    "whisper": "secret conversation",
    "phone": "phone conversation",
    "drive": "traveling",
    "walk": "walking",
    "sit": "seated conversation",
    "stand": "standing discussion",
    "cry": "emotional distress",
    "laugh": "laughter/humor",
    "think": "contemplation",
    "sleep": "resting",
    "eat": "dining",
    "drink": "drinking",
}


def extract_dialogue_content(dialogue):
    """
    Analyze dialogue text to extract key content, emotions, and topics.
    
    Args:
        dialogue: List of dialogue entries with 'line' field
    
    Returns:
        Dict with extracted content, emotions, keywords, speakers
    """
    if not dialogue:
        return {"content": "", "keywords": [], "speakers": set(), "emotions": []}
    
    full_text = " ".join(d.get("line", "").lower() for d in dialogue)
    speakers = set(d.get("speaker", "unknown") for d in dialogue if d.get("speaker"))
    
    # Extract keywords
    keywords = []
    emotions = []
    for keyword, label in EMOTIONAL_KEYWORDS.items():
        if keyword in full_text:
            keywords.append(label)
            emotions.append(label)
    
    # Check for question density
    question_count = full_text.count("?")
    exclamation_count = full_text.count("!")
    
    return {
        "content": full_text,
        "keywords": list(set(keywords)),
        "speakers": speakers,
        "emotions": list(set(emotions)),
        "question_density": question_count / max(len(dialogue), 1),
        "exclamation_density": exclamation_count / max(len(dialogue), 1)
    }


def analyze_scene_context(scene):
    """
    Analyze multiple contextual factors of a scene.
    
    Returns:
        Dict with scene context analysis
    """
    location = scene.get("location", "")
    time_of_day = scene.get("time_of_day", "")
    lighting = scene.get("lighting_style", "")
    color_tone = scene.get("color_tone", "")
    motion = scene.get("motion_intensity_score", 0)
    camera = scene.get("camera_movement", "")
    dialogue_speed = scene.get("dialogue_speed_wpm", 0)
    background_music = scene.get("background_music_mood", "")
    viewer_emotion = scene.get("viewer_emotion_prediction", "")
    
    return {
        "location": location,
        "time_of_day": time_of_day,
        "lighting": lighting,
        "color_tone": color_tone,
        "motion_intensity": motion,
        "camera_movement": camera,
        "dialogue_speed": dialogue_speed,
        "background_music": background_music,
        "viewer_emotion": viewer_emotion
    }


def build_narrative_summary(scene):
    """
    Build a detailed narrative summary by analyzing dialogue, context, and emotions.
    
    Args:
        scene: Complete scene dict
    
    Returns:
        str: Narrative scene summary (40-80 words)
    """
    # Extract components
    dialogue = scene.get("dialogue_text", [])
    characters = scene.get("characters", [])
    actions = scene.get("actions", [])
    background_activity = scene.get("background_activity", [])
    
    dialogue_analysis = extract_dialogue_content(dialogue)
    context = analyze_scene_context(scene)
    
    # Determine narrative arc
    arousal = scene.get("emotion_arousal_score", 0)
    dialogue_intensity = len(dialogue)
    motion_intensity = context["motion_intensity"]
    
    # Build summary components
    parts = []
    
    # === SETTING & ATMOSPHERE ===
    setting = f"{context['time_of_day'].title()} {context['location']}"
    if context["lighting"] and context["lighting"] != "unknown":
        setting += f" ({context['lighting']} lighting)"
    parts.append(setting)
    
    # === CHARACTER INVOLVEMENT ===
    char_description = ""
    if len(characters) >= 3:
        char_description = f"Multiple characters converge"
    elif len(characters) == 2:
        char_description = f"Two characters interact"
    elif len(characters) == 1:
        char_description = f"A solitary character"
    else:
        char_description = f"Characters are present"
    
    # === DIALOGUE/INTERACTION ===
    interaction = ""
    if dialogue_intensity == 0:
        interaction = "in quiet contemplation"
    elif dialogue_intensity < 3:
        interaction = "exchange brief words"
    elif dialogue_intensity < 6:
        interaction = "engage in conversation"
    elif dialogue_intensity < 10:
        interaction = "engage in active discussion"
    else:
        interaction = "engage in intense dialogue"
    
    # Add dialogue content if rich with emotion
    if dialogue_analysis["keywords"]:
        top_emotions = dialogue_analysis["keywords"][:2]
        interaction += f" about {', '.join(top_emotions)}"
    
    # === MOOD & TENSION ===
    mood = ""
    if arousal >= 0.5:
        mood = "high tension and conflict"
    elif arousal >= 0.3:
        mood = "emotional intensity"
    elif arousal >= 0.15:
        mood = "gentle unease"
    else:
        mood = "calm atmosphere"
    
    # === VISUAL DYNAMICS ===
    dynamics = ""
    if motion_intensity > 50:
        dynamics = "with rapid movement"
    elif motion_intensity > 20:
        dynamics = "with moderate activity"
    
    # === COMBINE INTO NARRATIVE ===
    if context["camera_movement"] and context["camera_movement"] != "static":
        dynamics += f" and {context['camera_movement']} camera work"
    
    # Build final summary
    summary = f"{char_description} {interaction} in {setting.lower()}, creating {mood}"
    
    if dynamics:
        summary += f" {dynamics}"
    
    if context["background_music"] and context["background_music"] != "unknown":
        summary += f". Background score: {context['background_music']}."
    else:
        summary += "."
    
    return summary.strip()


def build_scene_summary(scene):
    """Main entry point for summary generation."""
    return build_narrative_summary(scene)


def regenerate_summaries(json_file_path):
    """
    Load complete schema JSON, regenerate all scene_summary fields, save back.
    
    Args:
        json_file_path: Path to complete_schema.json
    """
    print(f"[SUMMARIZER] Loading: {json_file_path}")
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    scenes = schema.get("scenes", [])
    print(f"[SUMMARIZER] Processing {len(scenes)} scenes...")
    
    updated_count = 0
    for scene in scenes:
        old_summary = scene.get("scene_summary", "")
        new_summary = build_scene_summary(scene)
        
        scene["scene_summary"] = new_summary
        updated_count += 1
        
        scene_id = scene.get("scene_id", "unknown")
        print(f"  [{scene_id}] {new_summary}")
    
    # Save back
    print(f"[SUMMARIZER] Saving {updated_count} summaries to {json_file_path}...")
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Scene summaries regenerated -> {json_file_path}")


def main():
    """
    Pipeline entry point.
    When called by the pipeline, regenerates summaries on the final complete schema.
    Supports both pipeline execution (via MOVIE_NAME) and CLI execution (via sys.argv).
    """
    # Determine the JSON file to process
    json_file = None
    
    # Prefer TARGET_MOVIE (set by run_pipeline.py) over sys.argv
    target_movie = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME") or MOVIE_NAME
    
    # Only use sys.argv if it's a file path (not a command-line flag)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        json_file = sys.argv[1]
    else:
        os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)
        json_file = f"{OUTPUT_JSON_DIR}/{target_movie}_complete_schema.json"
    
    if not os.path.exists(json_file):
        print(f"[WARN] Scene summary file not found: {json_file}")
        return
    
    regenerate_summaries(json_file)


if __name__ == "__main__":
    main()
