#!/usr/bin/env python3
"""
Run all movies in the movies/ folder at once

Usage:
    python run_all_movies.py
    python run_all_movies.py --force  (regenerate all)
"""

import os
import subprocess
import sys
import json
from pathlib import Path


def find_all_movies():
    """Find all MP4 files in movies/ folder."""
    movies_dir = Path("movies")
    if not movies_dir.exists():
        print(f"[ERROR] movies/ folder not found")
        return []
    
    mp4_files = sorted(movies_dir.glob("*.mp4"))
    movie_names = [f.stem for f in mp4_files]
    
    return movie_names


def run_movie(movie_name, force=False):
    """Process a single movie."""
    cmd = [sys.executable, "src/run_pipeline.py", "--movie", movie_name]
    if force:
        cmd.append("--force")
    
    print(f"\n{'='*80}")
    print(f"Processing: {movie_name}")
    print(f"{'='*80}")
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def get_scene_count(movie_name):
    """Get scene count from output JSON."""
    output_file = f"output_json/{movie_name}_complete_schema.json"
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
            return len(data.get('scenes', []))
    except:
        return 0


def main():
    """Process all movies."""
    force = "--force" in sys.argv
    
    # Find movies
    movies = find_all_movies()
    
    if not movies:
        print("[ERROR] No MP4 files found in movies/")
        print("[INFO] Add your movies to movies/ folder first")
        sys.exit(1)
    
    print("\n" + "="*80)
    print(f"PROCESSING {len(movies)} MOVIE(S)")
    print("="*80)
    print(f"Movies found: {', '.join(movies)}")
    print("="*80)
    
    # Process each movie
    results = {}
    for i, movie in enumerate(movies, 1):
        print(f"\n[{i}/{len(movies)}] ", end="")
        
        success = run_movie(movie, force=force)
        
        if success:
            scenes = get_scene_count(movie)
            results[movie] = {'status': 'OK', 'scenes': scenes}
            print(f"✓ {movie}: {scenes} scenes")
        else:
            results[movie] = {'status': 'FAILED'}
            print(f"✗ {movie}: FAILED")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for movie, result in results.items():
        if result['status'] == 'OK':
            print(f"✓ {movie:30} {result['scenes']:4} scenes")
        else:
            print(f"✗ {movie:30} FAILED")
    
    successful = sum(1 for r in results.values() if r['status'] == 'OK')
    total = len(results)
    
    print(f"\nCompleted: {successful}/{total} movies")
    print(f"Output: output_json/")
    print("="*80 + "\n")
    
    return 0 if successful == total else 1


if __name__ == "__main__":
    sys.exit(main())
