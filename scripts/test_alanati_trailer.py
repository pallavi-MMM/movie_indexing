#!/usr/bin/env python3
"""Test pipeline on the local Alanati ramachandrudu trailer video.

This script:
1. Extracts basic frame info from the video (mock)
2. Processes it through safety → visual quality → VLM summarizer → fusion
3. Outputs a canonical scene JSON with confidences and provenance
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.run_local_pipeline import run_scene_pipeline


def main():
    """Test pipeline on the Alanati ramachandrudu trailer."""
    
    video_path = Path("movies/Alanati ramachandrudu - trailer.mp4")
    if not video_path.exists():
        print(f"ERROR: Video not found at {video_path}")
        return
    
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    
    # Create a scene dict for the trailer
    scene = {
        "scene_id": "alanati_trailer_001",
        "movie_id": "Alanati_Ramachandrudu",
        "title_name": "Alanati Ramachandrudu - Trailer",
        "video_path": str(video_path),
        "duration": 120.0,  # estimated ~2 min trailer
        "location": "Various",
        "scene_type": "Trailer",
    }
    
    print("=" * 70)
    print("TESTING PIPELINE: Alanati Ramachandrudu Trailer")
    print("=" * 70)
    print(f"\nVideo Details:")
    print(f"  Path: {video_path}")
    print(f"  Size: {file_size_mb:.1f} MB")
    print(f"  Duration (est): {scene['duration']:.0f} seconds")
    print(f"\nScene Input:")
    print(f"  Scene ID: {scene['scene_id']}")
    print(f"  Movie ID: {scene['movie_id']}")
    print(f"  Title: {scene['title_name']}")
    
    print(f"\nRunning pipeline stages...")
    print(f"  1. Safety analysis...")
    print(f"  2. Visual quality analysis...")
    print(f"  3. VLM summarizer...")
    print(f"  4. Fusion into canonical scene...")
    
    result = run_scene_pipeline(scene)
    
    print(f"\n✓ Pipeline complete!\n")
    print("=" * 70)
    print("CANONICAL SCENE OUTPUT")
    print("=" * 70)
    
    # Pretty print key fields
    print(f"\nIdentifiers:")
    print(f"  Scene ID: {result.get('scene_id')}")
    print(f"  Movie ID: {result.get('movie_id')}")
    print(f"  Title: {result.get('title_name')}")
    
    print(f"\nSafety Analysis:")
    safety_flags = result.get('safety_flags', {})
    for flag, value in safety_flags.items():
        print(f"  {flag}: {value}")
    
    print(f"\nQuality Analysis:")
    quality_flags = result.get('quality_flags', {})
    for flag, value in quality_flags.items():
        print(f"  {flag}: {value}")
    
    print(f"\nVLM Summary:")
    print(f"  Summary: {result.get('scene_summary', 'N/A')}")
    print(f"  Keywords: {result.get('keywords_auto_generated', [])}")
    
    print(f"\nCharacters Detected:")
    characters = result.get('characters', [])
    if characters:
        for char in characters:
            name = char.get('name', 'Unknown')
            screen_time = char.get('screen_time', 0.0)
            confidence = char.get('confidence', 0.0)
            print(f"  - {name}: screen_time={screen_time:.1f}s, confidence={confidence:.2f}")
    else:
        print(f"  (None detected)")
    
    print(f"\nField Confidences:")
    confs = result.get('field_confidences', {})
    for field, confidence in sorted(confs.items())[:10]:
        print(f"  {field}: {confidence}")
    if len(confs) > 10:
        print(f"  ... and {len(confs) - 10} more fields")
    
    print(f"\nField Provenance Summary:")
    prov = result.get('field_provenance', {})
    provenance_sources = set()
    for field, sources in prov.items():
        for src in sources:
            provenance_sources.add(src)
    print(f"  Data sources: {', '.join(sorted(provenance_sources))}")
    
    # Save full output
    output_file = Path("alanati_trailer_output.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 70}")
    print(f"✓ Full output saved to: {output_file}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
