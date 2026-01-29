"""
Audio Intelligence Analyzer (Phase III-A): Sound design & audio signals

Extracts sound intelligence without trying to classify every sound:
  - background_music_mood (from tempo, energy, spectral tone)
  - audio_peaks_detected (from RMS peak detection)
  - sfx_presence (peaks outside dialogue windows)
  - sfx_details (categorical classification)
  - narration_present (inference from dialogue structure)
  - narration_text (filled only if narration detected)
  - sound_design_notes (human-readable summary)

Uses librosa for audio analysis. Deterministic, explainable rules.
"""

import os
import json
import librosa
import numpy as np
from collections import defaultdict

# Global movie name (set by pipeline)
MOVIE_NAME = "Alanati ramachandrudu - trailer"

OUT_DIR = "outputs/scene_audio"
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================================
# RULE-BASED AUDIO ANALYSIS
# ============================================================================

def analyze_audio_signals(audio_path):
    """
    Extract raw audio signals: tempo, RMS (energy), spectral centroid (brightness).
    
    Returns dict with tempo, energy, spectral_centroid, peaks.
    """
    try:
        y, sr = librosa.load(audio_path, sr=None)
    except Exception as e:
        print(f"[WARN] Could not load audio: {e}")
        return None
    
    # Tempo (beats per minute)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.asarray(tempo).item()) if hasattr(tempo, '__iter__') else float(tempo)
    
    # Energy (RMS)
    rms = librosa.feature.rms(y=y)[0]
    mean_rms = float(np.mean(rms))
    std_rms = float(np.std(rms))
    
    # Spectral centroid (brightness)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    mean_spectral = float(np.mean(spectral_centroid))
    
    # Peak detection: find frames with RMS above (mean + 1.5 * std)
    threshold = mean_rms + (1.5 * std_rms)
    peaks = np.where(rms > threshold)[0]
    
    return {
        "tempo": tempo,
        "mean_rms": mean_rms,
        "std_rms": std_rms,
        "spectral_centroid": mean_spectral,
        "rms_frames": rms.tolist(),
        "peak_frames": peaks.tolist(),
        "sr": int(sr)
    }


def infer_background_music_mood(signals):
    """
    Infer background music mood from tempo, energy, and spectral content.
    
    Rules:
      - low tempo (<100) + low energy = calm
      - low tempo + high energy = tense
      - high tempo (>100) + high energy = energetic
      - low spectral centroid (<2000) = sad/minor
      - sudden RMS drops = suspense
    
    Returns: mood string
    """
    if not signals:
        return "unknown"
    
    tempo = signals.get("tempo", 0)
    mean_rms = signals.get("mean_rms", 0)
    spectral = signals.get("spectral_centroid", 0)
    
    # Normalize energy relative to std
    std_rms = signals.get("std_rms", 0)
    energy_level = "high" if std_rms > 0.05 else "low"
    
    # Spectral tone
    tone = "minor" if spectral < 2000 else "major"
    
    # Rule-based classification
    if tempo < 100:
        if energy_level == "high":
            return "tense"
        else:
            return "calm"
    else:  # tempo >= 100
        if energy_level == "high":
            return "energetic"
        else:
            return "moderate"


def detect_audio_peaks(signals, dialogue_timeline=None):
    """
    Detect audio peaks (sudden loud events).
    
    Peak = frame with RMS above (mean + 1.5 * std)
    
    Returns:
      - peaks_detected: bool
      - peak_count: int
      - peaks_in_dialogue: int (peaks aligned with dialogue)
      - peaks_outside_dialogue: int (potential SFX)
    """
    if not signals or not signals.get("peak_frames"):
        return {
            "peaks_detected": False,
            "peak_count": 0,
            "peaks_in_dialogue": 0,
            "peaks_outside_dialogue": 0
        }
    
    peak_frames = signals["peak_frames"]
    peak_count = len(peak_frames)
    peaks_detected = peak_count > 0
    
    # If no dialogue timeline provided, assume all peaks are SFX
    if not dialogue_timeline:
        return {
            "peaks_detected": peaks_detected,
            "peak_count": peak_count,
            "peaks_in_dialogue": 0,
            "peaks_outside_dialogue": peak_count
        }
    
    # Convert frames to time (frame_index / sr * hop_length / sr)
    sr = signals.get("sr", 22050)
    hop_length = 512
    peak_frames = np.array(signals.get("peak_frames", []))
    peak_times = (peak_frames * hop_length / sr).tolist()
    
    peaks_in_dialogue = 0
    peaks_outside_dialogue = 0
    
    for peak_time in peak_times:
        in_dialogue = False
        for start, end in dialogue_timeline:
            if start <= peak_time <= end:
                in_dialogue = True
                break
        
        if in_dialogue:
            peaks_in_dialogue += 1
        else:
            peaks_outside_dialogue += 1
    
    return {
        "peaks_detected": peaks_detected,
        "peak_count": peak_count,
        "peaks_in_dialogue": peaks_in_dialogue,
        "peaks_outside_dialogue": peaks_outside_dialogue
    }


def infer_sfx_presence(peak_analysis):
    """
    Determine if SFX (sound effects) are present.
    
    Logic: SFX are peaks NOT aligned with dialogue.
    If peaks_outside_dialogue > 0, then sfx_presence = True
    
    Returns: bool
    """
    return peak_analysis.get("peaks_outside_dialogue", 0) > 0


def classify_sfx_details(signals, peak_analysis):
    """
    Classify SFX categories (not individual sounds).
    
    Possible categories:
      - impact_sound (sharp, sudden peaks)
      - ambient_noise (low energy, continuous)
      - transition_effect (spectral changes)
      - action_sound (high energy, variable)
      - crowd_noise (multiple small peaks)
    
    Returns: list of category strings
    """
    categories = []
    
    if not signals or not peak_analysis.get("peaks_detected"):
        return categories
    
    rms_std = signals.get("std_rms", 0)
    peak_count = peak_analysis.get("peak_count", 0)
    peaks_outside = peak_analysis.get("peaks_outside_dialogue", 0)
    
    # Sudden, sharp peaks = impact_sound
    if peaks_outside > 0 and rms_std > 0.08:
        categories.append("impact_sound")
    
    # Multiple smaller peaks = crowd_noise or ambient
    if peak_count > 3 and rms_std < 0.08:
        categories.append("crowd_noise")
    
    # Continuous background variation = ambient_noise
    if rms_std > 0.05:
        categories.append("ambient_noise")
    
    # High spectral variation = transition_effect
    spectral = signals.get("spectral_centroid", 0)
    if spectral > 3000:
        categories.append("transition_effect")
    
    # High activity + high energy = action_sound
    if peak_count > 2 and rms_std > 0.06:
        categories.append("action_sound")
    
    return list(set(categories))  # Remove duplicates


def infer_narration_present(scene):
    """
    Infer if narration (voice-over) is present.
    
    Narration signal:
      - Few dialogue lines (<= 2) OR no dialogue
      - Long scene duration (> 10 seconds)
      - Would have single continuous speaker without turn-taking
    
    We infer from dialogue structure, not audio classification.
    
    Returns: bool
    """
    dialogue = scene.get("dialogue_text", [])
    duration = scene.get("duration", 0)
    
    # Few lines + long duration = likely narration
    if len(dialogue) <= 2 and duration > 10:
        return True
    
    # No dialogue at all (unusual, but check)
    if len(dialogue) == 0 and duration > 5:
        return True
    
    return False


def build_sound_design_notes(signals, peak_analysis, sfx_details, mood):
    """
    Generate human-readable sound design summary.
    
    Examples:
      - "Calm ambient score with minimal peaks."
      - "Tense background with intermittent impact sounds."
      - "Energetic, high-activity soundscape with crowd noise."
    
    Returns: str (50-100 chars, human-readable)
    """
    notes = []
    
    # Mood
    notes.append(f"{mood} background score" if mood != "unknown" else "Neutral sound design")
    
    # Peak activity
    peaks = peak_analysis.get("peaks_detected", False)
    peak_count = peak_analysis.get("peak_count", 0)
    peaks_outside = peak_analysis.get("peaks_outside_dialogue", 0)
    
    if peaks and peaks_outside > 2:
        notes.append("with multiple sharp audio peaks")
    elif peaks and peaks_outside > 0:
        notes.append("with intermittent audio peaks")
    elif peaks:
        notes.append("with minimal peaks")
    
    # SFX categories
    if sfx_details:
        sfx_str = " and ".join(sfx_details[:2])  # Top 2 categories
        notes.append(f"featuring {sfx_str}")
    
    # Finalize
    if len(notes) == 1:
        return notes[0] + "."
    else:
        return notes[0] + " " + " ".join(notes[1:]) + "."


def analyze_scene_audio(scene, audio_path):
    """
    Complete audio intelligence analysis for one scene.
    
    Returns dict with all 7 fields:
      - background_music_mood
      - sfx_presence
      - sfx_details
      - audio_peaks_detected
      - sound_design_notes
      - narration_present
      - narration_text
    """
    
    # === EXTRACT AUDIO SIGNALS ===
    signals = analyze_audio_signals(audio_path)
    
    if not signals:
        return {
            "background_music_mood": "unknown",
            "sfx_presence": False,
            "sfx_details": [],
            "audio_peaks_detected": False,
            "sound_design_notes": "Audio analysis unavailable.",
            "narration_present": False,
            "narration_text": ""
        }
    
    # === DIALOGUE TIMELINE (for peak classification) ===
    dialogue = scene.get("dialogue_text", [])
    dialogue_timeline = None
    if dialogue:
        dialogue_timeline = [(d.get("start", 0), d.get("end", 0)) for d in dialogue]
    
    # === INFER ALL AUDIO INTELLIGENCE FIELDS ===
    
    # 1. Background music mood
    mood = infer_background_music_mood(signals)
    
    # 2. Audio peaks
    peak_analysis = detect_audio_peaks(signals, dialogue_timeline)
    
    # 3. SFX presence
    sfx_presence = infer_sfx_presence(peak_analysis)
    
    # 4. SFX details (categories)
    sfx_details = classify_sfx_details(signals, peak_analysis)
    
    # 5. Narration detection
    narration_present = infer_narration_present(scene)
    
    # 6. Sound design notes
    sound_notes = build_sound_design_notes(signals, peak_analysis, sfx_details, mood)
    
    return {
        "background_music_mood": mood,
        "sfx_presence": sfx_presence,
        "sfx_details": sfx_details,
        "audio_peaks_detected": peak_analysis.get("peaks_detected", False),
        "sound_design_notes": sound_notes,
        "narration_present": narration_present,
        "narration_text": ""  # Only filled if narration_present = True (future work)
    }


def main():
    """Pipeline entry point."""
    import sys
    
    # Setup path
    REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    
    from src.movie_utils import resolve_movie
    
    movie = resolve_movie(sys.modules[__name__])
    audio_dir = f"outputs/scene_assets/{movie}"
    scene_index_dir = f"outputs/scene_index"
    
    if not os.path.exists(audio_dir):
        print(f"[WARN] Audio directory not found: {audio_dir}")
        return
    
    # Load scene metadata for dialogue info
    scene_files = [f for f in os.listdir(scene_index_dir) if f.startswith(movie) and f.endswith("_FINAL.json")]
    if not scene_files:
        print(f"[WARN] No scene index found for {movie}")
        return
    
    scene_file = os.path.join(scene_index_dir, scene_files[0])
    with open(scene_file, "r", encoding="utf-8") as f:
        scene_data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(scene_data, list):
        scenes = scene_data
    else:
        scenes = scene_data.get("scenes", [])
    
    scenes_by_id = {s["scene_id"]: s for s in scenes}
    
    print(f"[AUDIO INTELLIGENCE] Processing {movie}")
    audio_results = {}
    
    for scene_file_name in sorted(os.listdir(audio_dir)):
        if not scene_file_name.endswith("_audio.wav"):
            continue
        
        scene_id = scene_file_name.replace("_audio.wav", "")
        audio_path = os.path.join(audio_dir, scene_file_name)
        
        # Get scene metadata for dialogue
        scene_meta = scenes_by_id.get(scene_id, {})
        
        # Analyze audio
        audio_intel = analyze_scene_audio(scene_meta, audio_path)
        audio_results[scene_id] = audio_intel
        
        print(f"  [{scene_id}] mood={audio_intel['background_music_mood']}, "
              f"sfx={audio_intel['sfx_presence']}, "
              f"peaks={audio_intel['audio_peaks_detected']}, "
              f"narration={audio_intel['narration_present']}")
    
    # Save results
    movie_out_dir = os.path.join(OUT_DIR, movie)
    os.makedirs(movie_out_dir, exist_ok=True)
    
    output_file = os.path.join(movie_out_dir, f"{movie}_audio_intelligence.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "movie": movie,
            "total_scenes": len(audio_results),
            "audio_intelligence": audio_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Audio intelligence → {output_file}")


if __name__ == "__main__":
    main()
