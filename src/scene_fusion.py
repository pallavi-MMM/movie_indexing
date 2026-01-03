"""Simple fusion utilities to merge per-phase scene outputs into a canonical scene.

This module implements deterministic-first fusion rules with per-field confidence
and provenance aggregation. It is intentionally conservative: if no confidence is
provided for a conflicting scalar field, we prefer the first non-null value.
"""
from typing import Any, Dict, Iterable, List, Tuple
import json


def _uniq_list(items: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for it in items:
        key = json.dumps(it, sort_keys=True) if isinstance(it, dict) else json.dumps(it)
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def _pick_best_scalar(candidates: List[Tuple[Any, float, List[str]]]) -> Tuple[Any, float, List[str]]:
    """Pick scalar value with highest confidence. Candidates are tuples of
    (value, confidence_or_None, provenance_list).
    """
    # Filter out None values
    filtered = [(v, c if c is not None else -1.0, prov) for (v, c, prov) in candidates if v is not None]
    if not filtered:
        return None, None, []
    # Choose by confidence, then by order
    best = max(filtered, key=lambda t: (t[1],))
    val, conf, prov = best
    conf_out = None if conf < 0 else conf
    # provenance union
    prov_out = []
    for _, _, p in filtered:
        for x in p:
            if x not in prov_out:
                prov_out.append(x)
    return val, conf_out, prov_out


def merge_scenes_from_sources(sources: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge scenes produced by different phases.

    Each source is expected to be a dict with keys:
      - 'scene': the partial scene dict (can be same shape as final scene)
      - 'source': a string identifying the producer (module id)

    The function returns a merged scene dict with fields:
      - field_confidences: map of field -> confidence
      - field_provenance: map of field -> list of provenance strings
    """
    src_list = list(sources)
    merged: Dict[str, Any] = {}
    field_confidences: Dict[str, float] = {}
    field_provenance: Dict[str, List[str]] = {}

    # gather all field keys
    all_keys = set()
    for s in src_list:
        scene = s.get("scene", s)
        all_keys.update(scene.keys())

    # basic copy for identifiers
    for idk in ("scene_id", "movie_id"):
        for s in src_list:
            scene = s.get("scene", s)
            if idk in scene and scene[idk]:
                merged[idk] = scene[idk]
                break

    for field in sorted(all_keys):
        # skip identifiers which are already handled
        if field in ("scene_id", "movie_id"):
            continue

        candidates: List[Tuple[Any, float, List[str]]] = []
        for s in src_list:
            scene = s.get("scene", s)
            srcname = s.get("source") or s.get("__source") or "unknown"
            if field in scene:
                val = scene[field]
                conf = None
                provs = []
                if isinstance(scene, dict):
                    conf = scene.get("field_confidences", {}).get(field)
                    provs = scene.get("field_provenance", {}).get(field, [])
                # always append source identifier
                if srcname not in provs:
                    provs = provs + [srcname]
                candidates.append((val, conf, provs))

        if not candidates:
            continue

        # handle arrays specially: union unique
        first_val = candidates[0][0]
        if isinstance(first_val, list):
            # Special-case for character lists where items are objects with 'name', 'screen_time', and confidence
            if first_val and isinstance(first_val[0], dict) and field == "characters":
                # Aggregate by character name
                char_map = {}
                provs_all: List[str] = []
                confs_map = {}
                for val, conf, prov in candidates:
                    if isinstance(val, list):
                        for item in val:
                            name = item.get("name")
                            if not name:
                                continue
                            if name not in char_map:
                                char_map[name] = item.copy()
                                # initialize screen_time
                                if "screen_time" not in char_map[name]:
                                    char_map[name]["screen_time"] = 0.0
                            else:
                                # aggregate numeric fields such as screen_time
                                if "screen_time" in item and isinstance(item["screen_time"], (int, float)):
                                    char_map[name]["screen_time"] = float(char_map[name].get("screen_time", 0.0)) + float(item["screen_time"])
                            # track confidence per character
                            if conf is not None:
                                confs_map[name] = max(confs_map.get(name, 0.0), conf)
                    for p in prov:
                        if p not in provs_all:
                            provs_all.append(p)
                merged_chars = list(char_map.values())
                merged[field] = merged_chars
                # assign confidences per-character as a map
                if confs_map:
                    field_confidences[field] = {k: v for k, v in confs_map.items()}
                if provs_all:
                    field_provenance[field] = provs_all
                continue

            lists = []
            confs = []
            provs_all: List[str] = []
            for val, conf, prov in candidates:
                if isinstance(val, list):
                    lists.extend(val)
                if conf is not None:
                    confs.append(conf)
                for p in prov:
                    if p not in provs_all:
                        provs_all.append(p)
            merged[field] = _uniq_list(lists)
            field_confidences[field] = max(confs) if confs else None
            if provs_all:
                field_provenance[field] = provs_all
            continue

        # scalars / objects: pick best by confidence
        val, conf, prov = _pick_best_scalar(candidates)
        merged[field] = val
        if conf is not None:
            field_confidences[field] = conf
        if prov:
            field_provenance[field] = prov

    if field_confidences:
        merged["field_confidences"] = field_confidences
    if field_provenance:
        merged["field_provenance"] = field_provenance

    return merged


__all__ = ["merge_scenes_from_sources"]
