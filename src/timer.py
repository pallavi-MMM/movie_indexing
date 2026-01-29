import time
from contextlib import contextmanager
from typing import Iterator


def format_duration(seconds: float) -> str:
    """Return a human-friendly duration string."""
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.2f} s"


@contextmanager
def timer(name: str = None):
    """Context manager that yields and prints elapsed time on exit.

    Usage:
        with timer('step name'):
            do_work()
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        label = f"{name} " if name else ""
        print(f"[TIMING] {label}took {format_duration(elapsed)}")


def timeit(func):
    """Simple decorator that prints the elapsed time of the wrapped function."""

    def _wrapped(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - t0
            name = getattr(func, "__name__", str(func))
            print(f"[TIMING] {name} took {format_duration(elapsed)}")

    return _wrapped
