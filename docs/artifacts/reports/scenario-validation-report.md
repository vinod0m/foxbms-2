# Scenario Validation Report

**Generated:** 2026-09-20  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference

## Overview

This report documents the execution of mutation scenarios and change lifecycle demonstrations per master prompt Sections 16 and 14.8. All 20 isolated mutation scenarios are implemented, applied in-memory by the harness (`corpus.py scenario-test`), and detected with matching severity/category; all 3 change lifecycle demonstrations pass.

## Mutation Scenarios

### Target: 20 isolated mutation scenarios (minimum)

| Scenario ID | Type | Status | Expected Detector | Finding (severity / category) | Result |
|-------------|------|--------|--------------------|-------------------------------|--------|
| SCN-MUT-001 | Missing parent link | Implemented, detected | Traceability completeness checker | high / traceability | ✅ PASS |
| SCN-MUT-002 | Invalid link type | Implemented, detected | Link validator | high / traceability | ✅ PASS |
| SCN-MUT-003 | Stale revision | Implemented, detected | Revision consistency checker | medium / verification | ✅ PASS |
| SCN-MUT-004 | Unit/scaling mismatch | Implemented, detected | Parameter registry consistency (unit vs value scale) | medium / consistency | ✅ PASS |
| SCN-MUT-005 | HW/SW pin polarity mismatch | Implemented, detected | HSI/HW signal cross-check (polarity/direction) | high / traceability | ✅ PASS |
| SCN-MUT-006 | Incompatible timing | Implemented, detected | Timing budget checker (FTTI) | medium / verification | ✅ PASS |
| SCN-MUT-007 | Contradictory thresholds | Implemented, detected | Parameter registry threshold-order check | high / consistency | ✅ PASS |
| SCN-MUT-008 | Missing fault reaction | Implemented, detected | Fault reaction checker | medium / verification | ✅ PASS |
| SCN-MUT-009 | Unsupported ASIL downgrade | Implemented, detected | ASIL consistency checker | medium / verification | ✅ PASS |
| SCN-MUT-010 | False diagnostic coverage | Implemented, detected | Diagnostic coverage consistency checker | medium / verification | ✅ PASS |
| SCN-MUT-011 | Invalid config combination | Implemented, detected | Parameter registry mutually-exclusive config check | high / consistency | ✅ PASS |
| SCN-MUT-012 | Fabricated evidence class | Implemented, detected | Execution origin-vs-kind classification check | medium / evidence | ✅ PASS |
| SCN-MUT-013 | Unjustified non-applicability | Implemented, detected | Non-applicability justification checker | medium / verification | ✅ PASS |
| SCN-MUT-014 | Dangling evidence | Implemented, detected | Evidence reference existence check | high / provenance | ✅ PASS |
| SCN-MUT-015 | Duplicate identity | Implemented, detected | Duplicate-ID detector (in-profile) | high / traceability | ✅ PASS |
| SCN-MUT-016 | Source anchor drift | Implemented, detected | Source anchor symbol/location drift check | high / provenance | ✅ PASS |
| SCN-MUT-017 | Unsafe workflow promotion | Implemented, detected | Lifecycle status policy checker | medium / verification | ✅ PASS |
| SCN-MUT-018 | Incomplete change propagation | Implemented, detected | Change propagation (revision) checker | high / traceability | ✅ PASS |
| SCN-MUT-019 | Circular refinement | Implemented, detected | Refinement cycle checker | medium / verification | ✅ PASS |
| SCN-MUT-020 | Missing verification link | Implemented, detected | Verification completeness checker | medium / verification | ✅ PASS |

**Completion:** 20/20 (100%) — meets minimum requirement of 20.

**Matching rule:** a scenario passes iff the detector's actual findings include an
entry whose severity matches the expected severity AND (when set) whose category
matches the expected category, scoped to the scenario's `affected_ids`.

### Multi-Defect Interactions

Not implemented (isolated cases are complete; multi-defect scenarios remain a
future corpus extension).

### Clean Controls

Clean control = running the detector suite on the unmutated corpus and requiring
no finding at the mutated location. The acceptance suite (`corpus.py check`)
runs `validate` on the clean corpus every pass; with 16 findings, errors=0, and
no mutation-specific findings on unmutated artifacts, false positives are
controlled.

## Change Lifecycle Demonstrations

### Target: 3 complete demonstrations (minimum)

| Change ID | Type | Status | Baseline Before | Baseline After |
|-----------|------|--------|-----------------|----------------|
| SCN-CHG-001 | Safety threshold/timing | Implemented, passing | BAS-REF-001 | BAS-REF-002 |
| SCN-CHG-002 | HSI/hardware interface | Implemented, passing | BAS-REF-001 | BAS-REF-003 |
| SCN-CHG-003 | Software behavioral defect | Implemented, passing | BAS-REF-001 | BAS-REF-004 |

**Completion:** 3/3 (100%) — meets minimum requirement.

## Change Lifecycle Detail

### SCN-CHG-001: Cell Voltage Threshold (4.2V → 4.15V)

| Phase | Artifact | Status |
|-------|----------|--------|
| Baseline | BAS-REF-001 | ✅ |
| Trigger | Supplier change notification | ✅ |
| Impact Analysis | 6 artifacts, 2 links, 1 review, 1 evidence | ✅ |
| Decision | DEC-CHG-001 (approved) | ✅ |
| New Revisions | 6 artifacts to rev 2 | ✅ |
| Suspect Links | 1 link (test verifies) | ✅ |
| Required Updates | 8 updates identified | ✅ |
| Reverification | 3 tests selected | ✅ |
| Post-Change Baseline | BAS-REF-002 | ✅ |

**Validation:** Change lifecycle demonstrates complete traceability from trigger through impact analysis, decision, updates, reverification, to clean post-change baseline.

### SCN-CHG-002: AFE Interface Change (LTC6811 → ADI ADES1830)

| Phase | Artifact | Status |
|-------|----------|--------|
| Baseline | BAS-REF-001 | ✅ |
| Trigger | Obsolescence notice | ✅ |
| Impact Analysis | 9 artifacts, 5 links, 1 review, 1 evidence | ✅ |
| Decision | DEC-CHG-002 (approved) | ✅ |
| New Revisions | 6 artifacts to rev 2 | ✅ |
| Suspect Links | 5 links (all HSI/allocation/design/test) | ✅ |
| Required Updates | 11 updates including HW FMEDA, monitor redesign | ✅ |
| Reverification | 5 tests (new + regression) | ✅ |
| Post-Change Baseline | BAS-REF-003 | ✅ |

**Validation:** Major architecture change demonstrates cross-domain impact (HW, SW, HSI, verification, independent monitor).

### SCN-CHG-003: SOA Debounce Logic Defect

| Phase | Artifact | Status |
|-------|----------|--------|
| Baseline | BAS-REF-001 | ✅ |
| Trigger | Field report / integration test | ✅ |
| Impact Analysis | 4 artifacts, 3 links, 1 review, 1 evidence | ✅ |
| Decision | DEC-CHG-003 (approved) | ✅ |
| New Revisions | 4 artifacts to rev 2 | ✅ |
| Suspect Links | 3 links (SWR/design/test) | ✅ |
| Required Updates | 5 updates (design, req, impl, test, review) | ✅ |
| Reverification | 2 tests (updated + new transient case) | ✅ |
| Post-Change Baseline | BAS-REF-004 | ✅ |

**Validation:** Software behavioral defect demonstrates defect fix with state machine correction, new test case, and reverification.

## Evaluator-Only Manifest

Per master prompt Section 16, expected labels/oracles are kept separate from the
normal ingestible dataset under `scenarios/evaluator-only/`:

| Scenario | Oracle Manifest | Status |
|----------|----------------|--------|
| SCN-MUT-001 … SCN-MUT-020 | `scenarios/evaluator-only/SCN-MUT-*/oracle-manifest.json` | ✅ Created (20/20) |
| SCN-CHG-001 … SCN-CHG-003 | `scenarios/evaluator-only/SCN-CHG-*/oracle-manifest.json` | ✅ Created (3/3) |

## Scenario Validation Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Isolated mutation scenarios | ≥20 | 20 | ✅ |
| Mutation detection (severity+category match) | 20/20 | 20/20 | ✅ |
| Multi-defect interactions | After isolated | 0 | ⚠️ Future extension |
| Clean controls (no false positives) | Per scenario | via acceptance `validate` | ✅ |
| Change lifecycle demos | ≥3 | 3 | ✅ |
| Safety-related threshold change | 1 | 1 | ✅ |
| HSI/hardware interface change | 1 | 1 | ✅ |
| Software behavioral defect | 1 | 1 | ✅ |
| Evaluator manifests separated | All | 23/23 | ✅ |
| Expected labels outside dataset | All | 23/23 | ✅ |

## Gaps and Limitations

1. **Multi-defect interactions** — not yet implemented; isolated cases (20/20) are complete.
2. **Change lifecycles complete** — 3/3 meets requirement.

## Recommendations

1. Build multi-defect interaction scenarios on top of the completed isolated set.
2. Add legitimate exception scenarios (e.g., intentional `not_applicable`).

## Machine-Readable Data

See: `docs/artifacts/reports/scenario-validation-report.json` (regenerated by
`python3 docs/artifacts/tools/corpus.py scenario-test`).
