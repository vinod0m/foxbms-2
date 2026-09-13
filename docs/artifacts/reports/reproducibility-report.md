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
| Schema validation | JSON Schema (draft-07) | ✅ Deterministic |
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
| JSONL nodes/edges | Custom Python | ✅ | Sorted by ID |
| CSV inventory | Custom Python | ✅ | Sorted by ID |
| Markdown reports | Jinja2 templates | ✅ | Sorted, fixed template |
| Link registry | JSON partition | ✅ | Sorted by link_id |

### Round-Trip Import/Export

| Test | synthetic_reference | as_is | Status |
|------|---------------------|-------|--------|
| Export → Import → Export | ✅ Identical | ✅ Identical | Pass |
| Content hash preservation | ✅ | ✅ | Pass |
| Link integrity | ✅ | ✅ | Pass |
| Profile isolation | ✅ | ✅ | Pass |
| Variant filtering | ✅ | ✅ | Pass |

## Validation Tool Reproducibility

### Schema Validation

| Schema | Tool | Deterministic | Notes |
|--------|------|---------------|-------|
| artifact-base | Python jsonschema | ✅ | Strict mode |
| requirement | Python jsonschema | ✅ | Strict mode |
| design | Python jsonschema | ✅ | Strict mode |
| test_measure | Python jsonschema | ✅ | Strict mode |
| execution | Python jsonschema | ✅ | Strict mode |
| review | Python jsonschema | ✅ | Strict mode |
| link | Python jsonschema | ✅ | Strict mode |

### Consistency Checks

| Check | Tool | Deterministic | Notes |
|-------|------|---------------|-------|
| ID uniqueness | Python set | ✅ | O(n) |
| Link endpoint existence | Python dict lookup | ✅ | O(n) |
| Link type validity | Python enum | ✅ | O(n) |
| Parameter cross-ref | Python dict | ✅ | O(n) |
| Timing budget arithmetic | Python decimal | ✅ | Exact arithmetic |
| Profile isolation | Python set | ✅ | O(n) |

### Mutation Scenario Validation

| Scenario | Deterministic | Notes |
|----------|---------------|-------|
| SCN-MUT-001 | ✅ | Fixed patch, fixed expected finding |
| SCN-MUT-002 | ✅ | Fixed patch, fixed expected finding |

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
| Python | 3.11+ | ✅ | Standard library only |
| jsonschema | 4.x | ✅ | Pinned in requirements |
| Jinja2 | 3.x | ✅ | Pinned in requirements |
| Git | 2.x | ✅ | For commit hashes |
| SHA-256 | Built-in | ✅ | hashlib |

## Reproducibility Test Results

| Test | synthetic_reference | as_is | Status |
|------|---------------------|-------|--------|
| Fresh generation from canonical | ✅ Identical | ✅ Identical | Pass |
| Export → Import → Export cycle | ✅ Identical | ✅ Identical | Pass |
| Validation on regenerated | ✅ Pass | ✅ Pass | Pass |
| Reports from regenerated | ✅ Identical | ✅ Identical | Pass |
| Mutation detection on clean | ✅ Detects | ✅ Detects | Pass |
| Mutation detection on mutated | ✅ Finds expected | ✅ Finds expected | Pass |
| Change lifecycle application | ✅ Produces BAS-REF-002/3/4 | N/A | Pass |

## Limitations

1. **AI-generated content** - LLM output not deterministic across runs; canonical JSON is the stable artifact
2. **Timestamps in metadata** - Run metadata (not content) varies; excluded from content hashes
3. **Session IDs in reviews** - Unique per run; excluded from content comparison
4. **Git commit hashes** - Depend on repository state; pinned to 308028fb
5. **File system ordering** - JSON key ordering standardized; array sorting by ID

## Machine-Readable Data

See: `docs/artifacts/reports/reproducibility-report.json`
