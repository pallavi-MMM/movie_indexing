Repository Code Style and Conventions

Purpose
- Provide a lightweight, practical set of conventions to keep the codebase consistent and maintainable.

Python
- Use Python 3.11+ idioms where available (type hints, dataclasses for small structs).
- Keep functions small and single-responsibility.
- Add docstrings to public functions and modules.
- Use explicit imports (avoid "from module import *").
- Prefer descriptive variable names; avoid one-letter names except in short loops.
- Keep lines <= 88 characters where reasonable.

Formatting
- Use `black` (if available) to format code: `black .`.
- Use `isort` to sort imports: `isort .`.

Typing
- Add type hints to public functions and class methods.
- Use `typing` types (e.g. `Dict`, `List`, `Optional`) rather than bare `dict`/`list` in annotations where helpful.

Testing
- Add unit tests for any new functionality under `tests/`.
- Use fixtures to create deterministic data for tests.
- Keep tests fast and isolated: mock external heavy ML backends in CI.

Documentation
- Add module-level docstrings explaining purpose and public API.
- For non-trivial modules, add short usage examples in the README or module docs.

Commit Messages
- Use present-tense, short scope prefixes: `feat(...)`, `fix(...)`, `chore(...)`, `docs(...)`.

Why this matters
- These rules are intentionally lightweight so contributors can follow them without heavy tooling. When CI or contributor machines support formatters, run them before commits.
