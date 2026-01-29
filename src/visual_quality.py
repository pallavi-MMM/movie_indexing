"""Mock visual quality detectors: black frames, flash frames, bitrate drop.

Designed to be deterministic and dependency-free so CI can run quickly.
Heuristics:
- If explicit flags `black_frames_detected`/`flash_frames_detected` exist in input scene,
  honor them with high confidence.
- If `bitrate` numeric is present, mark `bitrate_drop_detected` True when below threshold.
- Otherwise provide low-confidence defaults.
"""

from typing import Dict, Any


def analyze_visual_quality(scene: Dict[str, Any]) -> Dict[str, Any]:
    flags = {
        "black_frames_detected": False,
        "flash_frames_detected": False,
        "bitrate_drop_detected": False,
    }
    confidences = {}
    provenance = {}

    # Explicit signals
    if isinstance(scene.get("black_frames_detected"), bool):
        flags["black_frames_detected"] = bool(scene["black_frames_detected"])
        confidences["black_frames_detected"] = 0.95
        provenance["black_frames_detected"] = ["visual_black_frame_detector"]

    if isinstance(scene.get("flash_frames_detected"), bool):
        flags["flash_frames_detected"] = bool(scene["flash_frames_detected"])
        confidences["flash_frames_detected"] = 0.95
        provenance["flash_frames_detected"] = ["visual_flash_detector"]

    # Bitrate heuristics: expect kbps
    bitrate = scene.get("bitrate")
    if isinstance(bitrate, (int, float)):
        # threshold: consider drop when below 500 kbps
        if bitrate < 500:
            flags["bitrate_drop_detected"] = True
            confidences["bitrate_drop_detected"] = 0.9
            provenance["bitrate_drop_detected"] = ["bitrate_monitor"]
        else:
            flags["bitrate_drop_detected"] = False
            confidences["bitrate_drop_detected"] = 0.8
            provenance["bitrate_drop_detected"] = ["bitrate_monitor"]

    # Defaults for absent signals: low-confidence negatives
    for k in list(flags.keys()):
        if k not in confidences:
            confidences[k] = 0.1
            provenance[k] = ["mock_visual_quality"]

    return {
        "quality_flags": flags,
        "field_confidences": confidences,
        "field_provenance": provenance,
    }


__all__ = ["analyze_visual_quality"]
