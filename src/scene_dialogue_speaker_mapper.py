import os
import json
from typing import Optional

OUT_DIR = "outputs/scene_dialogue"
SPEAKER_DIR = "outputs/scene_speakers"


def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers_to_dialogue(dialogue_segments, speaker_segments):
    # speaker_segments: list of {speaker, start, end}
    # dialogue_segments: list of {line, start, end, character}
    for seg in dialogue_segments:
        seg_start = seg.get("start")
        seg_end = seg.get("end")
        assigned: Optional[str] = None
        best_overlap = 0.0
        if seg_start is None or seg_end is None:
            seg["character"] = None
            continue
        for sp in speaker_segments:
            o = overlap(seg_start, seg_end, sp.get("start", 0.0), sp.get("end", 0.0))
            if o > best_overlap:
                best_overlap = o
                assigned = sp.get("speaker")
        seg["character"] = assigned if best_overlap > 0 else None
    return dialogue_segments


def process_movie(movie: str):
    dialogue_movie_dir = os.path.join(OUT_DIR, movie)
    speaker_movie_dir = os.path.join(SPEAKER_DIR, movie)

    if not os.path.exists(dialogue_movie_dir):
        print(f"[WARN] No dialogue dir for {movie}, skipping mapper")
        return

    # load speaker files into a map for quick lookups
    speaker_map = {}
    if os.path.exists(speaker_movie_dir):
        for fn in os.listdir(speaker_movie_dir):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(speaker_movie_dir, fn)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scene_id") or os.path.splitext(fn)[0]
            speaker_map[sid] = data.get("speaker_segments", [])

    # iterate dialogue files
    for fn in sorted(os.listdir(dialogue_movie_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(dialogue_movie_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sid = data.get("scene_id") or os.path.splitext(fn)[0]
        dialogue = data.get("dialogue_text", [])

        speakers = speaker_map.get(sid, [])
        if not speakers:
            # nothing to align; leave characters as-is (empty)
            print(f"[MAPPER] No speaker data for {sid}, leaving characters blank")
            continue

        mapped = assign_speakers_to_dialogue(dialogue, speakers)
        data["dialogue_text"] = mapped
        # write back in-place so downstream merger sees mapped dialogue
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[MAPPER] Mapped speakers for {sid}")


if __name__ == "__main__":
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    process_movie(movie)
