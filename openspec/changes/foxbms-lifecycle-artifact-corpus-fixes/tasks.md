# Tasks: foxBMS 2 Lifecycle Artifact Corpus Fixes

## Phase 1: Source Registry Regeneration

- [x] 1.1 Run `graphify update . --no-cluster` to extract fresh AST from codebase
- [x] 1.2 Write Python script `tools/regenerate_source_registry.py` that reads `graphify-out/graph.json` and generates canonical source registry
- [x] 1.3 Generate new `docs/artifacts/sources/source-registry.json` with AST-matched anchors (target: 42 anchors, all symbols verified)
- [x] 1.4 Remove 22 unused anchors from previous registry (FB2-SRC-COD-000011-000030 except used ones, FB2-SRC-DOC-000002-000004, FB2-SRC-TST-000003-000005)
- [x] 1.5 Verify all corpus `source_refs` resolve to new registry anchors
- [x] 1.6 Run `python3 docs/artifacts/tools/corpus.py validate` — verify 0 provenance errors

## Phase 2: Link Integrity Fixes

- [x] 2.1 Copy `docs/artifacts/reviews/records/review-vertical-slice.json` → `docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json` (so as_is links resolve)
- [x] 2.2 Verify `docs/artifacts/corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json` contains only 14 valid links (all source/target in synthetic_reference profile)
- [x] 2.3 Verify `docs/artifacts/traceability/link-registry/as_is/links-cell-voltage.json` has 20 valid links (all as_is artifacts)
- [x] 2.4 Verify `docs/artifacts/traceability/link-registry/synthetic_reference/links-cell-voltage.json` mirrors synthetic_reference registry
- [x] 2.5 Run `python3 docs/artifacts/tools/corpus.py validate` — verify 0 dangling link errors

## Phase 3: Mutation Scenarios (18 Missing)

- [x] 3.1 Create `docs/artifacts/scenarios/mutations/mutation-003-stale-revision.json` — stale revision/review mutation
- [x] 3.2 Create `docs/artifacts/scenarios/mutations/mutation-004-unit-mismatch.json` — unit/scaling mismatch
- [x] 3.3 Create `docs/artifacts/scenarios/mutations/mutation-005-pin-polarity-mismatch.json` — HW/SW pin/polarity mismatch
- [x] 3.4 Create `docs/artifacts/scenarios/mutations/mutation-006-timing-budget-overflow.json` — timing budget exceeds FTTI
- [x] 3.5 Create `docs/artifacts/scenarios/mutations/mutation-007-threshold-contradiction.json` — threshold order violation
- [x] 3.6 Create `docs/artifacts/scenarios/mutations/mutation-008-missing-fault-reaction.json` — missing fault reaction
- [x] 3.7 Create `docs/artifacts/scenarios/mutations/mutation-009-asil-downgrade.json` — unsupported ASIL downgrade
- [x] 3.8 Create `docs/artifacts/scenarios/mutations/mutation-010-false-diagnostic-coverage.json` — false diagnostic coverage
- [x] 3.9 Create `docs/artifacts/scenarios/mutations/mutation-011-invalid-config.json` — invalid config combination
- [x] 3.10 Create `docs/artifacts/scenarios/mutations/mutation-012-fabricated-evidence.json` — synthetic_fixture labeled as actual_host_run
- [x] 3.11 Create `docs/artifacts/scenarios/mutations/mutation-013-unjustified-na.json` — unjustified non-applicability
- [x] 3.12 Create `docs/artifacts/scenarios/mutations/mutation-014-dangling-evidence.json` — dangling evidence reference
- [x] 3.13 Create `docs/artifacts/scenarios/mutations/mutation-014-duplicate-id.json` — duplicate artifact ID within profile
- [x] 3.14 Create `docs/artifacts/scenarios/mutations/mutation-015-source-anchor-drift.json` — source anchor symbol/line drift
- [x] 3.15 Create `docs/artifacts/scenarios/mutations/mutation-015-unsafe-promotion.json` — unsafe workflow promotion
- [x] 3.16 Create `docs/artifacts/scenarios/mutations/mutation-016-incomplete-propagation.json` — incomplete change propagation
- [x] 3.17 Create `docs/artifacts/scenarios/mutations/mutation-016-circular-refinement.json` — circular refinement chain
- [x] 3.18 Create `docs/artifacts/scenarios/mutations/mutation-017-missing-verification.json` — missing verification link
- [x] 3.19 Create `docs/artifacts/scenarios/mutations/mutation-017-multi-defect.json` — multi-defect timing+threshold

## Phase 4: Evaluator Manifests for All Mutations (20)

- [x] 4.1 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-001/oracle-manifest.json` (verify existing)
- [x] 4.2 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-002/oracle-manifest.json` (verify existing)
- [x] 4.3 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-003/oracle-manifest.json`
- [x] 4.4 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-004/oracle-manifest.json`
- [x] 4.5 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-005/oracle-manifest.json`
- [x] 4.6 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-006/oracle-manifest.json`
- [x] 4.7 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-007/oracle-manifest.json`
- [x] 4.8 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-008/oracle-manifest.json`
- [x] 4.9 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-009/oracle-manifest.json`
- [x] 4.10 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-010/oracle-manifest.json`
- [x] 4.11 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-011/oracle-manifest.json`
- [x] 4.12 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-012/oracle-manifest.json`
- [x] 4.13 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-013/oracle-manifest.json`
- [x] 4.14 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-014/oracle-manifest.json`
- [x] 4.15 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-015/oracle-manifest.json`
- [x] 4.19 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-016/oracle-manifest.json`
- [x] 4.20 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-017/oracle-manifest.json`

## Phase 5: Evaluator Manifests for Existing Scenarios (5)

- [x] 5.1 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-001/oracle-manifest.json` (verify)
- [x] 5.2 Create `docs/artifacts/scenarios/evaluator-only/SCN-MUT-002/oracle-manifest.json` (verify)
- [x] 5.3 Create `docs/artifacts/scenarios/evaluator-only/SCN-CHG-001/oracle-manifest.json`
- [x] 5.4 Create `docs/artifacts/scenarios/evaluator-only/SCN-CHG-002/oracle-manifest.json`
- [x] 5.5 Create `docs/artifacts/scenarios/evaluator-only/SCN-CHG-003/oracle-manifest.json`

## Phase 6: Full Validation

- [x] 6.1 Write `tools/regenerate_source_registry.py` script using graphify AST
- [x] 6.2 Run `graphify update . --no-cluster` to get fresh AST
- [x] 6.3 Execute `python3 tools/regenerate_source_registry.py` → generate new `docs/artifacts/sources/source-registry.json`
- [x] 6.3 Run `python3 docs/artifacts/tools/corpus.py validate` — verify 0 errors, 0 provenance errors
- [x] 6.4 Run `python3 docs/artifacts/tools/corpus.py validate` — verify 0 dangling link errors
- [x] 6.5 Run `python3 docs/artifacts/tools/corpus.py scenario-test` — verify 20/20 mutations PASS, 3/3 change lifecycles PASS
- [x] 6.4 Run `python3 docs/artifacts/tools/corpus.py check` — verify all 8 gates PASS
- [x] 6.5 Run `python3 docs/artifacts/tools/corpus.py selftest` — verify 11/11 PASS
- [x] 6.6 Run `python3 docs/artifacts/tools/corpus.py check` — final acceptance suite PASSED
- [x] 6.7 Update tasks.md checkboxes to all complete
- [x] 6.8 Commit and push changes to `foxbms-2-synthetic-data` branch
