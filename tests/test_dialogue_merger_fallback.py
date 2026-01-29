import os
import json
import importlib
import unittest


class TestDialogueMergerFallback(unittest.TestCase):
    def setUp(self):
        self.repo = os.path.dirname(os.path.dirname(__file__))
        self.scenes_dir = os.path.join(self.repo, "outputs", "scenes")
        self.dialogue_dir = os.path.join(self.repo, "outputs", "scene_dialogue")
        os.makedirs(self.scenes_dir, exist_ok=True)
        os.makedirs(self.dialogue_dir, exist_ok=True)

    def tearDown(self):
        import shutil
        if os.path.exists(self.scenes_dir):
            shutil.rmtree(self.scenes_dir)
        if os.path.exists(self.dialogue_dir):
            shutil.rmtree(self.dialogue_dir)
        idx = os.path.join(self.repo, "outputs", "scene_index")
        if os.path.exists(idx):
            for f in os.listdir(idx):
                if f.startswith("FALLBACK_TEST_"):
                    os.remove(os.path.join(idx, f))

    def test_dialogue_merger_builds_from_segments(self):
        movie = "FALLBACK_TEST_MOVIE"

        # create segments file
        segs = {
            "movie_id": movie,
            "scenes": [
                {"scene_id": "scene_0001", "start_time": "00:00:00.000", "end_time": "00:00:05.000", "duration": 5},
            ]
        }
        with open(os.path.join(self.scenes_dir, f"{movie}_scenes.json"), "w", encoding="utf-8") as f:
            json.dump(segs, f)

        # create per-scene dialogue
        out_d = os.path.join(self.dialogue_dir, movie)
        os.makedirs(out_d, exist_ok=True)
        scene1 = {"scene_id": "scene_0001", "dialogue_text": [{"character": "A", "line": "hello"}], "dialogue_speed_wpm": 120}
        with open(os.path.join(out_d, "scene_0001.json"), "w", encoding="utf-8") as f:
            json.dump(scene1, f)

        m = importlib.import_module("src.scene_dialogue_merger")
        setattr(m, "TARGET_MOVIE", movie)
        m.main()

        out_path = os.path.join(self.repo, "outputs", "scene_index", f"{movie}_FINAL_WITH_DIALOGUE.json")
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertIn("dialogue_text", data[0])


if __name__ == "__main__":
    unittest.main()
