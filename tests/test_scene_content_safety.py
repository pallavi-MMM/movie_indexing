import unittest
import json

from src.scene_content_safety import assess_scene


class TestSceneContentSafety(unittest.TestCase):
    def test_knife_moderate_age_13(self):
        scene = {
            "objects": ["person", "knife", "cup"],
            "motion_intensity_score": 27.23,
            "profanity_present": None,
        }

        out = assess_scene(scene)
        self.assertEqual(out["violence_level"], "moderate")
        self.assertEqual(out["age_rating_suggestion"], "13+")
        self.assertIn("violence", out["sensitive_content_type"])

    def test_knife_high_motion_age_16(self):
        scene = {
            "objects": ["knife"],
            "motion_intensity_score": 50,
            "profanity_present": None,
        }

        out = assess_scene(scene)
        self.assertEqual(out["violence_level"], "high")
        self.assertEqual(out["age_rating_suggestion"], "16+")

    def test_profanity_escalates_to_16(self):
        scene = {
            "objects": ["person"],
            "motion_intensity_score": 0,
            "profanity_present": True,
        }

        out = assess_scene(scene)
        self.assertEqual(out["age_rating_suggestion"], "16+")

    def test_main_accepts_variants(self):
        import os
        repo = os.path.dirname(os.path.dirname(__file__))
        idx_dir = os.path.join(repo, "outputs", "scene_index")
        os.makedirs(idx_dir, exist_ok=True)

        movie = "VARIANT_MOVIE"
        # create a _FINAL_WITH_DIALOGUE_EMOTION variant
        src_path = os.path.join(idx_dir, f"{movie}_FINAL_WITH_DIALOGUE_EMOTION.json")
        scenes = [{"scene_id": "scene_0001", "objects": ["knife"], "motion_intensity_score": 0, "profanity_present": None}]
        with open(src_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f)

        # call the module with TARGET_MOVIE set
        import importlib
        m = importlib.import_module("src.scene_content_safety")
        setattr(m, "TARGET_MOVIE", movie)

        # run
        m.main()

        out_path = os.path.join(idx_dir, f"{movie}_FINAL_WITH_SAFETY.json")
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertIn("violence_level", data[0])
