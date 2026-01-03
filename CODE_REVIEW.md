# Code Review Findings: Potential Pitfalls and Recommendations

## Issues Found

### 1. **Silent Exception Swallowing in `run_local_pipeline.py`** ⚠️ MODERATE
**Location:** Line ~83 in `run_local_pipeline.py`
```python
if video_path:
    try:
        fap = FaceActorPipeline(...)
        ...
    except Exception:
        # On any runtime error, do not break the pipeline; leave characters_result None
        characters_result = None
```

**Issue:** This broad `except Exception` silently suppresses all errors, making debugging difficult. If the actor catalog has corrupt embeddings or FaceActorPipeline fails, the error is never logged.

**Recommendation:**
- Add debug logging (print or logging module) before silencing the exception
- Consider re-raising on specific errors (ValueError for embedding mismatch)
- At minimum, log the exception traceback for debugging

**Fix:** Add logging or conditional re-raising.

---

### 2. **Missing None Checks in Character Aggregation** ⚠️ LOW
**Location:** `src/scene_fusion.py` line ~122
```python
if isinstance(first_val, list):
    if first_val and isinstance(first_val[0], dict) and field == "characters":
        # Special-case for character lists...
        for val, conf, prov in candidates:
            if isinstance(val, list):
                for item in val:
                    name = item.get("name")
```

**Issue:** If `item` is a dict but missing the "name" key, it's silently skipped. If `screen_time` is not numeric, aggregation silently uses 0.0.

**Recommendation:** Add explicit validation or error handling for malformed character records.

---

### 3. **Empty Actor Catalog Handling** ⚠️ LOW
**Location:** `src/run_local_pipeline.py` line ~84-86
```python
if isinstance(actor_catalog, dict):
    for name, emb in actor_catalog.items():
        if isinstance(emb, list):
            fap.register_actor(name, emb)
```

**Issue:** If `actor_catalog` is an empty dict, FaceActorPipeline runs with zero actors. It will produce mock tracks but no actor matches. This is acceptable but should be documented.

**Recommendation:** This is acceptable behavior (empty catalog → no actor links). Consider adding a check to skip face->actor if actor_catalog is empty.

---

### 4. **No Validation of Embedding Dimension Mismatch** ⚠️ MODERATE
**Location:** `src/actor_db.py` line ~31
```python
def add_actor(self, name: str, embedding: List[float], ...):
    if len(embedding) != self.dim:
        raise ValueError("embedding dimension mismatch")
```

**Issue:** This raises ValueError but the caller in `run_local_pipeline.py` is wrapped in a broad `except Exception`, so the error is silently swallowed. The user will never know their embedding had wrong dimension.

**Recommendation:** Log the error before silencing, or validate embeddings at entry point (e.g., in the scene dict validation).

---

### 5. **Character Confidence Map Format Not Validated** ⚠️ LOW
**Location:** `src/scene_fusion.py` line ~135-140
```python
if isinstance(conf, dict):
    # conf maps item names to confidences
    item_conf = conf.get(name)
elif isinstance(conf, (int, float)):
    item_conf = conf
```

**Issue:** If `field_confidences["characters"]` is malformed (e.g., contains non-numeric values), no error is raised; the value is just skipped.

**Recommendation:** Add optional validation to detect malformed confidence maps early.

---

## Test Results

✓ All 7 code review tests passed locally:
- Minimal scene processing
- Full-context enrichment
- Face->actor pipeline (mocked)
- Actor DB persistence
- Multi-scene sequence processing
- Null/missing field handling
- Character aggregation edge cases

**Verdict:** No runtime failures on new movies, but silent error suppression is a concern for production debugging.

## Recommendations (Priority Order)

1. **HIGH:** Add logging/debugging to `except Exception` blocks so silent failures are traceable.
2. **MEDIUM:** Log embedding dimension mismatches explicitly before silencing.
3. **LOW:** Add optional validation for malformed character records and confidence maps.
4. **LOW:** Document expected format of actor_catalog and field_confidences in comments.
5. **OPTIONAL:** Consider using logging module instead of print for better observability.

## No Critical Bugs Found

The code is robust enough for new movie processing. The main issue is observability—errors are caught but not reported, which makes debugging production issues harder.
