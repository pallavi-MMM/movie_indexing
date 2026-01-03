from src.object_detector import YOLODetector
from PIL import Image


def test_mock_detection_returns_expected_structure(tmp_path):
    img_path = tmp_path / "f.jpg"
    img = Image.new("RGB", (640, 360), color=(255, 0, 0))
    img.save(str(img_path))

    det = YOLODetector(model_path="nonexistent.pt")
    out = det.detect_from_image(str(img_path))
    assert isinstance(out, list)
    assert len(out) == 1
    d = out[0]
    assert "type" in d and "bbox" in d and "confidence" in d and "model" in d
    assert d["model"] == "mock"


def test_auto_mode_accepts_real_backend_or_mock(tmp_path):
    img_path = tmp_path / "g.jpg"
    img = Image.new("RGB", (640, 360), color=(0, 255, 0))
    img.save(str(img_path))

    det = YOLODetector()  # may try to load real model
    out = det.detect_from_image(str(img_path))
    assert isinstance(out, list)
    assert all("type" in x and "bbox" in x and "confidence" in x for x in out)
