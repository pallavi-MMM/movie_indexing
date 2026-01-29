import os
import types
import unittest

from src.movie_utils import resolve_movie


class DummyModule(types.SimpleNamespace):
    pass


class TestResolveMovie(unittest.TestCase):
    def test_target_movie_priority(self):
        m = DummyModule(TARGET_MOVIE="alpha", MOVIE_NAME="beta")
        self.assertEqual(resolve_movie(m), "alpha")

    def test_movie_name_fallback(self):
        m = DummyModule(MOVIE_NAME="beta")
        # ensure no env var interferes
        os.environ.pop("MOVIE_NAME", None)
        self.assertEqual(resolve_movie(m), "beta")

    def test_env_fallback(self):
        os.environ["MOVIE_NAME"] = "envmovie"
        m = DummyModule()
        self.assertEqual(resolve_movie(m), "envmovie")
        os.environ.pop("MOVIE_NAME", None)

    def test_no_movie_raises(self):
        os.environ.pop("MOVIE_NAME", None)
        m = DummyModule()
        with self.assertRaises(RuntimeError):
            resolve_movie(m)


if __name__ == "__main__":
    unittest.main()
