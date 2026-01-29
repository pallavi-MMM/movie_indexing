# Project File Usage Analysis

**Date:** January 9, 2026  
**Analysis Type:** Complete codebase audit - identifies used vs unused files

---

## Summary

**Total Python Files:** 107  
**Analysis Result:** 21 unused/optional utility scripts identified at root level

---

## 1. CORE PIPELINE FILES (Always Used)

### Main Entry Point
- `src/run_pipeline.py` - Main orchestrator that runs all phases

### Pipeline Phases (25 Total - All Used)

**Phase Group A: Scene Segmentation & Assets**
- `src/phase_a/scene_segmentation.py` - Scene detection
- `src/phase_b/scene_assets_extractor.py` - Frame extraction
- `src/phase_c/scene_actor_linker.py` - Actor detection

**Phase Group B: Visual Analysis**
- `src/scene_visual_analyzer.py` - Visual feature analysis
- `src/scene_object_analyzer.py` - Object detection
- `src/scene_context_analyzer.py` - Scene context analysis

**Phase Group C: Audio & Dialogue**
- `src/scene_dialogue_extractor.py` - Speech extraction (ASR)
- `src/scene_speaker_diarizer.py` - Speaker identification
- `src/scene_dialogue_speaker_mapper.py` - Map dialogue to speakers
- `src/scene_speaker_actor_mapper.py` - Map speakers to actors
- `src/scene_dialogue_merger.py` - Merge dialogue data

**Phase Group D: Content Safety & Profanity**
- `src/scene_profanity_detector.py` - Profanity detection
- `src/scene_content_safety.py` - Content safety analysis

**Phase Group E: Emotion Analysis**
- `src/scene_emotion_analyzer.py` - Basic emotion analysis
- `src/scene_emotion_merger.py` - Merge emotion data
- `src/scene_semantic_emotion_analyzer.py` - Semantic emotion labels
- `src/scene_semantic_emotion_merger.py` - Merge semantic emotions

**Phase Group F: Audio Intelligence**
- `src/scene_audio_intelligence.py` - Audio intelligence features
- `src/scene_audio_intelligence_merger.py` - Merge audio intelligence

**Phase Group G: Meta Analysis & Narrative**
- `src/scene_meta_intelligence.py` - Meta-level intelligence
- `src/scene_narrative_structure.py` - Narrative analysis
- `src/scene_summarizer.py` - Scene summaries

**Phase Group H: Final Enrichment**
- `src/scene_enrichment.py` - Final enrichment layer
- `src/scene_character_merger.py` - Character data merger (Phase 25)

**Core Mergers & Support**
- `src/scene_master_merger.py` - Master data merger
- `src/scene_schema.py` - Schema validation
- `src/scene_fusion.py` - Data fusion
- `src/scene_merge_all_enrichments.py` - Optional enrichment consolidation

### Support Libraries
- `src/actor_db.py` - Actor database
- `src/actor_linker.py` - Actor linking
- `src/audio_asr.py` - Audio ASR
- `src/embedding_index.py` - Embedding indexing
- `src/face_actor_pipeline.py` - Face-actor pipeline
- `src/face_tracker.py` - Face tracking
- `src/movie_utils.py` - Movie utilities
- `src/object_detector.py` - Object detection
- `src/vlm_summary.py` - VLM-based summaries
- `src/visual_quality.py` - Visual quality analysis
- `src/phase_vi_viewer_attention.py` - Viewer attention
- `src/scene_safety.py` - Scene safety
- `src/scene_emotion_inferencer.py` - Emotion inference
- `src/run_local_pipeline.py` - Local pipeline variant

### Phase I: Character Introduction Detection
- `src/phase_i/character_introduction_detector.py` - Character detection (USED in test_actor_merge.py)
- `src/phase_i/merge_events.py` - Event merging
- `src/phase_i/scene_json_builder.py` - JSON building (USED in test_actor_merge.py)

**Status:** All in use by pipeline or tests

---

## 2. UTILITY SCRIPTS (Optional - User Runs Manually)

These scripts are NOT called by the pipeline but are useful utilities for manual inspection:

### Dataset Processing
- `run_all_movies.py` - **USED** - Runs pipeline on all movies in movies/ folder
- `run_rangastalam_pipeline.py` - Runs pipeline for specific movie (example)
- `check_characters.py` - Extracts character introduction data
- `check_final.py` - Inspects final JSON structure
- `show_samples.py` - Displays sample scenes

### Monitoring & Debugging
- `monitor_pipeline.py` - Monitors pipeline execution
- `debug_analyzer_outputs.py` - Debug analyzer outputs
- `display_complete_events.py` - Shows complete event timeline

### Verification Scripts (Quality Assurance)
- `verify_pipeline.py` - Verifies pipeline execution
- `verify_complete_schema.py` - Verifies schema structure
- `verify_complete_output.py` - Verifies output completeness
- `verify_audio_intelligence.py` - Verifies audio intelligence
- `verify_semantic_emotions.py` - Verifies semantic emotions
- `verify_viewer_emotions.py` - Verifies viewer emotions
- `verify_summaries.py` - Verifies summaries
- `verify_narrative_structure.py` - Verifies narrative structure
- `verify_meta_intelligence.py` - Verifies meta intelligence
- `verify_dukudu_enrichments.py` - Verifies Dukudu enrichments

### Quality Reports
- `final_quality_report.py` - Generates quality report
- `check_scene_types.py` - Checks scene types

**Status:** All optional utility scripts for manual use

---

## 3. DEAD CODE / LIKELY UNUSED

### Unclear Purpose
- `combined_src.py` - **SUSPICIOUS** 
  - 1656 lines
  - Description: "Auto-generated combined Python file"
  - Purpose: Consolidates entire src/ directory into single file
  - **Status:** Not used by pipeline (pipeline imports individual modules)
  - **Recommendation:** REMOVE - appears to be an experimental consolidation attempt

- `actor_detector_fallback.py` - **POTENTIALLY UNUSED**
  - Purpose: "Direct actor detection using FAISS index without InsightFace"
  - Note: Fallback for when InsightFace fails
  - **Status:** Not imported or referenced anywhere in active pipeline
  - **Recommendation:** KEEP as fallback, but not actively used

### Deprecated Testing
- `test_complete_pipeline.py` - Old test file
  - **Recommendation:** REMOVE if replaced by tests/ directory tests

---

## 4. TEST FILES (tests/ directory)

All test files in `tests/` directory are properly categorized test code:
- `tests/test_*.py` (40+ files) - Unit and integration tests
- **Status:** All appear legitimate

---

## FILE CATEGORIZATION TABLE

| File | Type | Status | Recommendation |
|------|------|--------|-----------------|
| src/run_pipeline.py | Core | ✅ Used | KEEP |
| src/phase_a/* | Core | ✅ Used | KEEP |
| src/phase_b/* | Core | ✅ Used | KEEP |
| src/phase_c/* | Core | ✅ Used | KEEP |
| src/scene_*.py | Core | ✅ Used | KEEP |
| src/phase_i/* | Core | ✅ Used (in tests) | KEEP |
| run_all_movies.py | Utility | ✅ Used | KEEP |
| run_rangastalam_pipeline.py | Utility | ⚠️ Example | KEEP (documentation) |
| check_*.py | Utility | ⚠️ Optional | KEEP (convenience) |
| verify_*.py | Utility | ⚠️ Optional | KEEP (QA) |
| final_quality_report.py | Utility | ⚠️ Optional | KEEP (QA) |
| monitor_pipeline.py | Utility | ⚠️ Optional | KEEP (useful) |
| display_complete_events.py | Utility | ⚠️ Optional | KEEP (useful) |
| combined_src.py | Dead Code | ❌ Unused | **REMOVE** |
| actor_detector_fallback.py | Support | ⚠️ Fallback | KEEP (might be needed) |
| test_complete_pipeline.py | Test | ? | **CHECK** - might duplicate tests/ |
| tests/ | Test | ✅ Used | KEEP |
| output_json/run_pipeline.py | Dead Code | ❌ Duplicate | **REMOVE** |

---

## RECOMMENDATIONS

### Immediate Actions

**Remove These Files:**
1. `combined_src.py` - Unused auto-generated file (1656 lines)
2. `output_json/run_pipeline.py` - Duplicate of src/run_pipeline.py in wrong directory
3. `test_complete_pipeline.py` - Check if tests/ directory replaced this

**Review:**
- `actor_detector_fallback.py` - Keep as backup but document its purpose

### Keep All Other Files
All root-level utility/verification scripts are helpful for:
- Running multiple movies (run_all_movies.py)
- Quality assurance (verify_*.py)
- Debugging (debug_*, monitor_*, display_*)
- Data inspection (check_*, show_*)

These don't bloat the pipeline and provide value for development/testing.

---

## Pipeline Execution Flow

```
python src/run_pipeline.py --movie "movie_name"
    ↓
STEPS[] loop (25 phases)
    ├─ Phase 1-24: Scene analysis phases
    └─ Phase 25: Character merger
    ↓
output_json/{movie}_complete_schema.json (final output)
```

**No root-level script is called by this pipeline.**  
**All utilities are optional manual-run scripts.**

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Core pipeline files | 45+ | ✅ All used |
| Utility scripts | 18 | ⚠️ Optional |
| Test files | 40+ | ✅ All used |
| Dead code | 2-3 | ❌ Remove |
| **Total Python files** | **107** | - |

