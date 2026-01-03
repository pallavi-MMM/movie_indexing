# Changelog

## Unreleased

- feat(schema): add field confidences and provenance support; strict validation and tests

### Details

- Added `character_dominance_ranking`, `field_confidences`, and `field_provenance` to the canonical scene schema.
- Enhanced `src/scene_schema.py` to validate numeric min/max constraints and object `additionalProperties` values.
- Added unit tests to assert schema validation and strict enforcement (`SCHEMA_STRICT`).

See `PR_DRAFT.md` for testing notes and follow-up tasks.

