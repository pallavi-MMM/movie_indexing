"""
Semantic emotion analyzer: Combines dialogue sentiment + audio arousal to generate:
- emotions (semantic labels like "tense", "calm", "happy", etc.)
- viewer_emotion_prediction (predicted viewer response)
- laugh_moment_flag (positive sentiment + high tempo)
- shock_moment_flag (sudden loud spike + fear keywords)
- climax_point_flag (highest motion + emotion in timeline)
"""

import os
import json
import re
from collections import defaultdict

SCENE_INDEX_DIR = "outputs/scene_index"
SCENE_DIALOGUE_DIR = "outputs/scene_dialogue"
SCENE_EMOTION_DIR = "outputs/scene_emotion"
OUTPUT_DIR = "outputs/scene_emotion"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# Sentiment Analysis
# ============================================================================

POSITIVE_KEYWORDS = {
    'love', 'happy', 'great', 'wonderful', 'amazing', 'excellent', 'good',
    'perfect', 'beautiful', 'awesome', 'fantastic', 'brilliant', 'superb',
    'delighted', 'joyful', 'pleased', 'glad', 'excited', 'wonderful',
    'thank', 'thanks', 'victory', 'win', 'success', 'celebrate'
}

NEGATIVE_KEYWORDS = {
    'hate', 'sad', 'angry', 'terrible', 'horrible', 'awful', 'bad',
    'worst', 'evil', 'death', 'die', 'kill', 'destroy', 'pain',
    'fear', 'scared', 'afraid', 'danger', 'crisis', 'attack', 'war',
    'tragic', 'heartbreak', 'loss', 'fail', 'defeat', 'suffer'
}

FEAR_KEYWORDS = {
    'fear', 'scared', 'afraid', 'terror', 'horror', 'scream', 'danger',
    'threat', 'attack', 'monster', 'ghost', 'evil', 'death', 'kill'
}

def analyze_sentiment(text):
    """
    Simple sentiment analysis from text.
    Returns: score in [-1, 1] where -1 is most negative, +1 is most positive
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Count keyword occurrences
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    
    # Simple scoring
    if positive_count + negative_count == 0:
        return 0.0
    
    score = (positive_count - negative_count) / (positive_count + negative_count)
    return max(-1.0, min(1.0, score))

def has_fear_keywords(text):
    """Check if text contains fear-related keywords"""
    if not text:
        return False
    text_lower = text.lower()
    return any(word in text_lower for word in FEAR_KEYWORDS)

# ============================================================================
# Emotion Mapping
# ============================================================================

def map_arousal_to_tempo(arousal_score):
    """Map arousal score (0-1) to tempo classification"""
    if arousal_score < 0.3:
        return "slow"
    elif arousal_score < 0.6:
        return "moderate"
    else:
        return "high"

def combine_sentiment_arousal(sentiment, arousal):
    """
    Combine dialogue sentiment + audio arousal to generate semantic emotion.
    
    sentiment: [-1, 1]
    arousal: [0, 1]
    """
    emotions = []
    
    # High arousal rules
    if arousal > 0.6:
        if sentiment < -0.3:
            emotions.append("tense")
        elif sentiment > 0.3:
            emotions.append("energetic")
        else:
            emotions.append("intense")
    
    # Low arousal rules
    elif arousal < 0.3:
        if sentiment < -0.3:
            emotions.append("sad")
        elif sentiment > 0.3:
            emotions.append("calm")
        else:
            emotions.append("neutral")
    
    # Moderate arousal
    else:
        if sentiment < -0.5:
            emotions.append("angry")
        elif sentiment < -0.2:
            emotions.append("worried")
        elif sentiment > 0.5:
            emotions.append("happy")
        elif sentiment > 0.2:
            emotions.append("content")
        else:
            emotions.append("neutral")
    
    return emotions

def map_to_viewer_emotion(scene_emotions, sentiment, arousal):
    """
    Map detected scene emotions to predicted viewer responses.
    
    scene_emotions: ["tense", "sad", etc.]
    Returns: viewer emotion prediction
    """
    viewer_mapping = {
        "tense": "anxiety",
        "angry": "frustration",
        "sad": "empathy",
        "worried": "concern",
        "calm": "relaxation",
        "happy": "joy",
        "content": "satisfaction",
        "energetic": "excitement",
        "intense": "engagement",
        "neutral": "neutrality"
    }
    
    # Map first emotion (primary emotion)
    if scene_emotions:
        primary = scene_emotions[0]
        return viewer_mapping.get(primary, "engagement")
    
    return "neutrality"

def detect_laugh_moment(sentiment, arousal, dialogue_text):
    """
    Detect laugh moments: positive sentiment + high tempo + humorous indicators
    """
    has_positive = sentiment > 0.3
    has_high_tempo = arousal > 0.6
    has_humor = any(word in (dialogue_text or "").lower() 
                   for word in ['laugh', 'joke', 'funny', 'haha', 'lol'])
    
    return has_positive and has_high_tempo and has_humor

def detect_shock_moment(dialogue_text, arousal, motion_data=None):
    """
    Detect shock moments: fear keywords + sudden changes
    
    motion_data can be: {"motion_intensity_score": 0.8}
    """
    has_fear = has_fear_keywords(dialogue_text)
    high_arousal_spike = arousal > 0.7
    
    # Check for motion spike if available
    motion_spike = False
    if motion_data and isinstance(motion_data, dict):
        motion_score = motion_data.get('motion_intensity_score', 0)
        motion_spike = motion_score > 0.7
    
    return has_fear and (high_arousal_spike or motion_spike)

# ============================================================================
# Climax Detection (Global Analysis)
# ============================================================================

def detect_climax_points(all_scenes_data, movie_name):
    """
    Detect climax points: highest combined emotion + motion across entire movie.
    
    Returns dict: {scene_id: True/False}
    """
    climax_map = {}
    
    if not all_scenes_data:
        return climax_map
    
    # Calculate overall intensity for each scene
    intensities = []
    
    for scene_idx, scene_data in enumerate(all_scenes_data):
        scene_id = scene_data.get('scene_id', f'scene_{scene_idx:04d}')
        
        # Get arousal score
        arousal = scene_data.get('arousal_score', 0)
        
        # Get motion intensity
        visual_data = scene_data.get('visual_data', {})
        motion = visual_data.get('motion_intensity_score', 0)
        
        # Calculate combined intensity
        intensity = (arousal + motion) / 2
        intensities.append((scene_id, intensity))
    
    if not intensities:
        return climax_map
    
    # Find top 10% of scenes by intensity
    sorted_by_intensity = sorted(intensities, key=lambda x: x[1], reverse=True)
    threshold_idx = max(1, len(sorted_by_intensity) // 10)  # Top 10%
    climax_threshold = sorted_by_intensity[threshold_idx][1]
    
    # Mark climax scenes
    for scene_id, intensity in intensities:
        climax_map[scene_id] = intensity >= climax_threshold
    
    return climax_map

# ============================================================================
# Main Processing
# ============================================================================

def load_dialogue_for_scene(movie_name, scene_id):
    """Load dialogue from scene_dialogue output"""
    dialogue_file = os.path.join(
        SCENE_DIALOGUE_DIR,
        movie_name,
        f"{scene_id}_dialogue.json"
    )
    
    if not os.path.exists(dialogue_file):
        return []
    
    try:
        with open(dialogue_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

def load_emotion_for_scene(movie_name, scene_id):
    """Load emotion data from scene_emotion output"""
    emotion_file = os.path.join(
        SCENE_EMOTION_DIR,
        movie_name,
        f"{scene_id}_emotion.json"
    )
    
    if not os.path.exists(emotion_file):
        return {}
    
    try:
        with open(emotion_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def analyze_scene_semantic_emotion(movie_name, scene_id, dialogue_data, emotion_data, visual_data=None):
    """
    Analyze semantic emotion for a single scene.
    
    Returns dict with:
    - emotions: ["tense", "angry", ...]
    - viewer_emotion_prediction: "anxiety"
    - laugh_moment_flag: bool
    - shock_moment_flag: bool
    - climax_point_flag: bool (set later)
    """
    
    # Combine all dialogue text
    if isinstance(dialogue_data, list):
        full_text = " ".join(
            item.get('text', '') if isinstance(item, dict) else str(item)
            for item in dialogue_data
        )
    else:
        full_text = ""
    
    # Get sentiment from dialogue
    sentiment = analyze_sentiment(full_text)
    
    # Get arousal from emotion data
    arousal = emotion_data.get('emotion_arousal_score', 0.5) if emotion_data else 0.5
    
    # Generate semantic emotions
    emotions = combine_sentiment_arousal(sentiment, arousal)
    
    # Predict viewer emotion
    viewer_emotion = map_to_viewer_emotion(emotions, sentiment, arousal)
    
    # Detect special moments
    laugh_flag = detect_laugh_moment(sentiment, arousal, full_text)
    shock_flag = detect_shock_moment(full_text, arousal, visual_data)
    
    return {
        "emotions": emotions,
        "viewer_emotion_prediction": viewer_emotion,
        "laugh_moment_flag": laugh_flag,
        "shock_moment_flag": shock_flag,
        "climax_point_flag": False,  # Will be set after global analysis
        "_metadata": {
            "sentiment_score": round(sentiment, 3),
            "arousal_score": round(arousal, 3),
            "dialogue_length": len(dialogue_data) if isinstance(dialogue_data, list) else 0
        }
    }

def main():
    """Process semantic emotions for all movies"""
    
    # Find all scene index files to discover movies
    if not os.path.exists(SCENE_INDEX_DIR):
        print("[INFO] No scene_index directory found")
        return
    
    # Get unique movies from FINAL files
    movies_found = set()
    for filename in os.listdir(SCENE_INDEX_DIR):
        if "_FINAL.json" in filename:
            movie_name = filename.replace("_FINAL.json", "").strip()
            movies_found.add(movie_name)
    
    if not movies_found:
        print("[INFO] No FINAL scene files found")
        return
    
    for movie_name in sorted(movies_found):
        print(f"\n[SEMANTIC EMOTION] Processing: {movie_name}")
        
        # Load full FINAL file to get all scenes and visual data
        final_file = os.path.join(SCENE_INDEX_DIR, f"{movie_name}_FINAL.json")
        
        if not os.path.exists(final_file):
            print(f"[WARN] FINAL file not found: {final_file}")
            continue
        
        try:
            with open(final_file, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load FINAL file: {e}")
            continue
        
        # Extract scenes
        scenes = final_data if isinstance(final_data, list) else final_data.get('scenes', [])
        
        # First pass: analyze each scene
        semantic_emotions = {}
        all_scenes_with_emotions = []
        
        for scene_data in scenes:
            scene_id = scene_data.get('scene_id', '')
            if not scene_id:
                continue
            
            # Load dialogue and emotion data
            dialogue = load_dialogue_for_scene(movie_name, scene_id)
            emotion = load_emotion_for_scene(movie_name, scene_id)
            
            # Get visual data from final file
            visual_data = scene_data.get('visual_data', {})
            
            # Analyze semantic emotion
            sem_emotion = analyze_scene_semantic_emotion(
                movie_name, scene_id, dialogue, emotion, visual_data
            )
            
            semantic_emotions[scene_id] = sem_emotion
            
            # Collect for climax detection
            all_scenes_with_emotions.append({
                'scene_id': scene_id,
                'arousal_score': emotion.get('emotion_arousal_score', 0.5),
                'visual_data': visual_data
            })
            
            print(f"  ✓ {scene_id}: {', '.join(sem_emotion['emotions'])}")
        
        # Second pass: detect climax points
        climax_map = detect_climax_points(all_scenes_with_emotions, movie_name)
        
        # Apply climax flags
        for scene_id, is_climax in climax_map.items():
            if scene_id in semantic_emotions:
                semantic_emotions[scene_id]['climax_point_flag'] = is_climax
                if is_climax:
                    print(f"  🎯 {scene_id}: CLIMAX POINT")
        
        # Save results
        output_file = os.path.join(OUTPUT_DIR, f"{movie_name}_semantic_emotions.json")
        
        output_data = {
            "movie": movie_name,
            "total_scenes": len(semantic_emotions),
            "semantic_emotions": semantic_emotions,
            "generated_at": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Semantic emotions saved → {output_file}")

if __name__ == "__main__":
    main()
