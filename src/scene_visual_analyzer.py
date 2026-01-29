import os
import cv2
import json
import numpy as np
from tqdm import tqdm

SCENE_ASSETS_DIR = "outputs/scene_assets"
OUTPUT_DIR = "outputs/scene_visual_index"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def analyze_scene_frames(frames_dir):
    frames = sorted(
        [
            os.path.join(frames_dir, f)
            for f in os.listdir(frames_dir)
            if f.endswith(".jpg")
        ]
    )

    if len(frames) < 2:
        return None

    # Read first frame
    prev = cv2.imread(frames[0])
    h, w, _ = prev.shape
    gray_prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)

    motion_scores = []
    brightness = []
    saturation = []

    for f in frames[1:]:
        img = cv2.imread(f)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray, gray_prev)
        motion_scores.append(np.mean(diff))

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        brightness.append(np.mean(hsv[:, :, 2]))
        saturation.append(np.mean(hsv[:, :, 1]))

        gray_prev = gray

    motion_intensity = float(np.mean(motion_scores))
    avg_brightness = np.mean(brightness)
    avg_saturation = np.mean(saturation)

    lighting = (
        "dark"
        if avg_brightness < 80
        else "normal" if avg_brightness < 160 else "bright"
    )
    color_tone = "muted" if avg_saturation < 60 else "vibrant"

    camera_movement = (
        "static"
        if motion_intensity < 5
        else "slow" if motion_intensity < 20 else "fast"
    )

    shot_type = "wide"
    face_ratio = 0.0  # placeholder (will refine later)
    if face_ratio > 0.3:
        shot_type = "close-up"
    elif face_ratio > 0.1:
        shot_type = "medium"

    return {
        "resolution": f"{w}x{h}",
        "aspect_ratio": round(w / h, 2),
        "motion_intensity_score": round(motion_intensity, 2),
        "camera_movement": camera_movement,
        "lighting_style": lighting,
        "color_tone": color_tone,
        "shot_type": shot_type,
    }


def main():
    target = globals().get("TARGET_MOVIE")
    for movie in os.listdir(SCENE_ASSETS_DIR):
        movie_path = os.path.join(SCENE_ASSETS_DIR, movie)
        if not os.path.isdir(movie_path):
            continue
        if target and movie != target:
            # skip movies not requested for this run
            continue

        results = []

        for scene in sorted(os.listdir(movie_path)):
            if not scene.endswith("_frames"):
                continue

            frames_dir = os.path.join(movie_path, scene)
            data = analyze_scene_frames(frames_dir)

            if data:
                scene_id = f"{movie}_{scene.replace('_frames','')}"
                results.append({"scene_id": scene_id, **data})

        out_path = f"{OUTPUT_DIR}/{movie}_scene_visuals.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"[OK] Visual metadata written: {out_path}")


if __name__ == "__main__":
    main()
