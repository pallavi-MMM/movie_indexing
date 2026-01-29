"""Lightweight ASR wrapper with a mock mode for CI and environments without models.

Design goals:
- Minimal external dependencies for tests (mock mode returns deterministic transcripts)
- Auto-detects available backends (faster_whisper / whisper) when mode='auto'
- Returns structured output with segments, timestamps and optional confidences
"""
from typing import Dict, List
import os
import wave


class ASR:
    def __init__(self, mode: str = "auto", model_name: str = "tiny"):
        """mode: 'auto'|'mock'|'whisper'|'faster_whisper'"""
        self.model_name = model_name
        self.mode = mode
        if self.mode == "auto":
            # detect available backends
            try:
                import faster_whisper  # type: ignore

                self.mode = "faster_whisper"
            except Exception:
                try:
                    import whisper  # type: ignore

                    self.mode = "whisper"
                except Exception:
                    self.mode = "mock"

    def transcribe_file(self, audio_path: str) -> Dict:
        """Transcribe a single audio file and return a dict with 'text' and 'segments'.

        segments: list of {start, end, text, confidence}
        """
        if self.mode == "mock":
            return self._mock_transcribe(audio_path)

        if self.mode == "faster_whisper":
            # Attempt faster_whisper usage (best-effort) — keep optional to avoid hard dependency
            try:
                from faster_whisper import WhisperModel  # type: ignore
                import torch

                DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
                COMPUTE_TYPE = "float16" if DEVICE.startswith("cuda") else "int8"

                model = WhisperModel(self.model_name, device=DEVICE, compute_type=COMPUTE_TYPE)
                segments = []
                text_parts = []
                # keep beam search and deterministic temperature
                for segment in model.transcribe(audio_path, beam_size=5, temperature=0.0):
                    start = getattr(segment, "start", None) or 0.0
                    end = getattr(segment, "end", None) or 0.0
                    txt = getattr(segment, "text", str(segment))
                    seg = {"start": start, "end": end, "text": txt, "confidence": None}
                    segments.append(seg)
                    text_parts.append(txt)
                return {"text": " ".join(text_parts), "segments": segments, "model": f"faster_whisper:{self.model_name}"}
            except Exception:
                # fallback to mock
                return self._mock_transcribe(audio_path)

        if self.mode == "whisper":
            try:
                import whisper  # type: ignore

                model = whisper.load_model(self.model_name)
                result = model.transcribe(audio_path)
                segments = []
                for seg in result.get("segments", []):
                    segments.append({"start": seg.get("start"), "end": seg.get("end"), "text": seg.get("text"), "confidence": seg.get("confidence")})
                return {"text": result.get("text"), "segments": segments, "model": f"whisper:{self.model_name}"}
            except Exception:
                return self._mock_transcribe(audio_path)

        # unknown mode: return mock
        return self._mock_transcribe(audio_path)

    def _mock_transcribe(self, audio_path: str) -> Dict:
        # Use audio duration heuristics for deterministic segmentation
        duration = 0.0
        try:
            with wave.open(audio_path, "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                duration = frames / float(rate) if rate else 0.0
        except Exception:
            # Not a WAV or unreadable; pretend 1 second
            duration = 1.0

        # Create a single segment for the full duration
        seg = {"start": 0.0, "end": duration, "text": "[mock transcript]", "confidence": 0.9}
        return {"text": "[mock transcript]", "segments": [seg], "model": "mock"}


__all__ = ["ASR"]
