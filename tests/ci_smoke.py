import os
import json
import shutil
import importlib
import sys
import os

# ensure repo root is on sys.path when running this helper directly
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Simple smoke test: create minimal scenes JSON and a segment file, then run the merger
OUT_DIR = "outputs"
SCENES_DIR = os.path.join(OUT_DIR, "scenes")
SEGMENTS_DIR = os.path.join(OUT_DIR, "scene_segments")
SCENE_INDEX_DIR = os.path.join(OUT_DIR, "scene_index")

movie = "DUMMY"

# cleanup previous
for d in (SCENES_DIR, SEGMENTS_DIR, SCENE_INDEX_DIR):
    if os.path.exists(d):
        shutil.rmtree(d)

os.makedirs(SCENES_DIR, exist_ok=True)
os.makedirs(SEGMENTS_DIR, exist_ok=True)
os.makedirs(SCENE_INDEX_DIR, exist_ok=True)

# create minimal scenes file
scenes = {"scenes": [{"scene_id": "scene_0001", "start_time": 0, "end_time": 10, "duration": 10}]}
with open(os.path.join(SCENES_DIR, f"{movie}_scenes.json"), "w", encoding="utf-8") as f:
    json.dump(scenes, f, indent=2)

# create a simple segment file for the same movie
segment = {"scene_id": "scene_0001", "scene_type": "dialogue", "scene_summary": "a scene"}
with open(os.path.join(SEGMENTS_DIR, f"{movie}_scene_0001.json"), "w", encoding="utf-8") as f:
    json.dump(segment, f, indent=2)

# set env so resolver finds this movie
os.environ["MOVIE_NAME"] = movie

# run merger
mod = importlib.import_module('src.scene_master_merger')
mod.main()

# verify output
out_path = os.path.join(SCENE_INDEX_DIR, f"{movie}_FINAL.json")
if not os.path.exists(out_path):
    raise SystemExit("Smoke failed: expected final JSON not created")

with open(out_path, "r", encoding="utf-8") as f:
    data = json.load(f)

assert isinstance(data, list) and data[0]["movie_id"] == movie
print("SMOKE OK: final JSON created for movie", movie)

# cleanup created smoke artifacts
for d in (SCENES_DIR, SEGMENTS_DIR, SCENE_INDEX_DIR):
    if os.path.exists(d):
        shutil.rmtree(d)

print("Smoke test passed and cleaned up.")
