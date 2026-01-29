import os
import json
import torch
import torchaudio
from dotenv import load_dotenv
from pyannote.audio import Pipeline

# --------------------------------------------------
# ENV
# --------------------------------------------------
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not found in .env file")

# --------------------------------------------------
# PATHS
# --------------------------------------------------
OUT_DIR = "outputs/scene_speakers"
os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------
# DEVICE
# --------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --------------------------------------------------
# PIPELINE (THIS IS THE FIX)
# --------------------------------------------------
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization", revision="main", token=HF_TOKEN
)
pipeline.to(device)


# --------------------------------------------------
# DIARIZATION
# --------------------------------------------------
def diarize_scene(scene_id, audio_path):
    waveform, sample_rate = torchaudio.load(audio_path)

    diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "speaker": speaker,
                "start": round(float(turn.start), 2),
                "end": round(float(turn.end), 2),
            }
        )

    return {"scene_id": scene_id, "speaker_segments": segments}


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    audio_dir = f"outputs/scene_assets/{movie}"
    movie_out_dir = os.path.join(OUT_DIR, movie)
    os.makedirs(movie_out_dir, exist_ok=True)

    for file in sorted(os.listdir(audio_dir)):
        if not file.endswith("_audio.wav"):
            continue

        scene_id = file.replace("_audio.wav", "")
        audio_path = os.path.join(audio_dir, file)

        print(f"[SPEAKER] {scene_id}")
        data = diarize_scene(scene_id, audio_path)

        out_path = os.path.join(movie_out_dir, f"{scene_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    print("[OK] Speaker diarization complete")


if __name__ == "__main__":
    main()
