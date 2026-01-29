import os
import json
import cv2
import numpy as np
import torch

# GPU optional - will use CPU if CUDA unavailable
HAS_FACE = True
try:
    import faiss
    from insightface.app import FaceAnalysis
except Exception as e:
    # environment might lack native libs (insightface / faiss). Provide a graceful
    # fallback so the pipeline can continue in environments without these deps.
    print(f"[WARN] Actor-linker imports failed, actor linking will be skipped: {e}")
    HAS_FACE = False
from collections import defaultdict

SCENE_ASSETS_DIR = "outputs/scene_assets"
OUTPUT_DIR = "outputs/scene_actor_index"
ACTOR_INDEX_PATH = r"E:\actor_data_set\index\actor_index.faiss"
ACTOR_LABELS_PATH = r"E:\actor_data_set\index\actor_labels.json"


SIM_THRESHOLD = float(os.getenv("ACTOR_SIM_THRESHOLD", 0.38))
TOP_K = int(os.getenv("ACTOR_TOP_K", 5))
MIN_FRAMES = int(os.getenv("ACTOR_MIN_FRAMES", 5))

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_faiss():
    if not os.path.exists(ACTOR_INDEX_PATH) or not os.path.exists(ACTOR_LABELS_PATH):
        raise FileNotFoundError(
            f"Actor index or labels not found at {ACTOR_INDEX_PATH} / {ACTOR_LABELS_PATH}"
        )
    index = faiss.read_index(ACTOR_INDEX_PATH)
    with open(ACTOR_LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
    return index, labels


def init_face_app():
    if not HAS_FACE:
        return None
    # Use available providers (CUDA if available, else CPU)
    try:
        import onnxruntime as rt

        providers = rt.get_available_providers()
        # Prefer TensorRT -> CUDA -> CPU
        if "TensorRTExecutionProvider" in providers:
            print("[GPU] Using TensorRT for face detection")
            app = FaceAnalysis(
                name="buffalo_l", providers=["TensorRTExecutionProvider"]
            )
            app.prepare(ctx_id=0, det_size=(640, 640))
        elif "CUDAExecutionProvider" in providers:
            print("[GPU] Using CUDA for face detection")
            app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
        else:
            print("[CPU] GPU providers unavailable, using CPU for face detection")
            app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=-1, det_size=(640, 640))
    except Exception as e:
        print(f"[WARN] Could not initialize face app: {e}")
        return None
    return app


def cosine_search(index, emb):
    if not HAS_FACE:
        return [], []
    emb = emb.astype("float32")
    faiss.normalize_L2(emb)
    D, I = index.search(emb, TOP_K)
    return D[0], I[0]


def process_scene(scene_frames_dir, face_app, index, labels):
    # when face libs unavailable, return empty list — this indicates no actor info
    if not HAS_FACE or face_app is None or index is None or labels is None:
        return []

    actor_stats = defaultdict(lambda: {"count": 0, "area_sum": 0.0})

    for img_name in os.listdir(scene_frames_dir):
        img_path = os.path.join(scene_frames_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue

        faces = face_app.get(img)
        for face in faces:
            emb = face.embedding.reshape(1, -1)
            scores, ids = cosine_search(index, emb)

            if len(scores) == 0:
                continue

            if scores[0] < SIM_THRESHOLD:
                continue

            actor = labels[ids[0]]
            area = (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1])

            actor_stats[actor]["count"] += 1
            actor_stats[actor]["area_sum"] += area

    results = []

    # 1️⃣ Collect raw dominance scores
    for actor, data in actor_stats.items():
        if data["count"] >= MIN_FRAMES:
            avg_area = data["area_sum"] / data["count"]
            score = data["count"] * avg_area
            results.append((actor, score))

    # 2️⃣ No valid actors
    if not results:
        return []

    # 3️⃣ Normalize to 0-1 scale & filter weak actors
    max_score = max(score for _, score in results)

    # Normalize scores to 0-1 range and filter weak actors (< 20% of max)
    filtered = []
    for actor, score in results:
        normalized_score = score / max_score  # Now in range [0, 1]
        if normalized_score >= 0.2:
            filtered.append((actor, normalized_score))

    # 4️⃣ Sort by dominance
    filtered.sort(key=lambda x: x[1], reverse=True)

    return filtered


def main():
    target = globals().get("TARGET_MOVIE")

    face_app = None
    index = None
    labels = None
    if HAS_FACE:
        try:
            face_app = init_face_app()
            index, labels = load_faiss()
        except Exception as e:
            print(f"[WARN] Could not initialize actor-linker models/index: {e}")

    for movie in os.listdir(SCENE_ASSETS_DIR):
        if target and movie != target:
            continue
        movie_dir = os.path.join(SCENE_ASSETS_DIR, movie)
        if not os.path.isdir(movie_dir):
            continue

        movie_results = []
        meta = {"movie": movie, "status": "ok", "found_scenes": 0}

        for item in sorted(os.listdir(movie_dir)):
            if not item.endswith("_frames"):
                continue

            scene_id = item.replace("_frames", "")
            frames_dir = os.path.join(movie_dir, item)

            ranked = process_scene(frames_dir, face_app, index, labels)
            if not ranked:
                # no valid detections for this scene
                continue

            movie_results.append(
                {
                    "scene_id": scene_id,
                    "characters": [r[0] for r in ranked],
                    "character_dominance_ranking": [
                        {"character": r[0], "score": float(round(float(r[1]), 3))}
                        for r in ranked
                    ],
                }
            )

        out_path = os.path.join(OUTPUT_DIR, f"{movie}_scene_actors.json")
        meta_path = os.path.join(OUTPUT_DIR, f"{movie}_scene_actors.meta.json")
        if movie_results:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(movie_results, f, indent=2, ensure_ascii=False)
            meta["found_scenes"] = len(movie_results)
            if os.path.exists(meta_path):
                os.remove(meta_path)
        else:
            meta["status"] = "no_actors"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

        if not HAS_FACE:
            print(f"[OK] Actor linking skipped for {movie} (missing native deps)")
        else:
            print(f"[OK] Actor indexing completed for {movie}")


if __name__ == "__main__":
    main()
