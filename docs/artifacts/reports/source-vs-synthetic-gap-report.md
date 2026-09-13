# Source vs Synthetic Gap Report

**Generated:** 2026-09-13  
**Baseline:** BAS-REF-001  
**Comparison:** as_is (source-grounded) vs synthetic_reference (hypothetical automotive project)

## Overview

This report documents the gaps between what is actually present in the foxBMS 2 source repository (as_is profile) and what is required for a complete hypothetical automotive BMS development project (synthetic_reference profile).

## Profile Definitions

| Aspect | as_is | synthetic_reference |
|--------|-------|---------------------|
| **Definition** | Faithful reconstruction of pinned foxBMS sources | Complete hypothetical automotive BMS project grounded in foxBMS |
| **Provenance** | source_observed, derived | source_observed, derived, synthetic |
| **Approval** | N/A (observation) | synthetic_decision (fictional roles) |
| **Production Authority** | false | false |
| **Verification Credit** | false | false |

## Gap Analysis by Category

### 1. Safety Engineering Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| Hazard Analysis | Derived (1) | Complete (1) | - |
| Safety Goals | Derived (1) | Complete (1) | - |
| FSRs | Back-inferred (4) | Forward-engineered (4) | Synthetic adds FSR-004 (independent monitor) |
| TSRs (HW) | Back-inferred (3) | Forward-engineered (3) | Timing budgets explicit |
| SWR (SW) | Back-inferred (3) | Forward-engineered (3) | Timing budgets explicit |
| Safety Analyses | Not present | FMEA, FTA, Dep. Failure, FFIO | Major gap |
| Safety Case | Not present | Skeleton with claims/args | Major gap |

### 2. System Engineering Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| Stakeholder Needs | Not documented | Synthetic (3 needs) | Complete gap |
| System Requirements | Implied by code | Explicit SYS reqs | Complete gap |
| System Architecture | Documented (3-layer) | Explicit HSI authority | Partial |
| HW/SW Allocation | Implied by modules | Explicit allocation | Gap |
| Integration Strategy | Implied | Explicit strategy | Gap |
| Validation Measures | Not present | Synthetic plan | Major gap |

### 3. Hardware Engineering Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| HW Requirements | Derived from datasheets | Explicit TSRs (3) | Partial |
| HW Architecture | Altium packages (not analyzed) | Referenced in HSI | Partial |
| HW Detailed Design | Altium files (not analyzed) | Not analyzed | Gap |
| HW Safety Analysis | Not present | FMEDA (synthetic) | Major gap |
| HW Verification | Not present | Synthetic procedures | Major gap |

### 4. Software Engineering Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| SW Requirements | Back-inferred (3) | Explicit SWRs (3) | Partial |
| SW Architecture | Documented (3-layer) | Explicit (1 arch) | Partial |
| SW Detailed Design | Source code | 3 detailed designs | Partial |
| Implementation Mapping | Source code | Explicit mapping | Partial |
| Coding Guidelines | .clang-format | Not documented | Gap |
| Static Analysis | Not documented | Plans/findings | Gap |
| Unit Verification | 80 tests (Unity/CMock) | 11 test measures (6 synthetic + 5 as_is grounded in real unit tests) | Partial |
| Integration Verification | Not present | Not generated | Major gap |
| Regression Selection | Not documented | "Always in regression" | Gap |

### 5. Verification & Validation Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| Verification Strategy | Not documented | Per FSR approach | Gap |
| Test Plans | Unity/CMock configs | 11 test measures | Partial |
| Test Specifications | Test source code | Structured TMS | Partial |
| Test Executions | CI runs (not captured) | 7 executions (1 actual_host_run + 6 synthetic_fixture) | Partial |
| Coverage Analysis | Not documented | Not generated | Gap |
| Anomaly Records | Not captured | Not generated | Gap |
| Validation Measures | Not present | Synthetic plan | Major gap |

### 6. Management & Supporting Process Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| Project Plan | Not present | Synthetic scope/plan | Complete gap |
| Safety Plan | Not present | Synthetic plan | Complete gap |
| Risk Register | Not present | Synthetic in plan | Complete gap |
| Config Management | Git history | Synthetic CM records | Partial |
| Change Management | Git commits/PRs | 3 lifecycle demos | Partial |
| Problem Resolution | GitHub issues | Findings + dispositions | Partial |
| QA/Reviews | Not formalized | 1 domain review | Major gap |
| Measurement | Not present | Synthetic metrics | Complete gap |
| Process Improvement | Not present | Synthetic records | Complete gap |
| Reuse Management | Implicit (FreeRTOS) | Explicit dispositions | Gap |

### 7. Lifecycle Continuation Artifacts

| Artifact | as_is | synthetic_reference | Gap |
|----------|-------|---------------------|-----|
| Release Notes | CHANGELOG.md | Synthetic in lifecycle | Partial |
| Production Test Plans | Not present | Synthetic | Gap |
| Calibration Specs | Not documented | Not generated | Gap |
| Installation/Ops/Service | Not present | Synthetic | Gap |
| Field Monitoring | Not present | Synthetic | Gap |
| Maintenance/Change | Git/PR history | 3 lifecycle demos | Partial |
| Decommissioning/Recycling | Not present | Synthetic assumptions | Gap |

## Quantitative Gap Summary

| Category | as_is Artifacts | synthetic_reference Artifacts | Coverage |
|----------|-----------------|-------------------------------|----------|
| Safety | 6 | 12 | 50% |
| System Engineering | 1 | 8 | 12% |
| Hardware | 3 | 8 | 38% |
| Software | 7 | 12 | 58% |
| Verification | 2 | 8 | 25% |
| Management | 0 | 7 | 0% |
| Lifecycle | 1 | 6 | 17% |
| **Total** | **25** | **55** | **45%** |

## Key Observations

### What foxBMS Provides (as_is Strengths)
1. **Complete working implementation** - All 20 features implemented in C
2. **Extensive unit test suite** - 120 tests with Unity/CMock
3. **Multiple AFE variants** - 7 AFE families supported
4. **Modular architecture** - Clear 3-layer separation
5. **Multiple hardware variants** - 7 slave board designs
6. **Bootloader with CAN update** - CRC64 verified
6. **Multiple hardware variants** - 7 slave board designs

### What Synthetic Reference Adds (synthetic_reference Value)
1. **Explicit safety engineering** - HARA, FSC, TSC, FSRs, TSRs, SWRs
2. **Traceability** - Complete vertical/lateral chains
3. **Parameter registry** - Single source of truth for 10 parameters
4. **Assumption management** - 12 explicit assumptions with validity
5. **Timing budgets** - FTTI allocation with 30ms margin
5. **Independent monitor** - Addresses FTTI violation
6. **Safety analyses** - FMEA, FTA, dependent failure (synthetic)
7. **Safety case** - Structured argument with claims/evidence
6. **Change management** - 3 full lifecycle demos
7. **Mutation scenarios** - 20/20 for corpus validation (severity+category matched)
8. **Tooling** - Corpus management CLI
7. **Reports** - 10 comprehensive reports

### What Neither Has (Remaining Gaps)
1. **FTA depth** - FTA skeleton exists (`FB2-SAF-ANL-000002`) with empty gate lists
2. **Integration tests** - Only unit tests
3. **Target hardware evidence** - All tests on host
4. **Human approval** - All pending
5. **Production authorization** - All false
6. **Tool qualification** - Approach only
7. **Cybersecurity** - Not addressed
8. **SOH algorithm** - Placeholder only

## Recommendations

### For foxBMS Project (as_is improvements)
1. Document explicit safety goals and FSRs
3. Create HSI specification document
4. Add integration test framework
5. Document coding guidelines and static analysis setup
6. Formalize change management process
7. Create safety plan and risk register

### For Synthetic Corpus (completeness)
1. Implement remaining 18 mutation scenarios
2. Generate FMEA/FTA artifacts
3. Create safety case with full argument structure
4. Implement tools/corpus.py CLI
3. Generate all 10 reports
4. Create mutation evaluator manifests
5. Complete 18 remaining mutation scenarios
6. Create 3 evaluator manifests for change lifecycles
