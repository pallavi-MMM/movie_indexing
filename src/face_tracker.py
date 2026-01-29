"""Lightweight face tracker with a deterministic mock mode for CI and fast development.

API:
  FaceTracker(mode='auto'|'mock'|'gpu')
    track(video_path: str, max_frames: int = 30) -> List[Dict]

The mock mode returns deterministic tracks with per-track representative embeddings so
downstream modules (actor linker) can be exercised without heavy dependencies.
"""

from typing import Dict, List, Any
import hashlib


class FaceTracker:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        # In auto mode, prefer GPU-backed implementations when available.
        if self.mode == "auto":
            # For now, default to mock when no heavy deps are available.
            try:
                import insightface  # type: ignore

                self.mode = "gpu"
            except Exception:
                self.mode = "mock"

    def track(self, video_path: str, max_frames: int = 30) -> List[Dict[str, Any]]:
        """Return a list of tracks. Each track is a dict like:
        {
            'track_id': int,
            'frames': [{'ts': float, 'bbox': [x1,y1,x2,y2]}],
            'embedding': [float,...],  # representative embedding
        }
        """
        if self.mode == "mock":
            return self._mock_track(video_path, max_frames)
        # gpu/backed implementation placeholder; if runtime error, fallback to mock
        try:
            if self.mode == "gpu":
                return self._gpu_track(video_path, max_frames)
        except Exception:
            return self._mock_track(video_path, max_frames)
        # fallback
        return self._mock_track(video_path, max_frames)

    def _gpu_track(self, video_path: str, max_frames: int) -> List[Dict[str, Any]]:
        """Attempt to perform GPU-backed face detection + embedding extraction.

        This method is intentionally permissive: if any required dependency is
        missing or a runtime error occurs, it raises an exception so callers can
        choose to fallback to the mock implementation.
        """
        try:
            import insightface  # type: ignore
            from insightface.app import FaceAnalysis  # type: ignore
            import cv2  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("GPU face-tracking dependencies not available") from exc

        app = FaceAnalysis(allowed_modules=["detection", "recognition"])
        app.prepare(ctx_id=0, det_size=(640, 640))

        cap = cv2.VideoCapture(video_path)
        frames = []
        count = 0
        while count < max_frames and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            count += 1
        cap.release()

        tracks = []
        # Very simple frame-level detection -> treat each detection as a short track
        tid = 0
        for f in frames:
            res = app.get(f)
            for r in res:
                tid += 1
                # bounding box
                x1, y1, x2, y2 = map(float, r.bbox.flatten().tolist())
                emb = (
                    r.embedding.tolist() if hasattr(r, "embedding") else [0.0, 0.0, 0.0]
                )
                tracks.append(
                    {
                        "track_id": tid,
                        "frames": [{"ts": 0.0, "bbox": [x1, y1, x2, y2]}],
                        "embedding": emb,
                    }
                )
        return tracks

    def _mock_track(self, video_path: str, max_frames: int) -> List[Dict[str, Any]]:
        # Deterministic pseudo-random generator based on path
        h = int(hashlib.sha256(video_path.encode("utf-8")).hexdigest()[:8], 16)
        n_tracks = 1 + (h % 2)  # 1 or 2 tracks
        tracks: List[Dict[str, Any]] = []
        for t in range(n_tracks):
            track_id = t + 1
            frames = []
            for i in range(min(max_frames, 8)):
                ts = float(i) * 0.5
                # simple deterministic bbox based on hashes
                x1 = 10 + ((h >> (t + i)) % 50)
                y1 = 20 + ((h >> (t + i + 3)) % 40)
                x2 = x1 + 60
                y2 = y1 + 80
                frames.append({"ts": ts, "bbox": [x1, y1, x2, y2]})
            # representative embedding: small deterministic vector
            emb = [float(((h >> (t + i)) & 3) / 3.0) for i in range(3)]
            tracks.append({"track_id": track_id, "frames": frames, "embedding": emb})
        return tracks


__all__ = ["FaceTracker"]
