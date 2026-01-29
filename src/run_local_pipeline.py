from typing import Dict, Any, List
import logging

from src.scene_safety import analyze_scene
from src.visual_quality import analyze_visual_quality
from src.vlm_summary import summarize_scene
from src.scene_fusion import merge_scenes_from_sources
from src.face_actor_pipeline import FaceActorPipeline

logger = logging.getLogger(__name__)


def run_scene_pipeline(scene: Dict[str, Any]) -> Dict[str, Any]:

    # Normalize input scene shallow copy
    base_scene = {k: v for k, v in scene.items()}

    # Run safety
    safety_out = analyze_scene(base_scene)
    safety_scene = {
        "scene_id": base_scene.get("scene_id"),
        "movie_id": base_scene.get("movie_id"),
    }
    safety_scene.update({"safety_flags": safety_out.get("safety_flags", {})})
    # include per-field confidences/provenance for the top-level safety field
    # compute an overall safety confidence as max of inner confidences
    s_conf_map = safety_out.get("field_confidences", {})
    overall_safety_conf = max(s_conf_map.values()) if s_conf_map else None
    if overall_safety_conf is not None:
        safety_scene.setdefault("field_confidences", {})
        safety_scene["field_confidences"]["safety_flags"] = overall_safety_conf
    if safety_out.get("field_provenance"):
        safety_scene.setdefault("field_provenance", {})
        # collapse provenance lists into top-level safety_flags provenance
        provs = []
        for lst in safety_out.get("field_provenance", {}).values():
            for p in lst:
                if p not in provs:
                    provs.append(p)
        safety_scene["field_provenance"]["safety_flags"] = provs

    # Run visual quality
    vq_out = analyze_visual_quality(base_scene)
    vq_scene = {
        "scene_id": base_scene.get("scene_id"),
        "movie_id": base_scene.get("movie_id"),
    }
    vq_scene.update({"quality_flags": vq_out.get("quality_flags", {})})
    if vq_out.get("field_confidences"):
        vq_scene.setdefault("field_confidences", {})
        # compute overall quality confidence as max
        q_conf_map = vq_out.get("field_confidences", {})
        vq_scene["field_confidences"]["quality_flags"] = (
            max(q_conf_map.values()) if q_conf_map else None
        )
    if vq_out.get("field_provenance"):
        provs = []
        for lst in vq_out.get("field_provenance", {}).values():
            for p in lst:
                if p not in provs:
                    provs.append(p)
        vq_scene.setdefault("field_provenance", {})
        vq_scene["field_provenance"]["quality_flags"] = provs

    # Prepare container for any additional sources (e.g., characters from face-actor pipeline)
    pre_sources: List[Dict[str, Any]] = []

    # Face tracking + actor linking (optional): if a video_path is provided,
    # and optionally an `actor_catalog` mapping name -> embedding list, run
    # the FaceActorPipeline to populate `characters`.
    characters_result = None
    video_path = base_scene.get("video_path")
    actor_catalog = base_scene.get("actor_catalog")
    if video_path:
        # create pipeline and register actors from provided catalog
        try:
            fap = FaceActorPipeline(dim=3, tracker_mode="mock")
            if isinstance(actor_catalog, dict):
                for name, emb in actor_catalog.items():
                    # expect embedding as list
                    if isinstance(emb, list):
                        fap.register_actor(name, emb)
            characters_result = fap.process_video(video_path)
        except Exception as e:
            # Log error for debugging but do not break the pipeline
            logger.warning(
                f"Face->actor pipeline failed for scene {base_scene.get('scene_id')}: {type(e).__name__}: {e}"
            )
            characters_result = None

    # If characters were found, include them as another source for fusion
    if characters_result is not None:
        char_scene = {
            "scene_id": base_scene.get("scene_id"),
            "movie_id": base_scene.get("movie_id"),
            "characters": characters_result,
        }
        # derive confidences/provenance map
        conf_map = {
            c.get("name"): c.get("confidence")
            for c in characters_result
            if c.get("name")
        }
        prov_map = {
            c.get("name"): c.get("provenance", [])
            for c in characters_result
            if c.get("name")
        }
        if conf_map:
            char_scene.setdefault("field_confidences", {})
            char_scene["field_confidences"]["characters"] = conf_map
        if prov_map:
            char_scene.setdefault("field_provenance", {})
            # flatten provenance into list for the characters field
            provs = []
            for lst in prov_map.values():
                for p in lst:
                    if p not in provs:
                        provs.append(p)
            char_scene["field_provenance"]["characters"] = provs
        pre_sources.append({"scene": char_scene, "source": "face_actor_pipeline"})

    # Prepare VLM inputs: give summarizer combined context (merge early signals)
    vlm_input = dict(base_scene)
    vlm_input.update(safety_out)
    vlm_input.update(vq_out)
    vlm_out = summarize_scene(vlm_input)
    vlm_scene = {
        "scene_id": base_scene.get("scene_id"),
        "movie_id": base_scene.get("movie_id"),
    }
    # include summarizer outputs
    vlm_scene["scene_summary"] = vlm_out.get("scene_summary")
    vlm_scene["keywords_auto_generated"] = vlm_out.get("keywords_auto_generated")
    if vlm_out.get("field_confidences"):
        vlm_scene.setdefault("field_confidences", {})
        for k, v in vlm_out.get("field_confidences", {}).items():
            vlm_scene["field_confidences"][k] = v
    if vlm_out.get("field_provenance"):
        vlm_scene.setdefault("field_provenance", {})
        for k, v in vlm_out.get("field_provenance", {}).items():
            vlm_scene["field_provenance"][k] = v

    # Build sources for fusion (include any pre_sources like face_actor_pipeline)
    sources: List[Dict[str, Any]] = (
        [
            {"scene": base_scene, "source": "input_scene"},
            {"scene": safety_scene, "source": "scene_safety"},
            {"scene": vq_scene, "source": "visual_quality"},
        ]
        + pre_sources
        + [
            {"scene": vlm_scene, "source": "vlm_summary"},
        ]
    )

    merged = merge_scenes_from_sources(sources)
    return merged


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: run_local_pipeline.py <scene_json>")
        sys.exit(2)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        scene = json.load(f)
    out = run_scene_pipeline(scene)
    print(json.dumps(out, indent=2))
