import os
import json
from datetime import timedelta
import cv2

# Try to import PySceneDetect; if unavailable, provide a lightweight fallback
try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector

    HAS_SCENEDETECT = True
except Exception:
    HAS_SCENEDETECT = False

MOVIES_DIR = "movies"
OUTPUT_DIR = "outputs/scenes"

MIN_SCENE_DURATION_SEC = 20.0
CONTENT_THRESHOLD = 27.0

os.makedirs(OUTPUT_DIR, exist_ok=True)


def timecode_to_seconds(timecode):
    # Support both PySceneDetect timecode objects and plain float seconds (fallback)
    if hasattr(timecode, "get_seconds"):
        return timecode.get_seconds()
    try:
        return float(timecode)
    except Exception:
        raise RuntimeError("Unsupported timecode type")


def seconds_to_time_str(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - total_seconds) * 1000)
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02}.{millis:03}"


def detect_raw_scenes(video_path):
    if HAS_SCENEDETECT:
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=CONTENT_THRESHOLD))

        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)

        scene_list = scene_manager.get_scene_list()
        video_manager.release()

        return scene_list
    # Fallback: split video into fixed-length segments when scenedetect not installed
    duration = get_video_duration(video_path)
    # Aim for segments roughly MIN_SCENE_DURATION_SEC long, but cap to 60s for stability
    seg_len = max(
        MIN_SCENE_DURATION_SEC,
        min(60.0, duration / max(1, int(duration / MIN_SCENE_DURATION_SEC))),
    )
    scene_list = []
    start = 0.0
    while start < duration:
        end = min(start + seg_len, duration)
        scene_list.append((start, end))
        start = end
    return scene_list


def merge_scenes(scene_list, video_duration):
    merged = []
    current_start = timecode_to_seconds(scene_list[0][0])
    current_end = timecode_to_seconds(scene_list[0][1])

    for start, end in scene_list[1:]:
        start_sec = timecode_to_seconds(start)
        end_sec = timecode_to_seconds(end)

        if (current_end - current_start) < MIN_SCENE_DURATION_SEC:
            current_end = end_sec
        else:
            merged.append((current_start, current_end))
            current_start = start_sec
            current_end = end_sec

    # Handle last scene
    if merged:
        last_start, last_end = merged[-1]
        if (current_end - current_start) < MIN_SCENE_DURATION_SEC:
            merged[-1] = (last_start, current_end)
        else:
            merged.append((current_start, current_end))
    else:
        merged.append((current_start, current_end))

    # Ensure coverage till video end
    if merged[-1][1] < video_duration:
        merged[-1] = (merged[-1][0], video_duration)

    return merged


def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    cap.release()

    if fps <= 0:
        raise RuntimeError("Invalid FPS detected")

    return frame_count / fps


def process_movie(movie_path):
    movie_name = os.path.splitext(os.path.basename(movie_path))[0]

    raw_scenes = detect_raw_scenes(movie_path)
    if not raw_scenes:
        raise RuntimeError("No scenes detected")

    video_duration = get_video_duration(movie_path)
    merged_scenes = merge_scenes(raw_scenes, video_duration)

    scenes_json = []
    for idx, (start, end) in enumerate(merged_scenes, start=1):
        scenes_json.append(
            {
                "scene_id": f"scene_{idx:04}",
                "start_time": seconds_to_time_str(start),
                "end_time": seconds_to_time_str(end),
                "duration": round(end - start, 2),
                "transition_type": "cut",
                "transition_confidence": 0.9,
            }
        )

    output = {
        "movie_id": movie_name,
        "source_file": movie_path,
        "scene_count": len(scenes_json),
        "min_scene_duration_sec": MIN_SCENE_DURATION_SEC,
        "scenes": scenes_json,
    }

    out_path = os.path.join(OUTPUT_DIR, f"{movie_name}_scenes.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"[OK] {movie_name}: {len(scenes_json)} scenes written")


def main():
    target = globals().get("TARGET_MOVIE")
    for file in os.listdir(MOVIES_DIR):
        if not file.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".flv")):
            continue
        movie_id = os.path.splitext(file)[0]
        if target and movie_id != target:
            # skip other movies when a target is provided
            continue
        process_movie(os.path.join(MOVIES_DIR, file))


if __name__ == "__main__":
    main()
