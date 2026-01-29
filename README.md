# Movie Scene Indexer

A collection of tools and pipelines to extract scene-level metadata from movies: audio transcriptions, object/face detection, speaker diarization, and scene-level indexing.

## Features

- YOLOv8-based object detection (optional GPU acceleration)
- Whisper / faster-whisper speech transcription
- Audio analysis with `librosa`
- Speaker diarization and actor linking (FAISS/ONNX optional)

## Requirements

This project uses `requirements.txt` for Python dependencies. Install into a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Notes:

- The repository does NOT include large model artifacts (e.g., `yolov8m.pt`). Download and place them at the project root or update paths in the code.
- For FAISS, choose `faiss-cpu` or a GPU-enabled FAISS build appropriate for your platform.
- ASR backends: `faster-whisper` and `whisper` are optional; the code auto-detects available backends.

## Quick start

Run the main pipeline on your local machine (example):

```bash
python run_all_movies.py
```

Or run pipeline for a single movie/task with the helper scripts (see `HOW_TO_RUN.md` for detailed examples).

## Project layout

- `src/` — core pipeline modules
- `scripts/` — helper and orchestration scripts
- `outputs/`, `output_json/`, `movie_event_json/` — generated outputs (ignored in git)
- `yolov8m.pt` — example model file (not included)

## Contributing

- Create issues for bugs or feature requests
- For code changes, open a pull request and describe the change

## License

Add a license file if you intend to publish this repository. Currently none is included.
