# Source vs Synthetic Gap Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Comparison:** `as_is` (source-grounded) vs `synthetic_reference` (hypothetical automotive project)

> Structural comparison only. Nothing here asserts ISO 26262 conformity, ASIL
> capability, ASPICE capability level, certification, human approval or tool
> qualification. All 153 indexed records are `human_approval_status: pending`
> and `production_authorized: false`.
>
> Every number is from a live tool run on 2026-09-29.

## 1. Overview

This report documents the gap between what is actually present in the pinned
foxBMS 2 source tree (`as_is`) and what a complete hypothetical automotive BMS
development project would require (`synthetic_reference`).

## 2. Profile Definitions

| Aspect | `as_is` | `synthetic_reference` |
|---|---|---|
| Definition | Faithful reconstruction of the pinned sources | Complete hypothetical automotive BMS project grounded in foxBMS |
| Provenance | `source_observed`, `derived` | `synthetic`, `source_observed`, `derived` |
| Approval | n/a (observation) | synthetic decision, fictional roles only |
| Production authority | `false` | `false` |
| Verification credit | `false` | `false` |

## 3. Population by Profile and Domain

| Domain | `as_is` | `synthetic_reference` | Total |
|---|---|---|---|
| hardware | 3 | 4 | 7 |
| management | 0 | 7 | 7 |
| safety | 7 | 23 | 30 |
| software | 33 | 7 | 40 |
| supporting | 1 | 1 | 2 |
| system | 0 | 3 | 3 |
| verification | 27 | 37 | 64 |
| **Total** | **71** | **82** | **153** |

The asymmetry is the point: `as_is` is dominated by `software` (33, almost
entirely the 26 static-analysis deviation records) and `verification` (27), while
`synthetic_reference` carries the safety, management and system records that
`as_is` has no equivalent of.

## 4. Gap Analysis by Category

### 4.1 Safety Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| Hazard analysis | 1 (`FB2-SAF-HAZ-000001`) | 1 | none |
| Safety goals | 1 (`FB2-SAF-SGO-000001`) | 1 | none |
| FSRs | 3 | 4 | synthetic adds `FB2-SAF-FSR-000004`, the independent monitor |
| TARA | **none** | 1 (`FB2-SAF-TAR-000001`, 8 threats, 9 mitigations) | **closed for synthetic** |
| Security requirements | **none** | 5 (`FB2-SAF-SEC-000001`…`-000005`) | **closed for synthetic** |
| Safety analyses | **none** | 4 (FMEA, FTA, dependent failure, freedom-from-interference) | major gap in `as_is` |
| Safety case | **none** | 1 skeleton (`FB2-SAF-SCS-000001`) | major gap in `as_is` |
| **Functional safety concept** | **none** | **none** | **open in both** |
| **Technical safety concept** | **none** | **none** | **open in both** |

The last two rows are the significant finding. A functional safety concept and a
technical safety concept are absent from **both** profiles, so ISO 26262 Part 3
is only partially mapped and the ASIL value on the safety goal has no
concept-phase derivation. This is recorded as `CORR-COV-010` in the coverage plan
and as findings `FB2-REV-FND-000020` / `-000021`.

### 4.2 System Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| Stakeholder needs | **none** | **none** | **open in both** (`SYS.1`, gap) |
| System requirements | **none** | **none** | **open in both** (`SYS.2`, gap) |
| System architecture / HSI authority | none | 1 (`FB2-SYS-HSI-000001`) | partial |
| HW/SW allocation | implied by modules | explicit via `allocated_to` links | partial |
| Integration strategy | implied | planning stubs `FB2-VER-TMS-000007`, `-000008` | partial, executions blocked |
| Validation measures | none | `FB2-VER-TMS-000009` stub, execution blocked | partial |

The previous revision of this report claimed synthetic stakeholder and system
requirements existed. They do not, and the coverage-plan claims asserting them
have been corrected under `CORR-COV-001`, `CORR-COV-002` and `CORR-COV-013`.

### 4.3 Hardware Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| HW requirements | 3 TSRs | 4 TSRs | partial |
| HW architecture | Altium packages, not analyzed | referenced in HSI | **format-limited** (`HWE.2`) |
| HW detailed design | Altium binaries, not analyzed | not analyzed | **format-limited** (`HWE.3`) |
| HW safety analysis (FMEDA) | none | not generated | open |
| HW integration test | none | none | open (`HWE.4`, gap) |

`HWE.2` and `HWE.3` are limited by CAD format, not by effort. Only real hardware
analysis closes them.

### 4.4 Software Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| SW requirements | 3 SWRs | 3 SWRs | none |
| SW architecture / design | 3 DSNs | 3 DSNs | none |
| Static-analysis deviations | **26 records** | none | `as_is` strength |
| Unit verification | 5 test measures, 14 executions incl. real host sweeps | 11 test measures, 11 executions | partial, `SWE.4` partially mapped |
| Integration verification | none | planning stub, execution blocked | open |
| Regression selection | not documented | not documented | open in both |

The 26 MISRA deviation records are the single largest block of `as_is` evidence
and were not present in the corpus when this report was first written.

### 4.5 Verification and Validation

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| Test measures | 5 | 11 | — |
| Test executions | 14 | 11 | — |
| **Target-hardware executions** | **0** | **0** | **open in both** |
| Security-requirement verification | n/a | **none** | open (`FB2-REV-FND-000008`…`-000012`) |
| Coverage analysis | none | none | open |
| Anomaly records | 7 finding artifacts | 14 finding artifacts | — |
| Validation measures | none | stub, execution blocked | open |

`actual_product_evidence` is 0/16 and the tool states why: `execution_kind` has
no target-hardware member, so none can be claimed.

### 4.6 Management and Supporting Processes

This is the category with the largest honest gaps. All statuses are read from
`governance/coverage-plan.json` as corrected on 2026-09-29.

| Process | Artifact | `as_is` | `synthetic_reference` | Disposition |
|---|---|---|---|---|
| Project management (MAN.3) | Project Plan, Schedule, Resource Plan, Progress Reports | none | **scope statement only** (`FB2-MAN-SCO-000001`) | **gap** |
| Risk management (MAN.5) | Risk Register, Risk Analyses, Mitigation Plans | none | **TARA threat table only** (`FB2-SAF-TAR-000001`) | **gap** |
| Measurement (MAN.6) | Measurement Plan, Metrics Definitions, Measurement Results | none | **100 acceptance criteria on 26 records, no plan** | **partially mapped** |
| Process improvement (PIM.3) | Improvement Proposals, Improvement Records, Effectiveness Evaluation | none | **none** | **gap** |
| Quality assurance (SUP.1) | QA Plan, Review Records, Audit Records | 1 review | 5 records | `mapped`, but no process-definition record |
| Configuration management (SUP.8) | CM Plan, Configuration Items, Baselines, Change Control | Git history | Git + Waf | `mapped`, but no process-definition record |
| Problem resolution (SUP.9) | Problem Reports, Resolution Records, Trend Analysis | GitHub issues | 7 finding artifacts | `mapped`, but no process-definition record |
| Change request management (SUP.10) | Change Requests, Impact Analyses, Change Decisions | commits/PRs | 3 change records + 3 lifecycle scenarios | `mapped`, but no process-definition record |
| Traceability management (SUP.11) | Traceability Matrix, Links, Coverage Reports | — | **the corpus itself**, 283 links | `mapped` |
| Reuse management (REU.2) | Reuse Strategy, Assessments, Records | FreeRTOS, vendor drivers | reuse inventory | `mapped` |
| Safety plan (ISO Part 2) | — | none | `FB2-MAN-SPL-000001` | present |

**Note the internal disagreement, stated rather than hidden.** `SUP.1`, `SUP.8`,
`SUP.9` and `SUP.10` read `mapped` in `process_inventory`, while the generated
`views/supporting-processes/supporting-processes.md` reports that no
*process-definition* record exists for those families. These are different
claims — review, change and configuration evidence does exist — and both
readings are now recorded in the coverage plan. Those four entries were outside
the scope of the correction pass that fixed `MAN.3`, `MAN.5`, `MAN.6` and
`PIM.3`.

### 4.7 Lifecycle Continuation

| Artifact | `as_is` | `synthetic_reference` | Disposition |
|---|---|---|---|
| Release plan / notes / checklist | version history in pinned source | **none** | `SPL.2` **partially mapped** |
| Production and end-of-line test | none | none | **gap** (ISO Part 7) |
| Operation and field monitoring | none | none | **gap** |
| Service and maintenance | none | none | **gap** |
| Decommissioning and recycling | none | none | **gap** |

None of the domains `production`, `operation`, `service` or `decommissioning`
appears in any record in either profile. The generated
`views/production-operation-service/lifecycle-continuation.md` reports all five
areas as coverage gaps.

## 5. Key Observations

### What foxBMS Provides (`as_is` strengths)

1. **Working implementation** — 612 inventoried source files across 24 modules,
   22 features, 23 variants, all accounted for.
2. **A real test suite that can be run and whose failures are real** — the
   macOS host run executed 136 in-scope tests: 94 passed, 5 failed, 37 build
   failures. The 5 failures are a genuine defect in the product's test setup,
   not a harness artefact.
3. **Extensive static-analysis evidence** — 26 MISRA deviation records, the
   largest single block of `as_is` evidence in the corpus.
4. **Modular architecture** with a documented 3-layer separation and a
   system-owned HSI authority record.
5. **Multiple AFE variants** and multiple hardware board designs referenced from
   the inventory.

### What the Synthetic Reference Adds

1. **Explicit safety engineering** — HARA, safety goals, 4 FSRs, TSRs, SWRs,
   FMEA, FTA, dependent-failure and freedom-from-interference analyses, and a
   safety case skeleton.
2. **A real threat analysis and security requirement set** — `FB2-SAF-TAR-000001`
   with 8 threats and 9 mitigations, and `FB2-SAF-SEC-000001`…`-000005`, with 5
   measurable security requirements.
3. **Traceability** — 283 links, 0 dangling, with a documented direction
   convention.
4. **Parameter and assumption registries** — 10 parameters, 12 assumptions with
   stated validity.
5. **Timing budgets** — FTTI allocation with an explicit 20 ms margin.
6. **Change management** — 3 full lifecycle scenarios, all structurally complete.
7. **Negative-scenario machinery** — 20/20 mutation scenarios detected by the rule each declares (repaired 2026-09-29; see finding `FB2-REV-FND-000032`).
8. **Adversarial review layer** — challenge and meta review passes that found
   4 high-severity findings, two of them about the original review itself.

### What Neither Has — Remaining Gaps

1. **Functional safety concept and technical safety concept** — absent from both
   profiles. ISO 26262 Part 3 is only partially mapped, and the ASIL assignment
   on `FB2-SAF-SGO-000001` has no justification (`FB2-REV-FND-000020`, `-000021`).
2. **Stakeholder needs and system requirements** — absent from both profiles
   (`SYS.1`, `SYS.2`).
3. **Target-hardware evidence** — 0 executions. No test in either profile ran on
   a BMS controller.
4. **177 of 313 repository tests blocked** on proprietary TI HALCoGen output
   across 34 distinct `HL_*.h` headers.
5. **Integration tests** — only unit-level verification exists.
6. **Human approval** — pending for all 153 records; none performed.
7. **Production authorization** — `false` for all 153 records.
8. **Tool qualification** — approach only; no qualification record exists.
9. **Security-requirement verification** — the 5 security requirements have no
   test measure in either direction (`FB2-REV-FND-000008`…`-000012`).
10. **Machine-readable fault reaction** — no FSR carries a `fault_reaction`
    field, so no checker can consume the reaction requirement
    (`FB2-REV-FND-000013`…`-000019`).
11. **Project plan, risk register, measurement plan, improvement records** — all
    absent (§4.6).
12. **Lifecycle continuation** — production, operation, service and
    decommissioning are empty in both profiles.
13. **SOH algorithm** — placeholder in the pinned source, so it is a source-side
    gap the corpus cannot close.

**The previously reported gap "Cybersecurity — Not addressed" is closed.** The
TARA and the five security requirements now exist and are linked. The residual
cybersecurity gap is narrower and different: those requirements are
**unverified** and carry **no design, test measure or execution**. That is gap 9
above, not gap 7.

## 6. Recommendations

### For the foxBMS product (`as_is` improvements)

1. Type the `DATA_Write4DataBlocks` parameters in
   `src/app/engine/database/database.h` so the shipped CMock configuration can
   use `:when_ptr: :compare_data` as intended, or add explicit `:treat_as`
   entries, or register CMock callbacks in the five affected tests. This is a
   real, compiler-independent defect.
2. Run HALCoGen under a TI licence, or move verification to a Linux host, to
   unblock the 177 blocked tests.
3. Document explicit safety goals and FSRs, and add a `fault_reaction` field so
   the reaction requirement is machine-readable.
4. Execute the test suite on target hardware; nothing in this corpus substitutes
   for it.
5. Formalize change, problem-resolution and quality-assurance processes so the
   evidence that exists is backed by a process definition.
6. Create the missing project plan, risk register, measurement plan and
   improvement records.

### For the synthetic corpus (completeness)

1. Author the functional safety concept and technical safety concept, then supply
   the ASIL justification the safety goal currently lacks.
2. Author stakeholder needs and a system requirements specification, closing
   `SYS.1` and `SYS.2`.
3. Author verification measures and executions for the five security
   requirements.
4. Populate `fault_reaction` across all seven FSR instances.
5. Fix the safety case timing argument `ARG-003`, which a review found to be
   arithmetically wrong.
6. Resolve the `verifies`-direction convention jointly with the schema owner.
7. Resolve the duplicated `FB2-REV-000001` record and the stale
   `feature-inventory.json` summary count.
8. ~~Have the repository owner correct the conformity claim in
   `TRACEABILITY_DOCUMENT.md` at the root, recorded as `FB2-REV-FND-000022`.~~
   **DONE 2026-09-29:** the repository owner authorised amending the file and it was
   corrected — conformity sentence, IEC 61508 clause rows and a fabricated
   human-approval sign-off block removed, ASIL values relabelled hypothetical, false
   "automatically generated" provenance claim replaced. Finding at revision 3,
   disposition `accepted`. The residual item is that the file is still hand-authored
   and outside the toolchain's reach, so nothing detects a regression.
9. Build production, operation, service and decommissioning records, or state
   explicitly that they are out of scope for this corpus.
