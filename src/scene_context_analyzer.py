import os
import json
import torch
# lazy import for open_clip (heavy) to avoid import-time failures
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

SCENE_ASSETS_DIR = "outputs/scene_assets"
OUTPUT_DIR = "outputs/scene_context_index"
SAMPLE_FRAMES = 6

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lazy model variables
_ctx_model = None
_ctx_preprocess = None
_ctx_tokenizer = None
from src.device import DEVICE as _ctx_device
_ctx_loaded = False

def load_context_model():
    global _ctx_model, _ctx_preprocess, _ctx_tokenizer, _ctx_loaded
    if _ctx_loaded:
        return _ctx_model, _ctx_preprocess, _ctx_tokenizer
    _ctx_loaded = True
    try:
        import open_clip
        from PIL import Image
        model, preprocess = open_clip.create_model_from_pretrained(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        try:
            model = model.to(_ctx_device)
        except Exception:
            pass
        model.eval()
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        _ctx_model = model
        _ctx_preprocess = preprocess
        _ctx_tokenizer = tokenizer
    except Exception as e:
        print(f"[WARN] Could not load scene context model: {e}")
        _ctx_model = None
        _ctx_preprocess = None
        _ctx_tokenizer = None
    return _ctx_model, _ctx_preprocess, _ctx_tokenizer

# Conservative prompts only
LOCATION_PROMPTS = [
    "a street",
    "inside a house",
    "inside an office",
    "inside a hospital",
    "inside a vehicle",
    "a market area"
]

TIME_PROMPTS = [
    "daytime",
    "nighttime",
    "indoor artificial lighting"
]

INDOOR_OUTDOOR = {
    "a street": "outdoor",
    "a market area": "outdoor",
    "inside a house": "indoor",
    "inside an office": "indoor",
    "inside a hospital": "indoor",
    "inside a vehicle": "indoor"
}


def sample_frames(frames):
    if len(frames) <= SAMPLE_FRAMES:
        return frames
    idx = np.linspace(0, len(frames) - 1, SAMPLE_FRAMES).astype(int)
    return [frames[i] for i in idx]


@torch.no_grad()
def classify_scene(frames_dir):
    frames = sorted(
        [os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(".jpg")]
    )

    if not frames:
        return None

    frames = sample_frames(frames)

    model, preprocess, tokenizer = load_context_model()
    if model is None or preprocess is None or tokenizer is None:
        return None

    image_features = []
    for f in frames:
        img = Image.open(f).convert("RGB")
        image = preprocess(img).unsqueeze(0).to(_ctx_device)
        features = model.encode_image(image)
        image_features.append(features)

    image_features = torch.cat(image_features, dim=0).mean(dim=0, keepdim=True)
    image_features /= image_features.norm(dim=-1, keepdim=True)

    # Location
    text = tokenizer(LOCATION_PROMPTS).to(_ctx_device)
    text_features = model.encode_text(text)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    scores = (image_features @ text_features.T).squeeze(0)
    loc_idx = scores.argmax().item()
    location = LOCATION_PROMPTS[loc_idx]

    # Time of day
    text = tokenizer(TIME_PROMPTS).to(_ctx_device)
    text_features = model.encode_text(text)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    scores = (image_features @ text_features.T).squeeze(0)
    time_of_day = TIME_PROMPTS[scores.argmax().item()]

    return {
        "location": location.replace("a ", "").replace("inside ", ""),
        "time_of_day": time_of_day.replace("time", ""),
        "indoor_outdoor": INDOOR_OUTDOOR.get(location, "unknown"),
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
            data = classify_scene(frames_dir)

            if data:
                scene_id = f"{movie}_{scene.replace('_frames','')}"
                results.append({
                    "scene_id": scene_id,
                    **data
                })

        out_path = f"{OUTPUT_DIR}/{movie}_scene_context.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"[OK] Scene context written: {out_path}")


if __name__ == "__main__":
    main()
