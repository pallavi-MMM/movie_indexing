import os
import json
from typing import Dict, List, Optional

OUT_DIALOGUE = "outputs/scene_dialogue"
OUT_ACTORS = "outputs/scene_actor_index"


def _strip_movie_prefix(sid: str) -> str:
    if "_" in sid and sid.count("_") >= 2:
        # drop leading '<movie>_' prefix
        return sid.split("_", 1)[1]
    return sid


def build_actor_map(actor_json_path: str) -> Dict[str, dict]:
    if not os.path.exists(actor_json_path):
        return {}
    with open(actor_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    m = {}
    for item in data:
        sid = item.get("scene_id")
        if not sid:
            continue
        m[sid] = item
        m[_strip_movie_prefix(sid)] = item
    return m


def map_speakers_to_actors(speaker_segments: List[dict], actor_item: dict) -> Dict[str, Optional[str]]:
    """Return mapping from speaker id (e.g., SPEAKER_00) to actor name (or None).

    Strategy:
     - If actor_item has 'character_dominance_ranking', use it as ordered actor list.
     - Order unique speakers by earliest start-time and map 1:1 to ordered actors.
    """
    if not speaker_segments or not actor_item:
        return {}

    actors = [r.get("character") for r in actor_item.get("character_dominance_ranking", []) if r.get("character")]
    if not actors:
        actors = actor_item.get("characters", []) or []
    if not actors:
        return {}

    # collect earliest appearance per speaker
    speaker_first: Dict[str, float] = {}
    for s in speaker_segments:
        sp = s.get("speaker")
        if not sp:
            continue
        st = s.get("start", 0.0)
        if sp not in speaker_first or st < speaker_first[sp]:
            speaker_first[sp] = st

    # sort speakers by first appearance
    sorted_speakers = sorted(speaker_first.keys(), key=lambda k: speaker_first[k])

    mapping: Dict[str, Optional[str]] = {}
    for i, sp in enumerate(sorted_speakers):
        if i < len(actors):
            mapping[sp] = actors[i]
        else:
            mapping[sp] = None
    return mapping


def process_movie(movie: str):
    dialogue_dir = os.path.join(OUT_DIALOGUE, movie)
    actor_file = os.path.join(OUT_ACTORS, f"{movie}_scene_actors.json")

    if not os.path.exists(dialogue_dir):
        print(f"[MAPPER_ACTOR] No dialogue dir for {movie}, skipping")
        return

    actor_map = build_actor_map(actor_file)
    if not actor_map:
        print(f"[MAPPER_ACTOR] No actor index for {movie}, skipping mapping")
        return

    # iterate dialogue files and try to map speakers to actors per-scene
    for fn in sorted(os.listdir(dialogue_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(dialogue_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sid = data.get("scene_id") or os.path.splitext(fn)[0]
        sid_candidate = sid
        actor_item = actor_map.get(sid_candidate) or actor_map.get(_strip_movie_prefix(sid_candidate))
        if not actor_item:
            print(f"[MAPPER_ACTOR] No actor data for scene {sid}, skipping")
            continue

        # gather speaker segments: we don't have global speaker files here, so reconstruct from dialogue
        dialogue_segments = data.get("dialogue_text", [])
        # build pseudo speaker_segments: aggregate times per speaker
        speaker_segments = []
        for seg in dialogue_segments:
            sp = seg.get("character")
            st = seg.get("start")
            en = seg.get("end")
            if not sp:
                continue
            speaker_segments.append({"speaker": sp, "start": st or 0.0, "end": en or 0.0})

        if not speaker_segments:
            print(f"[MAPPER_ACTOR] No speaker segments for {sid}, skipping")
            continue

        mapping = map_speakers_to_actors(speaker_segments, actor_item)
        if not mapping:
            print(f"[MAPPER_ACTOR] Could not build mapping for {sid}")
            continue

        # apply mapping to dialogue segments
        for seg in dialogue_segments:
            sp = seg.get("character")
            if sp in mapping and mapping[sp] is not None:
                seg["character"] = mapping[sp]
            # if mapping is None, keep original speaker id or None

        data["dialogue_text"] = dialogue_segments
        data["character_mapping"] = mapping

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[MAPPER_ACTOR] Mapped speakers -> actors for {sid}")


if __name__ == "__main__":
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    process_movie(movie)
