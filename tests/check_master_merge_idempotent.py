import json
import sys
import os


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src import scene_master_merger


def main():
    outpath = scene_master_merger.OUTPUT_FILE

    with open(outpath, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    # run merger (it will overwrite the same file)
    scene_master_merger.main()

    with open(outpath, "r", encoding="utf-8") as f:
        new = json.load(f)

    # ignore metadata-generated timestamps when comparing
    def normalize(scenes):
        out = []
        for s in scenes:
            t = dict(s)
            t.pop("metadata_generated_at", None)
            out.append(t)
        return out

    if normalize(baseline) == normalize(new):
        print("OK: master merger produced identical output (ignoring timestamps)")
        return 0

    # else find first differing scene (ignoring metadata_generated_at)
    for i, (b, n) in enumerate(zip(normalize(baseline), normalize(new))):
        if b != n:
            print("DIFF at index", i, "scene_id", b.get("scene_id"))
            return 2

    print("Output differs but lengths may be different")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
