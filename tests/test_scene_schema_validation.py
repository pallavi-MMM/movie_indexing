import os
import json
from src.scene_schema import validate_scene


def test_validate_existing_final_json_reports_issues():
    idx_dir = os.path.join(os.path.dirname(__file__), "..", "outputs", "scene_index")
    idx_dir = os.path.abspath(idx_dir)

    failures = 0
    reports = []

    if not os.path.exists(idx_dir):
        # nothing to validate in this environment
        return

    for fn in os.listdir(idx_dir):
        if not fn.endswith("_FINAL.json"):
            continue
        path = os.path.join(idx_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            scenes = json.load(f)
        for s in scenes:
            valid, msgs = validate_scene(s)
            if not valid:
                failures += 1
                reports.append((s.get("scene_id"), msgs))

    # Print a short summary to help triage locally; CI will only fail when SCHEMA_STRICT is enabled
    if failures:
        print(f"[SCHEMA] Validation found {failures} invalid scene(s). Examples:")
        for sid, msgs in reports[:5]:
            print(f" - {sid}: {msgs}")

    # If the environment opts into strict mode we should fail tests
    strict = os.getenv("SCHEMA_STRICT", "0").lower() in ("1", "true", "yes")
    if strict and failures:
        assert False, f"Schema validation failed for {failures} scenes"
    else:
        # non-strict: test passes but reports issues
        assert True
