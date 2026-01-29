"""
Meta Intelligence Analyzer (Phase VI): Final enrichment layer
Computes scene priority, viewer attention, keywords, and cinematic style.

This runs LAST because it needs all scenes to compute relative priorities.
"""

import os
import json
import re
from collections import Counter

SCENE_INDEX_DIR = "outputs/scene_index"
OUTPUT_JSON_DIR = "output_json"

os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)

# ============================================================================
# Keyword Extraction
# ============================================================================

# Common stopwords to filter out
STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "am",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    "that",
    "this",
    "these",
    "those",
    "as",
    "if",
    "not",
    "no",
    "yes",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    "about",
    "up",
    "down",
    "out",
    "so",
    "than",
    "then",
    "there",
    "here",
    "now",
    "just",
    "only",
    "over",
    "under",
    "me",
    "him",
    "them",
    "us",
    "tell",
    "said",
    "say",
    "think",
    "know",
    "want",
    "go",
    "come",
    "see",
    "look",
    "like",
    "love",
    "day",
    "time",
    "way",
    "thing",
    "one",
    "two",
    "three",
    "cause",
    "reason",
    "ok",
    "yeah",
    "oh",
    "ah",
    "well",
    "dont",
    "didnt",
    "wont",
    "cant",
    "couldnt",
    "shouldnt",
    "wouldnt",
    "isnt",
    "arent",
    "wasnt",
    "werent",
    "havent",
    "hasnt",
    "hadnt",
    "doesnt",
    "dont",
}


def extract_keywords(dialogue_lines, objects, location):
    """
    Extract meaningful keywords from dialogue, objects, and location.
    Returns list of top keywords.
    """
    keywords = []

    # Extract from dialogue - split into words and filter
    if dialogue_lines:
        for line in dialogue_lines:
            if isinstance(line, dict):
                text = line.get("line", "")
            else:
                text = str(line)

            # Simple word extraction: lowercase, remove punctuation, split
            words = re.findall(r"\b[a-z]+\b", text.lower())
            keywords.extend([w for w in words if w not in STOPWORDS and len(w) > 2])

    # Extract from objects
    if objects:
        if isinstance(objects, list):
            for obj in objects:
                if isinstance(obj, dict):
                    obj_type = obj.get("type", "")
                    if obj_type:
                        keywords.append(obj_type.lower())
                elif isinstance(obj, str):
                    keywords.append(obj.lower())

    # Add location
    if location and isinstance(location, str):
        loc_words = re.findall(r"\b[a-z]+\b", location.lower())
        keywords.extend([w for w in loc_words if w not in STOPWORDS])

    # Get top 5 keywords by frequency
    if keywords:
        counter = Counter(keywords)
        top_keywords = [word for word, count in counter.most_common(5)]
        return top_keywords

    return []


# ============================================================================
# Cinematic Style Classification
# ============================================================================


def classify_cinematic_style(
    lighting, camera_movement, motion, arousal, emotion_labels
):
    """
    Classify cinematic style based on visual and emotional characteristics.

    lighting: "dark", "normal", "bright"
    camera_movement: "static", "slow", "moderate", "fast"
    motion: 0-100 (motion_intensity_score)
    arousal: 0-1 (emotion_arousal_score)
    emotion_labels: ["tense", "calm", etc.]
    """

    # Normalize values
    motion_norm = motion / 100.0 if motion else 0

    styles = []

    # Dark + emotional + slow = Drama
    if lighting == "dark" and arousal > 0.3:
        if motion_norm < 0.4:
            styles.append("drama")

    # Fast + bright/vibrant + high motion = Action
    if motion_norm > 0.6:
        if camera_movement in ["fast", "moderate"]:
            styles.append("action")

    # Dark + fast + high motion = Thriller
    if lighting == "dark" and motion_norm > 0.6 and camera_movement == "fast":
        styles.append("thriller")

    # Low motion + low arousal = Calm/Slice-of-life
    if motion_norm < 0.3 and arousal < 0.3:
        styles.append("slice-of-life")

    # High arousal + emotional labels = Emotional Drama
    if arousal > 0.5 and any(
        label in ["sad", "angry", "tense"] for label in emotion_labels
    ):
        styles.append("emotional-drama")

    # Comedy indicators
    if any(label in emotion_labels for label in ["happy", "content"]):
        if motion_norm > 0.4:
            styles.append("comedy")

    # Default to most prominent characteristic
    if not styles:
        if motion_norm > 0.5:
            styles.append("dynamic")
        elif arousal > 0.5:
            styles.append("intense")
        else:
            styles.append("contemplative")

    return styles[0] if styles else "neutral"


# ============================================================================
# Scene Priority & Attention Scoring
# ============================================================================


def compute_scene_priority_and_attention(scenes):
    """
    Compute scene priority and viewer attention scores for all scenes.

    Returns:
    - priority_scores: {scene_id: score}
    - attention_scores: {scene_id: score}
    """

    priority_scores = {}
    attention_scores = {}

    # First pass: collect raw metrics
    metrics = {}

    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        if not scene_id:
            continue

        # Extract relevant metrics
        emotion_arousal = scene.get("emotion_arousal_score", 0)
        emotion_variation = scene.get("emotion_scene_variation_score", 0)
        motion_intensity = scene.get("motion_intensity_score", 0)
        dialogue_count = len(scene.get("dialogue_text", []))
        dialogue_speed = scene.get("dialogue_speed_wpm", 0)
        audio_activity = scene.get("audio_activity_score", 0)
        characters_count = len(scene.get("characters", []))
        objects_count = len(scene.get("objects", []))

        metrics[scene_id] = {
            "arousal": emotion_arousal,
            "variation": emotion_variation,
            "motion": motion_intensity,
            "dialogue_count": dialogue_count,
            "dialogue_speed": dialogue_speed,
            "audio_activity": audio_activity,
            "characters": characters_count,
            "objects": objects_count,
            "laugh": scene.get("laugh_moment_flag", False),
            "shock": scene.get("shock_moment_flag", False),
            "climax": scene.get("climax_point_flag", False),
        }

    if not metrics:
        return priority_scores, attention_scores

    # Normalize scores across all scenes
    max_arousal = max((m["arousal"] for m in metrics.values()), default=1)
    max_variation = max((m["variation"] for m in metrics.values()), default=1)
    max_motion = max((m["motion"] for m in metrics.values()), default=1)
    max_dialogue = max((m["dialogue_count"] for m in metrics.values()), default=1)
    max_dialogue_speed = max((m["dialogue_speed"] for m in metrics.values()), default=1)
    max_audio = max((m["audio_activity"] for m in metrics.values()), default=1)

    # Compute priority: emotion intensity + dialogue density + character presence
    for scene_id, metric in metrics.items():
        # Emotion intensity: arousal + variation
        emotion_score = (
            metric["arousal"] / max_arousal if max_arousal else 0
        ) * 0.4 + (metric["variation"] / max_variation if max_variation else 0) * 0.3

        # Dialogue density: count + speed
        dialogue_score = (
            metric["dialogue_count"] / max_dialogue if max_dialogue else 0
        ) * 0.4 + (
            metric["dialogue_speed"] / max_dialogue_speed if max_dialogue_speed else 0
        ) * 0.1

        # Character dominance
        character_score = metric["characters"] * 0.2

        # Special moments bonus
        special_bonus = 0
        if metric["shock"]:
            special_bonus += 0.3
        if metric["climax"]:
            special_bonus += 0.2
        if metric["laugh"]:
            special_bonus += 0.1

        priority = (
            emotion_score * 0.4
            + dialogue_score * 0.4
            + character_score * 0.2
            + special_bonus
        )
        priority_scores[scene_id] = round(priority, 3)

        # Compute attention score: motion + emotion + dialogue with different weights
        motion_score = (metric["motion"] / max_motion if max_motion else 0) * 0.3
        audio_score = (metric["audio_activity"] / max_audio if max_audio else 0) * 0.2

        attention = (
            motion_score  # Visual dynamics: 30%
            + emotion_score * 0.3  # Emotional engagement: 30%
            + (dialogue_score * 0.5) * 0.2  # Dialogue contribution: 20%
            + audio_score  # Audio intensity: 20%
        )
        attention_scores[scene_id] = round(min(1.0, attention), 3)  # Normalize to 0-1

    # Rank by priority to determine true priorities
    ranked = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)

    return priority_scores, attention_scores, ranked


# ============================================================================
# Key Plot Point Detection
# ============================================================================


def detect_key_plot_points(scenes, ranked_scenes):
    """
    Detect key plot points based on priority ranking and special flags.
    """
    plot_points = {}

    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        if not scene_id:
            continue

        is_key = False
        reasons = []

        # Top 3 priority scenes are key plot points
        if any(scene_id == s[0] for s in ranked_scenes[:3]):
            is_key = True
            reasons.append("high-priority")

        # Shock moments are plot points
        if scene.get("shock_moment_flag", False):
            is_key = True
            reasons.append("shock-moment")

        # Climax point is definitely a plot point
        if scene.get("climax_point_flag", False):
            is_key = True
            reasons.append("climax")

        # Character introduction (first appearance)
        if scene.get("characters", []):
            is_key = True
            reasons.append("character-focus")

        # High dialogue density with emotional content
        if (
            len(scene.get("dialogue_text", [])) > 5
            and scene.get("emotion_arousal_score", 0) > 0.5
        ):
            is_key = True
            reasons.append("emotional-dialogue")

        if is_key:
            plot_points[scene_id] = {"is_key": True, "reasons": reasons}
        else:
            plot_points[scene_id] = {"is_key": False, "reasons": []}

    return plot_points


# ============================================================================
# Main Processing
# ============================================================================


def load_final_complete_schema(movie_name):
    """Load the current complete schema"""
    schema_file = os.path.join(OUTPUT_JSON_DIR, f"{movie_name}_complete_schema.json")

    if not os.path.exists(schema_file):
        return None

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load complete schema: {e}")
        return None


def enrich_with_meta_intelligence(complete_schema):
    """Add meta intelligence fields to complete schema"""

    if not complete_schema or "scenes" not in complete_schema:
        return complete_schema

    scenes = complete_schema["scenes"]

    # Compute global metrics
    priority_scores, attention_scores, ranked_scenes = (
        compute_scene_priority_and_attention(scenes)
    )
    plot_points = detect_key_plot_points(scenes, ranked_scenes)

    # Enrich each scene
    for scene in scenes:
        scene_id = scene.get("scene_id", "")

        # 1. Scene Priority
        scene["scene_priority"] = priority_scores.get(scene_id, 0.0)

        # 2. Viewer Attention Score
        scene["viewer_attention_score"] = attention_scores.get(scene_id, 0.0)

        # 3. Key Plot Point
        plot_data = plot_points.get(scene_id, {})
        scene["key_plot_point"] = plot_data.get("is_key", False)

        # 4. Auto-generated Keywords
        keywords = extract_keywords(
            scene.get("dialogue_text", []),
            scene.get("objects", []),
            scene.get("location", ""),
        )
        scene["keywords_auto_generated"] = keywords

        # 5. Cinematic Style
        cinematic_style = classify_cinematic_style(
            scene.get("lighting_style", "normal"),
            scene.get("camera_movement", "moderate"),
            scene.get("motion_intensity_score", 0),
            scene.get("emotion_arousal_score", 0),
            scene.get("emotions", []),
        )
        scene["cinematic_style"] = cinematic_style

        # 6. Symbolism Elements (simple rule-based)
        symbolism = []
        if scene.get("characters", []):
            symbolism.append("character-driven")
        if scene.get("shock_moment_flag", False):
            symbolism.append("dramatic-tension")
        if scene.get("laugh_moment_flag", False):
            symbolism.append("comedic-relief")
        if scene.get("climax_point_flag", False):
            symbolism.append("narrative-peak")
        if "crowd" in str(scene.get("background_activity", [])).lower():
            symbolism.append("social-commentary")
        if scene.get("lighting_style") == "dark":
            symbolism.append("mystery-shadow")

        scene["symbolism_elements"] = symbolism

    # Update timestamp
    import datetime

    complete_schema["generated_at"] = datetime.datetime.now().isoformat()

    return complete_schema


def main():
    """Process meta intelligence for all movies or specific TARGET_MOVIE"""

    # Check if a specific movie is targeted from pipeline
    target_movie = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME")

    if not os.path.exists(OUTPUT_JSON_DIR):
        print("[INFO] No output_json directory found")
        return

    movies_found = set()
    for filename in os.listdir(OUTPUT_JSON_DIR):
        if "_complete_schema.json" in filename:
            movie_name = filename.replace("_complete_schema.json", "")
            movies_found.add(movie_name)

    # Filter to target movie if specified
    if target_movie:
        movies_found = {target_movie}

    if not movies_found:
        print("[INFO] No complete schema files found")
        return

    for movie_name in sorted(movies_found):
        print(f"\n[META INTELLIGENCE] Processing: {movie_name}")

        # Load complete schema
        complete_schema = load_final_complete_schema(movie_name)
        if not complete_schema:
            print(f"[WARN] Could not load complete schema for {movie_name}")
            continue

        # Enrich with meta intelligence
        enriched_schema = enrich_with_meta_intelligence(complete_schema)

        # Save
        output_file = os.path.join(
            OUTPUT_JSON_DIR, f"{movie_name}_complete_schema.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_schema, f, indent=2, ensure_ascii=False)

        # Print summary
        scenes = enriched_schema["scenes"]
        key_scenes = [s for s in scenes if s.get("key_plot_point", False)]
        avg_attention = (
            sum(s.get("viewer_attention_score", 0) for s in scenes) / len(scenes)
            if scenes
            else 0
        )

        print(f"  ✓ Scene priorities computed")
        print(f"  ✓ Viewer attention scores: avg {avg_attention:.3f}")
        print(f"  ✓ Key plot points identified: {len(key_scenes)}")
        print(f"  ✓ Keywords extracted for all scenes")
        print(f"  ✓ Cinematic styles classified")
        print(f"[OK] Meta intelligence enriched → {output_file}")


if __name__ == "__main__":
    main()
