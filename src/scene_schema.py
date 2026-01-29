"""Lightweight scene schema validator used to sanity-check per-scene dicts.

This intentionally avoids external dependencies so it can run in CI without extra installs.
It performs non-mutating checks and returns (is_valid, messages) so callers can decide how to proceed.
"""

from typing import Any, Dict, List, Tuple
import os
import json
from pathlib import Path

# When SCHEMA_STRICT is truthy (1/true), callers should fail-fast on validation errors.
STRICT = os.getenv("SCHEMA_STRICT", "0").lower() in ("1", "true", "yes")


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_scene(scene: Dict[str, Any]) -> Tuple[bool, List[str]]:
    msgs: List[str] = []

    if not isinstance(scene, dict):
        return False, ["scene is not a dict"]

    # Minimal required checks
    if "scene_id" not in scene:
        msgs.append("missing scene_id")
    if "movie_id" not in scene:
        msgs.append("missing movie_id")

    # Load canonical schema if available and perform type checks for known fields
    try:
        schema_path = Path(__file__).parent / "schema" / "scene_schema.json"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as sf:
                schema = json.load(sf)
            props = schema.get("properties", {})

            def _check_type(val, expected):
                if expected is None:
                    return True
                if isinstance(expected, list):
                    return any(_check_type(val, t) for t in expected)
                if expected == "string":
                    return isinstance(val, str) or val is None
                if expected == "number":
                    return _is_number(val) or val is None
                if expected == "boolean":
                    return isinstance(val, bool) or val is None
                if expected == "array":
                    return isinstance(val, list) or val is None
                if expected == "object":
                    return isinstance(val, dict) or val is None
                return True

            for field, spec in props.items():
                if field in scene:
                    expected = spec.get("type")
                    val = scene[field]
                    # Accept null for nullable types
                    if val is None:
                        continue
                    # arrays of objects/items
                    if expected == "array" and isinstance(val, list):
                        items = spec.get("items")
                        item_type = items.get("type") if items else None
                        for i, item in enumerate(val):
                            if item_type == "object" and isinstance(item, dict):
                                # shallow check item properties if available
                                subprops = items.get("properties", {})
                                for subk, subspec in subprops.items():
                                    if subk in item:
                                        if not _check_type(
                                            item[subk], subspec.get("type")
                                        ):
                                            msgs.append(
                                                f"field {field}[{i}].{subk} has invalid type"
                                            )
                                        # numeric constraints (minimum/maximum)
                                        if subspec.get(
                                            "type"
                                        ) == "number" and _is_number(item[subk]):
                                            if (
                                                "minimum" in subspec
                                                and item[subk] < subspec["minimum"]
                                            ):
                                                msgs.append(
                                                    f"field {field}[{i}].{subk} below minimum {subspec['minimum']}"
                                                )
                                            if (
                                                "maximum" in subspec
                                                and item[subk] > subspec["maximum"]
                                            ):
                                                msgs.append(
                                                    f"field {field}[{i}].{subk} above maximum {subspec['maximum']}"
                                                )
                            else:
                                if not _check_type(item, item_type):
                                    msgs.append(f"field {field}[{i}] has invalid type")
                    else:
                        # basic types
                        if isinstance(expected, list):
                            ok = any(_check_type(val, t) for t in expected)
                        else:
                            ok = _check_type(val, expected)
                        if not ok:
                            msgs.append(
                                f"field {field} has invalid type (expected {expected}, got {type(val).__name__})"
                            )
                        # handle object additionalProperties (e.g., field_confidences)
                        if expected == "object" and isinstance(val, dict):
                            addl = spec.get("additionalProperties")
                            if isinstance(addl, dict):
                                # validate each value against additionalProperties schema
                                for k2, v2 in val.items():
                                    # additionalProperties can be a schema or contain a oneOf
                                    if isinstance(addl.get("oneOf"), list):
                                        matched = False
                                        option_msgs: List[str] = []
                                        for opt in addl["oneOf"]:
                                            opt_type = opt.get("type")
                                            if opt_type and _check_type(v2, opt_type):
                                                # numeric constraints on this option
                                                if opt_type == "number" and _is_number(
                                                    v2
                                                ):
                                                    if (
                                                        "minimum" in opt
                                                        and v2 < opt["minimum"]
                                                    ):
                                                        option_msgs.append(
                                                            f"below minimum {opt['minimum']}"
                                                        )
                                                        continue
                                                    if (
                                                        "maximum" in opt
                                                        and v2 > opt["maximum"]
                                                    ):
                                                        option_msgs.append(
                                                            f"above maximum {opt['maximum']}"
                                                        )
                                                        continue
                                                # object-with-additionalProperties case
                                                if opt_type == "object" and isinstance(
                                                    v2, dict
                                                ):
                                                    inner_addl = opt.get(
                                                        "additionalProperties"
                                                    )
                                                    if isinstance(inner_addl, dict):
                                                        ok_inner = True
                                                        for in_k, in_v in v2.items():
                                                            in_type = inner_addl.get(
                                                                "type"
                                                            )
                                                            if (
                                                                in_type
                                                                and not _check_type(
                                                                    in_v, in_type
                                                                )
                                                            ):
                                                                ok_inner = False
                                                                option_msgs.append(
                                                                    f"nested field {in_k} has invalid type (expected {in_type})"
                                                                )
                                                                break
                                                            if (
                                                                in_type == "number"
                                                                and _is_number(in_v)
                                                            ):
                                                                if (
                                                                    "minimum"
                                                                    in inner_addl
                                                                    and in_v
                                                                    < inner_addl[
                                                                        "minimum"
                                                                    ]
                                                                ):
                                                                    ok_inner = False
                                                                    option_msgs.append(
                                                                        f"nested field {in_k} below minimum {inner_addl['minimum']}"
                                                                    )
                                                                    break
                                                                if (
                                                                    "maximum"
                                                                    in inner_addl
                                                                    and in_v
                                                                    > inner_addl[
                                                                        "maximum"
                                                                    ]
                                                                ):
                                                                    ok_inner = False
                                                                    option_msgs.append(
                                                                        f"nested field {in_k} above maximum {inner_addl['maximum']}"
                                                                    )
                                                                    break
                                                        if not ok_inner:
                                                            # this option doesn't fully match
                                                            continue
                                                # option validated
                                                matched = True
                                                break
                                        if not matched:
                                            msgs.append(
                                                f"field {field}.{k2} has invalid value ({'; '.join(option_msgs) or 'does not match allowed types'})"
                                            )
                                    else:
                                        expected_type = addl.get("type")
                                        if expected_type and not _check_type(
                                            v2, expected_type
                                        ):
                                            msgs.append(
                                                f"field {field}.{k2} has invalid type (expected {expected_type})"
                                            )
                                        # numeric min/max checks
                                        if expected_type == "number" and _is_number(v2):
                                            if (
                                                "minimum" in addl
                                                and v2 < addl["minimum"]
                                            ):
                                                msgs.append(
                                                    f"field {field}.{k2} below minimum {addl['minimum']}"
                                                )
                                            if (
                                                "maximum" in addl
                                                and v2 > addl["maximum"]
                                            ):
                                                msgs.append(
                                                    f"field {field}.{k2} above maximum {addl['maximum']}"
                                                )
            # If jsonschema available, run full validation to capture structural errors
            try:
                import jsonschema
                from jsonschema import ValidationError

                try:
                    jsonschema.validate(instance=scene, schema=schema)
                except ValidationError as ve:
                    msgs.append(str(ve.message))
            except Exception:
                # jsonschema not installed or validation failed to import — that's OK
                pass
    except Exception:
        # keep old behavior if schema can't be loaded
        pass

    is_valid = len(msgs) == 0
    return is_valid, msgs


def enforce_scene(scene: Dict[str, Any]):
    """Validate and either return (True, []) or raise RuntimeError when STRICT is enabled."""
    valid, msgs = validate_scene(scene)
    if not valid and STRICT:
        raise RuntimeError(f"Scene validation failed: {msgs}")
    return valid, msgs
