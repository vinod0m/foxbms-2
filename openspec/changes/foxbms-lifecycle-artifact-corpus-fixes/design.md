# Design: Fix foxBMS 2 Lifecycle Artifact Corpus

## Approach

This design addresses four interconnected fixes to the existing corpus:

1. **Source Registry Regeneration** — Replace fabricated registry with AST-derived anchors
2. **Mutation Scenarios + Evaluator Manifests** — Implement 18 missing mutations + 5 evaluator manifests
3. **Link Integrity Fixes** — Resolve dangling links, ensure profile-partitioned resolution
4. **Evaluator Manifests** — Create 5 missing oracle manifests for existing scenarios

## Component 1: Source Registry Regeneration

### Algorithm
1. Run `graphify update .` to extract fresh AST
2. Parse `graphify-out/graph.json` for all C functions in `src/` and `conf/`
3. For each function, create anchor with:
   - `anchor_id`: `FB2-SRC-COD-XXXXXX` (sequential)
   - `source_type`: "code"
   - `location`: { repository, commit, path, symbol, line_range, working_file_hash }
   - `content_hash`: SHA256 of function body
   - `retrieval_date`: current date
4. For header functions, use `.h` path and declared symbol
5. Preserve existing hardware, documentation, test anchors (they're not fabricated)
6. Remove 22 unused anchors

### Data Structures
```json
{
  "schema_version": "1.0.0",
  "created_at": "2026-09-10T...",
  "updated_at": "2026-09-10T...",
  "repository_commit": "308028fb",
  "anchors": [
    {
      "anchor_id": "FB2-SRC-COD-000001",
      "source_type": "code",
      "location": {
        "repository": "foxbms-2",
        "commit": "308028fb",
        "path": "src/app/application/soa/soa.c",
        "symbol": "SOA_CheckVoltages",
        "line_range": "120-180",
        "working_file_hash": "sha256:abc123..."
      },
      "content_hash": "sha256:...",
      "retrieval_date": "2026-09-10T..."
    }
  ]
}
```

### Implementation
- Python script using `graphify-out/graph.json` as input
- Output: `docs/artifacts/sources/source-registry.json`
- Validate: all corpus `source_refs` resolve to new anchors

## Component 2: Mutation Scenarios (18 Missing) + Evaluator Manifests

### Mutation Categories to Implement

| ID | Category | Description |
|----|----------|-------------|
| SCN-MUT-003 | Stale revision/review | Artifact revision mismatch |
| SCN-MUT-004 | Unit/scaling mismatch | Parameter unit/scaling inconsistency |
| SCN-MUT-005 | HW/SW pin/polarity mismatch | HSI pin/polarity conflict |
| SCN-MUT-006 | Timing budget overflow | Timing budget exceeds FTTI |
| SCN-MUT-007 | Threshold contradiction | Warning/derating/shutdown order violated |
| SCN-MUT-008 | Missing fault reaction | Safety req without fault reaction |
| SCN-MUT-009 | ASIL downgrade | ASIL downgraded without justification |
| SCN-MUT-010 | False diagnostic coverage | Unsupported diagnostic coverage claim |
| SCN-MUT-011 | Invalid config combo | Mutually exclusive options enabled |
| SCN-MUT-012 | Fabricated evidence | synthetic_fixture labeled as actual_host_run |
| SCN-MUT-013 | Unjustified N/A | Requirement marked N/A without justification |
| SCN-MUT-013 | Dangling evidence | Evidence references non-existent artifact |
| SCN-MUT-014 | Duplicate ID | Duplicate artifact ID within profile |
| SCN-MUT-014 | Source anchor drift | Source anchor symbol/line mismatch |
| SCN-MUT-015 | Unsafe workflow promotion | production_authorized=true without approval |
| SCN-MUT-015 | Incomplete change propagation | Change missing dependent artifacts |
| SCN-MUT-016 | Circular refinement | Refinement chain forms cycle |
| SCN-MUT-016 | Missing verification | Safety req without verifies/validates link |
| SCN-MUT-017 | Multi-defect timing+threshold | Combined timing + threshold errors |

### Artifact Structure per Mutation
```
docs/artifacts/scenarios/mutations/mutation-XXX-<category>.json
{
  "id": "FB2-SCN-MUT-XXX",
  "scenario_id": "SCN-MUT-XXX",
  "scenario_type": "mutation",
  "baseline_ref": "BAS-REF-001",
  "patch": { "operation": "modify|delete|add", "affected_links": [...], "new_value": {...} },
  "affected_ids": [...],
  "trigger": { "source": "...", "description": "..." },
  "expected_detector": "traceability_checker|link_validator|semantic_rule",
  "expected_finding": { "finding_id": "FB2-FND-MUT-XXXXXX", "severity": "high|medium", "category": "traceability|verification|...", "description": "..." },
  "impact_paths": [...],
  "expected_remediation": "Description of fix",
  "oracle_manifest_ref": "SCN-MUT-XXX/oracle-manifest.json"
}
```

### Evaluator Manifest Structure
```
docs/artifacts/scenarios/evaluator-only/SCN-MUT-XXX/oracle-manifest.json
{
  "scenario_id": "SCN-MUT-XXX",
  "expected_findings": [
    {
      "finding_id": "FB2-FND-MUT-XXXXXX",
      "severity": "high|medium",
      "category": "traceability|verification|evidence|traceability|provenance|process",
      "description": "...",
      "affected_ids": [...],
      "expected_detector": "traceability_checker|link_validator|semantic_rule"
    }
  ]
}
```

## Component 3: Link Integrity Fixes

### Dangling Link Resolution
1. **Review artifact**: Copy `docs/artifacts/reviews/records/review-vertical-slice.json` → `docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json` so `as_is` links resolve
2. **Synthetic reference links**: Ensure all 14 links in `docs/artifacts/corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json` reference only synthetic_reference artifacts (already fixed)

### Link Registry Structure
```
docs/artifacts/traceability/link-registry/
├── as_is/
│   └── links-cell-voltage.json          # 20 links, all as_is artifacts
└── synthetic_reference/
    └── links-cell-voltage.json          # 14 links, all synthetic_reference artifacts

docs/artifacts/corpus/synthetic_reference/traceability/link-registry/synthetic_reference/
└── links-cell-voltage.json              # Mirror of above
```

### Link Validation Rules
- Profile-aware resolution: `as_is` links → `as_is` artifacts; `synthetic_reference` → `synthetic_reference`
- Cross-profile links flagged as dangling
- Required metadata: link_id, source_id/revision, target_id/revision, relation_type, profile, scenario_id, baseline_id, variant_applicability, rationale, provenance, review_state, change_suspect_status

## Component 4: Evaluator Manifests for Existing Scenarios

### Missing Manifests (5 total)
| Scenario | Path | Expected Finding |
|----------|------|------------------|
| SCN-MUT-001 | `scenarios/evaluator-only/SCN-MUT-001/oracle-manifest.json` | FB2-FND-MUT-000001 |
| SCN-MUT-002 | `scenarios/evaluator-only/SCN-MUT-002/oracle-manifest.json` | FB2-FND-MUT-000002 |
| SCN-CHG-001 | `scenarios/evaluator-only/SCN-CHG-001/oracle-manifest.json` | Change lifecycle findings |
| SCN-CHG-002 | `scenarios/evaluator-only/SCN-CHG-002/oracle-manifest.json` | Change lifecycle findings |
| SCN-CHG-003 | `scenarios/evaluator-only/SCN-CHG-003/oracle-manifest.json` | Change lifecycle findings |

### Oracle Manifest Schema
```json
{
  "scenario_id": "SCN-MUT-001",
  "expected_findings": [
    {
      "finding_id": "FB2-FND-MUT-000001",
      "severity": "high",
      "category": "traceability",
      "description": "FSR FB2-SAF-FSR-000001 has no parent safety goal (missing refines link)",
      "affected_ids": ["FB2-SAF-FSR-000001", "FB2-SAF-SGO-000001"],
      "expected_detector": "traceability_checker"
    }
  ]
}
```

## Implementation Sequence

### Phase 1: Source Registry Regeneration (Day 1)
1. Run `graphify update . --no-cluster` to get fresh AST
2. Write Python script `tools/regenerate_source_registry.py` using graphify AST
2. Generate new `docs/artifacts/sources/source-registry.json`
3. Update corpus artifacts' `source_refs` if needed
4. Run `python3 docs/artifacts/tools/corpus.py validate` — expect 0 errors

### Phase 2: Link Integrity Fixes (Day 1-2)
1. Copy review artifact to `corpus/as_is/reviews/records/`
2. Verify synthetic_reference links all resolve
3. Run `python3 docs/artifacts/tools/corpus.py validate` — expect 0 errors

### Phase 3: Mutation Scenarios (Day 2-3)
1. Create 18 mutation JSON files in `scenarios/mutations/`
2. Create 20 evaluator manifests in `scenarios/evaluator-only/SCN-MUT-XXX/`
3. Run `python3 docs/artifacts/tools/corpus.py scenario-test` — all PASS

### Phase 4: Evaluator Manifests for Existing Scenarios (Day 3)
1. Create 5 missing evaluator manifests for SCN-MUT-001, 002, CHG-001, 002, 003
2. Run `python3 docs/artifacts/tools/corpus.py scenario-test` — all PASS

### Phase 5: Full Validation (Day 3)
1. Run full acceptance suite: `python3 docs/artifacts/tools/corpus.py check`
2. Run self-tests: `python3 docs/artifacts/tools/corpus.py selftest`
3. All gates PASS

## Validation Checkpoints

| Checkpoint | Command | Expected |
|------------|---------|----------|
| Source registry | `python3 tools/regenerate_source_registry.py` | 42 anchors, all match AST |
| Corpus validate | `python3 docs/artifacts/tools/corpus.py validate` | 0 errors |
| Link validation | `python3 docs/artifacts/tools/corpus.py validate` | 0 dangling |
| Mutation tests | `python3 docs/artifacts/tools/corpus.py scenario-test` | 20/20 PASS |
| Change lifecycle | `python3 docs/artifacts/tools/corpus.py scenario-test` | 3/3 PASS |
| Full acceptance | `python3 docs/artifacts/tools/corpus.py check` | PASSED |
| Self-tests | `python3 docs/artifacts/tools/corpus.py selftest` | 11/11 PASS |

## Files to Modify/Create

### New Files
- `tools/regenerate_source_registry.py` — regeneration script
- `docs/artifacts/sources/source-registry.json` — regenerated
- `docs/artifacts/scenarios/mutations/mutation-003-*.json` through `mutation-020-*.json` (18 files)
- `docs/artifacts/scenarios/evaluator-only/SCN-MUT-003/...` through `SCN-MUT-020/` (18 dirs + manifests)
- `docs/artifacts/scenarios/evaluator-only/SCN-MUT-001/oracle-manifest.json` (existing, verify)
- `docs/artifacts/scenarios/evaluator-only/SCN-MUT-002/oracle-manifest.json` (existing, verify)
- `docs/artifacts/scenarios/evaluator-only/SCN-CHG-001/oracle-manifest.json`
- `docs/artifacts/scenarios/evaluator-only/SCN-CHG-002/oracle-manifest.json`
- `docs/artifacts/scenarios/evaluator-only/SCN-CHG-003/oracle-manifest.json`
- `docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json` (copy)

### Modified Files
- `docs/artifacts/sources/source-registry.json` — replaced
- `docs/artifacts/corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json` — verify 14 valid links
- `docs/artifacts/tools/corpus.py` — may need minor updates for new mutation types

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AST extraction misses symbols | Graphify already extracted 2817 functions; validate against corpus refs |
| Mutation detection fails | Test each mutation with `scenario-test` before committing |
| Evaluator manifest mismatch | Validate manifests against schema before committing |
| Link resolution breaks | Run `validate` after each link change |

## Acceptance Criteria

- [ ] `python3 docs/artifacts/tools/corpus.py check` → PASSED
- [ ] `python3 docs/artifacts/tools/corpus.py validate` → 0 errors, 0 dangling links
- [ ] `python3 docs/artifacts/tools/corpus.py scenario-test` → 20/20 mutations PASS, 3/3 change lifecycles PASS
- [ ] `python3 docs/artifacts/tools/corpus.py selftest` → 11/11 PASS
- [ ] Source registry: 42 anchors, all match AST symbols
- [ ] All 20 mutations have evaluator manifests
- [ ] 5 evaluator manifests for existing scenarios created
- [ ] 0 dangling links in validation
- [ ] Corpus status: `synthetic_ready_with_limitations` or better
