import os
import types
from typing import Any


def resolve_movie(module: Any) -> str:
    """Resolve the movie name for a run.

    Priority:
      1. module.TARGET_MOVIE (set by orchestrator)
      2. module.MOVIE_NAME (if set explicitly)
      3. ENV var MOVIE_NAME

    Raises RuntimeError with a helpful message when no movie is found.
    """
    # module can be a module object or a dict-like globals()
    tm = None
    if isinstance(module, types.ModuleType):
        tm = getattr(module, "TARGET_MOVIE", None)
        mn = getattr(module, "MOVIE_NAME", None)
    elif isinstance(module, dict):
        tm = module.get("TARGET_MOVIE")
        mn = module.get("MOVIE_NAME")
    else:
        tm = getattr(module, "TARGET_MOVIE", None)
        mn = getattr(module, "MOVIE_NAME", None)

    if tm:
        return tm
    if mn:
        return mn

    env = os.getenv("MOVIE_NAME")
    if env:
        return env

    raise RuntimeError(
        "No movie specified. Run via `src/run_pipeline.py --movie <name>` or set TARGET_MOVIE / MOVIE_NAME (env or module)"
    )
