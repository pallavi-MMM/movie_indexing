import os
import json
import shutil
import importlib
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src import scene_master_merger as merger


class TestPerMovieIsolation(unittest.TestCase):
    def setUp(self):
        self.out_dir = "outputs"
        self.scenes_dir = os.path.join(self.out_dir, "scenes")
        self.seg_dir = os.path.join(self.out_dir, "scene_segments")
        self.index_dir = os.path.join(self.out_dir, "scene_index")
        for d in (self.scenes_dir, self.seg_dir, self.index_dir):
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)

    def tearDown(self):
        for d in (self.scenes_dir, self.seg_dir, self.index_dir):
            if os.path.exists(d):
                shutil.rmtree(d)

    def _write_scene_and_segment(self, movie, scene_id, summary):
        scenes = {"scenes": [{"scene_id": scene_id, "start_time": 0, "end_time": 5, "duration": 5}]}
        with open(os.path.join(self.scenes_dir, f"{movie}_scenes.json"), "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=2)
        segment = {"scene_id": scene_id, "scene_summary": summary}
        with open(os.path.join(self.seg_dir, f"{movie}_scene_0001.json"), "w", encoding="utf-8") as f:
            json.dump(segment, f, indent=2)

    def test_final_jsons_different_for_different_movies(self):
        # movie A
        self._write_scene_and_segment("MOVA", "scene_0001", "first movie")
        os.environ["MOVIE_NAME"] = "MOVA"
        importlib.reload(merger)
        merger.main()
        out_a = os.path.join(self.index_dir, "MOVA_FINAL.json")
        self.assertTrue(os.path.exists(out_a))

        # movie B
        self._write_scene_and_segment("MOVB", "scene_0001", "second movie")
        os.environ["MOVIE_NAME"] = "MOVB"
        importlib.reload(merger)
        merger.main()
        out_b = os.path.join(self.index_dir, "MOVB_FINAL.json")
        self.assertTrue(os.path.exists(out_b))

        with open(out_a, "r", encoding="utf-8") as f:
            da = json.load(f)
        with open(out_b, "r", encoding="utf-8") as f:
            db = json.load(f)

        self.assertNotEqual(da, db)
        self.assertEqual(da[0]["movie_id"], "MOVA")
        self.assertEqual(db[0]["movie_id"], "MOVB")


if __name__ == "__main__":
    unittest.main()
