"""Mock VLM-based summary module.

This module provides a lightweight, dependency-free summarizer that mimics
what a VLM-based summarizer might produce. It consumes scene fields such as
`dialogue_text`, `characters`, `objects`, `visual_quality` and `safety_flags`
and returns a short `scene_summary`, `keywords_auto_generated`, and per-field
confidences/provenance so fusion can ingest them.

The implementation is deterministic and mock-first so CI remains fast.
"""
from typing import Dict, Any, List


def _collect_dialogue(dialogue: List[Dict[str, Any]]) -> str:
    if not dialogue:
        return ""
    # join a few key lines
    lines = [d.get("line", "") for d in dialogue[:3]]
    return " ".join(l for l in lines if l)


def summarize_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dict with `scene_summary`, `keywords_auto_generated`, and
    `field_confidences`/`field_provenance` keys.
    """
    summary_parts: List[str] = []
    keywords: List[str] = []
    confidences: Dict[str, float] = {}
    provenance: Dict[str, List[str]] = {}

    # Dialogue-driven summary
    dialogue_text = scene.get("dialogue_text") or []
    dialogue_snip = _collect_dialogue(dialogue_text)
    if dialogue_snip:
        summary_parts.append(f"Dialogue: {dialogue_snip}")
        confidences["scene_summary.dialogue"] = 0.85
        provenance.setdefault("scene_summary", []).append("vlm_dialogue_encoder")

    # Character-driven summary
    chars = scene.get("characters") or []
    if isinstance(chars, list) and chars:
        # chars may be list of names or objects with 'name'
        names = []
        for c in chars:
            if isinstance(c, dict):
                n = c.get("name")
                if n:
                    names.append(n)
            elif isinstance(c, str):
                names.append(c)
        if names:
            summary_parts.append(f"Characters: {', '.join(names[:3])}")
            keywords.extend(names[:5])
            confidences["scene_summary.characters"] = 0.8
            provenance.setdefault("scene_summary", []).append("vlm_visual_encoder")

    # Objects
    objs = scene.get("objects") or []
    if isinstance(objs, list) and objs:
        obj_types = []
        for o in objs[:5]:
            if isinstance(o, dict):
                t = o.get("type")
                if t:
                    obj_types.append(t)
        if obj_types:
            summary_parts.append(f"Objects: {', '.join(obj_types)}")
            keywords.extend(obj_types)
            confidences["scene_summary.objects"] = 0.75
            provenance.setdefault("scene_summary", []).append("vlm_object_encoder")

    # Visual quality / safety influence
    vq = scene.get("quality_flags") or {}
    safety = scene.get("safety_flags") or {}
    if vq.get("black_frames_detected"):
        summary_parts.append("Visual issues: black frames detected")
        keywords.append("black_frames")
        confidences.setdefault("scene_summary.visual_quality", 0.7)
        provenance.setdefault("scene_summary", []).append("visual_quality_detector")
    if safety.get("violence"):
        summary_parts.append("Content note: violent content")
        keywords.append("violence")
        confidences.setdefault("scene_summary.safety", 0.9)
        provenance.setdefault("scene_summary", []).append("scene_safety")

    # Build final summary string
    if summary_parts:
        scene_summary = " | ".join(summary_parts)
    else:
        scene_summary = "No salient dialogue or visual cues detected."
        confidences["scene_summary.fallback"] = 0.2
        provenance.setdefault("scene_summary", []).append("vlm_fallback")

    # keywords dedupe
    kw_unique = []
    for k in keywords:
        if k not in kw_unique:
            kw_unique.append(k)

    out = {
        "scene_summary": scene_summary,
        "keywords_auto_generated": kw_unique,
        "field_confidences": confidences,
        "field_provenance": provenance,
    }
    return out


__all__ = ["summarize_scene"]
