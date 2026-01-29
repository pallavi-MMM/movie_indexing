#!/usr/bin/env python3
"""Quick example: run the local lightweight pipeline on a single scene JSON.

Usage:
    python scripts/run_scene_example.py

This demonstrates the new mock-first, production-ready local pipeline
that doesn't require heavy ML dependencies.
"""

import json
import tempfile
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.run_local_pipeline import run_scene_pipeline


def main():
    """Run a simple example scene through the pipeline."""

    # Create a sample scene
    scene = {
        "scene_id": "example_scene_001",
        "movie_id": "EXAMPLE_MOVIE",
        "title_name": "Opening Scene",
        "dialogue_text": [
            {"character": "Alice", "line": "Welcome!"},
            {"character": "Bob", "line": "Great to be here!"},
        ],
        "objects": [
            {"type": "laptop", "color": "silver"},
            {"type": "desk", "color": "oak"},
        ],
        "emotions": ["excited", "welcoming"],
        "location": "Home office",
    }

    print("=" * 60)
    print("EXAMPLE: Local Pipeline (Mock-First, Production-Ready)")
    print("=" * 60)
    print(f"\nInput scene: {scene['scene_id']} ({scene['movie_id']})")
    print(f"  Dialogue lines: {len(scene['dialogue_text'])}")
    print(f"  Objects: {len(scene['objects'])}")
    print(f"  Location: {scene.get('location')}\n")

    # Run the pipeline
    print("Running pipeline stages...")
    print("  1. Safety analysis...")
    print("  2. Visual quality analysis...")
    print("  3. VLM summarizer...")
    print("  4. Fusion into canonical scene...")

    result = run_scene_pipeline(scene)

    print("\nPipeline complete!\n")
    print("=" * 60)
    print("OUTPUT SCENE (Canonical JSON)")
    print("=" * 60)
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("KEY OUTPUTS")
    print("=" * 60)
    print(f"✓ Scene ID: {result['scene_id']}")
    print(f"✓ Movie ID: {result['movie_id']}")
    print(f"✓ Scene Summary: {result.get('scene_summary', 'N/A')[:100]}...")
    print(f"✓ Keywords: {result.get('keywords_auto_generated', [])}")
    print(f"✓ Safety Flags: {result.get('safety_flags', {})}")
    print(f"✓ Quality Flags: {result.get('quality_flags', {})}")
    print(f"✓ Field Confidences Present: {'field_confidences' in result}")
    print(f"✓ Field Provenance Present: {'field_provenance' in result}")

    # Save example output
    output_path = Path("example_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull output saved to: {output_path}")


if __name__ == "__main__":
    main()
