import os
import sys
import shutil
import builtins
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src import run_pipeline as rp


class TestRunPipelineCLI(unittest.TestCase):
    def setUp(self):
        self.scenes_dir = os.path.join(REPO_ROOT, "outputs", "scenes")
        if os.path.exists(self.scenes_dir):
            shutil.rmtree(self.scenes_dir)
        os.makedirs(self.scenes_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.scenes_dir):
            shutil.rmtree(self.scenes_dir)

    def test_find_available_movies(self):
        with open(os.path.join(self.scenes_dir, "A_scenes.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.scenes_dir, "B_scenes.json"), "w") as f:
            f.write("{}")

        movies = rp.find_available_movies()
        self.assertEqual(movies, ["A", "B"])

    def test_choose_movie_interactive(self):
        with open(os.path.join(self.scenes_dir, "X_scenes.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.scenes_dir, "Y_scenes.json"), "w") as f:
            f.write("{}")

        original_input = builtins.input
        try:
            builtins.input = lambda prompt=None: "2"
            chosen = rp.choose_movie_interactive(["X", "Y"])
            self.assertEqual(chosen, "Y")
        finally:
            builtins.input = original_input

    def test_list_flag_prints(self):
        with open(os.path.join(self.scenes_dir, "L_scenes.json"), "w") as f:
            f.write("{}")

        # capture stdout
        from io import StringIO

        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            rp.main(["--list"])
            out = sys.stdout.getvalue()
            self.assertIn("L", out)
        finally:
            sys.stdout = old_stdout

    def test_force_flag_cleans(self):
        movie = "T"

        # create some fake outputs for the movie
        repo = os.path.dirname(os.path.dirname(__file__))
        assets = os.path.join(repo, "outputs", "scene_assets", movie)
        dialogue = os.path.join(repo, "outputs", "scene_dialogue", movie)
        visual = os.path.join(
            repo, "outputs", "scene_visual_index", f"{movie}_scene_visuals.json"
        )
        index = os.path.join(repo, "outputs", "scene_index", f"{movie}_FINAL.json")

        os.makedirs(assets, exist_ok=True)
        os.makedirs(dialogue, exist_ok=True)
        with open(visual, "w") as f:
            f.write("{}")
        os.makedirs(os.path.dirname(index), exist_ok=True)
        with open(index, "w") as f:
            f.write("{}")

        # ensure files exist
        self.assertTrue(os.path.isdir(assets))
        self.assertTrue(os.path.isdir(dialogue))
        self.assertTrue(os.path.exists(visual))
        self.assertTrue(os.path.exists(index))

        # call cleaner
        rp.clean_movie_outputs(movie)

        # assert removed
        self.assertFalse(os.path.exists(assets))
        self.assertFalse(os.path.exists(dialogue))
        self.assertFalse(os.path.exists(visual))
        self.assertFalse(os.path.exists(index))

    def test_master_merger_runs_last(self):
        # Ensure orchestrator keeps master merger as the final step
        self.assertEqual(rp.STEPS[-1], "src.scene_master_merger")


if __name__ == "__main__":
    unittest.main()
