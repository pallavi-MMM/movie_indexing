"""
Character Introduction Detection Pipeline

This module detects when characters are first introduced in a movie by analyzing:
1. Scene-level character appearance data
2. Actor detection outputs
3. Timeline tracking
"""

import json
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import timedelta


@dataclass
class CharacterIntroduction:
    """Represents a character's first appearance in the movie."""

    character_id: str
    character_name: str
    introduction_time_seconds: float
    introduction_time_formatted: str
    scene_id: str
    scene_index: int
    appearance_confidence: float
    first_scene_duration: float
    description: str = ""
    visual_features: Dict[str, Any] = None

    def __post_init__(self):
        if self.visual_features is None:
            self.visual_features = {}


class CharacterIntroductionDetector:
    """Detects character introductions from scene data and actor information."""

    def __init__(
        self,
        movie_name: str,
        scenes_data: Dict[str, Any],
        actors_data: Dict[str, Any] = None,
    ):
        """
        Initialize the detector.

        Args:
            movie_name: Name of the movie
            scenes_data: Complete scene data with timeline information
            actors_data: Complete actor/character data if available
        """
        self.movie_name = movie_name
        self.scenes_data = scenes_data
        self.actors_data = actors_data or {}
        self.character_introductions = []
        self.character_first_appearance = {}  # Track first scene for each character

    def detect_introductions(self) -> List[CharacterIntroduction]:
        """
        Detect character introductions across all scenes.

        Returns:
            List of CharacterIntroduction objects sorted by time
        """
        print("[DETECTING] Detecting character introductions...")

        scenes = self.scenes_data.get("scenes", [])
        if not scenes:
            print("  ⚠️  No scenes found in scene data")
            return []

        # First pass: collect all character appearances and track first occurrence
        character_timeline = {}  # character_id -> list of (scene_index, scene_id, time)
        character_name_map = {}  # character_id -> preferred character_name

        for scene_idx, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", f"scene_{scene_idx:04d}")
            start_time = self._parse_time(scene.get("start_time", 0))
            duration = self._parse_time(scene.get("duration", 0))

            # Extract characters from this scene
            characters = self._extract_scene_characters(scene, scene_idx)

            for char_info in characters:
                char_id = char_info["character_id"]
                char_name = char_info["character_name"]
                confidence = char_info.get("confidence", 0.8)

                # Store preferred character name (first one we see)
                if char_id not in character_name_map:
                    character_name_map[char_id] = char_name

                if char_id not in character_timeline:
                    character_timeline[char_id] = []

                character_timeline[char_id].append(
                    {
                        "scene_index": scene_idx,
                        "scene_id": scene_id,
                        "start_time": start_time,
                        "duration": duration,
                        "character_name": char_name,
                        "confidence": confidence,
                        "screen_time": char_info.get("screen_time", duration),
                    }
                )

        # Second pass: create introduction records for first appearance of each character
        for char_id, appearances in character_timeline.items():
            if not appearances:
                continue

            # Sort by scene index to get first appearance
            appearances.sort(key=lambda x: x["scene_index"])
            first = appearances[0]

            # Use the stored character name to ensure consistency
            char_name = character_name_map.get(char_id, first["character_name"])

            introduction = CharacterIntroduction(
                character_id=char_id,
                character_name=char_name,
                introduction_time_seconds=first["start_time"],
                introduction_time_formatted=self._format_time(first["start_time"]),
                scene_id=first["scene_id"],
                scene_index=first["scene_index"],
                appearance_confidence=first["confidence"],
                first_scene_duration=first["duration"],
                description=f"First appearance in {first['scene_id']}",
            )

            self.character_introductions.append(introduction)
            self.character_first_appearance[char_id] = {
                "character_name": char_name,
                "introduction_time": first["start_time"],
                "scene_id": first["scene_id"],
            }

        # Sort by introduction time
        self.character_introductions.sort(key=lambda x: x.introduction_time_seconds)

        print(
            f"✓ Detected {len(self.character_introductions)} unique character introductions\n"
        )

        return self.character_introductions

    def _extract_scene_characters(
        self, scene: Dict[str, Any], scene_idx: int
    ) -> List[Dict[str, Any]]:
        """
        Extract character information from a scene.

        Args:
            scene: Scene dictionary
            scene_idx: Index of the scene

        Returns:
            List of character info dicts
        """
        characters = []
        seen_char_ids = set()  # Track already added characters

        # Check multiple possible sources of character data

        # Source 1: Direct characters field
        if "characters" in scene and isinstance(scene["characters"], list):
            for char in scene["characters"]:
                if isinstance(char, dict):
                    char_id = char.get("id", char.get("character_id"))
                    if not char_id:
                        # Generate ID from character name
                        char_name = char.get(
                            "name",
                            char.get("character_name", f"Character {len(characters)}"),
                        )
                        char_id = f"char_{char_name.lower().replace(' ', '_')}"

                    # Skip duplicates
                    if char_id in seen_char_ids:
                        continue
                    seen_char_ids.add(char_id)

                    characters.append(
                        {
                            "character_id": char_id,
                            "character_name": char.get(
                                "name",
                                char.get(
                                    "character_name", f"Character {len(characters)}"
                                ),
                            ),
                            "confidence": char.get("confidence", 0.8),
                            "screen_time": scene.get("duration", 0),
                            "role": char.get("role", "supporting"),
                        }
                    )
                elif isinstance(char, str):
                    char_id = f"char_{char.lower().replace(' ', '_')}"

                    # Skip duplicates
                    if char_id in seen_char_ids:
                        continue
                    seen_char_ids.add(char_id)

                    characters.append(
                        {
                            "character_id": char_id,
                            "character_name": char,
                            "confidence": 0.9,
                            "screen_time": scene.get("duration", 0),
                            "role": "unknown",
                        }
                    )

        # Source 2: actors field (sometimes used for character data)
        if "actors" in scene and isinstance(scene["actors"], list):
            for actor in scene["actors"]:
                if isinstance(actor, dict):
                    char_id = actor.get("character_id", actor.get("id"))
                    if not char_id:
                        char_name = actor.get(
                            "character_name",
                            actor.get("name", f"Character {len(characters)}"),
                        )
                        char_id = f"char_{char_name.lower().replace(' ', '_')}"

                    # Skip if we already have this character
                    if char_id in seen_char_ids:
                        continue
                    seen_char_ids.add(char_id)

                    characters.append(
                        {
                            "character_id": char_id,
                            "character_name": actor.get(
                                "character_name",
                                actor.get("name", f"Character {len(characters)}"),
                            ),
                            "confidence": actor.get("confidence", 0.8),
                            "screen_time": scene.get("duration", 0),
                            "role": actor.get("role", "unknown"),
                        }
                    )

        # Source 3: speaker/dialogue analysis
        if "dialogue" in scene and isinstance(scene["dialogue"], list):
            speakers = set()
            for dialogue in scene["dialogue"]:
                if isinstance(dialogue, dict) and "speaker" in dialogue:
                    speakers.add(dialogue["speaker"])

            for speaker in speakers:
                char_id = f"char_{speaker.lower().replace(' ', '_')}"

                # Skip if we already have this character
                if char_id in seen_char_ids:
                    continue
                seen_char_ids.add(char_id)

                characters.append(
                    {
                        "character_id": char_id,
                        "character_name": speaker,
                        "confidence": 0.7,  # Lower confidence for dialogue-only detection
                        "screen_time": scene.get("duration", 0),
                        "role": "speaker",
                    }
                )

        return characters

    def generate_output_json(self) -> Dict[str, Any]:
        """
        Generate complete JSON output for character introductions.

        Returns:
            Dictionary with character introduction data
        """
        output = {
            "metadata": {
                "pipeline_version": "1.0",
                "detector_type": "character_introduction",
                "movie_name": self.movie_name,
                "total_characters": len(self.character_introductions),
                "total_movie_duration_seconds": self._get_total_duration(),
            },
            "character_introductions": [
                asdict(intro) for intro in self.character_introductions
            ],
            "introduction_timeline": self._build_timeline(),
            "character_map": self.character_first_appearance,
            "statistics": self._calculate_statistics(),
        }

        return output

    def _build_timeline(self) -> Dict[str, Any]:
        """Build a chronological timeline of introductions."""
        timeline = {}

        for intro in self.character_introductions:
            time_key = self._format_time(intro.introduction_time_seconds)
            if time_key not in timeline:
                timeline[time_key] = []

            timeline[time_key].append(
                {
                    "character_id": intro.character_id,
                    "character_name": intro.character_name,
                    "scene_id": intro.scene_id,
                    "confidence": intro.appearance_confidence,
                }
            )

        return timeline

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics about character introductions."""
        if not self.character_introductions:
            return {
                "total_introductions": 0,
                "avg_introduction_time": 0,
                "earliest_introduction_time": None,
                "latest_introduction_time": None,
            }

        times = [
            intro.introduction_time_seconds for intro in self.character_introductions
        ]

        return {
            "total_introductions": len(self.character_introductions),
            "avg_introduction_time_seconds": sum(times) / len(times),
            "avg_introduction_time_formatted": self._format_time(
                sum(times) / len(times)
            ),
            "earliest_introduction_time_seconds": min(times),
            "earliest_introduction_time_formatted": self._format_time(min(times)),
            "latest_introduction_time_seconds": max(times),
            "latest_introduction_time_formatted": self._format_time(max(times)),
        }

    def _get_total_duration(self) -> float:
        """Get total movie duration from scenes."""
        scenes = self.scenes_data.get("scenes", [])
        if not scenes:
            return 0.0

        last_scene = scenes[-1]
        end_time = last_scene.get("end_time", 0)
        if end_time:
            end_time = self._parse_time(end_time)

        if end_time:
            return end_time

        start_time = self._parse_time(last_scene.get("start_time", 0))
        duration = self._parse_time(last_scene.get("duration", 0))
        return start_time + duration

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to HH:MM:SS.mmm format."""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _parse_time(time_value: Any) -> float:
        """Parse time from various formats to seconds."""
        if isinstance(time_value, (int, float)):
            return float(time_value)

        if isinstance(time_value, str):
            # Try HH:MM:SS.mmm format
            if ":" in time_value:
                parts = time_value.split(":")
                hours = int(parts[0])
                minutes = int(parts[1])
                secs = float(parts[2])
                return hours * 3600 + minutes * 60 + secs

            # Try to parse as float string
            try:
                return float(time_value)
            except ValueError:
                return 0.0

        return 0.0

    def print_summary(self):
        """Print a summary of detected introductions."""
        print("\n" + "=" * 100)
        print("[SUMMARY] CHARACTER INTRODUCTION SUMMARY")
        print("=" * 100)

        print(f"\nMovie: {self.movie_name}")
        print(f"Total Characters Introduced: {len(self.character_introductions)}")
        print(f"Movie Duration: {self._format_time(self._get_total_duration())}")

        if not self.character_introductions:
            print("\n⚠️  No character introductions detected")
            return

        print("\n" + "─" * 100)
        print("INTRODUCTION TIMELINE (First 15 characters):")
        print("─" * 100)

        for idx, intro in enumerate(self.character_introductions[:15], 1):
            print(f"\n{idx}. {intro.character_name}")
            print(f"   Time: {intro.introduction_time_formatted}")
            print(f"   Scene: {intro.scene_id}")
            print(f"   Confidence: {intro.appearance_confidence:.2f}")
            print(f"   Scene Duration: {intro.first_scene_duration:.1f}s")

        if len(self.character_introductions) > 15:
            print(f"\n... and {len(self.character_introductions) - 15} more characters")

        print("\n" + "=" * 100)


class CharacterIntroductionPipeline:
    """Main pipeline for character introduction detection."""

    def __init__(self):
        self.output_dir = "movie_event_json"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(
        self, movie_name: str, scene_file: str = None, actor_file: str = None
    ) -> str:
        """
        Run the character introduction detection pipeline.

        Args:
            movie_name: Name of the movie
            scene_file: Path to scene JSON file (auto-detected if None)
            actor_file: Path to actor/character JSON file (optional)

        Returns:
            Path to output JSON file
        """
        print("\n" + "=" * 100)
        print("[PIPELINE] CHARACTER INTRODUCTION DETECTION PIPELINE")
        print("=" * 100)
        print(f"Movie: {movie_name}\n")

        # Auto-detect scene file if not provided
        if scene_file is None:
            scene_file = self._find_scene_file(movie_name)

        if not os.path.exists(scene_file):
            raise FileNotFoundError(f"Scene file not found: {scene_file}")

        print(f"📂 Loading scene data from: {scene_file}")
        with open(scene_file, "r", encoding="utf-8") as f:
            scenes_data = json.load(f)

        # Load actor data if available
        actors_data = None
        if actor_file and os.path.exists(actor_file):
            print(f"📂 Loading actor data from: {actor_file}")
            with open(actor_file, "r", encoding="utf-8") as f:
                actors_data = json.load(f)

        # Run detection
        detector = CharacterIntroductionDetector(movie_name, scenes_data, actors_data)
        detector.detect_introductions()

        # Generate output
        output_data = detector.generate_output_json()

        # Save output
        output_path = os.path.join(
            self.output_dir, f"{movie_name}_character_introductions.json"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Character introduction data saved to: {output_path}")

        # Print summary
        detector.print_summary()

        return output_path

    def _find_scene_file(self, movie_name: str) -> str:
        """Auto-detect scene file path."""
        possible_paths = [
            f"output_json/{movie_name}_complete_schema.json",
            f"outputs/scene_index/{movie_name}_scenes_final.json",
            f"outputs/movie_events/{movie_name}_events.json",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(f"Could not find scene file for movie: {movie_name}")


# ============================================================================
# ENTRY POINT
# ============================================================================


def main():
    # Example usage with different movies
    pipeline = CharacterIntroductionPipeline()

    # Auto-detect and process first available movie from output_json
    import glob

    schema_files = glob.glob("output_json/*_complete_schema.json")
    if not schema_files:
        print("[ERROR] No complete schema files found in output_json/")
        return

    for schema_file in schema_files:
        movie_name = os.path.basename(schema_file).replace("_complete_schema.json", "")
        print(f"\nProcessing: {movie_name}")

        try:
            pipeline.run(movie_name, schema_file)
        except Exception as e:
            print(f"[ERROR] Error processing {movie_name}: {e}")


if __name__ == "__main__":
    main()
