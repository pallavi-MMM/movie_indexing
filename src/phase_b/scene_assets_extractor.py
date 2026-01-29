import os
import json
import cv2
import subprocess
from math import ceil

MOVIES_DIR = "movies"
SCENES_JSON_DIR = "outputs/scenes"
OUTPUT_DIR = "outputs/scene_assets"

FRAME_INTERVAL_SEC = 1.0  # sample one frame per second
MIN_FRAMES = 1
MAX_FRAMES = 100000

os.makedirs(OUTPUT_DIR, exist_ok=True)


def time_to_seconds(t):
    h, m, rest = t.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def extract_frames(video_path, start, end, out_dir):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    start_frame = int(start * fps)
    end_frame = int(end * fps)
    total_frames = end_frame - start_frame

    duration_sec = max(0.0, end - start)
    # number of frames = one per second, but at least 1
    num_frames = max(MIN_FRAMES, int(ceil(duration_sec / FRAME_INTERVAL_SEC)))

    os.makedirs(out_dir, exist_ok=True)

    count = 0
    for s in range(num_frames):
        frame_time = start + s * FRAME_INTERVAL_SEC
        if frame_time >= end:
            break
        frame_id = int(frame_time * fps)
        if frame_id >= end_frame:
            break

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imwrite(os.path.join(out_dir, f"frame_{count+1:03}.jpg"), frame)
        count += 1

    # ensure at least one frame saved: fall back to start frame
    if count == 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ret, frame = cap.read()
        if ret:
            os.makedirs(out_dir, exist_ok=True)
            cv2.imwrite(os.path.join(out_dir, f"frame_001.jpg"), frame)

    cap.release()


def extract_audio(video_path, start, end, out_audio):
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-to",
        str(end),
        "-i",
        video_path,
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        out_audio,
    ]
    subprocess.run(cmd, check=True)


def process_movie(movie_name):
    video_path = os.path.join(MOVIES_DIR, movie_name)
    movie_id = os.path.splitext(movie_name)[0]

    with open(os.path.join(SCENES_JSON_DIR, f"{movie_id}_scenes.json"), "r") as f:
        scenes_data = json.load(f)

    movie_out_dir = os.path.join(OUTPUT_DIR, movie_id)
    os.makedirs(movie_out_dir, exist_ok=True)

    for scene in scenes_data["scenes"]:
        scene_id = scene["scene_id"]
        start = time_to_seconds(scene["start_time"])
        end = time_to_seconds(scene["end_time"])

        frames_dir = os.path.join(movie_out_dir, f"{scene_id}_frames")
        audio_path = os.path.join(movie_out_dir, f"{scene_id}_audio.wav")

        extract_frames(video_path, start, end, frames_dir)
        extract_audio(video_path, start, end, audio_path)

    print(f"[OK] Assets extracted for {movie_id}")


def main():
    target = globals().get("TARGET_MOVIE")
    for file in os.listdir(MOVIES_DIR):
        if not file.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".flv")):
            continue
        movie_id = os.path.splitext(file)[0]
        if target and movie_id != target:
            continue
        process_movie(file)


if __name__ == "__main__":
    main()
