
import argparse
import importlib
import json
import os
import sys
import shutil
import time
from typing import List


# ensure repo root is on sys.path so `import src.xxx` works when running script
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.timer import format_duration


STEPS: List[str] = [
    "src.phase_a.scene_segmentation",
    "src.phase_b.scene_assets_extractor",
    "src.phase_c.scene_actor_linker",
    "src.scene_visual_analyzer",
    "src.scene_object_analyzer",
    "src.scene_context_analyzer",
    "src.scene_dialogue_extractor",
    "src.scene_speaker_diarizer",
    "src.scene_dialogue_speaker_mapper",
    "src.scene_speaker_actor_mapper",
    "src.scene_dialogue_merger",
    "src.scene_profanity_detector",
    "src.scene_emotion_analyzer",
    "src.scene_emotion_merger",
    "src.scene_semantic_emotion_analyzer",  # Semantic emotion analysis
    "src.scene_content_safety",
    # Master merger should run last so it can merge all per-phase outputs
    "src.scene_master_merger",
    "src.scene_semantic_emotion_merger",  # Merge semantic emotions into final schema
    "src.scene_audio_intelligence",  # Phase III-A: Audio & sound design intelligence
    "src.scene_audio_intelligence_merger",  # Merge audio intelligence into final schema
    "src.scene_meta_intelligence",  # Phase VI - Final meta intelligence enrichment
    "src.scene_narrative_structure",  # Phase III-B: Narrative structure analysis
    "src.scene_summarizer",  # Phase VII - Generate signal-based scene summaries
    "src.scene_enrichment",  # Phase VIII - Populate missing fields and add complexity scores
    "src.scene_character_merger",  # Merge character introductions into final JSON
]


def run_module(mod_name: str, movie: str, stop_on_error: bool = False):
    print(f"[STEP] Running {mod_name}")
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        import traceback
        print(f"[WARN] Could not import {mod_name}: {e}")
        print(traceback.format_exc())
        if stop_on_error:
            raise
        return

    # attempt to set MOVIE_NAME if available (best-effort)
    if hasattr(mod, "MOVIE_NAME"):
        try:
            old_movie = getattr(mod, "MOVIE_NAME")
            setattr(mod, "MOVIE_NAME", movie)
            # Update common module-level path constants that were computed at import-time
            # (many modules define e.g. INPUT_JSON = f"outputs/scene_index/{MOVIE_NAME}_..."),
            # so rewrite those strings to refer to the requested movie.
            try:
                if old_movie:
                    for name, val in list(vars(mod).items()):
                        if not isinstance(name, str) or not isinstance(val, str):
                            continue
                        if old_movie in val and name.upper().endswith(("_JSON", "_DIR", "_FILE", "_PATH", "_OUT", "_OUTPUT")):
                            new_val = val.replace(old_movie, movie)
                            setattr(mod, name, new_val)
                            print(f"[INFO] Updated {mod.__name__}.{name} -> {new_val}")
            except Exception:
                # best-effort only; don't crash the pipeline on unexpected module globals
                pass
        except Exception:
            pass
    # best-effort target movie filter modules can honor
    try:
        setattr(mod, "TARGET_MOVIE", movie)
    except Exception:
        pass
    # Propagate global device choice to modules so import-time model inits can use it
    try:
        from src.device import DEVICE as __DEVICE
        setattr(mod, "DEVICE", __DEVICE)
    except Exception:
        pass

    # call main() if present, but do not allow one failing module to stop the whole pipeline
    if hasattr(mod, "main"):
        try:
            mod.main()
        except Exception as e:
            print(f"[ERROR] {mod_name}.main() failed: {e}")
            if stop_on_error:
                raise
    else:
        print(f"[WARN] Module {mod_name} has no main(), skipping")


def find_final_path(movie: str) -> str:
    # prefer the safety-annotated final file
    target = f"outputs/scene_index/{movie}_FINAL_WITH_SAFETY.json"
    if os.path.exists(target):
        return target

    # fallback to emotion-augmented
    alt = f"outputs/scene_index/{movie}_FINAL_WITH_EMOTION.json"
    if os.path.exists(alt):
        return alt

    alt2 = f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_EMOTION.json"
    if os.path.exists(alt2):
        return alt2

    # last resort master
    master = f"outputs/scene_index/{movie}_FINAL.json"
    return master


def find_available_movies():
    """Discover movie ids by scanning `outputs/scenes/` for `<movie>_scenes.json` files."""
    scene_dir = os.path.join(REPO_ROOT, "outputs", "scenes")
    if not os.path.exists(scene_dir):
        return []
    movies = []
    for f in sorted(os.listdir(scene_dir)):
        if f.endswith("_scenes.json"):
            movies.append(f[: -len("_scenes.json")])
    return movies


def clean_movie_outputs(movie: str):
    """Remove per-movie output files and folders to force fresh generation.

    This is conservative and best-effort: it removes common per-movie artifacts
    under `outputs/` so subsequent phase runs will regenerate them.
    """
    removed = []
    repo = REPO_ROOT

    candidates = [
        os.path.join(repo, "outputs", "scenes", f"{movie}_scenes.json"),
        os.path.join(repo, "outputs", "scene_assets", movie),
        os.path.join(repo, "outputs", "scene_dialogue", movie),
        os.path.join(repo, "outputs", "scene_actor_index", f"{movie}_scene_actors.json"),
        os.path.join(repo, "outputs", "scene_visual_index", f"{movie}_scene_visuals.json"),
        os.path.join(repo, "outputs", "scene_object_index", f"{movie}_scene_objects.json"),
        os.path.join(repo, "outputs", "scene_context", f"{movie}_scene_context.json"),
        os.path.join(repo, "outputs", "scene_speakers", movie),
        os.path.join(repo, "outputs", "scene_emotion", movie),
    ]

    # remove any scene_index files that start with the movie prefix
    index_dir = os.path.join(repo, "outputs", "scene_index")
    if os.path.exists(index_dir):
        for fname in os.listdir(index_dir):
            if fname.startswith(f"{movie}_"):
                candidates.append(os.path.join(index_dir, fname))

    for path in candidates:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                removed.append(path)
            elif os.path.exists(path):
                os.remove(path)
                removed.append(path)
        except Exception as e:
            print(f"[WARN] Could not remove {path}: {e}")

    if removed:
        print(f"[INFO] Removed {len(removed)} existing per-movie artifacts for '{movie}'")
    else:
        print(f"[INFO] No existing artifacts found to remove for '{movie}'")


def choose_movie_interactive(movies):
    """Prompt user to choose a movie from `movies` list and return the chosen movie id.

    Exits with code 1 if the user cancels (selects 0).
    """
    print("Available movies:")
    for i, m in enumerate(movies, start=1):
        print(f"  {i}. {m}")

    while True:
        choice = input(f"Select movie [1-{len(movies)}] (or 0 to cancel): ").strip()
        if choice == "0":
            print("Cancelled")
            sys.exit(1)
        try:
            idx = int(choice)
        except ValueError:
            print("Invalid input, enter a number.")
            continue

        if 1 <= idx <= len(movies):
            return movies[idx - 1]
        print("Invalid selection, try again.")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--movie", default=None, help="target movie identifier (optional)")
    parser.add_argument("--list", action="store_true", help="list available movies and exit")
    parser.add_argument("--force", action="store_true", help="remove existing per-movie outputs before run (ensure fresh generation)")
    parser.add_argument("--stop-on-error", action="store_true", help="stop the pipeline when a module fails")
    parser.add_argument("--show-final", action="store_true", help="print final JSON to stdout")
    parser.add_argument("--dump-path", help="write the final JSON to this path (optional)")
    args = parser.parse_args(argv)

    movie = args.movie

    # listing shortcut
    if args.list:
        movies = find_available_movies()
        if not movies:
            print("[INFO] No movies found in outputs/scenes/")
            return
        print("Available movies:")
        for m in movies:
            print(f" - {m}")
        return

    # interactive selection when --movie omitted
    if not movie:
        movies = find_available_movies()
        if not movies:
            print("[ERROR] --movie is required. Example: --movie 'Ravi_teja'")
            parser.print_help()
            sys.exit(2)
        movie = choose_movie_interactive(movies)

    # Run conservative subset of steps in defined order. Some modules may be
    # no-ops depending on existing outputs; this preserves core behavior.
    if args.force:
        clean_movie_outputs(movie)

    timings = []
    for mod in STEPS:
        start = time.perf_counter()
        try:
            run_module(mod, movie)
        except Exception as e:
            duration = time.perf_counter() - start
            timings.append((mod, duration, False))
            print(f"[ERROR] Module {mod} failed: {e}")
            raise
        else:
            duration = time.perf_counter() - start
            timings.append((mod, duration, True))
            print(f"[TIMING] {mod} finished in {format_duration(duration)}")

    # Summary
    print("\n[SUMMARY] Step timings:")
    total = 0.0
    for name, dur, ok in timings:
        total += dur
        status = "OK" if ok else "FAIL"
        print(f" - {name}: {format_duration(dur)} ({status})")
    print(f"[SUMMARY] Total time: {format_duration(total)}\n")

    final_path = find_final_path(movie)

    if not os.path.exists(final_path):
        print(f"[ERROR] Expected final JSON not found: {final_path}")
        sys.exit(2)

    print(f"[OK] Final scene JSON available at: {final_path}")

    with open(final_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[INFO] Scenes: {len(data)}")

    if args.dump_path:
        with open(args.dump_path, "w", encoding="utf-8") as o:
            json.dump(data, o, indent=2, ensure_ascii=False)
        print(f"[OK] Final JSON written to {args.dump_path}")

    if args.show_final:
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
