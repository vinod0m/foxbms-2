# Standards Mapping Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Locked standards:** ISO 26262:2018, ASPICE PAM 4.1 (`governance/standards-lock.json`, `locked_by: safety`)

> This report records a **structural mapping** from corpus artifacts to
> standard clause and process references. It is **not** a conformity
> assessment. Nothing here asserts ISO 26262 conformity, an ASIL capability, an
> IEC 61508 conformity, certification, tool qualification, or an ASPICE
> capability level. All 153 indexed records are `human_approval_status: pending`
> and `production_authorized: false`. No human has approved anything in this
> corpus.
>
> Every status below is read from `governance/coverage-plan.json` as it stands on
> 2026-09-29. Fifteen corrections (`CORR-COV-001` … `CORR-COV-015`) have been
> applied to that file; where a status was corrected, the reason is recorded
> there and summarised in §4.

## 1. Standards Lock

| Standard ID | Title | Edition |
|---|---|---|
| `ISO_26262_2018` | ISO 26262:2018 — Road vehicles — Functional safety | 2018 |
| `ASPICE_PAM_41` | Automotive SPICE Process Assessment Model (PAM) v4.1 | 4.1 |

**IEC 61508 is not locked and no corpus record was authored against it.** No corpus record was authored against IEC 61508. It is absent from `governance/standards-lock.json`, which locks exactly two standards: `ISO_26262_2018` (2018) and `ASPICE_PAM_41` (4.1). No requirement, `standards_mapping`, analysis, test measure or work product in `corpus/`, `governance/`, `schemas/`, `sources/`, `traceability/` or `scenarios/` references it. The standard is **not** alien to the product: the pinned source lists it as a candidate (`docs/general/safety/safety.rst:60`) and cites IEC 61508-3:2010 in `docs/references.bib`. The defect is that the corpus performed no IEC 61508 work, so it cannot supply compliance evidence for it. See §5.

## 2. ISO 26262:2018 Part Coverage

| Part | Status | Basis on disk |
|---|---|---|
| Part 1 — Vocabulary | referenced | terminology used consistently; no separate vocabulary artifact |
| Part 2 — Management of functional safety | `mapped` | `FB2-MAN-SPL-000001` Safety Plan (management domain), roles, tailoring |
| Part 3 — Concept phase | **`partially_mapped`** | HARA `FB2-SAF-HAZ-000001` and safety goal `FB2-SAF-SGO-000001` exist in both profiles. **No functional safety concept and no technical safety concept record exists.** The only item definition is the TARA's `item_and_scope`, which defines the security item, not the functional-safety item. |
| Part 4 — System-level product development | **`partially_mapped`** | HSI interface authority `FB2-SYS-HSI-000001` only. No system requirements record; no technical safety concept record. |
| Part 5 — Hardware-level product development | `partially_mapped` | 7 hardware requirement records (`FB2-HW-TSR-000001..000004` in both profiles); FMEDA and quantitative analysis not generated. |
| Part 6 — Software | **`partially_mapped`** | SW requirements (`FB2-SW-SWR-000001..000003`), architecture and detailed design are backed. **Unit verification is only partially mapped** — `SWE.4` is recorded `partially_mapped` with blocked execution records. |
| Part 7 — Production | **`gap`** | No production, end-of-line test, operation, service or decommissioning record exists in either profile. None of the domains `production`, `operation`, `service`, `decommissioning` appears in any record. |
| Part 8 — Supporting processes | **`gap`** | No supporting-domain **process-definition** record exists for configuration management, change management, documentation, QA, measurement or process improvement. The generated `views/supporting-processes/supporting-processes.md` reports all six families as coverage gaps. |
| Part 9 — ASIL | `mapped` | ASIL field values recorded on `FB2-SAF-SGO-000001` (`ASIL_D`) and `FB2-SAF-FSR-000004` (`ASIL_B`); FMEA, FTA, dependent failure analysis, freedom-from-interference. See §6 for the caveat. |
| Part 10 — Guidelines | referenced | methodology guidance |
| Part 11 — Semiconductors | `not_applicable` | foxBMS is a BMS platform, not semiconductor development. `reference_decision: APP-ISO-11`. |
| Part 12 — Motorcycles | `not_applicable` | foxBMS targets automotive/industrial energy storage. `reference_decision: APP-ISO-12`. |

Part coverage across the 12 ISO parts: **2 `mapped`, 4 `partially_mapped`,
2 `gap`, 2 `referenced`, 2 `not_applicable`**. Parts 11 and 12 are
`not_applicable` by recorded decision with rationale and `reference_decision`,
not by absence.

The acceptance gate `standards_mapping` reports 44/44 because it counts that
every locked process and every ISO part carries an **explicit disposition**. It
does not assert that any of those dispositions is favourable, and **two ISO
parts and six ASPICE processes are now `gap`**.

## 3. ASPICE Process Inventory

32 process entries: **28 applicable**, **4 explicitly `not_applicable`**
(`MLE.1`–`MLE.4`, each with a rationale and a `reference_decision` of
`APP-MLE-ALL`).

### Disposition across the 28 applicable processes

| Disposition | Count | Processes |
|---|---|---|
| `mapped` | 12 | SYS.3, SWE.1, SWE.2, SWE.3, HWE.1, ACQ.4, SUP.1, SUP.8, SUP.9, SUP.10, SUP.11, REU.2 |
| `partially_mapped` | 10 | SYS.4, SYS.5, SWE.4, SWE.5, SWE.6, HWE.2, HWE.3, VAL.1, SPL.2, MAN.6 |
| `gap` | 6 | SYS.1, SYS.2, HWE.4, MAN.3, MAN.5, PIM.3 |

### The six `gap` processes, with what is actually missing

| Process | Expected artifacts (retained) | What exists |
|---|---|---|
| `SYS.1` Requirements Elicitation | Stakeholder Needs, Use Cases, Operational Scenarios | **Nothing.** No stakeholder-needs, use-case or operational-scenario record in either profile. |
| `SYS.2` System Requirements Analysis | System Requirements Specification, System Modes/States, Interface Requirements | **Nothing.** `corpus/synthetic_reference/system/` holds only the HSI design. |
| `HWE.4` Hardware Integration and Test | HW Integration Plan, HW Test Specification, HW Test Results | Synthetic test specs only; `as_is` has no explicit HW test record. |
| `MAN.3` Project Management | Project Plan, Schedule, Resource Plan, Progress Reports | `FB2-MAN-SCO-000001` "Project Scope" only — a scope statement is a boundary declaration, not a plan. |
| `MAN.5` Risk Management | Risk Register, Risk Analyses, Mitigation Plans | `FB2-SAF-TAR-000001` TARA threat table only — security threat risk, not project risk; its own `residual_risk_acceptance.acceptance_exists` is `false`. |
| `PIM.3` Process Improvement | Improvement Proposals, Improvement Records, Effectiveness Evaluation | **Nothing.** Findings and reviews are improvement *inputs*, not improvement records. |

Every `expected_artifacts` and `capability_attributes` list above is retained
unchanged. Only statuses were corrected. No expectation was deleted or narrowed,
and no artifact was fabricated to make a status true.

## 4. Corrections Applied to the Coverage Plan

15 corrections recorded, all dated 2026-09-29.

| ID | Target | Before | After |
|---|---|---|---|
| CORR-COV-001 | `SYS.1` disposition | `mapped` | `gap` |
| CORR-COV-002 | `SYS.2` disposition | `mapped` | `gap` |
| CORR-COV-003 | `SPL.2` disposition | `mapped` | `partially_mapped` |
| CORR-COV-004 | ISO Part 7 | `mapped` | `gap` |
| CORR-COV-005 | ISO Part 4 | `mapped` | `partially_mapped` |
| CORR-COV-006 | `MAN.3` disposition | `mapped` | `gap` |
| CORR-COV-007 | `MAN.5` disposition | `mapped` | `gap` |
| CORR-COV-008 | `MAN.6` disposition | `mapped` | **`partially_mapped`** |
| CORR-COV-009 | `PIM.3` disposition | `mapped` | `gap` |
| CORR-COV-010 | ISO Part 3 | `mapped` | `partially_mapped` |
| CORR-COV-011 | ISO Part 6 | `mapped` | **`partially_mapped`** |
| CORR-COV-012 | ISO Part 8 | `mapped` | **`gap`** |
| CORR-COV-013 | `artifact_coverage_targets.requirements` | overclaim | `partially_mapped` |
| CORR-COV-014 | `artifact_coverage_targets.process` | overclaim | `partially_mapped` |
| CORR-COV-015 | `capability_dimension.level_1_performed` | overclaim | `not_met` |

Two of these (`CORR-COV-008` on `MAN.6`, `CORR-COV-011` on ISO Part 6) did not
land on the status the originally reported reality suggested. Verification
against disk found evidence on **both** sides of each claim, so both were
recorded as `partially_mapped` and the divergence is stated in the reason rather
than resolved in whichever direction is more convenient. In `MAN.6`'s case the
originally reported claim that "no metric definitions" exist was found to be
inaccurate as written: 26 records carry 100 `acceptance_criteria` entries, each
with a named measure, threshold and unit.

### Two residual disagreements, left visible

1. `SUP.1`, `SUP.8`, `SUP.9` and `SUP.10` still read `mapped` in
   `process_inventory`, while the generated supporting-processes view reports
   no **process-definition** record for those families. These are different
   claims — review, change and configuration evidence does exist — and both
   readings are now stated in the plan rather than one being silently chosen.
2. `sources/feature-inventory.json` carries `summary.total_features: 20` while
   holding 22 feature records. `corpus.py inventory` reports 22.

## 5. A Conformity Claim in the Hand-Authored Root Document — Corrected

`TRACEABILITY_DOCUMENT.md` at the **repository root** **stated** under "1.1 Purpose"
"Provides evidence for compliance with ISO 26262, IEC 61508, and other
applicable safety standards", stated under "1.2 Scope" "Safety Requirements
(ASIL-D, ASIL-B)", and carried a document-control sign-off block naming a safety
engineer as reviewer, a safety manager as approver, and the document status as
approved. That approval never existed.

- The IEC 61508 reference was unsupported: the standard is not in the standards
  lock and no corpus record was authored against it. Note that the pinned
  source *does* list IEC 61508 as a candidate standard and cite IEC 61508-3:2010,
  so the standard is a legitimate consideration for the product; the defect was
  that compliance evidence was claimed for work never performed. The correction
  removed the two IEC 61508-3 clause rows and replaced them with an explicit
  not-engaged note rather than deleting the standard from consideration.
- The conformity claim was unsupported: all corpus records are unapproved and
  unauthorized, and no certification, tool qualification or third-party
  assessment record exists.
- The `asil` field on `FB2-SAF-SGO-000001` carries no justification field, which
  the corpus's own validator flags as an open finding.
- `git ls-tree -r 308028fb` contains no `TRACEABILITY` entry, so the file is
  corpus output, not pinned upstream source.

**The repository owner explicitly authorised amending the file.** It lies outside the
absolute `docs/artifacts/` write boundary, and that authorisation is the sole basis
for the out-of-boundary write; it is recorded verbatim in the finding. The file was
corrected on 2026-09-29 and is recorded as finding **`FB2-REV-FND-000022`** at
revision 3 (severity `high`, category `consistency`, disposition `accepted`) at
`docs/artifacts/reviews/findings/finding-000022-root-traceability-document-conformity-claim.json`.
The §9 standards-reference preamble in that file was also corrected so it no longer
implied the removed IEC rows were corpus references.

**Residual risk, not closed by that disposition:** the file remains hand-authored
and outside the toolchain's reach, so nothing will detect a regression.

## 6. ASIL: What the Records Actually Say

`FB2-SAF-SGO-000001` carries `"asil": "ASIL_D"` and
`FB2-SAF-FSR-000004` carries `safety_allocation.asil: "ASIL_B"`. Those field
values are real and traceable to those records.

They are **not** an ASIL determination. An ASIL classification derives from
hazard analysis and risk assessment through a functional safety concept and a
technical safety concept. **Neither of those concept records exists in the
corpus** (`CORR-COV-010`). The values are therefore field entries on synthetic
records with no concept-phase derivation behind them, and this report does not
present them as evidence of ASIL capability.

## 7. What Structural Mapping Is Not

| This report establishes | This report does **not** establish |
|---|---|
| Every locked process and ISO part has an explicit, recorded disposition | That any disposition is favourable — 2 ISO parts and 6 ASPICE processes are `gap` |
| 283 traceability links resolve with 0 dangling | That the linked artifacts are correct, only that they resolve |
| Clause references are recorded per record | That the clause text was ingested; it was not, and unverified references are marked as such |
| The corpus holds a safety plan, HARA, safety goals and safety analyses | ISO 26262 conformity, ASIL capability, or certification |
| ASPICE process references are recorded | Any ASPICE capability level, for any process |

No process in this corpus is assessed at any ASPICE capability level. The
`capability_dimension.level_1_performed` entry in the coverage plan has been
corrected to `not_met` and now carries an explicit note that it defines what
Level 1 would require rather than asserting that Level 1 was reached.
