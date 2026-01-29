import os
import json
import librosa
import numpy as np

OUT_DIR = "outputs/scene_emotion"
os.makedirs(OUT_DIR, exist_ok=True)


def analyze_audio(audio_path):
    y, sr = librosa.load(audio_path, sr=None)

    rms = np.mean(librosa.feature.rms(y=y))
    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    return {
        "emotion_arousal_score": round(float(rms), 4),
        "emotion_scene_variation_score": round(float(zcr), 4),
        "audio_activity_score": round(float(tempo), 2)
    }


def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    audio_dir = f"outputs/scene_assets/{movie}"

    for scene in sorted(os.listdir(audio_dir)):
        if not scene.endswith("_audio.wav"):
            continue

        scene_id = scene.replace("_audio.wav", "")
        scene_path = os.path.join(audio_dir, scene)

        scores = analyze_audio(scene_path)

        out = {
            "scene_id": scene_id,
            **scores
        }

        # write into per-movie folder to avoid name collisions across movies
        movie_out_dir = os.path.join(OUT_DIR, movie)
        os.makedirs(movie_out_dir, exist_ok=True)
        with open(os.path.join(movie_out_dir, f"{scene_id}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)

        print(f"[EMOTION] {scene_id} done")

    print("[OK] Emotion analysis complete")


if __name__ == "__main__":
    main()
