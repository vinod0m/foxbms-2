# Standards Mapping Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Locked standards:** ISO 26262:2018, ASPICE PAM 4.1 (`governance/standards-lock.json`, `locked_by: safety`)

> This report records a **structural mapping** from corpus artifacts to
> standard clause and process references. It is **not** a conformity
> assessment. Nothing here asserts ISO 26262 conformity, an ASIL capability, an
> IEC 61508 conformity, certification, tool qualification, or an ASPICE
> capability level. All **263** indexed records are `human_approval_status: pending`
> and `production_authorized: false`. No human has approved anything in this
> corpus.
>
> Every status below is read from `governance/coverage-plan.json` as it stands on
> 2026-10-01. **Sixteen** corrections are recorded in that file
> (`CORR-COV-001` … `CORR-COV-016`). `CORR-COV-016` (2026-10-01) was a
> substantive audit that ignored the disposition text: it derived every
> process's backing set from each artefact's own
> `standards_mappings[].reference` and asked whether those records carry the
> engineering the process defines. It demoted 23 of the 28 applicable ASPICE
> processes and 8 of the 10 applicable ISO parts, and raised nothing.

## 1. Standards Lock

| Standard ID | Title | Edition |
|---|---|---|
| `ISO_26262_2018` | ISO 26262:2018 — Road vehicles — Functional safety | 2018 |
| `ASPICE_PAM_41` | Automotive SPICE Process Assessment Model (PAM) v4.1 | 4.1 |

**IEC 61508 is not locked and no corpus record was authored against it.** No corpus record was authored against IEC 61508. It is absent from `governance/standards-lock.json`, which locks exactly two standards: `ISO_26262_2018` (2018) and `ASPICE_PAM_41` (4.1). No requirement, `standards_mapping`, analysis, test measure or work product in `corpus/`, `governance/`, `schemas/`, `sources/`, `traceability/` or `scenarios/` references it. The standard is **not** alien to the product: the pinned source lists it as a candidate (`docs/general/safety/safety.rst:60`) and cites IEC 61508-3:2010 in `docs/references.bib`. The defect is that the corpus performed no IEC 61508 work, so it cannot supply compliance evidence for it. See §5.

## 2. ISO 26262:2018 Part Coverage

| Part | Status | Basis on disk, as audited 2026-10-01 |
|---|---|---|
| Part 1 — Vocabulary | `referenced` | Terminology used consistently; no separate vocabulary artefact. Unchanged. |
| Part 2 — Management of functional safety | **`partially_mapped`** | Backing record is `FB2-MAN-SPL-000001` **and it is not a safety plan**: `artifact_type: design`, `design_level: architecture`, with `decomposition`, `interfaces`, `behavior_model`, `budgets`, `failure_response` and `implementation_mapping` **all empty**, and a `responsibilities` list of seven activity headings that assigns none of them to a role. Roles: absent. Tailoring: absent. Its own `constraints` field says `Independent confirmation for ASIL D (not achieved in synthetic)`. |
| Part 3 — Concept phase | **`partially_mapped`** | Item definition `FB2-SAF-ITE-000001`, functional safety concept `FB2-SAF-FSC-000001` (36,125 B) and technical safety concept `FB2-SAF-TSC-000001` (48,044 B) all exist and are substantial. **The concept is not closed:** `FB2-REV-FND-000025` (high) is the timing budget's arithmetic not closing, and `FB2-REV-FND-000024` (high) is the contactor reaction requirement contradicting itself. Writing the concepts exposed four more contradictions, `FB2-REV-FND-000023..000027`, raised and deliberately **not** corrected in place. All three are synthetic and unapproved. |
| Part 4 — System-level product development | **`partially_mapped`** | HSI interface authority `FB2-SYS-HSI-000001` and eight system requirements `FB2-SYS-SYR-000001..000008` exist. **No system-architecture record** exists — the HSI record's own `design_level` is `interface_specification`, one interface rather than the architecture. **No system modes or states record exists.** The two high findings above both sit inside this part. |
| Part 5 — Hardware-level product development | `partially_mapped` | 7 hardware requirement records (`FB2-HW-TSR-000001..000004` in both profiles). **Hardware architecture, block diagrams and interface schematics are absent**, and the schematic sources are Altium `.SchDoc` files in the separate `foxBMS2_hw` repository whose anchors read `content_hash: unresolved`. **No FMEDA**: the four `safety_analysis` records are FMEA, FTA, dependent-failure and freedom-from-interference, all synthetic. |
| Part 6 — Software | **`partially_mapped`** | SW requirements, architecture and 26 justified coding-guideline deviations exist. **Software interface requirements absent.** The `as_is` design records were extracted from existing code, not designed. **Unit verification is only partial:** the upstream Unity/CMock suite was never executed by this corpus; the 15 host runs are the SIL harness over 313 CeeDling targets. No coverage run exists. |
| Part 7 — Production | **`partially_mapped`** | Six post-development records now exist — `FB2-REL-RLS-000001`, `FB2-PRD-EOL-000001` (six test stations), `FB2-PRD-CAL-000001` (six parameters), `FB2-OPS-MON-000001` (five signals, four incident classes), `FB2-SVC-SVC-000001` (five procedures), `FB2-DEC-DCM-000001` (five end-of-life assumptions). **All six carry `evidence_state.any_step_executed: false`** and each declares itself fictional and authorising nothing. Content real; performance zero. |
| Part 8 — Supporting processes | **`partially_mapped`** | Six supporting-process records exist (`FB2-SUP-QAP/CFM/PRB/CHC/SPL/RUS-000001`), each with definition, inputs, outputs, accountable role, acceptance criteria, a performed instance and communication records. **Two measured shortfalls:** the QA record's independence is stated and explicitly **not** achieved (risk RSK-003), and **five of the six processes these records describe are themselves `partially_mapped`** after the audit. **No supporting process is `mapped`.** |
| Part 9 — ASIL | **`partially_mapped`** | ASIL field values are recorded and traceable: `FB2-SAF-SGO-000001` `asil: ASIL_D`, `FB2-SAF-FSR-000004` `safety_allocation.asil: ASIL_B`. **No ASIL assignment methodology exists. No justification exists:** `FB2-SAF-SGO-000001` carries no `safety_allocation`, no `asil_allocation_scope` and no justification field at all, unlike the three SWR records which each declare `classification_kind: reconstructed_back_inference`. See §6. |
| Part 10 — Guidelines | `referenced` | methodology guidance. Unchanged. |
| Part 11 — Semiconductors | `not_applicable` | foxBMS is a BMS platform, not semiconductor development. `reference_decision: APP-ISO-11`. |
| Part 12 — Motorcycles | `not_applicable` | foxBMS targets automotive/industrial energy storage. `reference_decision: APP-ISO-12`. |

Part coverage across the 12 ISO parts: **0 `mapped`, 8 `partially_mapped`,
2 `referenced`, 2 `not_applicable`**. Before the audit it read 6 `mapped`,
2 `partially_mapped`, 2 `gap`, 2 `referenced`. Parts 11 and 12 are
`not_applicable` by recorded decision with rationale and `reference_decision`,
not by absence.

**The `standards_mapping` gate measures something different from all of this.**
It reports **33/38** — how many of the 38 applicable entries name an artefact
identifier that resolves (ASPICE 25/28, ISO 8/10). It does **not** assert that any
disposition is favourable. The old `44/44` counted keys in the inventory file
divided by itself; `16/38` replaced it on 2026-09-29; `33/38` is where it stands
after `CORR-COV-016`, because that pass rewrote each disposition to name the
record it rests on. **The number that reflects substance went the other way:**
4 ASPICE processes `mapped` instead of 12, and **0 ISO parts** instead of 6.

The three ASPICE entries the gate reports as unbacked are `SWE.3`, `HWE.3` and
`HWE.4` — the three processes **no artefact in the corpus references at all**.

## 3. ASPICE Process Inventory

32 process entries: **28 applicable**, **4 explicitly `not_applicable`**
(`MLE.1`–`MLE.4`, each with a rationale and a `reference_decision` of
`APP-MLE-ALL`).

### Disposition across the 28 applicable processes, before and after the audit

| Disposition | Before (2026-09-29) | **After (2026-10-01)** |
|---|---:|---:|
| `mapped` | 12 | **4** |
| `partially_mapped` | 10 | **21** |
| `gap` | 6 | **3** |

The **4** that remain `mapped`, with the evidence that was checked:

| Process | Backing record | Content that discharges the expectation |
|---|---|---|
| `MAN.3` Project Management | `FB2-MAN-PLN-000001` (`project_plan`, 24,465 B) | six-phase lifecycle model; eight-package WBS with named accountable roles and dated phases; schedule with critical path and per-package float; six gates with entry/exit criteria; resource assignment; five actual-vs-planned progress records; three communication records. All four expected families present. |
| `MAN.5` Risk Management | `FB2-MAN-RSK-000001` (`risk_register`) | eight entries across eight categories, each with ordinal-pair exposure on a stated scale, an owner, dated mitigation actions and a residual exposure with its argument; two residuals equal their inherent because no action was taken, recorded rather than presented as progress. All three expected families present. |
| `MAN.6` Measurement | `FB2-MAN-MSM-000001` (`measurement_plan`) | named population with exclusions and known bias; six collection rules with cadence and collector role; six metrics each with definition, unit, formula, baseline, target, control limit and action on breach; analysis method requiring every charted point to be an observation record; six observations with derivations. All three expected families present. |
| `PIM.3` Process Improvement | `FB2-PIM-IMP-000001`, `-000002` (`process_improvement`) | baseline, hypothesis with falsification condition, change made, effectiveness evaluation with arithmetic written out, counter-evidence, verdict. Verdicts: one `partially_effective`, one `insufficient_evidence`, **none effective** — the honest outcome, left as it is. All three expected families present. |

None of the four is an upgrade. Each was already `mapped` and was re-examined
rather than assumed.

### The 3 `gap` processes — no backing artefact of any kind

| Process | Status before | Evidence for the gap |
|---|---|---|
| **`SWE.3`** Software Detailed Design and Unit Construction | **`mapped`** | **ZERO artefacts reference SWE.3 in any `standards_mappings[].reference` string**, measured across the 106 distinct reference strings in the corpus. No detailed-design record (the 8 `design` records are `design_level: architecture` and name SWE.2); no source-code record (the 14 `implementation` and 26 `deviation` records name SWE.4); no unit-test specification (the 33 `test_measure` records name SWE.4/5/6). The superseded text read `mapped - source code inventoried; detailed design extracted; unit tests mapped` and named no artefact. |
| **`HWE.3`** Hardware Detailed Design | `partially_mapped` | **ZERO artefacts reference HWE.3**, same measurement. No schematics, PCB layout, BOM or component specification. The Altium sources live in `foxBMS2_hw` and are unverifiable from here. The superseded text read `partially_mapped - design packages referenced; detailed analysis limited by CAD format` and named no record. |
| `HWE.4` Hardware Integration and Test | `gap` | **ZERO artefacts reference HWE.4**, same measurement. No HW integration plan, test specification or test result in either profile. |

### The 21 `partially_mapped` processes, and which family of expectation is missing

Every `expected_artifacts` list below is **retained in full** in the coverage
plan. The list is not narrowed to match the status; the status is set to match
what the records actually contain.

| Process | Expected artifacts (retained) | Which family has no record |
|---|---|---|
| `SYS.1` | Stakeholder Needs, Use Cases, Operational Scenarios | **Operational Scenarios.** Needs exist but carry `is_a_real_elicitation = false` |
| `SYS.2` | System Requirements Specification, System Modes/States, Interface Requirements | **System Modes/States** and **Interface Requirements**; requirements back-inferred, not analysed |
| `SYS.3` | System Architecture, HW/SW Allocation, HSI Specification | **System Architecture.** Allocation exists only inside the two safety concepts |
| `SYS.4` | Integration Plan, Integration Test Specification, Integration Test Results | **All three.** `FB2-VER-EXE-000007` is `none`/`blocked` |
| `SYS.5` | Qualification Test Plan, Qualification Test Specification, Qualification Test Results | **All three.** Every synthetic execution is blocked or an unretained fixture |
| `SWE.1` | Software Requirements Specification, SW Interface Requirements | **SW Interface Requirements**; back-inference is not analysis |
| `SWE.2` | Software Architecture, Component Design, Interface Specifications | **Interface Specifications** — the `interfaces` field is a signal table, not a specification |
| `SWE.4` | SW Unit Verification Measures, Unit Test Specifications, Unit Test Results | **Unit Test Specifications**; and the only results are from the SIL host harness, not the upstream Unity/CMock suite |
| `SWE.5` | SW Integration Plan, SW Integration Test Specification, SW Integration Test Results | **All three.** `FB2-VER-EXE-000007` is `none`/`blocked` |
| `SWE.6` | SW Qualification Test Plan, SW Qualification Test Specification, SW Qualification Test Results | **All three.** `FB2-VER-EXE-000008` is `none`/`blocked` |
| `HWE.1` | Hardware Requirements Specification, HW Interface Requirements | **HW Interface Requirements** |
| `HWE.2` | Hardware Architecture, Block Diagrams, Interface Schematics | **All three**, and the schematics live in the external `foxBMS2_hw` repository |
| `VAL.1` | Validation Plan, Validation Test Specification, Validation Results | **Validation Plan** and **Validation Results** — all four executions are `none`/`blocked`; zero validations executed |
| `ACQ.4` | Supplier List, Monitoring Records, Supplier Assessments | **Supplier Assessments** — no supplier is under contract, no advisory source consulted |
| `SPL.2` | Release Plan, Release Notes, Release Checklist | **Release Notes**; nothing was released (`any_step_executed: false`) |
| `SUP.1` | QA Plan, Review Records, Audit Records | **Audit Records**; review independence stated and explicitly not achieved |
| `SUP.8` | CM Plan, Configuration Items, Baselines, Change Control | **Change Control** (deferred to `FB2-SUP-CHC-000001`) and **status accounting** (not automated; 326 of 489 links stale, none suspect) |
| `SUP.9` | Problem Reports, Resolution Records, Trend Analysis | **Trend Analysis** — the backing record says one intake cycle cannot produce one |
| `SUP.10` | Change Requests, Impact Analyses, Change Decisions | Families all present for a **fictional project only**; nothing raised against the real product |
| `SUP.11` | Traceability Matrix, Traceability Links, Coverage Reports | Families all present, but **link currency is not maintained** — 326 of 489 stale, none suspect |
| `REU.2` | Reuse Strategy, Reuse Assessments, Reuse Records | **Reuse Assessments** — none completed for any element |

Every `expected_artifacts` and `capability_attributes` list above is retained
unchanged. Only statuses were corrected. No expectation was deleted or narrowed,
and no artefact was fabricated to make a status true.

## 4. Corrections Applied to the Coverage Plan

**16** corrections recorded. `CORR-COV-001`…`015` are dated 2026-09-29;
`CORR-COV-016` is dated 2026-10-01 and is the substantive audit.

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
| **CORR-COV-016** | **every `mapped`/`partially_mapped` ASPICE process, and every `mapped`/`partially_mapped` ISO part** | **ASPICE 12/10/6, ISO 6 `mapped`** | **ASPICE 4/21/3, ISO 0 `mapped`** |

Two of the first fifteen (`CORR-COV-008` on `MAN.6`, `CORR-COV-011` on ISO Part 6) did not
land on the status the originally reported reality suggested. Verification
against disk found evidence on **both** sides of each claim, so both were
recorded as `partially_mapped` and the divergence is stated in the reason rather
than resolved in whichever direction is more convenient. In `MAN.6`'s case the
originally reported claim that "no metric definitions" exist was found to be
inaccurate as written: 26 records carry 100 `acceptance_criteria` entries, each
with a named measure, threshold and unit.

### `CORR-COV-016` — the substantive audit, and why the first pass missed `SWE.3`

`CORR-COV-001`…`015` read each disposition and asked whether the corpus
contradicted it. That question has a blind spot: a disposition can name a
process that **nothing in the corpus references at all**, and nothing
contradicts that, because there is nothing to check. `SWE.3` sat at `mapped` in
that state.

`CORR-COV-016` asks a different question. It extracts each artefact's own
`standards_mappings[].reference` strings — **183 of the 263 indexed records carry
such mappings, spanning 106 distinct reference strings; 80 carry none** — and
builds every process's backing set from that, then asks whether the backing
records carry the engineering that process defines. Three failure classes
followed, and each was demoted:

| Failure class | Example | Result |
|---|---|---|
| **(a) No artefact references the process at all** | `SWE.3` — 0 occurrences across 106 reference strings; same for `HWE.3` and `HWE.4` | → `gap` |
| **(b) A record exists with the right `artifact_type`, but one of the process's own `expected_artifacts` families has no record** | `ACQ.4` has no Supplier Assessment; `SUP.9` has no Trend Analysis; `SPL.2` has no Release Notes | → `partially_mapped` with the missing family named |
| **(c) A record exists and is substantial, but the activity the process names was not performed** | needs declared not elicited; requirements back-inferred not analysed; release documented not released; monitoring performed only on a fictional project | → `partially_mapped` with the non-performance named |

Several demotions cite the backing record's **own** text as evidence, which is
the strongest form available here because the record says it itself:

| Record | Its own words | Consequence |
|---|---|---|
| `FB2-SUP-PRB-000001` (SUP.9) | "The trend this process is supposed to produce cannot be produced from a corpus of one intake cycle." | no Trend Analysis → `partially_mapped` |
| `FB2-SUP-CFM-000001` (SUP.8) | "Currency of a link's recorded revisions is not automated. The process describes the control and does not claim the tooling enforces it." | status accounting not performed → `partially_mapped` |
| `FB2-SUP-QAP-000001` (SUP.1) | "every review record in it is an automated review produced by the same process that produced the artifacts, and no human reviewer exists" | no independent review, no audit → `partially_mapped` |
| `FB2-SUP-SPL-000001` (ACQ.4) | "It does not include a component inventory that has been checked against an advisory source, because no advisory source was consulted"; "No supplier is under contract" | no Supplier Assessment → `partially_mapped` |
| `FB2-SUP-RUS-000001` (REU.2) | "It does not complete a reuse assessment for any individual element"; independence "cannot hold" for the modified vendor drivers | no Reuse Assessment → `partially_mapped` |
| `FB2-REL-RLS-000001` (SPL.2, ISO Part 7) | `any_step_executed: false`; "The release it describes has not happened" | documented, not performed → `partially_mapped` |

**One measured figure carries most of the `SUP.11` demotion:** of the corpus's
489 links, **326 record an endpoint revision that differs from the endpoint
artefact's current revision, and all 489 carry `change_suspect_status: false`.**
The status accounting the process defines would have produced 326 findings and
produced none.

Nothing in `CORR-COV-016` raised a status. Every `expected_artifacts` list and
every `capability_attributes` list is retained byte-for-byte; no expectation was
deleted or narrowed; no artefact was fabricated to make a status true.

### One residual disagreement, left visible

`sources/feature-inventory.json` carries `summary.total_features: 20` while
holding 22 feature records. `corpus.py inventory` reports 22. The earlier
version of this report also listed a second residual — that `SUP.1`, `SUP.8`,
`SUP.9` and `SUP.10` read `mapped` while the supporting-processes view reported
no process-definition record. **That residual is closed**: six supporting-process
records now exist, and the four processes are `partially_mapped` with their
specific shortfalls named rather than sitting at `mapped`.

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

**Residual risk, closed since, by construction rather than by discipline:** at
revision 4 the document became **generated** at
`docs/artifacts/views/traceability/traceability-document.md` by
`corpus.py render`, and the repository-root file and the `reports/` copy were
reduced to content-free pointers. The hand-authored, out-of-reach condition no
longer holds for these paths. The residual that *does* remain is different and is
stated as such: the generated document is only as honest as the records it
derives from.

## 6. ASIL: What the Records Actually Say

`FB2-SAF-SGO-000001` carries `"asil": "ASIL_D"` and
`FB2-SAF-FSR-000004` carries `safety_allocation.asil: "ASIL_B"`. Those field
values are real and traceable to those records.

They are **not** an ASIL determination. An ASIL classification derives from
hazard analysis and risk assessment through a functional safety concept and a
technical safety concept. Since `CORR-COV-010` those two concept records **do**
exist (`FB2-SAF-FSC-000001`, `FB2-SAF-TSC-000001`), and the TSC does allocate
the safety goal across six architectural elements — but **two high-severity
findings stand open inside the concept phase**: the timing budget's arithmetic
does not close (`FB2-REV-FND-000025`) and the contactor reaction requirement
contradicts itself (`FB2-REV-FND-000024`). A concept whose own budget does not
close has not established an ASIL derivation.

Measured, as of 2026-10-01: **`FB2-SAF-SGO-000001` carries no
`safety_allocation`, no `asil_allocation_scope` and no justification field of any
kind.** The three software requirement records do carry an `asil_allocation_scope`
declaring `classification_kind: reconstructed_back_inference` and
`is_a_determination_for_the_real_product: false`; the safety goal does not carry
even that. ISO Part 9 is therefore recorded `partially_mapped` — the field values
exist, the methodology and the justification do not — and this report does not
present the values as evidence of ASIL capability.

## 7. What Structural Mapping Is Not

| This report establishes | This report does **not** establish |
|---|---|
| Every locked process and ISO part has an explicit, recorded disposition | That any disposition is favourable — **0 of 10** applicable ISO parts and **4 of 28** applicable ASPICE processes are `mapped`; **3** ASPICE processes have no backing artefact at all |
| 489 traceability links resolve with 0 dangling | That the linked artifacts are correct, only that they resolve — and that their endpoint revisions are current, which they are not for 326 of them |
| Clause references are recorded per record | That the clause text was ingested; it was not, and unverified references are marked as such |
| The corpus holds a HARA, safety goals, safety concepts, safety analyses and a measurement plan | ISO 26262 conformity, ASIL capability, or certification. It does **not** hold a safety plan: `FB2-MAN-SPL-000001` is a `design` record with six empty structural fields |
| ASPICE process references are recorded | Any ASPICE capability level, for any process |

No process in this corpus is assessed at any ASPICE capability level. The
`capability_dimension.level_1_performed` entry in the coverage plan has been
corrected to `not_met` and now carries an explicit note that it defines what
Level 1 would require rather than asserting that Level 1 was reached.
