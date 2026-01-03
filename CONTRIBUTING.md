Contributing

Quick start
- Create a branch for your change: `git checkout -b feat/your-topic`.
- Run tests: `python -m pytest -q` (or use the helper in `scripts/run_tests.ps1`).
- Keep changes focused and include tests for new behavior.
- Open a PR against `main` with a clear description and testing notes.

PR checklist
- [ ] Tests added/updated
- [ ] Code documented where needed
- [ ] Lint/format applied (if available)
- [ ] CI passes

Notes on ML-backed code
- Heavy ML backends are guarded behind "mock-first" or optional import paths to keep CI and contributors nimble.
- If adding GPU dependencies, put them behind clear optional flags and add permissive tests that skip when the environment lacks the dependency.
