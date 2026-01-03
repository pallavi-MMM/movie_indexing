"""Mock-friendly scene safety and age-rating detector.

This module implements a deterministic, dependency-free safety analyzer used
for CI and prototyping. It returns structured safety flags, per-field
confidences, and provenance so the fusion step can consume them.
"""
from typing import Dict, Any


def analyze_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a scene for safety-related flags.

    Returns a dict with keys:
      - safety_flags: {violence: bool, nudity: bool, drug_use: bool, strong_language: bool}
      - field_confidences: map of flag -> confidence (0.0-1.0)
      - field_provenance: map of flag -> list of provenance strings
    """
    flags = {
        "violence": False,
        "nudity": False,
        "drug_use": False,
        "strong_language": False,
    }
    confidences = {}
    provenance = {}

    # Heuristics (mock/deterministic): prefer explicit fields when present
    if isinstance(scene.get("profanity_present"), bool):
        flags["strong_language"] = bool(scene["profanity_present"])
        confidences["strong_language"] = 0.9 if scene["profanity_present"] else 0.2
        provenance["strong_language"] = ["dialogue_profanity_detector"]

    vl = scene.get("violence_level")
    if isinstance(vl, str):
        vl_lower = vl.lower()
        if "high" in vl_lower or "graphic" in vl_lower:
            flags["violence"] = True
            confidences["violence"] = 0.95
            provenance["violence"] = ["visual_violence_detector"]
        elif "low" in vl_lower or "minor" in vl_lower:
            flags["violence"] = False
            confidences["violence"] = 0.4
            provenance["violence"] = ["visual_violence_detector"]

    # Nudity and drug use are not detected in mock mode unless explicitly present
    if scene.get("nudity_present") is True:
        flags["nudity"] = True
        confidences["nudity"] = 0.9
        provenance["nudity"] = ["visual_nudity_detector"]

    if scene.get("drug_use_present") is True:
        flags["drug_use"] = True
        confidences["drug_use"] = 0.85
        provenance["drug_use"] = ["visual_drug_detector"]

    # Default low-confidence outputs for unspecified flags
    for k in list(flags.keys()):
        if k not in confidences:
            confidences[k] = 0.1
            provenance[k] = ["mock_scene_safety"]

    return {"safety_flags": flags, "field_confidences": confidences, "field_provenance": provenance}


__all__ = ["analyze_scene"]
