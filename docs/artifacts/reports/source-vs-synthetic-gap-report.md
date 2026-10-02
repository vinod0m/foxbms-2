# Source vs Synthetic Gap Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Comparison:** `as_is` (source-grounded) vs `synthetic_reference` (hypothetical automotive project)

> Structural comparison only. Nothing here asserts ISO 26262 conformity, ASIL
> capability, ASPICE capability level, certification, human approval or tool
> qualification. All **263** indexed records are `human_approval_status: pending`
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
| verification | 41 | 70 | 111 |
| software | 25 | 29 | 54 |
| safety | 6 | 32 | 38 |
| system | 0 | 21 | 21 |
| management | 0 | 14 | 14 |
| supporting | 8 | 4 | 12 |
| hardware | 7 | 0 | 7 |
| production | 0 | 2 | 2 |
| decommissioning | 0 | 1 | 1 |
| operation | 0 | 1 | 1 |
| release | 0 | 1 | 1 |
| service | 0 | 1 | 1 |
| **Total** | **90** | **173** | **263** |

The asymmetry is the point, and it has moved. `as_is` is still dominated by
`verification` (41) and `software` (25, of which 26 deviation records sit in the
shared deviation family), while `synthetic_reference` now carries the safety,
management, system, supporting and **all four post-development lifecycle
domains** that `as_is` has no equivalent of. `as_is` has **zero** records in
management, system, supporting-management sense, production, operation, release,
service or decommissioning.

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
| **Item definition** | **none** | 1 (`FB2-SAF-ITE-000001`) | closed for synthetic |
| **Functional safety concept** | **none** | **1** (`FB2-SAF-FSC-000001`, 36,125 B) | **closed for synthetic 2026-09-29** |
| **Technical safety concept** | **none** | **1** (`FB2-SAF-TSC-000001`, 48,044 B) | **closed for synthetic 2026-09-29**, but see below |

**This section was materially wrong before 2026-09-29 and is corrected here.**
The two concept records exist in `synthetic_reference`, allocate the safety goal
across six architectural elements, and state the item assumptions, the
detection/reaction/degraded-operation strategies, the inside/outside safety
scope, the HW/SW allocation and the diagnostic-coverage assumptions. Writing them
exposed four contradictions in the pre-existing records, raised as
`FB2-REV-FND-000023..000027` and deliberately **not** corrected in place.

Two high-severity findings stand open **inside** the concept phase, which is why
ISO Part 3 is `partially_mapped` rather than `mapped`:
`FB2-REV-FND-000025` — the timing budget's arithmetic does not close — and
`FB2-REV-FND-000024` — the contactor reaction requirement contradicts itself.
A concept whose own budget does not close has not established an ASIL
derivation. `FB2-SAF-SGO-000001` carries `asil: ASIL_D` with **no justification
field of any kind**: no `safety_allocation`, no `asil_allocation_scope`.

### 4.2 System Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| Stakeholder needs | **none** | **5** (`FB2-SYS-NED-000001..000005`) | declared, **not elicited** — each carries `is_a_real_elicitation = false` |
| Operational scenarios | **none** | **none** | **open in both** — the 5 `SCN-*` records are mutation/change-lifecycle harness scenarios |
| Use cases | **none** | **4** (`FB2-SYS-UC-000001..000004`) | closed for synthetic |
| System requirements | **none** | **8** (`FB2-SYS-SYR-000001..000008`) | partial — **no modes/states, no interface requirements**; back-inferred not analysed |
| System modes / states | **none** | **none** | **open in both** |
| System architecture | **none** | **none** | **open in both** — `FB2-SYS-HSI-000001` is an interface specification, not an architecture |
| HSI authority | none | 1 (`FB2-SYS-HSI-000001`, `design_level: interface_specification`) | closed for synthetic |
| HW/SW allocation | implied by modules | in the two safety concepts + `allocated_to` links | partial — no allocation record of its own |
| Integration strategy | implied | planning stubs `FB2-VER-TMS-000007`, `-000008` | partial, executions blocked |
| Validation measures | none | `FB2-VER-TMS-000009` stub + `000012`…`000015` | partial — **all executions blocked; zero validations run** |

This section was corrected three times and now reflects disk. Revision 1 claimed
synthetic stakeholder and system requirements existed when they did not
(corrected under `CORR-COV-001`, `-002`, `-013`). Revision 2 kept calling them
absent after they were authored on 2026-09-29. This revision, 2026-10-01,
records what exists and names what is still missing from each: elicitation was
not performed, no operational scenario exists, no modes/states record exists and
no system architecture exists. `SYS.1`, `SYS.2` and `SYS.3` are all
`partially_mapped`.

### 4.3 Hardware Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| HW requirements | 3 TSRs | 4 TSRs | partial |
| HW architecture | none | none | **open** (`HWE.2`) — no block diagram, no architecture record |
| HW detailed design | none | none | **open** (`HWE.3`, `gap`) — no schematics, PCB layout, BOM or component specification |
| HW safety analysis (FMEDA) | none | none | **open** — the 4 `safety_analysis` records are FMEA, FTA, dependent-failure and FFI; **none is an FMEDA** |
| HW integration test | none | none | **open** (`HWE.4`, `gap`) |

**Zero corpus records reference `HWE.3` or `HWE.4` in any
`standards_mappings[].reference` string.** `HWE.3` was recorded
`partially_mapped` until 2026-10-01 on the strength of "design packages
referenced; detailed analysis limited by CAD format" — a sentence that named no
record.

The underlying limitation is real and is not a matter of effort: the schematic
sources are Altium `.SchDoc` files that live in the **separate `foxBMS2_hw`
repository**. Anchors `FB2-SRC-HW-000001..000003` read
`content_hash: unresolved` and
`hash_status: external_design_file_unverifiable_from_this_repository`, because
the files are present neither in this working tree nor in any commit of it.
**10 non-review records cite those anchors** (6 hardware requirements,
`FB2-SAF-ANL-000003`, `FB2-SAF-ITE-000001`, `FB2-SAF-TSC-000001`,
`FB2-SYS-HSI-000001`), plus 4 review records that review them. Their hardware
provenance rests on a design file this repository cannot show.

### 4.4 Software Engineering

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| SW requirements | 3 SWRs | 3 SWRs | none |
| SW architecture / design | 3 DSNs | 3 DSNs | none |
| Static-analysis deviations | **26 records** | none | `as_is` strength |
| Unit verification | 5 test measures, 16 executions incl. both real host sweeps | 28 test measures, 28 executions | partial, `SWE.4` partially_mapped |
| Integration verification | none | planning stub, execution blocked | open |
| Regression selection | not documented | not documented | open in both |
| Detailed design (`SWE.3`) | none | none | **open, `gap`** — 0 records reference SWE.3 |

The 26 MISRA deviation records are the single largest block of `as_is` evidence
and were not present in the corpus when this report was first written.

### 4.5 Verification and Validation

| Artifact | `as_is` | `synthetic_reference` | Gap |
|---|---|---|---|
| Test measures | 5 | 28 | — |
| Test executions | **16** (15 real host runs + 1 blocked) | **28** (22 blocked + 6 synthetic_fixture) | — |
| **Target-hardware executions** | **0** | **0** | **open in both** |
| Security-requirement verification | n/a | **none** | open (`FB2-REV-FND-000008`…`-000012`) |
| Coverage analysis | none | none | open |
| Anomaly records | 7 finding artifacts | 14 finding artifacts | — |
| Validation measures | none | stub, execution blocked | open |

`actual_product_evidence` is **0/33** and the tool states why: `execution_kind`
has no target-hardware member, so none can be claimed. Of the 44 execution
records, 15 are host runs of real product code and 29 are `synthetic_fixture` or
blocked. The 4 `tests/unit-hw/test_tms570_*.c` target-hardware tests in the
repository were never even attempted by the SIL harness.

### 4.6 Management and Supporting Processes

This remains the category with the largest honest gaps. **All statuses are read
from `governance/coverage-plan.json` as audited on 2026-10-01
(`CORR-COV-016`)** — the "Backing record" column names the artefact whose own
`standards_mappings[].reference` names the process, and the "Gap" column names
the specific missing family from the process's own `expected_artifacts`.

| Process | Backing record | Disposition | Which family is missing |
|---|---|---|---|
| Project management (MAN.3) | `FB2-MAN-PLN-000001` `project_plan` | **`mapped`** | — all four families present |
| Risk management (MAN.5) | `FB2-MAN-RSK-000001` `risk_register` | **`mapped`** | — all three present |
| Measurement (MAN.6) | `FB2-MAN-MSM-000001` `measurement_plan` | **`mapped`** | — all three present |
| Process improvement (PIM.3) | `FB2-PIM-IMP-000001`/`000002` | **`mapped`** | — all three present; no verdict is `effective` |
| Quality assurance (SUP.1) | `FB2-SUP-QAP-000001` + 15 review records | `partially_mapped` | **Audit Records**; independence stated and **not** achieved |
| Configuration management (SUP.8) | `FB2-SUP-CFM-000001` | `partially_mapped` | **Change Control** (deferred) and **status accounting** (not automated) |
| Problem resolution (SUP.9) | 13 `finding` records + `FB2-SUP-PRB-000001` | `partially_mapped` | **Trend Analysis** — the record says one cycle cannot produce one |
| Change request management (SUP.10) | `FB2-MAN-CHG-000001..000003` | `partially_mapped` | families present for a **fictional project only** |
| Traceability management (SUP.11) | 3 `change` records + **547 links** | `partially_mapped` | **link currency** — 326 of 547 links stale, none suspect |
| Reuse management (REU.2) | `FB2-SUP-RUS-000001` | `partially_mapped` | **Reuse Assessments** — none completed |
| Supplier monitoring (ACQ.4) | `FB2-SUP-SPL-000001` | `partially_mapped` | **Supplier Assessments** — no supplier under contract |
| Safety plan (ISO Part 2) | `FB2-MAN-SPL-000001` — **`artifact_type: design`**, six empty structural fields | `partially_mapped` | **Roles** and **Tailoring**; it is not a safety plan |

**The earlier internal disagreement is closed.** `SUP.1`, `SUP.8`, `SUP.9` and
`SUP.10` used to read `mapped` in `process_inventory` while the generated
`views/supporting-processes/supporting-processes.md` reported that no
*process-definition* record existed for those families. Six supporting-process
records now exist, and the four processes are `partially_mapped` with the
specific missing family named in each — so the plan and the generated view now
say the same thing. `CORR-COV-016` also found that two records the *previous*
pass had leaned on do not support what was claimed: `FB2-MAN-SPL-000001` is a
`design` record, not a safety plan, and every post-development record carries
`any_step_executed: false`.

### 4.7 Lifecycle Continuation

| Artifact | `as_is` | `synthetic_reference` | Disposition |
|---|---|---|---|
| Release plan / notes / checklist | version history in pinned source | `FB2-REL-RLS-000001` + `FB2-SUP-CHC-000001` | `SPL.2` **`partially_mapped`** — no Release Notes; nothing released |
| Production and end-of-line test | none | `FB2-PRD-EOL-000001` (6 stations) | ISO Part 7 **`partially_mapped`** — documented, not performed |
| Operation and field monitoring | none | `FB2-OPS-MON-000001` (5 signals, 4 incident classes) | ISO Part 7 **`partially_mapped`** |
| Service and maintenance | none | `FB2-SVC-SVC-000001` (5 procedures) | ISO Part 7 **`partially_mapped`** |
| Decommissioning and recycling | none | `FB2-DEC-DCM-000001` (5 end-of-life assumptions) | ISO Part 7 **`partially_mapped`** |
| Calibration and programming | none | `FB2-PRD-CAL-000001` (6 parameters) | ISO Part 7 **`partially_mapped`** |

**All six post-development records carry `evidence_state.any_step_executed:
false`**, and each declares itself fictional and authorising nothing on real
equipment. The content is real; the performance is zero. `as_is` has **no**
record in any of these six domains, so the lifecycle-continuation evidence is
entirely synthetic.

## 5. Key Observations

### What foxBMS Provides (`as_is` strengths)

1. **Working implementation** — 612 inventoried source files across 24 modules,
   22 features, 23 variants, all accounted for.
2. **A real test suite that can be run and whose failures are real** — the SIL
   host harness attempted **all 313** CeeDling targets: **222 passed, 7 failed,
   84 build failures**, of which the harness itself classifies **16 as real
   product defects**. The earlier strict run's 5 failures are a genuine defect in
   the product's test setup, not a harness artefact. The SIL run also produced a
   finding against itself: **53 of its 245 green tests assert nothing**
   (`FB2-REV-FND-000042`).
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
3. **Traceability** — **547 links, 0 dangling**, with a documented direction
   convention. And a measured limit: **326 links carry a stale endpoint revision
   and none is marked suspect** (§4.6, `SUP.11`).
4. **Parameter and assumption registries** — 10 parameters, 12 assumptions with
   stated validity.
5. **Timing budgets** — FTTI allocation with an explicit 20 ms margin.
6. **Change management** — 3 full lifecycle scenarios, all structurally complete.
7. **Negative-scenario machinery** — 20/20 mutation scenarios detected by the rule each declares (repaired 2026-09-29; see finding `FB2-REV-FND-000032`).
8. **Adversarial review layer** — challenge, cross_domain and meta review passes
   that found **8 high-severity findings**, one of them about the original review
   itself. **15 review records, 49 embedded findings, 144/259 = 64% coverage.**
9. **Process governance that states its own shortfalls** — 6 supporting-process
   records, a measurement plan, a risk register, a project plan and two
   improvement records, each naming the family it cannot discharge.

### What Neither Has — Remaining Gaps

1. **System architecture** — no record exists in either profile. The functional
   and technical safety concepts now exist (`FB2-SAF-FSC-000001`,
   `FB2-SAF-TSC-000001`) but two high-severity findings stand open inside the
   concept phase: the timing budget's arithmetic does not close
   (`FB2-REV-FND-000025`) and the contactor reaction requirement contradicts
   itself (`FB2-REV-FND-000024`). ISO Part 3 and Part 4 are `partially_mapped`.
2. **Stakeholder needs are declared, not elicited** — 5 need records exist, each
   carrying `is_a_real_elicitation = false`, and **no operational scenario
   record exists**. `SYS.1` is `partially_mapped`; `as_is` remains at `gap`.
3. **System requirements analysis** — 8 system requirement records exist but
   there is **no system modes/states record and no system-level interface
   requirements record**, and the requirements were back-inferred from code
   rather than analysed. `SYS.2` is `partially_mapped`.
4. **Target-hardware evidence** — 0 of 33. No test in either profile ran on a
   BMS controller, and the 4 `tests/unit-hw/test_tms570_*.c` target-hardware tests
   were never attempted.
5. **`SWE.3` and `HWE.3` have no backing artefact at all** — **zero** corpus
   records reference either process in any `standards_mappings[].reference`
   string. Detailed design, schematics, PCB layout, BOM and component
   specifications are absent. `SWE.3` was recorded `mapped` until 2026-10-01.
6. **Integration and qualification tests** — planning stubs with blocked
   executions; no plan and no specification in any case.
7. **Human approval** — pending for all **263** records; none performed.
8. **Production authorization** — `false` for all **263** records.
9. **Tool qualification** — approach only; no qualification record exists.
10. **Security-requirement verification** — the 5 security requirements have no
    executed result in either direction (`FB2-REV-FND-000041`; the measures now
    exist, the executions are blocked).
11. **Machine-readable fault reaction** — no FSR carries a `fault_reaction`
    field, so no checker can consume the reaction requirement
    (`FB2-REV-FND-000013`…`-000019`).
12. **Lifecycle continuation** — all six areas are documented in the
    `synthetic_reference` profile and **none was performed**
    (`any_step_executed: false`); all six are empty in `as_is`.
13. **SOH algorithm** — placeholder in the pinned source, so it is a source-side
    gap the corpus cannot close.
14. **Hardware provenance** — **10 records' hardware provenance rests on Altium
    design files in the external `foxBMS2_hw` repository**, which this repository
    cannot verify (`content_hash: unresolved`). 4 more records (review records)
    cite the same three anchors.
15. **Link revision currency** — 326 of 547 links are stale and none is marked
    suspect (§4.6).
16. **6 synthetic executions record `pass` with no retained evidence** — the
    fixture never existed and `evidence/synthetic-fixtures/` holds no fixture artefact
    (only a `MANIFEST.md` documenting the gap, whose own finding reference
    `FB2-REV-FND-000143` resolves to no record).

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
2. The SIL harness already reaches all 313 CeeDling targets by mocking the
   `HL_*.h` interface boundary, so the HALCoGen exclusion is no longer the
   binding constraint on a host run. What it *cannot* provide is TI register
   semantics. If those are needed, run HALCoGen under a TI licence, or move
   verification to a Linux host where the ELF compiler accepts the TI section
   attributes unchanged.
3. Document explicit safety goals and FSRs, and add a `fault_reaction` field so
   the reaction requirement is machine-readable.
4. Execute the test suite on target hardware; nothing in this corpus substitutes
   for it.
5. Formalize change, problem-resolution and quality-assurance processes so the
   evidence that exists is backed by a process definition.
6. The project plan, risk register, measurement plan and improvement records now
   exist and are the four ASPICE processes that survive the 2026-10-01 audit at
   `mapped`. The remaining supporting-process gap is narrower: each of SUP.1,
   SUP.8, SUP.9, SUP.10, SUP.11, ACQ.4 and REU.2 is missing one named family, and
   each record says which.

### For the synthetic corpus (completeness)

1. ~~Author the functional safety concept and technical safety concept.~~ **DONE
   2026-09-29:** `FB2-SAF-FSC-000001` and `FB2-SAF-TSC-000001` exist. The open
   items are narrower — close `FB2-REV-FND-000025` (the timing budget does not
   close) and `FB2-REV-FND-000024` (the contactor reaction requirement
   contradicts itself), then supply the ASIL justification `FB2-SAF-SGO-000001`
   has no field for.
2. Author the three artefacts that close `SYS.1`, `SYS.2` and `SYS.3`: an
   operational scenario, a system modes/states record, and a system architecture.
   The stakeholder needs and system requirements that now exist are declared and
   back-inferred respectively.
3. Author a detailed-design record, a source-code record and a unit-test
   specification that each declare `SWE.3` in their own `standards_mappings`, and
   do the same for `HWE.3`. Both are `gap` because nothing references them.
4. Author verification measures **and executions** for the five security
   requirements. The measures now exist; the executions are blocked.
5. Populate `fault_reaction` across all seven FSR instances.
6. Fix the safety case timing argument `ARG-003`, which a review found to be
   arithmetically wrong.
7. Resolve the `verifies`-direction convention jointly with the schema owner.
8. ~~Resolve the duplicated `FB2-REV-000001` record.~~ **DONE:** the duplicate has
   been removed and every `(profile, id)` pair in the corpus is now unique. The
   **stale `feature-inventory.json` summary count (20 vs 22) remains open** — it
   is a summary field the tool already reports correctly.
9. Give `render_e2e_html.py` an owning section for `artifact_type:
   implementation`, so its `--check` stops exiting 1 on 14 records.
10. Implement link revision currency so `change_suspect_status` becomes a derived
    value rather than a blanket `false` on all 547 links.
11. Retain the evidence for the 6 `synthetic_fixture` executions, or delete those
    execution records. A `pass` with no retained fixture is worse than an honest
    gap.
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
