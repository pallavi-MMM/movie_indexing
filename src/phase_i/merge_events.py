"""
Character Introductions Event JSON

Organizes character introductions with timestamps and metadata.
"""

import json
import os
from typing import Dict, List, Any


def process_character_json(movie_name: str):
    """Process character introductions JSON."""
    
    char_intro_path = f"movie_event_json/{movie_name}_character_introductions.json"
    
    if not os.path.exists(char_intro_path):
        print(f"[ERROR] File not found: {char_intro_path}")
        return
    
    with open(char_intro_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Save structured output
    output_path = f"movie_event_json/{movie_name}_complete_events.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Processed {output_path}")
    print(f"  Characters: {len(data.get('character_introductions', []))}")
    
    return output_path


def _create_integrated_timeline(characters: List[Dict]) -> List[Dict]:
    """Create timeline of character introduction events."""
    events = []
    
    # Add character events
    for char in characters:
        events.append({
            "event_type": "character_introduction",
            "timestamp": char.get("introduction_time_seconds", 0),
            "character_name": char.get("character_name"),
            "scene_id": char.get("scene_id"),
            "confidence": char.get("appearance_confidence", 0)
        })
    
    # Sort by timestamp
    events.sort(key=lambda x: x.get("timestamp", 0))
    
    return events


def main():
    import glob
    
    print("\n" + "="*100)
    print("[PROCESSING] Character Introductions")
    print("="*100 + "\n")
    
    # Process all movies
    char_intro_files = glob.glob("movie_event_json/*_character_introductions.json")
    
    if not char_intro_files:
        print("[ERROR] No character introduction files found")
        return
    
    for char_file in char_intro_files:
        movie_name = os.path.basename(char_file).replace("_character_introductions.json", "")
        print(f"Processing: {movie_name}")
        
        try:
            process_character_json(movie_name)
        except Exception as e:
            print(f"[ERROR] Error processing {movie_name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
