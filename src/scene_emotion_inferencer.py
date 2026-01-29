import json
from datetime import datetime


def infer_emotion(scene):
    emotions = set()
    viewer_emotion = "neutral"

    motion = scene.get("motion_intensity_score") or 0
    wpm = scene.get("dialogue_speed_wpm") or 0
    lighting = scene.get("lighting_style", "")
    audio_activity = scene.get("audio_activity_score") or 0
    profanity = scene.get("profanity_present")

    # 🔊 High motion + fast dialogue → tension
    if motion > 30 and wpm > 140:
        emotions.add("tense")
        viewer_emotion = "anxiety"

    # ⚠️ Dark + sudden motion → shock
    if lighting == "dark" and motion > 35:
        emotions.add("shock")
        viewer_emotion = "fear"

    # 🔥 Aggression signal
    if profanity is True or wpm > 170:
        emotions.add("aggressive")
        viewer_emotion = "anger"

    # 😄 Laughter heuristic (light motion + fast speech)
    if motion < 10 and 120 < wpm < 150:
        emotions.add("humor")
        viewer_emotion = "amusement"

    if not emotions:
        emotions.add("neutral")

    return {
        "emotions": sorted(list(emotions)),
        "viewer_emotion_prediction": viewer_emotion,
        "laugh_moment_flag": "humor" in emotions,
        "shock_moment_flag": "shock" in emotions,
        "climax_point_flag": False,  # filled later globally
    }


def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    input_json = f"outputs/scene_index/{movie}_FINAL.json"
    output_json = f"outputs/scene_index/{movie}_FINAL_WITH_EMOTION.json"

    with open(input_json, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    for scene in scenes:
        emotion_data = infer_emotion(scene)
        scene.update(emotion_data)
        scene["metadata_generated_at"] = datetime.utcnow().isoformat()

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)

    print(f"[OK] Emotion inference complete → {output_json}")


if __name__ == "__main__":
    main()
