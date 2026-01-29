import os
import json
import cv2
import numpy as np
from collections import Counter
from tqdm import tqdm
import torch

# Use GPU when available (falls back to CPU)
from src.device import DEVICE as DEVICE

SCENE_ASSETS_DIR = "outputs/scene_assets"
OUTPUT_DIR = "outputs/scene_object_index"
MAX_FRAMES = 12
CONF_THRESHOLD = 0.4

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lazy model holder to avoid heavy imports at module import-time
model = None
_model_loaded = False

def get_model():
    global model, _model_loaded
    if _model_loaded:
        return model
    _model_loaded = True
    try:
        from ultralytics import YOLO
        m = YOLO("yolov8m.pt")
        try:
            if DEVICE == "cuda":
                m = m.to(DEVICE)
        except Exception:
            pass
        model = m
    except Exception as e:
        print(f"[WARN] Could not load object detection model: {e}")
        model = None
    return model


def sample_frames(frames, max_frames=MAX_FRAMES):
    if len(frames) <= max_frames:
        return frames
    idxs = np.linspace(0, len(frames) - 1, max_frames).astype(int)
    return [frames[i] for i in idxs]


def analyze_scene_objects(frames_dir):
    frames = sorted(
        [os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(".jpg")]
    )

    if not frames:
        return None

    frames = sample_frames(frames)

    object_counter = Counter()
    person_count = 0

    for f in frames:
        img = cv2.imread(f)
        m = get_model()
        if m is None:
            # Model unavailable — skip detections
            continue
        results = m(img, conf=CONF_THRESHOLD, verbose=False)

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls]
                object_counter[label] += 1
                if label == "person":
                    person_count += 1

    if not object_counter:
        return None

    objects = [obj for obj, cnt in object_counter.items() if cnt >= 2]

    # convert simple object labels -> canonical object dicts
    canonical_objects = []
    for obj_label in objects:
        canonical_objects.append({
            "type": obj_label,
            "model": None,
            "year": None,
            "color": None,
            "details": json.dumps({"count": int(object_counter.get(obj_label, 0))})
        })

    actions = []
    if any(o["type"] == "person" for o in canonical_objects):
        actions.append("human_activity")
    if any(o["type"] == "car" for o in canonical_objects):
        actions.append("driving")

    background_activity = []
    if person_count > len(frames) * 2:
        background_activity.append("crowd_movement")

    return {
        "objects": canonical_objects,
        "actions": actions,
        "background_activity": background_activity,
        "vfx_presence": False,
        "cg_characters_present": False
    }


def main():
    target = globals().get("TARGET_MOVIE")
    for movie in os.listdir(SCENE_ASSETS_DIR):
        movie_path = os.path.join(SCENE_ASSETS_DIR, movie)
        if not os.path.isdir(movie_path):
            continue
        if target and movie != target:
            continue

        results = []

        for scene in sorted(os.listdir(movie_path)):
            if not scene.endswith("_frames"):
                continue

            frames_dir = os.path.join(movie_path, scene)
            data = analyze_scene_objects(frames_dir)

            if data:
                scene_id = f"{movie}_{scene.replace('_frames','')}"
                results.append({
                    "scene_id": scene_id,
                    **data
                })

        out_path = f"{OUTPUT_DIR}/{movie}_scene_objects.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"[OK] Object data written: {out_path}")


if __name__ == "__main__":
    main()
