"""YOLOv8 object detector wrapper.

Prefers GPU-backed `ultralytics` YOLO model when available and the model
artifact is present (e.g., `yolov8m.pt`). In environments without the model or
library the wrapper falls back to a deterministic mock detector for tests.
"""
from typing import Dict, List, Optional
import os
import numpy as np


class YOLODetector:
    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), "..", "yolov8m.pt")
        self.device = device
        self._model = None
        # do not import heavy libs at import time — lazy load

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from ultralytics import YOLO  # type: ignore

            # Attempt to load specified model (may raise if file missing)
            self._model = YOLO(self.model_path)
            # attempt to set device
            try:
                self._model.to(self.device)
            except Exception:
                # best-effort: ignore if device selection fails
                pass
            return self._model
        except Exception:
            # library or model not available — keep _model None and use mock
            self._model = None
            return None

    def detect_from_image(self, image_path: str) -> List[Dict]:
        """Detect objects in an image and return normalized results.

        Returns a list of dicts:
          - type: label (string)
          - bbox: [x1, y1, x2, y2]
          - confidence: float
          - model: model identifier used (string)
        """
        model = self._load_model()
        if model is None:
            return self._mock_detect(image_path)

        # real model inference
        try:
            results = model.predict(source=image_path, imgsz=640, conf=0.25)
            out = []
            for r in results:
                boxes = getattr(r, "boxes", None)
                if boxes is None:
                    continue
                for b in boxes:
                    try:
                        xyxy = b.xyxy.tolist()[0]
                    except Exception:
                        xyxy = [float(x) for x in b.xyxy]
                    label = getattr(b, "cls", None)
                    # Attempt to get human label if model has names
                    try:
                        names = model.model.names if hasattr(model, "model") else None
                        lbl = names[int(label)] if names and label is not None else str(int(label) if label is not None else "")
                    except Exception:
                        lbl = str(int(label) if label is not None else "")
                    conf = float(b.conf[0]) if hasattr(b, "conf") else 0.0
                    out.append({"type": lbl, "bbox": [xyxy[0], xyxy[1], xyxy[2], xyxy[3]], "confidence": conf, "model": os.path.basename(self.model_path)})
            return out
        except Exception:
            # On any runtime error, fallback to mock
            return self._mock_detect(image_path)

    def _mock_detect(self, image_path: str) -> List[Dict]:
        # Deterministic fake detector: returns a single object based on filename hash
        fn = os.path.basename(image_path)
        h = sum(ord(c) for c in fn) % 100
        # simple bbox within 640x360 range
        x1 = float((h % 100) / 100.0 * 100)
        y1 = float(((h * 3) % 100) / 100.0 * 50)
        x2 = x1 + 50.0
        y2 = y1 + 50.0
        return [{"type": "mock_object", "bbox": [x1, y1, x2, y2], "confidence": 0.75, "model": "mock"}]


__all__ = ["YOLODetector"]


