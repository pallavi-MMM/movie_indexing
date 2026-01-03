import os
from src.audio_asr import ASR


def test_mock_asr_returns_structure(tmp_path):
    wav = tmp_path / "test.wav"
    # create a tiny WAV file (1 second, 1 channel, 16-bit)
    import wave
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000)

    asr = ASR(mode="mock")
    out = asr.transcribe_file(str(wav))
    assert "text" in out and "segments" in out
    assert isinstance(out["segments"], list)
    seg = out["segments"][0]
    assert seg["start"] == 0.0
    assert seg["end"] >= 0.9
    assert seg["text"] == "[mock transcript]"


def test_auto_mode_falls_back_to_mock_when_no_backend(tmp_path):
    wav = tmp_path / "t2.wav"
    import wave
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 8000)

    asr = ASR(mode="auto")
    out = asr.transcribe_file(str(wav))
    # Accept either mock or a real backend; ensure structure is present
    assert "model" in out
    assert isinstance(out["segments"], list)
