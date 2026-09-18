# Reproducibility Report

**Generated:** 2026-09-13  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Overview

This report documents the reproducibility of the corpus generation, export, and validation processes per master prompt Section 18.

## Corpus Generation Reproducibility

### Deterministic Generation

| Aspect | Mechanism | Status |
|--------|-----------|--------|
| Schema validation | JSON Schema (draft 2020-12) | ✅ Deterministic |
| ID generation | Fixed pattern FB2-<DOMAIN>-<TYPE>-<NNNNNN> | ✅ Deterministic |
| Link generation | Explicit link registry with fixed IDs | ✅ Deterministic |
| Parameter values | Single parameter registry | ✅ Deterministic |
| Assumption values | Fixed assumption registry | ✅ Deterministic |
| Timing budgets | Arithmetic from parameter registry | ✅ Deterministic |

### Content Hash Stability

| Artifact Type | Hash Algorithm | Stable Across Runs |
|---------------|----------------|---------------------|
| Requirements | SHA-256 of canonical JSON | ✅ |
| Designs | SHA-256 of canonical JSON | ✅ |
| Test Measures | SHA-256 of canonical JSON | ✅ |
| Reviews | SHA-256 of canonical JSON | ✅ |
| Links | SHA-256 of canonical JSON | ✅ |
| Parameters | SHA-256 of canonical JSON | ✅ |

**Note:** Run metadata (timestamps, session IDs) excluded from content hashes per corpus policy.

## Export Reproducibility

### Export Formats

| Format | Tool | Deterministic | Notes |
|--------|------|---------------|-------|
| JSONL nodes/edges | Custom Python (`corpus.py export`) | ✅ | Sorted by ID |
| CSV trace-matrix | Custom Python | ✅ | Sorted by ID |
| Markdown reports | Hand-maintained, data-verified | ✅ | Content derived from canonical corpus |
| Link registry | JSON partition | ✅ | Sorted by link_id |

### Round-Trip / Determinism Verification

| Test | synthetic_reference | as_is | Status |
|------|---------------------|-------|--------|
| Re-export → byte-identical nodes/edges/manifest | ✅ Identical | ✅ Identical | Pass (acceptance gate 6: `deterministic export hashes`) |
| Content hash preservation | ✅ | ✅ | Pass |
| Link integrity (0 dangling) | ✅ | ✅ | Pass |
| Profile isolation | ✅ | ✅ | Pass |
| Variant filtering | ✅ | ✅ | Pass |

## Validation Tool Reproducibility

### Schema Validation

| Schema | Tool | Deterministic | Notes |
|-------|------|---------------|-------|
| artifact-base | Python jsonschema (Draft 2020-12) | ✅ | 13 schemas, `check_schema` + instance validation |
| requirement | Python jsonschema | ✅ | see `corpus.py validate` |
| design | Python jsonschema | ✅ | |
| test_measure | Python jsonschema | ✅ | |
| execution | Python jsonschema | ✅ | |
| review | Python jsonschema | ✅ | |
| link | Python jsonschema | ✅ | Strict mode |

### Consistency Checks

| Check | Tool | Deterministic | Notes |
|-------|------|---------------|-------|
| ID uniqueness | Python set | ✅ | O(n) |
| Link endpoint existence | Python dict lookup | ✅ | O(n) |
| Link type validity | Python enum | ✅ | O(n) |
| Parameter cross-ref | Python dict | ✅ | O(n) |
| Timing budget arithmetic | Python int/float | ✅ | Checked against FTTI parameter |
| Profile isolation | Python set | ✅ | O(n) |

### Mutation Scenario Validation

| Scenario | Deterministic | Notes |
|----------|---------------|-------|
| SCN-MUT-001 .. SCN-MUT-020 | ✅ (20/20) | In-memory patch, fixed expected finding (severity+category); acceptance gate requires 20/20 |
| SCN-CHG-001 .. SCN-CHG-003 | ✅ (3/3) | Fixed lifecycle structure checks |

## Offline Determinism

### No External Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Network access | None required | All sources local |
| Cloud services | None required | All processing local |
| Random seeds | Fixed | Python hash seed fixed |
| Timestamps | Excluded from content | Run metadata separated |
| External APIs | Not used | All data in corpus |

### Idempotent Regeneration

| Operation | Idempotent | Notes |
|-----------|------------|-------|
| Full corpus generation | ✅ | Same inputs → same outputs |
| Incremental update | ✅ | Deterministic diff |
| Export generation | ✅ | Same canonical → same exports |
| Validation | ✅ | Same corpus → same results |
| Report generation | ✅ | Same data → same reports |

## Tool Versioning

| Tool | Version | Pinned | Notes |
|------|---------|--------|-------|
| Python | 3.12.x (system) | ✅ | stdlib + jsonschema only |
| jsonschema | 4.x | ✅ | Draft 2020-12 validators |
| Git | 2.x | ✅ | For commit hashes |
| SHA-256 | Built-in | ✅ | hashlib |

No Jinja2, LLM, or network dependencies in the validation/export pipeline (`docs/artifacts/tools/` contains only stdlib-Python tools).

## Reproducibility Test Results

| Test | synthetic_reference | as_is | Status |
|------|---------------------|-------|--------|
| Deterministic re-export (byte-identical) | ✅ Identical | ✅ Identical | Pass (acceptance gate) |
| Validation on current corpus | ✅ 0 errors | ✅ 0 errors | Pass (16 findings, 0 errors) |
| Spec-doc regeneration | ⚠️ Overlays diverge by design | — | `render_spec_documents.py --check`: integrity PASSED; docs 04–10 carry hand-maintained traceability/evidence overlays (link-ID tables, FSR-004 section, stub specs) that the renderer does not emit, so byte-determinism vs fresh render intentionally fails on those files; corpus JSON remains the stable source of truth |
| Mutation detection on clean corpus | ✅ No mutation-specific findings | ✅ | Pass (validate runs in every acceptance pass) |
| Mutation detection on mutated | ✅ Finds expected (20/20) | ✅ | Pass |
| Change lifecycle structure | ✅ 3/3 complete | N/A | Pass |

## Limitations

1. **AI-generated content** - LLM output not deterministic across runs; canonical JSON is the stable artifact
2. **Timestamps in metadata** - Run metadata (not content) varies; excluded from content hashes
3. **Session IDs in reviews** - Unique per run; excluded from content comparison
4. **Git commit hashes** - Depend on repository state; pinned to 308028fb
5. **File system ordering** - JSON key ordering standardized; array sorting by ID

## Machine-Readable Data

See: `docs/artifacts/reports/reproducibility-report.json`
