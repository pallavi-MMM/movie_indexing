import json
import os
import sys

# allow running tests from repo root
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.scene_content_safety import assess_scene


def main():
    path = "outputs/scene_index/Ravi_teja_FINAL_WITH_SAFETY.json"
    with open(path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    updated = []
    for scene in baseline:
        new = scene.copy()
        new.update(assess_scene(scene))
        updated.append(new)

    # compare baseline vs updated (non-exact order-insensitive compare of the dicts)
    for b, u in zip(baseline, updated):
        if b.get("violence_level") != u.get("violence_level") or b.get("age_rating_suggestion") != u.get("age_rating_suggestion"):
            print("DIFFERENT:", b.get("scene_id"), b.get("violence_level"), b.get("age_rating_suggestion"), "->", u.get("violence_level"), u.get("age_rating_suggestion"))
            return 2

    print("OK: safety assessment idempotent for existing file (no change in core safety fields)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
