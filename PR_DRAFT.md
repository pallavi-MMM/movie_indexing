Title: Add schema fields for confidence & provenance, strict validation and tests

Summary
-------
This change extends the canonical scene schema (`src/schema/scene_schema.json`) to include:
- `character_dominance_ranking` (ranked characters with normalized scores)
- `field_confidences` (map of field -> confidence score in [0,1])
- `field_provenance` (map of field -> list of provenance strings)

Additionally:
- `src/scene_schema.py` was enhanced to validate numeric bounds and `additionalProperties` types.
- Unit tests were added (`tests/test_schema_fields_and_strict.py`) and updated test harness to be robust.
- A small developer requirements file `dev-requirements.txt` was added for test deps.

Why
---
These fields provide the foundation for structured, confidence-aware fusion and downstream reasoning. Strict validation helps catch regressions early and makes the pipeline deterministic when appropriate.

Testing
-------
- `pytest` passes locally (30 tests, 0 failures, warnings present).
- Added tests validate correct behavior and strict-mode enforcement.

Notes/Followups
--------------
- Add a changelog entry and CI workflow that runs tests on PRs.
- Next tasks: add changelog, create `scene_fusion` module (merge + provenance), add unit tests for fusion.

Reviewer checklist
------------------
- [ ] Schema additions look correct and have clear descriptions
- [ ] Tests cover success & failure cases
- [ ] No unexpected changes to existing behavior


Changelog entry (draft)
-----------------------
- feat(schema): add field confidences and provenance support; strict validation and tests


