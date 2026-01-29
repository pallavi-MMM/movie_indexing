"""
Scene Character Merger

Merges character introductions from movie_event_json into the final complete schema.
Adds character data to the end of the movie output JSON without creating separate files.
"""

import json
import os
import glob
from typing import Dict, List, Any


# set `TARGET_MOVIE` or `MOVIE_NAME` on imported modules before calling `main()`.
# If neither is present, we try to infer a single available movie from `output_json`.
MOVIE_NAME = None


def get_target_movie() -> str:
    """Resolve the target movie name.

    Resolution order:
    1. `TARGET_MOVIE` global (set by `run_pipeline` when importing modules)
    2. `MOVIE_NAME` global (if pre-set elsewhere)
    3. Environment variables `TARGET_MOVIE` or `MOVIE_NAME`
    4. If there is exactly one file in `output_json/*_complete_schema.json`, infer that movie
    5. Otherwise return None (caller should handle)
    """
    # Best-effort from module globals (run_pipeline sets TARGET_MOVIE)
    movie = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME") or os.environ.get("TARGET_MOVIE") or os.environ.get("MOVIE_NAME")
    if movie:
        return movie

    # Try to infer from existing output JSON files if there is exactly one candidate
    candidates = [os.path.basename(p).replace("_complete_schema.json", "") for p in glob.glob("output_json/*_complete_schema.json")]
    if len(candidates) == 1:
        print(f"[INFO] No target movie provided; inferring movie='{candidates[0]}' from output_json")
        return candidates[0]

    return None

def load_character_introductions(movie: str) -> Dict[str, Any]:
    """
    Load character introductions from movie_event_json folder.
    Looks for {movie}_character_introductions.json or {movie}-movie_character_introductions.json
    """
    # Try exact match first
    paths_to_try = [
        f"movie_event_json/{movie}_character_introductions.json",
        f"movie_event_json/{movie}-movie_character_introductions.json",
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load {path}: {e}")
                return None
    
    # Fallback: search for any matching file
    pattern = f"movie_event_json/*{movie}*character_introductions.json"
    matches = glob.glob(pattern)
    if matches:
        try:
            with open(matches[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load {matches[0]}: {e}")
    
    return None

def load_complete_schema(movie: str) -> Dict[str, Any]:
    """Load the complete schema JSON from output_json."""
    output_path = f"output_json/{movie}_complete_schema.json"
    
    if not os.path.exists(output_path):
        print(f"[WARN] Complete schema not found: {output_path}")
        return None
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {output_path}: {e}")
        return None

def merge_character_data(complete_schema: Dict, char_intro_data: Dict) -> Dict:
    """
    Merge character introductions into the complete schema.
    Adds character data at the end of the JSON structure.
    """
    if not complete_schema or not char_intro_data:
        return complete_schema
    
    character_intros = char_intro_data.get('character_introductions', [])
    
    # Extract character info and build appearances map
    appearances = {}
    char_names = set()
    
    for intro in character_intros:
        char_name = intro.get('character_name', '').lower()
        scene_id = intro.get('scene_id', '')
        
        if char_name and scene_id:
            char_names.add(char_name)
            if char_name not in appearances:
                appearances[char_name] = []
            if scene_id not in appearances[char_name]:
                appearances[char_name].append(scene_id)
    
    # Update metadata
    if 'metadata' not in complete_schema:
        complete_schema['metadata'] = {}
    
    complete_schema['metadata']['total_character_introductions'] = len(character_intros)
    complete_schema['metadata']['total_unique_characters'] = len(char_names)
    
    # Add/update characters section at the end
    complete_schema['characters'] = {
        'introductions': character_intros,
        'appearances': appearances,
        'summary': {
            'total_unique': len(char_names),
            'total_introductions': len(character_intros),
            'total_appearances': sum(len(scenes) for scenes in appearances.values())
        }
    }
    
    return complete_schema

def save_complete_schema(movie: str, data: Dict) -> None:
    """Save the merged complete schema back to output_json."""
    output_path = f"output_json/{movie}_complete_schema.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Merged character data into {output_path}")
        # Guard access to metadata in case it is missing (some code paths save without metadata)
        meta = data.get('metadata') or {}
        print(f"     Characters: {meta.get('total_character_introductions', 0)}")
    except Exception as e:
        print(f"[ERROR] Failed to save {output_path}: {e}")

def main():
    """Main entry point for the module."""
    movie = MOVIE_NAME
    
    print(f"[INFO] Merging character introductions for {movie}...")
    
    # Load complete schema
    complete_schema = load_complete_schema(movie)
    if not complete_schema:
        print(f"[WARN] Could not load complete schema, skipping character merge")
        return
    
    # Load character introductions
    char_intro_data = load_character_introductions(movie)
    if not char_intro_data:
        print(f"[WARN] No character introductions found for {movie}")
        # Still save the schema even if no character data
        save_complete_schema(movie, complete_schema)
        return
    
    # Merge character data into schema
    complete_schema = merge_character_data(complete_schema, char_intro_data)
    
    # Save merged schema
    save_complete_schema(movie, complete_schema)

if __name__ == "__main__":
    main()
