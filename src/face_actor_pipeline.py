"""Pipeline that runs face-tracking and links tracks to actors using ActorDB.

This is a mock-first implementation: it uses `FaceTracker(mode='mock')` and
`ActorDB`/`ActorLinker` to map tracks to actor names with confidences and
screen-time aggregation.
"""

from typing import Dict, Any, List

from src.face_tracker import FaceTracker
from src.actor_db import ActorDB
from src.actor_linker import ActorLinker


class FaceActorPipeline:
    def __init__(self, dim: int = 3, tracker_mode: str = "mock"):
        self.tracker = FaceTracker(mode=tracker_mode)
        self.actor_db = ActorDB(dim=dim)
        self.linker = ActorLinker(mode="mock")

    def register_actor(
        self, name: str, embedding: List[float], metadata: Dict[str, Any] = None
    ):
        self.actor_db.add_actor(name, embedding, metadata)
        # keep ActorLinker in sync
        self.linker.add_actor(name, embedding)

    def process_video(
        self, video_path: str, max_frames: int = 30
    ) -> List[Dict[str, Any]]:
        tracks = self.tracker.track(video_path, max_frames=max_frames)
        # Aggregate tracks into characters with screen_time and provenance
        chars: Dict[str, Dict[str, Any]] = {}
        for tr in tracks:
            emb = tr.get("embedding")
            # compute screen_time heuristically as number of frames * 0.5
            frames = tr.get("frames", [])
            screen_time = float(len(frames)) * 0.5
            match = self.linker.match_embedding(emb)
            name = match.get("name") if match.get("matched") else "unknown"
            conf = match.get("confidence", 0.0)
            prov = ["face_tracker"]
            if name not in chars:
                chars[name] = {
                    "name": name,
                    "screen_time": screen_time,
                    "confidence": conf,
                    "provenance": prov,
                }
            else:
                chars[name]["screen_time"] += screen_time
                chars[name]["confidence"] = max(chars[name]["confidence"], conf)
                for p in prov:
                    if p not in chars[name]["provenance"]:
                        chars[name]["provenance"].append(p)

        # Convert to list
        out = [v for k, v in chars.items()]
        return out


__all__ = ["FaceActorPipeline"]
