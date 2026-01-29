import json
from datetime import datetime


# --- Heuristic keyword sets ---
VIOLENT_OBJECTS = {"knife", "gun", "blood", "weapon", "sword"}
DRUG_OBJECTS = {"syringe", "pill", "drug"}
ADULT_OBJECTS = {"nudity", "bed"}

_AGE_LEVELS = {
    "U": 0,
    "13+": 1,
    "16+": 2,
    "18+": 3,
}


def _level_to_age(level: int) -> str:
    # inverse lookup for levels used in output
    for k, v in _AGE_LEVELS.items():
        if v == level:
            return k
    return "U"


def assess_scene(scene):
    objects = set(o.lower() for o in scene.get("objects", []))
    profanity = scene.get("profanity_present")
    motion = scene.get("motion_intensity_score") or 0

    violence_level = "none"
    sensitive_types = []
    age_rating = "U"
    age_level = _AGE_LEVELS[age_rating]

    # 🔪 Violence detection
    if objects & VIOLENT_OBJECTS:
        violence_level = "moderate"
        age_level = max(age_level, _AGE_LEVELS["13+"])
        sensitive_types.append("violence")

        if motion > 35:
            violence_level = "high"
            age_level = max(age_level, _AGE_LEVELS["16+"])

    # 💊 Drug detection
    if objects & DRUG_OBJECTS:
        sensitive_types.append("drug_use")
        age_level = max(age_level, _AGE_LEVELS["16+"])

    # 🔞 Adult content (visual heuristic only)
    if objects & ADULT_OBJECTS:
        sensitive_types.append("adult")
        age_level = max(age_level, _AGE_LEVELS["18+"])

    # 🗯️ Profanity escalation
    if profanity is True:
        # escalate when profanity detected
        age_level = max(age_level, _AGE_LEVELS["16+"])

    # 📛 Brand safety
    brand_clearance = True if violence_level in {"high", "moderate"} else False

    age_rating = _level_to_age(age_level)

    return {
        "violence_level": violence_level,
        "scene_rating_flags": {
            "violence": "violence" in sensitive_types,
            "drug_use": "drug_use" in sensitive_types,
            "nudity": "adult" in sensitive_types,
            "strong_language": profanity,
        },
        "age_rating_suggestion": age_rating,
        "sensitive_content_type": sensitive_types,
        "brand_clearance_required": brand_clearance,
    }


def main():
    import sys
    from src.movie_utils import resolve_movie
    import os

    movie = resolve_movie(sys.modules[__name__])

    # prefer emotion-augmented finals, but accept several variants
    candidates = [
        f"outputs/scene_index/{movie}_FINAL_WITH_EMOTION.json",
        f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_EMOTION.json",
        f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_PROFANITY.json",
        f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE.json",
        f"outputs/scene_index/{movie}_FINAL.json",
    ]

    input_json = None
    for p in candidates:
        if os.path.exists(p):
            input_json = p
            break

    if not input_json:
        raise FileNotFoundError(f"No suitable final JSON found for movie '{movie}'; checked: {candidates}")
    output_json = f"outputs/scene_index/{movie}_FINAL_WITH_SAFETY.json"

    with open(input_json, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    for scene in scenes:
        # validate scene shape before assessing (non-blocking)
        try:
            from scene_schema import validate_scene
            valid, msgs = validate_scene(scene)
            import os
            strict = os.getenv("SCHEMA_STRICT", "0").lower() in ("1", "true", "yes")
            if not valid:
                if strict:
                    raise RuntimeError(f"Scene validation failed for {scene.get('scene_id')}: {msgs}")
                print(f"[WARN] Scene {scene.get('scene_id')} failed validation: {msgs}")
        except Exception:
            # don't break the pipeline for validator errors
            pass

        safety_data = assess_scene(scene)
        scene.update(safety_data)
        scene["metadata_generated_at"] = datetime.utcnow().isoformat()

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)

    print(f"[OK] Content safety analysis complete → {output_json}")


if __name__ == "__main__":
    main()
