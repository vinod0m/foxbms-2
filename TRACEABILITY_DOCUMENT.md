# foxBMS 2 - End-to-End Traceability Document

> ## ⚠️ READ FIRST — what this document is and is not
>
> **This is a synthetic engineering corpus, not a conformity or certification package.**
>
> - It does **not** establish compliance with ISO 26262, IEC 61508, or any other standard.
> - It does **not** assert an Automotive SPICE capability level. No ASPICE assessment has been performed.
> - Every `ASIL-x` label is a **hypothetical value in a fictional reference project**, assigned to demonstrate how ASIL allocation works. It is **not** an ASIL assigned to the real foxBMS 2 product, which has never undergone a HARA. The synthetic safety goal `FB2-SAF-SGO-000001` carries the field value `ASIL_D` with **no justification field**, which the corpus's own detector flags.
> - The real foxBMS 2 project is a **research/development platform** that its own documentation states must be adapted by the user before any product use.
> - No artifact here carries human approval, tool qualification, or production authorization. Across the corpus every record is `human_approval_status: pending`, `production_authorized: false` and `product_verification_credit: false`.
> - **This file has never been approved by anyone.** There is no approver, no reviewer and no signature on it, and there never was. See §14.
> - Authoring: automated review only. Automated review is **not** organizational independence and is **not** human confirmation.
>
> See `docs/artifacts/README.md` and `docs/artifacts/governance/corpus-policy.json`.

## Document Information
- **Project**: foxBMS 2 - Battery Management System (synthetic reference corpus)
- **Version**: 2.x
- **Baseline**: BAS-REF-001
- **Pinned source commit**: `308028fb` (tag `v1.11.0`) — this is the commit the *source* inventories are pinned to, **not** a commit that contains these corpus artifacts
- **Document Version**: 3.0
- **Date**: 2026-09-29
- **Provenance**: hand-authored at the repository root. **Not generated, not tool-maintained, not under the corpus toolchain's control.** See §15.
- **Classification**: Internal — synthetic corpus, not a certification package

## 1. Introduction

This document is a hand-written reading aid over the synthetic foxBMS 2 lifecycle artifact corpus. It links requirements, design elements and test cases across the engineering process areas of a **hypothetical** automotive BMS project grounded in the real foxBMS 2 sources. The corpus keeps two profiles explicitly separate: `as_is` (what the pinned source demonstrably does) and `synthetic_reference` (a fictional project used to exercise the full lifecycle).

Because this file is hand-authored, its **relationships are quoted from the corpus link registries** and its **counts are quoted from a live `corpus.py` run**. Every identifier below resolves against the corpus index; every table row was checked. Where the corpus does not hold a record, the cell says so rather than naming one.

### 1.1 Purpose
This document establishes bidirectional traceability between:
- Stakeholder Requirements → System Requirements → Software Requirements → Software Architecture → Software Detailed Design → Verification

It does **not** provide evidence of standards compliance. Traceability here demonstrates that a coherent chain of records exists and can be navigated; it is not a demonstration that the chain is correct, that the requirements are right, or that any standard's obligations are met.

### 1.2 Scope
Covers the synthetic foxBMS 2 lifecycle artifact corpus including:
- Safety requirements carrying **hypothetical** ASIL-D and ASIL-B labels (fictional reference project; not assigned to the real product)
- Hardware Requirements (AFE, Contactor, Communication)
- Software Requirements (AFE driver, SOA, Contactor control)
- Software Architecture and Detailed Design
- Verification and Validation evidence

### 1.3 Traceability Strategy
Bidirectional traceability is maintained through:
- Unique identifiers for all artifacts, in the **four real forms the corpus uses** (the previous revision of this file stated a single scheme `FB2-XXXX-XXXXXXXX`; no record uses that form and it has been removed):

  | Form | Example | Applies to | Registry |
  |------|---------|-----------|----------|
  | `FB2-<DOMAIN>-<TYPE>-<NNNNNN>` | `FB2-SAF-FSR-000001`, `FB2-SW-SWR-000001`, `FB2-VER-TMS-000011` | Artifact records (requirements, designs, analyses, measures, executions, scenarios, concepts, TARA) | `corpus/`, `scenarios/`, `reviews/` |
  | `FB2-REV-<NNNNNN>` | `FB2-REV-000001` | Review records (earlier generation) | `reviews/records/` |
  | `FB2-REV-FND-<NNNNNN>` | `FB2-REV-FND-000022` | Finding records (current generation) | `reviews/findings/` |
  | `FB2-<KIND>-<NNNNNN>` / `FB2-<KIND>-<NNN>` | `FB2-PRM-000001`, `FB2-LNK-SAF-000021`, `FB2-ASM-001`, `FB2-SRC-COD-000004` | Parameters, links, assumptions, source anchors — registry entries, not lifecycle artifacts | `shared/`, `traceability/`, `sources/` |

  Two of these are shorter than the six-digit artifact form: assumptions use **three** digits (`FB2-ASM-001` … `FB2-ASM-012`) and parameters use **six** with no domain segment (`FB2-PRM-000001` … `FB2-PRM-000010`). `FB2-SW-TSR-*` and `FB2-SW-DSN-000004` do **not** exist; the previous revision of this file cited both.
- Traceability links with relation types (`refines`, `allocated_to`, `implements`, `verifies`, `validates`, `mitigates`, `supports`, `result_of`, `reviewed_by`, `changes`)
- Profile-based isolation (`as_is` vs `synthetic_reference`) — the same identifier may exist in both profiles with different content, by design
- Baseline-referenced artifacts (`BAS-REF-001`)

Scenario records additionally carry a short `scenario_id` key (`SCN-MUT-001` … `SCN-MUT-020`, `SCN-CHG-001` … `SCN-CHG-003`) which is what `corpus.py check` keys its acceptance suite on. Both forms are real; §5.2 and §5.3 give the six-digit artifact form and name the short key alongside it.

## 2. Traceability Levels and Artifact Types

### 2.1 Traceability Levels

A **reading order**, not a maturity model, a capability level, or an ASPICE process assessment result.

| Level | Description | Artifact Types | Profile |
|-------|-------------|----------------|---------|
| L1 | Stakeholder Requirements | Use Cases, Safety Goals | as_is, synthetic_reference |
| L2 | System Requirements | Hazards, Safety Goals, FSRs | as_is, synthetic_reference |
| L3 | Technical / Software Requirements | FSRs, SWRs, TSRs | as_is, synthetic_reference |
| L4 | Architecture and Design | System Design, HSI, Software Design | as_is, synthetic_reference |
| L5 | Detailed Design | Software Designs | as_is, synthetic_reference |
| L6 | Software Units | Source Files, Software Units | as_is |
| L7 | Verification | Test Measures, Executions, Reviews | as_is, synthetic_reference |

### 2.2 Artifact Type Definitions

| Artifact Type | ID prefix | Description | Present in corpus |
|---------------|-----------|-------------|-------------------|
| Hazard | `FB2-SAF-HAZ` | Hazard analysis | 1 per profile |
| Safety Goal | `FB2-SAF-SGO` | Safety goal carrying `fault_tolerant_time_interval_ms`, `safe_state`, `degraded_state` and an `asil` **field value**. That field is a **hypothetical label in a fictional project**; it is not an ASIL determination of the real product, and `FB2-SAF-SGO-000001` carries no justification field | 1 per profile |
| Safety Concept | `FB2-SAF-FSC`, `FB2-SAF-TSC` | Functional / Technical Safety Concept. Both are synthetic and each states in its own `limitations` that it establishes no ASIL capability for any real product | 1 each (synthetic_reference) |
| FSR | `FB2-SAF-FSR` | Functional Safety Requirement | 1–4 per profile |
| TSR | `FB2-HW-TSR` | Technical Safety Requirement. There is **no `FB2-SW-TSR-*` family** in the corpus | 3 (as_is) / 4 (synthetic_reference) |
| SWR | `FB2-SW-SWR` | Software Requirement | 3 per profile |
| Design | `FB2-SW-DSN`, `FB2-SYS-HSI` | Detailed Design / Hardware-Software Interface | 4 per profile |
| Software Unit | `FB2-SW-DEV` | Software unit, `as_is` profile only | 26 (as_is) |
| Test Measure | `FB2-VER-TMS` | Test Measure Specification | 5 (as_is) / 20 (synthetic_reference) |
| Execution | `FB2-VER-EXE` | Test Execution Record | 14 (as_is) / 20 (synthetic_reference) |
| Review | `FB2-REV-NNNNNN`, `FB2-REV-FND-NNNNNN` | Review record / finding record | 15 reviews, 30 findings |
| Safety Analysis | `FB2-SAF-ANL` | FMEA, FTA, DFA, FFI | 4 (synthetic_reference) |
| Cybersecurity Requirement | `FB2-SAF-SEC` | Security requirement | 5 (synthetic_reference) |
| Scenario | `FB2-SCN-MUT-NNNNNN`, `FB2-SCN-CHG-NNNNNN` | Mutation / change lifecycle | 20 + 3 |
| Parameter | `FB2-PRM` | Parameter registry entry | 10 |
| Assumption | `FB2-ASM` | Assumption registry entry (three-digit form) | 12 |
| Link | `FB2-LNK` | Typed link registry entry | 283 links across two profiles |
| Source anchor | `FB2-SRC` | Pinned source location | 102 |

## 3. Traceability Matrix

All rows below are quoted from `docs/artifacts/traceability/link-registry/<profile>/links-cell-voltage.json` and from the `referenced_requirements` / `decomposition` / `source_refs` fields of the records themselves.

### 3.1 Hazard → Safety Goal → FSR Traceability

Profile `synthetic_reference`. There is **one** hazard, `FB2-SAF-HAZ-000001`; the previous revision of this file listed a second, `FB2-SAF-HAZ-000002`, which does not exist in the corpus.

| Hazard ID | Hazard | Link | Safety Goal ID | Safety Goal | Link | FSR IDs (refines) |
|-----------|--------|------|----------------|-------------|------|--------------------|
| FB2-SAF-HAZ-000001 | Cell Overvoltage / Undervoltage Hazard | `FB2-LNK-SAF-000001` (`mitigates`, goal→hazard) | FB2-SAF-SGO-000001 | Cell Voltage Safety Goal; FTTI 100 ms; `asil` field = ASIL_D, **hypothetical, unjustified, not a determination of the real product** | `FB2-LNK-SAF-000002`, `-000003`, `-000004`, `-000021` (`refines`, FSR→goal) | FB2-SAF-FSR-000001, FB2-SAF-FSR-000002, FB2-SAF-FSR-000003, FB2-SAF-FSR-000004 |

### 3.2 Safety Goal → FSR → TSR/SWR Traceability

| Safety Goal | FSR ID | FSR | TSR / SWR allocated to the FSR (`allocated_to`) | Link |
|------------|--------|-----|------------------------------------------------|------|
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001 | Cell Voltage Acquisition and Validation | FB2-HW-TSR-000001, FB2-HW-TSR-000002, FB2-SW-SWR-000001 | `FB2-LNK-SAF-000005`, `-000006`, `-000008` |
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000002 | SOA Voltage Limit Monitoring with Debounce | FB2-SW-SWR-000002 | `FB2-LNK-SAF-000009` |
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000003 | Contactor Opening on SOA Violation | FB2-HW-TSR-000003, FB2-SW-SWR-000003 | `FB2-LNK-SAF-000007`, `-000010` |
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000004 | Independent Hardware Voltage Monitor | FB2-HW-TSR-000004 | `FB2-LNK-SAF-000058` |

`FB2-SAF-FSR-000004` and `FB2-HW-TSR-000004` exist **only in the `synthetic_reference` profile**; the `as_is` profile stops at FSR-000003 and TSR-000003. The previous revision of this file cited `FB2-SW-TSR-000001` … `-000004`, none of which exist.

### 3.3 FSR / SWR → Design → Source Traceability

| SWR implemented (`implements`) | Design ID | Design | Source anchors | Pinned source path | Lines |
|---------------------------|-----------|--------|----------------|-------------------|-------|
| FB2-SW-SWR-000001 | FB2-SW-DSN-000001 | AFE Driver Architecture (LTC Family) — `FB2-LNK-SAF-000011` | FB2-SRC-COD-000001, FB2-SRC-COD-000002 | `src/app/driver/afe/api/afe.h` | 45–52, 55–62 |
| FB2-SW-SWR-000002 | FB2-SW-DSN-000002 | SOA Voltage Monitoring Module — `FB2-LNK-SAF-000012` | FB2-SRC-COD-000004, `-000005`, `-000006` | `src/app/application/soa/soa.c` | 120–180, 185–240, 245–300 |
| FB2-SW-SWR-000003 | FB2-SW-DSN-000003 | Contactor State Machine — `FB2-LNK-SAF-000013` | FB2-SRC-COD-000007, FB2-SRC-COD-000008 | `src/app/driver/contactor/contactor.c` | 150–350, 355–420 |

`FB2-SW-DSN-000001.decomposition` names three children: `FB2-SW-DSN-000002`, `FB2-SW-DSN-000003` and **`FB2-SW-DSN-000004`**. The third does not exist. It is a **declared forward reference** to a design element the corpus has never authored, recorded as finding `FB2-REV-FND-000030` and listed in the allowlist of `docs/artifacts/tools/check_references.py`. It is a gap, not a broken link, and the missing design was deliberately not invented.

`FB2-SW-DEV-000001` … `FB2-SW-DEV-000026` (software units) exist in the `as_is` profile only; five of them carry `refines` links into `FB2-SW-DSN-000001`. The `synthetic_reference` profile has no software-unit records.

### 3.4 Requirements → Test Measures → Executions Traceability

**`as_is` profile.** Every row is a real `verifies` link plus the matching `result_of` link to an execution record.

| Test Measure | Test | Verifies | Link | Execution | `execution_kind` | Outcome |
|--------------|------|----------|------|-----------|------------------|---------|
| FB2-VER-TMS-000001 | SOA Voltage Limit Detection | FB2-SAF-FSR-000002, FB2-SW-SWR-000002 | `FB2-LNK-SAF-000014`, `-000015` | FB2-VER-EXE-000001 (`FB2-LNK-SAF-000018`) | `actual_host_run` | pass |
| FB2-VER-TMS-000002 | Contactor State Machine and Fault Response | FB2-SAF-FSR-000003, FB2-SW-SWR-000003 | `FB2-LNK-SAF-000016`, `-000017` | FB2-VER-EXE-000002 (`FB2-LNK-SAF-000026`) | `actual_host_run` | pass |
| FB2-VER-TMS-000003 | AFE Cell Voltage Plausibility Checks | FB2-SAF-FSR-000001, FB2-SW-SWR-000001 | `FB2-LNK-SAF-000021`, `-000022` | FB2-VER-EXE-000003 (`FB2-LNK-SAF-000027`) | `actual_host_run` | pass |
| FB2-VER-TMS-000004 | LTC6813-1 AFE Driver Communication and Measurement | FB2-HW-TSR-000001, FB2-HW-TSR-000002 | `FB2-LNK-SAF-000023`, `-000024` | FB2-VER-EXE-000004 (`FB2-LNK-SAF-000028`) | `none` | **blocked** |
| FB2-VER-TMS-000005 | Contactor Driver Configuration and Control | FB2-HW-TSR-000003 | `FB2-LNK-SAF-000025` | FB2-VER-EXE-000005 (`FB2-LNK-SAF-000029`) | `actual_host_run` | pass |

The previous revision of this file paired `FB2-SAF-FSR-000001`/`FB2-SW-SWR-000001` with `FB2-VER-TMS-000001` (that measure verifies FSR-000002/SWR-000002), described `FB2-VER-TMS-000003` as covering the independent monitor, and reported an execution of type `synthetic_fixture` with outcome `planned` for it. No execution record has that combination. `FB2-SAF-FSR-000004` / `FB2-HW-TSR-000004` are verified by `FB2-VER-TMS-000004` in the `synthetic_reference` profile only.

**`synthetic_reference` profile.** 20 test measures, 20 execution records: 6 `synthetic_fixture` with outcome `pass`, 14 `none` with outcome `blocked`. **No `actual_host_run` and no target-hardware execution exists in this profile.** The target-hardware measure `FB2-VER-TMS-000011` (HIL Fault Reaction) has `FB2-VER-EXE-000011` recorded as `none` / `blocked`; its `unblocking_conditions` name HALCoGen, which is not available in this workspace.

### 3.5 Design → Source Code → Test Traceability

| Design ID | Pinned source path | Anchored symbols | Test Measures |
|-----------|-------------------|------------------|---------------|
| FB2-SW-DSN-000001 | `src/app/driver/afe/api/afe.h` | `AFE_GetCellVoltages`, `AFE_GetCellTemperatures` | FB2-VER-TMS-000003, FB2-VER-TMS-000004, FB2-VER-TMS-000007 |
| FB2-SW-DSN-000002 | `src/app/application/soa/soa.c` | `SOA_CheckVoltageLimits`, `SOA_CheckCurrentLimits`, `SOA_CheckTemperatureLimits` | FB2-VER-TMS-000001, FB2-VER-TMS-000007, FB2-VER-TMS-000010 |
| FB2-SW-DSN-000003 | `src/app/driver/contactor/contactor.c` | `CONTACTOR_StateMachine`, `CONTACTOR_CheckFeedback` | FB2-VER-TMS-000002, FB2-VER-TMS-000007 |

**No line or branch coverage figure is stated here, because none was measured.** The corpus contains no gcov/lcov output, no coverage artifact and no coverage gate. The previous revision of this file asserted a `100% line/branch` *target and achievement* for each row; the target is recorded on the test measures, the achievement was never measured, and the "100% achieved" column has been removed. The only measured test result in the corpus is the host run in §6.1.

## 4. Safety Analysis Traceability

### 4.1 Safety Analysis Traceability

`synthetic_reference` profile. Analysis ids and types quoted from the records; related-ids columns are the ids the records themselves name.

| Analysis ID | Type | Record title | Related Safety Goal | Related FSRs |
|-------------|------|--------------|--------------------|--------------|
| FB2-SAF-ANL-000001 | FMEA | FMEA: Cell Voltage Acquisition and Protection Chain | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001, FB2-SAF-FSR-000002, FB2-SAF-FSR-000003 |
| FB2-SAF-ANL-000002 | FTA | FTA: Cell Overvoltage Not Mitigated Within FTTI (HE-01) | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001, FB2-SAF-FSR-000002, FB2-SAF-FSR-000003 |
| FB2-SAF-ANL-000003 | Dependent Failure | DFA: Main Path and Independent Monitor | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001, FB2-SAF-FSR-000004 |
| FB2-SAF-ANL-000004 | Freedom From Interference | FFI: Coexisting Safety and Non-Safety Functions | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000004 |

The previous revision of this file wrote the FSR column as a range `FB2-SAF-FSR-000001..0004`, a string no tool can resolve. Ranges are expanded above.

## 5. Verification and Validation Traceability

### 5.1 Review Traceability

**Corpus-wide figures** (from a live `corpus.py coverage` run on 2026-09-29):

| Quantity | Value | Source |
|----------|-------|--------|
| Review records | 15 | `reviews/records/` |
| Finding records | 30 (23 `accepted`, 7 `partial`) | `reviews/findings/` |
| Finding entries carried *inside* review records | 49 | sum of `findings[]` over the 15 review records |
| Artifacts covered by a `reviewed_by` link | 144 / 186 | `corpus.py coverage` → `automated_review_coverage` |
| Artifacts with human approval | **0 / 220** | `corpus.py coverage` → `human_approval` |

The "5 findings" figure that appeared in the previous revision of this file is **not a corpus count**. It is the `findings` array length of the single record `FB2-REV-000001` (Review: Cell Voltage Protection Vertical Slice, 17 artifacts, 5 findings). It is retained below, scoped to that record.

| Review ID | Review type | Artifacts reviewed | Findings in this record | Status |
|-----------|-------------|--------------------|-------------------------|--------|
| FB2-REV-000001 | domain | 17 | 5 | `human_approval_status: pending`; `production_authorized: false` |
| FB2-REV-000014 | cross_domain | 17 | 4 | as above |

The other 13 review records cover 16–33 artifacts each and carry 2–5 findings each. No review record is approved; every one names a `reviewer_identity` that is an **automated agent session** (e.g. `role: safety_engineer`, `session_id: opencode-…`), not a person.

### 5.2 Mutation Scenario Traceability

All 20 mutations are present and all 20 are detected. `corpus.py check` prints `PASS SCN-MUT-001` … `PASS SCN-MUT-020` with a matching-scope finding count for each; `corpus.py coverage` prints `negative_scenario_validation: 20/20`. The previous revision of this file reported `6/20 functional` and marked four scenarios as `Documented Limitation`. That was wrong and has been corrected.

| Mutation artifact | Short key | Type | Target | Detector | Result |
|-------------------|-----------|------|--------|----------|--------|
| FB2-SCN-MUT-000001 | SCN-MUT-001 | Missing Parent Link in Refinement Chain | FB2-SAF-FSR-000001 | traceability checker | PASS (6 findings) |
| FB2-SCN-MUT-000002 | SCN-MUT-002 | Invalid Link Type | FB2-LNK-SAF-000014 | link validator | PASS (3) |
| FB2-SCN-MUT-000003 | SCN-MUT-003 | Stale Revision Reference | FB2-SAF-FSR-000001 | revision checker | PASS (2) |
| FB2-SCN-MUT-000004 | SCN-MUT-004 | Unit/Scaling Mismatch in Parameter | FB2-PRM-000001 | parameter unit checker | PASS (1) |
| FB2-SCN-MUT-000005 | SCN-MUT-005 | HW/SW Pin/Polarity Mismatch in HSI | FB2-SYS-HSI-000001, FB2-HW-TSR-000001 | HSI/SW checker | PASS (1) |
| FB2-SCN-MUT-000006 | SCN-MUT-006 | Timing Budget Exceeds FTTI | FB2-SAF-SGO-000001 | FTTI checker | PASS (2) |
| FB2-SCN-MUT-000007 | SCN-MUT-007 | Threshold Order Contradiction | FB2-PRM-000001 | threshold validator | PASS (1) |
| FB2-SCN-MUT-000008 | SCN-MUT-008 | Missing Fault Reaction | FB2-SAF-FSR-000002 | safety requirement checker | PASS (2) |
| FB2-SCN-MUT-000009 | SCN-MUT-009 | Unsupported ASIL Downgrade | FB2-SAF-SGO-000001 | ASIL validator | PASS (2) |
| FB2-SCN-MUT-000010 | SCN-MUT-010 | False Diagnostic Coverage Claim | FB2-SAF-FSR-000003 | diagnostic coverage checker | PASS (4) |
| FB2-SCN-MUT-000011 | SCN-MUT-011 | Invalid Configuration Combination | FB2-MAN-SCO-000001 | config checker | PASS (1) |
| FB2-SCN-MUT-000012 | SCN-MUT-012 | Fabricated Evidence Classification | FB2-VER-EXE-000001 | evidence classifier | PASS (2) |
| FB2-SCN-MUT-000013 | SCN-MUT-013 | Unjustified Non-Applicability | FB2-SAF-FSR-000004 | applicability validator | PASS (1) |
| FB2-SCN-MUT-000014 | SCN-MUT-014 | Dangling Evidence Reference | FB2-VER-TMS-000001 | evidence validator | PASS (2) |
| FB2-SCN-MUT-000015 | SCN-MUT-015 | Duplicate Artifact ID Within Profile | FB2-SAF-FSR-000001 | identity checker | PASS (3) |
| FB2-SCN-MUT-000016 | SCN-MUT-016 | Source Anchor Drift | FB2-SAF-ANL-000001 | drift detector | PASS (1) |
| FB2-SCN-MUT-000017 | SCN-MUT-017 | Unsafe Workflow Promotion | FB2-SAF-SGO-000001 | governance checker | PASS (4) |
| FB2-SCN-MUT-000018 | SCN-MUT-018 | Incomplete Change Propagation | FB2-PRM-000001 | impact analyzer | PASS (1) |
| FB2-SCN-MUT-000019 | SCN-MUT-019 | Circular Refinement Chain | FB2-SAF-HAZ-000001, FB2-SAF-SGO-000001 | cycle detector | PASS (2) |
| FB2-SCN-MUT-000020 | SCN-MUT-020 | Missing Verification Link | FB2-VER-TMS-000001 | verification checker | PASS (2) |

`PASS` here means the injected defect was **detected**. It does not mean the corpus is defect-free, and it carries no verification credit for the real product.

### 5.3 Change Lifecycle Traceability

`corpus.py coverage` prints `3/3 change lifecycles` and `corpus.py check` prints `PASS SCN-CHG-001: structure complete` for each.

| Change artifact | Short key | Type | Trigger | Affected artifacts | Affected links | New revisions | Suspect links | Result |
|-----------------|-----------|------|---------|-------------------|----------------|---------------|---------------|--------|
| FB2-SCN-CHG-000001 | SCN-CHG-001 | safety_threshold | Cell supplier change notification, 2026-09-15 | 6 | 2 | 6 | 1 | structure complete |
| FB2-SCN-CHG-000002 | SCN-CHG-002 | hsi_interface | LTC6811 obsolescence (NRND), 2026-10-01 | 9 | 5 | 6 | 5 | structure complete |
| FB2-SCN-CHG-000003 | SCN-CHG-003 | software_behavioral_defect | Field report / integration test — SOA debounce counter not reset on recovery | 4 | 3 | 4 | 3 | structure complete |

**Declared forward references.** Each change record names a `post_change_baseline` of `BAS-REF-002`, `BAS-REF-003` and `BAS-REF-004` respectively. **None of those baselines exists** — `BAS-REF-001` is the only baseline id in the corpus. The previous revision of this file presented `BAS-REF-002` … `BAS-REF-004` as though they existed. They are declarations of work not yet performed and are marked as such here.

## 6. Verification and Validation Evidence

### 6.1 What Was Actually Executed

Every number in this table is from a tool run or a log file, with the method stated. There is no estimated or asserted coverage anywhere in this section.

| Measurement | Value | Method / source |
|-------------|-------|-----------------|
| Corpus host unit-test run, total tests | 136 | `docs/artifacts/.work/verification-env/logs/results-strict.json`, field `total` |
| …passing | 94 | same file, field `passed_tests` |
| …failing | 5 | same file, field `failed_tests` |
| …build failures | 37 | same file, field `build_failures` |
| Assertions tested / passed / failed | 332 / 323 / 8 | same file |
| Host platform | Darwin arm64, Apple clang 17.0.0, Ruby 4.0.7 | same file, field `host` |
| **Target-hardware executions** | **0 / 25** | `corpus.py coverage` → `actual_product_evidence: 0/25 - 0 target-hardware executions: execution_kind has no target-hardware member, so none can be claimed (blocked, not fabricated)` |
| Execution records by kind | 34 total: 13 `actual_host_run` (as_is), 6 `synthetic_fixture` (synthetic_reference), 15 `none` | `corpus.py coverage` → `actual_product_evidence` detail |
| Line/branch coverage | **not measured** | no coverage artifact, no coverage tool output and no coverage gate exist in the corpus |

**The host run is not target-hardware evidence and carries no verification credit.** macOS is not an upstream-supported foxBMS platform, and the corpus records say so on the execution records themselves. A HALCoGen-based hardware-in-the-loop measure exists (`FB2-VER-TMS-000011`) and is recorded as blocked.

### 6.2 Mutation and Change Scenario Validation

| Measurement | Value | Method |
|-------------|-------|--------|
| Mutation scenarios defined / detected | 20 / 20 | `corpus.py check` → `scenario-test`; `corpus.py coverage` → `negative_scenario_validation` |
| Change lifecycles validated | 3 / 3 | same |
| Semantic consistency check categories executed | 10 / 10 per run | `corpus.py coverage` → `semantic_consistency_checks` |
| Links resolving without a dangling endpoint | 460 / 460 | `corpus.py coverage` → `traceability_integrity` |

### 6.3 Review Coverage

| Measurement | Value | Method |
|-------------|-------|--------|
| Artifacts covered by a `reviewed_by` link | 144 / 186 | `corpus.py coverage` → `automated_review_coverage` |
| Review records | 15 | `reviews/records/` |
| Artifacts with human approval | 0 / 220 | `corpus.py coverage` → `human_approval` |
| Artifacts with production authorization | 0 / 220 | `corpus.py coverage` → `production_authorization` |

## 7. Configuration and Variant Traceability

### 7.1 Variant Traceability

Ids quoted from `docs/artifacts/sources/variant-matrix.json` and from the `variant_applicability`
field across the corpus. `corpus.py inventory` reports `612/612 source files, 24 modules, 22
features, 23 variants`.

| Variant ID | Description | Category | Modelled in `synthetic_reference` |
|------------|-------------|----------|------------------------------------|
| VAR-REF-001 | foxBMS 2 Reference Configuration — master + 12-cell **LTC6811** slaves | reference | yes — referenced by every `synthetic_reference` record |
| VAR-AFE-LTC-6806 | LTC6806 12-cell Slave | afe | no |
| VAR-AFE-LTC-6813 | LTC6813-1 18-cell Slave | afe | **yes** |
| VAR-AFE-ADI-1830 | ADI ADES1830 16-cell Slave | afe | no |
| VAR-AFE-MAXIM-17841B | Maxim MAX17841B 14-cell Slave | afe | no |
| VAR-AFE-MAXIM-17852 | Maxim MAX17852 14-cell Slave | afe | no |
| VAR-AFE-NXP-MC33775A | NXP MC33775A 14-cell Slave | afe | no |
| VAR-AFE-TI-BQ79XXX | TI BQ79xxx AFE Family | afe | no |
| VAR-CURRENT-SENSOR-LEM | LEM CAB500 Current Sensor | current_sensor | no |
| VAR-CURRENT-SENSOR-HONEYWELL | Honeywell BAS6C-X00 Current Sensor | current_sensor | no |
| VAR-IMD-BENDER-IR155 | Bender IR155 Insulation Monitor | imd | no |
| VAR-TEMP-EPCOS-B57251 | EPCOS B57251 Temperature Sensor (lookup-table) | temperature_sensor | **yes** |
| VAR-TEMP-MURATA | Murata NCXXXXH103 Temperature Sensor | temperature_sensor | no |
| VAR-TEMP-SEMI | Semitec 103JT Temperature Sensor | temperature_sensor | no |
| VAR-TEMP-TDK | TDK NTCG/NTCGS Temperature Sensors | temperature_sensor | no |
| VAR-TEMP-VISHAY | Vishay NTC Temperature Sensors | temperature_sensor | no |
| VAR-BAL-HISTORY | History-based Balancing Strategy | balancing | **yes** |
| VAR-BAL-NONE | No Balancing | balancing | **yes** |
| VAR-SOC-DEBUG | SOC Debug Strategy | soc_method | **yes** |
| VAR-SOE-DEBUG | SOE Debug Strategy | soe_method | **yes** |
| VAR-SOH-NONE | SOH None (placeholder) | soh_method | **yes** |
| VAR-OS-POSIX | POSIX Unit Test Build | build | no |
| VAR-OS-WIN32 | Win32 Unit Test Build | build | no |
| VAR-BOOTLOADER | Bootloader Enabled | bootloader | **yes** |

Two corrections against the previous revision of this file. It listed **`VAR-AFE-LTC-6811`**, which
does not exist as a variant: the LTC6811 is the *reference configuration itself* (`VAR-REF-001`),
not a variant of it. And it listed 4 variants where the matrix holds 23, so 19 were omitted.

### 7.2 Parameter Traceability

All 10 entries in `docs/artifacts/shared/parameter-registry.json`. The registry has **no `referenced_by` field**, so the previous revision's "Referenced By" column was unverifiable; it is replaced by the fields the registry actually records.

| Parameter ID | Name | Value | Unit | Tolerance | Domain | Assumptions | Configuration |
|--------------|------|-------|------|-----------|--------|-------------|---------------|
| FB2-PRM-000001 | cell_voltage_max | 4200 | mV | 4199–4201 absolute | Cell voltage upper limit for SOA monitoring | FB2-ASM-001 | VAR-REF-001 |
| FB2-PRM-000002 | cell_voltage_min | 2500 | mV | — | Cell voltage lower limit | FB2-ASM-001 | VAR-REF-001 |
| FB2-PRM-000003 | afe_acquisition_period_ms | 50 | ms | — | AFE acquisition period | FB2-ASM-004 | VAR-REF-001 |
| FB2-PRM-000004 | ftti_ms | 100 | ms | — | Fault tolerant time interval | FB2-ASM-004, FB2-ASM-006 | VAR-REF-001 |
| FB2-PRM-000005 | contactor_mechanical_time_ms | 30 | ms | — | Contactor mechanical opening time | FB2-ASM-006 | VAR-REF-001 |
| FB2-PRM-000006 | independent_monitor_latency_ms | 50 | ms | — | Independent monitor latency | FB2-ASM-008 | VAR-REF-001 |
| FB2-PRM-000007 | soa_debounce_count | 2 | count | — | SOA debounce | FB2-ASM-005 | VAR-REF-001 |
| FB2-PRM-000008 | pack_current_max_charge | 200 | A | — | Maximum charge current | FB2-ASM-009 | VAR-REF-001 |
| FB2-PRM-000009 | pack_current_max_discharge | 400 | A | — | Maximum discharge current | FB2-ASM-009 | VAR-REF-001 |
| FB2-PRM-000010 | cell_temperature_max | 600 | 0.1°C | — | Maximum cell temperature | FB2-ASM-010 | VAR-REF-001 |

The previous revision listed four parameters and had `ftti_ms` and `afe_acquisition_period_ms` **swapped** between `FB2-PRM-000003` and `FB2-PRM-000004`.

## 8. Assumption Traceability

The assumption registry `docs/artifacts/shared/assumption-registry.json` holds `FB2-ASM-001` … `FB2-ASM-012`, in the **three-digit** form. These ids resolve. Five are reproduced below with the fields the registry records; the full set of 12 is in the registry.

| Assumption ID | Statement (abridged) | Validity conditions | Invalidation consequence |
|---------------|----------------------|----------------------|---------------------------|
| FB2-ASM-001 | Lithium-ion cell chemistry, nominal 3.7 V, operating range 2.5–4.2 V | Applies to Li-ion, LiFePO4, NMC | Voltage limits must be reconfigured per chemistry |
| FB2-ASM-002 | Thermal runaway initiates at cell voltage > 4.3 V and elevated temperature | Valid for NMC/LCO chemistries | **ASIL assignment may change; FTTI budget may need revision** |
| FB2-ASM-004 | AFE SPI communication latency < 5 ms including DMA | Assumes 1 MHz SPI, DMA available | FTTI budget exceeded; acquisition period must change |
| FB2-ASM-006 | Contactor mechanical opening time ≤ 30 ms worst case | Valid for the specified contactor | FTTI budget exceeded; independent monitor requirement affected |
| FB2-ASM-008 | Independent hardware voltage monitor can be implemented | Requires PCB space, separate power | Must rely on main-path timing optimisation |

`FB2-ASM-002` is the load-bearing assumption for the ASIL story: it says in its own `invalidation_consequence` that the ASIL assignment may change. The `asil` field on `FB2-SAF-SGO-000001` rests on it and on nothing else, and carries no justification.

## 9. Standards Reference Traceability

**This is a reference index, not a compliance matrix.** It records which corpus artifacts a clause
refers to. It does **not** assert that the clause's obligations are satisfied, that the clause text
has been verified against the normative standard, or that any assessment occurred.

`governance/standards-lock.json` locks exactly two standards:

- `ISO_26262_2018` (ISO 26262:2018, parts 1–12)
- `ASPICE_PAM_41` (Automotive SPICE PAM v4.1)

Neither standard's normative text is reproduced anywhere in the corpus; the lock records
`document_digest: not_ingested` and `rights_policy.normative_text_reproduction: false`. The clause
identifiers below are therefore **the corpus's own references against a locked standard's own part
and clause structure** — they are not verified citations against the normative text, because the
normative text has not been ingested. The proprietary standards themselves are not present.

| Standard | Clause (corpus reference) | Related Artifacts | Verification method actually present |
|----------|--------|-------------------|---------------------------------------|
| ISO 26262-6 | 6.4.4 | FSRs, TSRs, SWRs | review; test measures and executions exist (§3.4) |
| ISO 26262-6 | 6.4.5 | Test Measures, Executions | execution records exist; **no target-hardware execution** (§6.1) |
| ISO 26262-6 | 6.4.6 | Safety Analyses (FMEA, FTA, DFA, FFI) | review of `FB2-SAF-ANL-000001` … `-000004` |

**ISO 26262-2 and -3 are additionally carried** in the corpus mappings: `ISO 26262-2` (management) and
`ISO 26262-3` (concept phase) are the parts the governance records, findings and safety concepts map
themselves to. `corpus.py coverage` prints `standards_mapping: 44/44 - ASPICE processes 32/32, ISO parts 12/12` — that is a count of *mappings present*, not a conformity score.

### 9.1 IEC 61508 — candidate standard, not engaged

The previous revision of this file carried two rows in this table citing IEC 61508-3 clauses 7.4.4
and 7.4.5, and its own §9 preamble asserted that the clause ids in the table "are the corpus's own
references". That assertion was false for IEC 61508 and has been removed together with the rows.

The precise position, stated exactly:

- **IEC 61508 is not locked.** `governance/standards-lock.json` locks only `ISO_26262_2018` and `ASPICE_PAM_41`.
- **The corpus has performed no IEC 61508 work.** `reports/final-acceptance-report.json` records `iec_61508_records_in_corpus: 0`. No requirement, mapping, analysis, test measure or work product in `corpus/`, `governance/`, `schemas/`, `sources/`, `traceability/` or `scenarios/` references it.
- **It is nonetheless a legitimate candidate for this product.** The pinned source lists IEC 61508 as a candidate standard and cites IEC 61508-3:2010. It is therefore **not** deleted from the project's consideration, and the finding that prompted its removal says so explicitly.
- **The corpus cannot supply anything for an IEC 61508 clause row.** Producing one would require the standard to be added to the lock and the referenced records to be authored. Neither has happened.

To engage IEC 61508: add it to `governance/standards-lock.json` with the same rights-handling
metadata, author the records the clause requires, then add the rows here. Until then this document
carries no IEC 61508 reference, because it has nothing behind it.

## 10. Traceability Matrix Summary

### 10.1 Corpus-Wide Figures

**Authoritative source: `python3 docs/artifacts/tools/corpus.py coverage`** (or
`reports/coverage-report.json`, which is the same tool's own output and is regenerated by that
command). `reports/coverage-report.md` is a **snapshot** written by hand on 2026-09-29 from an
earlier run: it reports `source_grounding 76/154`, `traceability_integrity 283/283`,
`automated_review 82/123` and `human_approval 0/154`, all of which are stale. The previous revision
of this file pointed readers at that snapshot as "authoritative, tool-computed figures"; it is not
authoritative, and the pointer has been corrected.

Live run on 2026-09-29:

| # | Dimension | Achieved | Note as printed by the tool |
|---|-----------|----------|------------------------------|
| 1 | scope_accounting | 1/1 | source/feature/variant inventories present |
| 2 | artifact_population | 13/13 | families populated |
| 3 | standards_mapping | 44/44 | ASPICE processes 32/32, ISO parts 12/12 |
| 4 | source_grounding | 80/220 | artifacts with `source_refs` (102 anchors available) |
| 5 | traceability_integrity | 460/460 | 460 links, 0 dangling |
| 6 | semantic_consistency_checks | 10/10 | 10 check categories executed per run |
| 7 | automated_review_coverage | 144/186 | 144/186 artifacts covered by 15 review records |
| 8 | verification_planning | 25/7 | 25 test measures for 7 FSRs |
| 9 | **actual_product_evidence** | **0/25** | 0 target-hardware executions; blocked, not fabricated |
| 10 | synthetic_fixture_coverage | 148/43 | 148 synthetic_reference artifacts (target 43) |
| 11 | negative_scenario_validation | 20/20 | 20/20 mutations; 3/3 change lifecycles |
| 12 | final_status | `synthetic_ready_with_limitations` | — |
| 13 | export_reproducibility | 1/1 | export manifest present |
| 14 | **human_approval** | **0/220** | all artifacts pending human approval (none performed) |
| 15 | **production_authorization** | **0/220** | `production_authorized=false` for all artifacts (by policy) |

Record counts: `corpus.py validate` validates **243 artifact files**; the artifact index
de-duplicates on `(profile, id)` and holds **220** records (166 `synthetic_reference`, 71 `as_is`,
the balance being profile-shared), plus 23 scenario records under `scenarios/`. A ratio printed
above 100% — dimension 10 — is an over-coverage count, not a score.

### 10.2 Traceability Completeness

The previous revision of this section asserted `95%`, `100%` and "Complete chain" for six chain
directions with **no method stated**. None of those six figures was computed by any tool in the
corpus. They have been replaced with the closest measured proxy, named as such.

| Chain direction | What is actually measured | Value | Method |
|-----------------|--------------------------|-------|--------|
| Requirement → Design → Test | safety requirements with **no** `fault_reaction` field | 7 open validation findings (`FB2-SAF-FSR-000001` ×2, `-000002` ×2, `-000003` ×2, `-000004` ×1) | `corpus.py validate` semantic rule, category `verification`, severity `medium` |
| ASIL derivation | safety goals whose `asil` field has no justification | 2 open validation findings (one per profile) | same run: `safety goal FB2-SAF-SGO-000001 ASIL ASIL_D lacks justification` |
| Test → Design → Requirement | execution records whose measure has no `verifies` link | 0 | every `result_of` target measure carries ≥1 `verifies` link |
| Hazard → Safety Goal → FSR | hazards with a `mitigates` edge to a safety goal | 1 / 1 | link registry `FB2-LNK-SAF-000001`; `FB2-SAF-HAZ-000001` is the only hazard |
| FSR → Design → Code | designs implementing an SWR | 3 / 3 | `implements` links `FB2-LNK-SAF-000011` … `-000013`; `FB2-SW-DSN-000004` is a declared forward reference (§3.3) |
| Parameter → Artifacts | parameters with a recorded assumption and configuration link | 10 / 10 | `assumptions[]` and `configuration_selection[]` in the parameter registry |
| Assumption → Artifacts | assumptions referenced by a concept or parameter | 12 / 12 registered; 9 referenced by `FB2-SAF-FSC-000001`, 5 by `FB2-SAF-TSC-000001` | `assumption_refs` / `concept_assumptions` fields |
| **Product evidence** | target-hardware executions | **0 / 25** | `actual_product_evidence` dimension |

A live `corpus.py validate` raises **9 findings, `errors=0`**: 7 × missing `fault_reaction`, 2 ×
`ASIL_D` without justification. All 9 are severity `medium`, category `verification`. These are the
*validator's* findings raised fresh on each run; they are distinct from the 30 recorded finding
records in `reviews/findings/`. A prior remediation pass reduced the validator's finding count from
21 to 9; the remaining 9 are the ones above.

`traceability_integrity: 460/460` means every link endpoint resolves. It says nothing about whether
the links are correct, and it is not a completeness percentage.

## 11. Tools and Automation

### 11.1 Tooling Used in This Workspace

| Tool | Role | Where its output lives |
|------|------|------------------------|
| `docs/artifacts/tools/corpus.py` | corpus index, schema validation, link validation, semantic rules, coverage, export, acceptance suite | `reports/*.json`, `exports/`, `views/` |
| `docs/artifacts/tools/check_references.py` | resolves every id-shaped payload-field reference; checks FTTI arithmetic | stdout, exit code |
| `docs/artifacts/tools/render_spec_documents.py` | renders the nine spec documents | `spec-documents/` |
| `graphify` | code structure extraction | `graphify-out/` |
| Ceedling / Unity / CMock | host unit-test build and run | `docs/artifacts/.work/verification-env/logs/results-strict.json` |
| HALCoGen | hardware-in-the-loop | **not available in this workspace**; the target-hardware measure is recorded as blocked |

Ceedling is installed under `docs/artifacts/.work/verification-env/.work-gems/`. It was invoked
through that local gem set; the run is the 136-test host run in §6.1, which passed 94, failed 5
and recorded 37 build failures. **No foxBMS source, test, configuration or build file was modified
by the work this document describes.**

### 11.2 Traceability Automation Rules

These are the rules `corpus.py validate` executes. They are stated because they bound what the
numbers above can mean.

- All artifacts validated against JSON schemas
- Identity uniqueness enforced per profile (cross-profile duplicates are intentional)
- Link endpoints validated against the artifact registry
- Provenance refs validated against registries
- Semantic consistency rules enforced (10 categories per run)
- `human_approval_status: approved` and `production_authorized: true` are **rejected** by the validator
- Free-string id references in payload fields are resolved by `check_references.py`, not by the link validator

## 12. Change Management Traceability

### 12.1 Baseline Management

| Baseline ID | Pinned source commit | Tag | Date | Meaning |
|-------------|---------------------|-----|------|---------|
| BAS-REF-001 | 308028fb | v1.11.0 | 2026-09-08 | The **only** baseline in the corpus. It pins the *source* inventory (what the real repository demonstrably contains at that commit). The corpus artifacts themselves are generated work product, not content of that commit — `git ls-tree -r 308028fb` contains no `TRACEABILITY` entry. |

The previous revision of this file listed `BAS-REF-001` with "All corpus artifacts" in the Artifacts
column, implying the corpus lives at that commit. It does not. The column has been corrected.

### 12.2 Change Impact Traceability

| Change artifact | Baseline before | Baseline after (**declared, not created**) | Artifacts affected | Links affected | Reverification measures selected |
|-----------------|-----------------|------------------------------------------|-------------------|----------------|---------------------------------|
| FB2-SCN-CHG-000001 | BAS-REF-001 | BAS-REF-002 | 6 | 2 | 3 |
| FB2-SCN-CHG-000002 | BAS-REF-001 | BAS-REF-003 | 9 | 5 | 5 |
| FB2-SCN-CHG-000003 | BAS-REF-001 | BAS-REF-004 | 4 | 3 | 3 |

The previous revision chained these as a sequence (`BAS-REF-001 → 002 → 003 → 004`). The records do
not: each change's `baseline_before` is `BAS-REF-001`, and the three `post_change_baseline` values
are declared forward references to baselines that do not exist. Whether to author them or to mark
the changes as not-yet-baselined is an open decision; it is the substance of finding
`FB2-REV-FND-000030` for the same class of problem.

## 13. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| ASIL | Automotive Safety Integrity Level (ISO 26262). In this corpus an `ASIL-x` value is a **hypothetical field value in a fictional project**, not a determination for the real product |
| FSR | Functional Safety Requirement |
| TSR | Technical Safety Requirement |
| SWR | Software Requirement |
| HSI | Hardware-Software Interface |
| FTTI | Fault Tolerant Time Interval |
| FMEA | Failure Mode and Effects Analysis |
| FTA | Fault Tree Analysis |
| DFA | Dependent Failure Analysis |
| FFI | Freedom From Interference |
| LCOV / gcov | Line/branch coverage tools. **Not used in this corpus; no coverage figure exists** |
| HALCoGen | Hardware-in-the-loop generator named as an unblocking condition on the target-hardware measure |

The previous revision of this glossary listed `ASIL` and `FFI` twice each and omitted `DFA` and `LCOV`.

### Appendix B: Referenced Documents

The first is a corpus baseline id. The remaining four are **identifiers in the pinned upstream
foxBMS 2 source**, not corpus artifacts — they are not resolvable in the artifact index and are
listed only as pointers for a reader who wants the real project's documentation.

| Id | Title | Kind |
|----|-------|------|
| BAS-REF-001 | Baseline Reference (pinned source commit `308028fb`) | corpus baseline |
| SAFETY | Safety Manual (upstream `docs/general/safety/`) | pinned source document |
| SOFTWARE_STRUCTURE | Software Structure (upstream `docs/general/`) | pinned source document |
| SOFTWARE_VERIFICATION | Software Verification (upstream `docs/general/`) | pinned source document |
| SOFTWARE_TESTING | Software Testing (upstream `docs/general/`) | pinned source document |

---

## 14. Document Control — no approval exists

| Field | Value |
|-------|-------|
| Authored by | an automated agent session. Role names appearing in this corpus (`safety_engineer`, `quality_engineer`, `sw_engineer`, `cybersecurity_engineer`, `configuration_manager`, `system_engineer`, `verification_engineer`) are **fictional corpus role labels**. No person held any of them and no person reviewed this document. |
| Reviewed by | **nobody.** No human review of this file has taken place. |
| Approved by | **nobody.** There is no approval. |
| Independent confirmation | **none.** The author is not independent of the content, and no third party has confirmed anything. |
| Human approval status, this document | `pending` — it has never been submitted for approval and would not pass an approval gate as written. |
| Human approval status, corpus-wide | `pending` for all 220 indexed records (`corpus.py coverage` → `human_approval: 0/220`) |
| Production authorized | `false` for this document and for all 220 indexed records (`corpus.py coverage` → `production_authorization: 0/220`) |
| Tool qualification | **none.** `corpus.py` is an unqualified script. No tool-qualification record exists anywhere in the corpus and none is claimed. |
| Certification | **none claimed.** No certification body, certificate or third-party assessment record exists. |
| ASPICE capability level | **not asserted.** No assessment has been performed. |
| Distribution | Internal. Contains no claim intended for external use. |

The previous revision of this document ended its document-control block with three rows naming a
safety engineer as reviewer and a safety manager as approver, and recording the status of the
document as approved. **No such review and no such approval ever took place.** The block presented
fictional corpus role labels as though they were people who had signed off, and it contradicted both
the READ FIRST header in the same file and the state of all 220 corpus records. It has been removed
and replaced by the table above, which states the real position.

## 15. Provenance and Drift Risk

**This file is hand-authored. It is not generated, not regenerated, and not under the control of any
tool in this repository.** The previous revision of this file ended with the sentence "This document
is automatically generated from the foxBMS 2 lifecycle artifact corpus. Manual edits will be
overwritten on next generation." That was false, and it was actively harmful: it told the next editor
that the authorised repairs recorded in finding `FB2-REV-FND-000022` would be erased on the next
run, inviting exactly the reversion the finding exists to prevent.

The truth, stated plainly:

- **No generator reads or rewrites this file.** `docs/artifacts/tools/corpus.py` indexes
  `corpus/`, `reviews/` and `scenarios/` and writes `exports/`, `views/`, `reports/*.json` and
  `spec-documents/`. It never opens the repository root. `git ls-tree -r 308028fb` contains no
  `TRACEABILITY` entry, so the file is not a build output either.
- **Nothing here is automatically kept in step with the corpus.** Every table in this document is a
  hand-transcription. When the corpus changes, this document does not change with it.
- **Therefore it is subject to drift, and the drift is undetectable by tooling.** There is no CI
  gate over this file. Nothing in `corpus.py check` would notice if the corpus grew by 40 records or
  if an identifier below stopped resolving.
- **The authoritative surfaces are elsewhere.** `docs/artifacts/README.md`,
  `docs/artifacts/views/`, `docs/artifacts/reports/coverage-report.json` and
  `docs/artifacts/reports/final-acceptance-report.json` are the surfaces to read for current state.
  Where this document and those disagree, **they are right and this document is wrong.**
- **The durable fix is not implemented.** Relocating the file under `docs/artifacts/` and generating
  it from the canonical records would put it under the guard-field discipline that governs every
  generated surface. That is an engineering decision the repository owner has not taken, and it is
  recorded as the residual risk of finding `FB2-REV-FND-000022`.
- **A reader who checks one thing should check this:** the READ FIRST header. If it is gone, the
  document has drifted.
