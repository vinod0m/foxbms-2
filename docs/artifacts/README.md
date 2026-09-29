# foxBMS 2 Lifecycle Artifact Corpus

**Repository:** `/Users/vinod/Downloads/SoftwareDevLabs/foxbms-2`
**Commit:** `308028fb` (v1.11.0)
**Last session:** 2026-09-29
**Status:** `synthetic_ready_with_limitations`

---

## ⚠️ Critical Warning Labels

| Label | Meaning |
|-------|---------|
| **SYNTHETIC** | This is a synthetic development corpus, NOT a certification package. foxBMS, SoftwareDevLabs and this corpus are NOT ISO 26262 compliant and NOT ASIL certified. The corpus holds a **structural mapping** to clause references; that is not conformity. |
| **HUMAN_APPROVAL_PENDING** | All 153 indexed records have `human_approval_status: pending`. **No human has approved anything in this corpus.** AI reviews are automated; distinct agent sessions are NOT organisational independence or human confirmation. |
| **PRODUCTION_UNAUTHORIZED** | All 153 indexed records have `production_authorized: false` and `product_verification_credit: false`. No generated record grants production authority. |
| **NO_TARGET_HARDWARE_EVIDENCE** | 0 of 16 required target-hardware executions exist. A real macOS **host** run exists (94/136 tests passing) but macOS is **not an upstream-supported foxBMS platform** and a host run is **not** target-hardware evidence. It carries no verification credit. |
| **AS_IS vs SYNTHETIC_REFERENCE** | Two profiles: `as_is` (faithful reconstruction of pinned sources, 71 records) and `synthetic_reference` (hypothetical automotive BMS project, 82 records). Field-level provenance distinguishes `source_observed` (57), `derived` (36) and `synthetic` (60). |
| **NO NORMATIVE TEXT** | ISO 26262 and ASPICE PAM normative text NOT reproduced. Only metadata, methodology mappings and clause/process references are used, per rights policy. |
| **KNOWN_GOVERNANCE_CORRECTIONS** | 15 status claims in `governance/coverage-plan.json` were verified against disk and corrected on 2026-09-29 (`CORR-COV-001` … `CORR-COV-015`). Two landed on a *different* status than first reported, because verification found evidence on both sides; both record the divergence. Every `expected_artifacts` list was retained unchanged and no artifact was fabricated to make a status true. |
| **TRACEABILITY_DOCUMENT_IS_TOOL_OWNED** | `TRACEABILITY_DOCUMENT.md` at the **repository root** claimed ISO 26262 and IEC 61508 compliance evidence and an ASIL-D/ASIL-B capability, and carried a fabricated `Status: APPROVED` sign-off block. The repository owner **explicitly authorised amending it**, and it was corrected by hand on 2026-09-29 (finding `FB2-REV-FND-000022` revision 3). **The durable fix has since been implemented, at revision 4 of that finding:** the document is now **generated** at `views/traceability/traceability-document.md` by `corpus.py render` from the canonical records, carrying the same provenance header and guard-field contract as every other generated view, with every figure computed at render time. The repository-root path and `reports/TRACEABILITY_DOCUMENT.md` are now content-free pointers to it. The drift risk is closed by construction rather than by human discipline. |

---

## Current State at a Glance

All figures from a live tool run on 2026-09-29.

| Measure | Value |
|---|---|
| Acceptance suite | **PASSED** — 8 stages, 10 gate lines, 0 FAIL |
| Schema-validated artifact files | 177 |
| Unique `(profile, id)` records | 153 |
| Traceability links | **283, 0 dangling** |
| Validator findings / errors | 21 / **0** |
| Finding artifacts recorded | 22 |
| Coverage dimensions | 15 |
| Mutation scenarios | **20 / 20** detected |
| Change lifecycles | **3 / 3** complete |
| Toolchain self-tests | **11 PASS, 0 FAIL** |
| Source inventory | 612/612 files, 24 modules, 22 features, 23 variants |
| Export | 153 nodes, 283 edges |
| Review records / unique IDs covered | 12 / 82 of 123 (**67%**) |
| Target-hardware executions | **0 / 16** |
| Human approval | **0 / 153** — all pending |
| Production authorization | **0 / 153** — all false |

### Records by type and domain

| By type | | By domain | | By profile | |
|---|---|---|---|---|---|
| requirement | 26 | verification | 64 | `synthetic_reference` | 82 |
| deviation | 26 | software | 40 | `as_is` | 71 |
| execution | 25 | safety | 30 | | |
| finding | 22 | management | 7 | **By lifecycle** | |
| test_measure | 16 | hardware | 7 | draft | 73 |
| review | 12 | system | 3 | reviewed | 51 |
| design | 8 | supporting | 2 | baselined | 29 |
| scenario | 5 | | | | |
| safety_analysis | 4 | **Total** | **153** | | |
| change | 3 | | | | |
| hazard | 2 | | | | |
| safety_goal | 2 | | | | |
| safety_case | 1 | | | | |
| tara | 1 | | | | |

### The 15 coverage dimensions

| Dimension | Ratio | % |
|---|---|---|
| scope_accounting | 1/1 | 100% |
| artifact_population | 13/13 | 100% |
| standards_mapping | 44/44 | 100% |
| source_grounding | 76/154 | 49% |
| traceability_integrity | 283/283 | 100% |
| semantic_consistency_checks | 10/10 | 100% |
| automated_review_coverage | 82/123 | 67% |
| verification_planning | 16/7 | 229% (ratio, not a score) |
| actual_product_evidence | 0/16 | **0%** |
| synthetic_fixture_coverage | 82/43 | 191% (ratio, not a score) |
| negative_scenario_validation | 20/20 | 100% (measured: 20 scenarios executed, 20 detected by their own declared rule) |
| export_reproducibility | 1/1 | 100% |
| human_approval | 0/154 | **0%** |
| production_authorization | 0/154 | **0%** (correctly false) |
| final_status | `synthetic_ready_with_limitations` | — |

### Three different population counts — all correct

| Count | What it measures |
|---|---|
| **177** | schema-validated artifact *files* (154 corpus/review + 23 scenario) |
| **154** | artifact *files* carrying an `id` under `corpus/` + `reviews/` |
| **153** | unique `(profile, id)` records in the artifact index |
| **123** | unique artifact *IDs* across both profiles |

154 exceeds 153 because `FB2-REV-000001` exists in two files with identical
content; the index de-duplicates on `(profile, id)`. 153 exceeds 123 because 30
IDs exist in both profiles by design (profile isolation, not duplication).

---

## Directory Structure

```
docs/artifacts/
├── README.md                           # This file
├── _control/                           # Execution control artifacts
│   ├── foxbms_lifecycle_artifact_master_prompt.md
│   ├── execution-plan.md
│   ├── progress.json
│   ├── decisions.jsonl
│   ├── work-queue.json
│   └── resume.md
├── governance/                         # Corpus governance
│   ├── corpus-policy.json
│   ├── standards-lock.json             # ISO 26262:2018, ASPICE PAM 4.1
│   ├── scope-and-applicability.json
│   ├── coverage-plan.json              # 32 processes, 15 corrections
│   ├── role-and-review-policy.json
│   └── coverage-plan corrections array (CORR-COV-001..015)
├── sources/                            # Source registry + inventories
│   ├── source-registry.json            # 102 anchors, pinned to 308028fb
│   ├── source-inventory.json
│   ├── feature-inventory.json          # 22 feature records
│   ├── variant-matrix.json
│   └── permitted-extracts/
├── schemas/                            # JSON Schemas (draft 2020-12) — 15 files
│   ├── artifact-base.schema.json
│   ├── assumption.schema.json
│   ├── change.schema.json
│   ├── design.schema.json
│   ├── deviation.schema.json
│   ├── execution.schema.json
│   ├── finding.schema.json
│   ├── link.schema.json
│   ├── parameter.schema.json
│   ├── requirement.schema.json
│   ├── review.schema.json
│   ├── scenario.schema.json
│   ├── source_anchor.schema.json
│   ├── tara.schema.json
│   └── test_measure.schema.json
├── corpus/                             # Canonical engineering records
│   ├── shared/
│   ├── as_is/                          # 71 records
│   │   ├── hardware/  (3)
│   │   ├── reviews/records/
│   │   ├── safety/    (7)
│   │   ├── software/  (33, incl. 26 deviation records)
│   │   ├── system/    (NOTE-gap.md only)
│   │   ├── management/(NOTE-gap.md only)
│   │   └── verification/ (27, incl. 14 executions)
│   ├── synthetic_reference/            # 82 records
│   │   ├── hardware/  (4)
│   │   ├── management/(7: 3 change, scope, safety plan, finding, review)
│   │   ├── safety/    (23, incl. TARA + 5 SEC requirements)
│   │   ├── shared/    (parameter + assumption registries)
│   │   ├── software/  (7)
│   │   ├── system/    (3, incl. HSI authority)
│   │   ├── traceability/link-registry/
│   │   └── verification/ (37)
│   └── scenarios/
│       ├── change-lifecycles/          # 3 scenarios
│       └── mutations/                  # 20 scenarios
├── traceability/                       # Canonical typed links — 283 links
│   ├── link-registry/
│   │   ├── as_is/                      # 111 links
│   │   └── synthetic_reference/        # 172 links
│   ├── rules/
│   └── queries/
├── reviews/                            # Review records and findings
│   ├── records/                        # 13 files → 12 unique review records
│   ├── findings/                       # 22 finding artifacts
│   └── closure/
├── views/                              # Generated human-readable views — 11 files
│   ├── management/management.md
│   ├── concept-and-safety/concept-and-safety.md
│   ├── system/system.md
│   ├── hardware/hardware.md
│   ├── software/software.md
│   ├── verification-validation/verification-validation.md
│   ├── production-operation-service/lifecycle-continuation.md
│   ├── supporting-processes/supporting-processes.md
│   ├── standards-mapping/standards-mapping.md
│   ├── traceability/traceability.md
│   └── traceability/traceability-document.md   # the canonical traceability doc
├── exports/                            # Portable exports — 4 files
│   ├── manifest.json                   # content hashes
│   ├── nodes.jsonl                     # 153 nodes
│   ├── edges.jsonl                     # 283 edges
│   └── trace-matrix.csv
├── evidence/
│   ├── actual-runs/
│   └── synthetic-fixtures/
├── spec-documents/                     # 10 generated spec documents
├── tools/                              # Validation tooling
│   ├── corpus.py                       # main CLI
│   ├── render_spec_documents.py        # spec-document generator
│   └── repo_model.py
├── tests/                              # Corpus toolchain tests
├── reports/                            # Reports (see table below)
├── diagrams/                           # Interactive diagrams (archify)
└── .work/                              # Temporary (gitignored)
    └── verification-env/               # macOS host-run environment + RUNBOOK.md
```

---

## Two Profiles

### `as_is` — Faithful Reconstruction
- **What it is:** reconstruction of what the pinned foxBMS sources (commit `308028fb`) demonstrate
- **Content:** observed behaviour, existing artifacts and tests, justified inferences, evidence gaps, contradictions, proposed changes
- **Provenance:** `source_observed` (direct from source), `derived` (logical inference)
- **Does NOT:** rewrite inconvenient facts, assert undocumented stakeholder intent, or back-infer requirements as historical specifications
- **71 records.** Note `as_is/system/` and `as_is/management/` hold only
  `NOTE-gap.md` files recording searches that found nothing.

### `synthetic_reference` — Hypothetical Automotive BMS Project
- **What it is:** a complete, coherent hypothetical automotive BMS project grounded in foxBMS
- **Content:** fictional item, vehicle context, stakeholders, lifecycle, parameter set. Reuses source-grounded behaviour where justified; fills gaps with labelled synthetic content
- **Provenance:** `synthetic`, `source_observed`, `derived` (field-level)
- **82 records.** Key additions over `as_is`: independent HW monitor
  (`FB2-SAF-FSR-000004`), timing budgets, parameter registry, assumption
  registry, safety analyses, safety case, TARA, five security requirements,
  change lifecycles, mutation scenarios

**Both profiles share:** source registry, schemas, link semantics, ID scheme,
variant matrix, coverage plan.

---

## ID Scheme

```
FB2-<DOMAIN>-<TYPE>-<NNNNNN>
```

| Domain | Types |
|--------|-------|
| SYS (System) | REQ, DSN, TMS, EXE, REV, ASM, PRM, LNK, CHG, FND, SCN |
| HW (Hardware) | REQ, DSN, TMS, EXE, REV, ASM, PRM, LNK, CHG, FND, SCN |
| SW (Software) | REQ, DSN, TMS, EXE, REV, ASM, PRM, LNK, CHG, FND, SCN |
| SAF (Safety) | HAZ, SGO, FSR, SEC, TAR, ANL, SCS, TSR, SSM, TMS, EXE, REV, ASM, PRM, LNK, CHG, FND, SCN |
| VER (Verification) | TMS, EXE, REV, FND, ASM, PRM, LNK, CHG, SCN |
| REV (Review) | FND |
| MAN (Management) | SCO, SPL, CHG, REV, PRM, LNK, CHG, FND, SCN |
| CFG (Configuration) | PRM, LNK, CHG, FND, SCN |

**Rules:** never renumber established IDs; exact revisions on baseline-controlled
links; supersession/deletion/tombstones defined in schemas.

---

## Link Semantics

Ten relation types are in use across 283 links.

| Relation | Count | Direction |
|----------|------:|-----------|
| `reviewed_by` | 167 | artifact → review record |
| `verifies` | 32 | test measure → requirement (**test measure is the source**) |
| `result_of` | 16 | execution → the measure it resulted from |
| `supports` | 16 | analysis / TARA → requirement or goal |
| `changes` | 16 | change record → artifact it revises |
| `refines` | 13 | FSR → safety goal; scenario → parent scenario |
| `allocated_to` | 13 | HW/SW requirement → FSR it satisfies |
| `implements` | 6 | design → requirement it implements |
| `mitigates` | 2 | safety goal → hazard |
| `validates` | 2 | test measure → requirement (validation direction) |

**Every link has:** ID, endpoints with revisions, relation type,
profile/scenario/variant context, rationale, provenance, review state, change
suspect status.

> **Direction convention warning.** The test measure is the **source** and the
> requirement is the **target**, so a verified requirement appears as a link
> target, never as a source. The validator's rule inspects only the source side,
> so it fires on correctly verified requirements. See `FB2-REV-FND-000001`.
> Examine verification links on **both** sides before concluding a requirement
> is unverified.

---

## Evidence Classification

| Execution kind | Description | Present? |
|----------------|-------------|----------|
| `none` | No execution planned/performed | 1 record |
| `actual_host_run` | Executed on a development host — **not target hardware** | 13 records |
| `actual_simulation_run` | Simulator with captured logs | — |
| `synthetic_fixture` | Synthetic test data for corpus validation | part of the 12 |
| **target hardware** | — | **no such member exists in the enum** |

| Outcome | Description | `as_is` count |
|---------|-------------|--------------:|
| `pass` | All acceptance criteria met | 4 |
| `fail` | Criteria not met | 9 |
| `inconclusive` | Incomplete/ambiguous | — |
| `not_run` | Planned but not executed | — |
| `blocked` | Cannot execute (missing HW/tools) | 1 |

**Orthogonal:** execution kind ≠ outcome. Planning is not execution.
Fabricated numbers = `synthetic_fixture`. `actual_product_evidence` is **0/16**
because `execution_kind` has no target-hardware member, so none can be claimed
without fabricating one.

---

## The macOS Host Run

A real test-suite run was performed on the build host on 2026-09-29.

| Measure | Value |
|---|---|
| Platform | Darwin arm64, kernel 27.0.0 |
| Toolchain | ruby 4.0.7 +PRISM [arm64-darwin27] |
| Tests in scope | 136 |
| **Passed** | **94** |
| **Failed** | **5** |
| Build failures | 37 |
| Assertions | 332 tested, 323 passed, 8 failed |
| Blocked on HALCoGen | **177 of 313** repository tests, across **34 distinct `HL_*.h` headers** |

**macOS is not an upstream-supported foxBMS platform.** This is a host run and
carries no target-hardware verification credit.

**The 5 failures are a real defect in the product's test setup, not a harness
artefact.** `src/app/engine/database/database.h:209` declares the database
access API with untyped `void *` parameters; the shipped Ceedling config sets
`:cmock: :when_ptr: :compare_data`, so CMock cannot learn the pointed-to size
and emits a pointer-**identity** check. The tests pass a pointer to their own
`static` copy while the code under test passes a different one. This is
compiler- and platform-independent, so the same five tests are expected to fail
under GNU gcc on Linux. **No result was adjusted to make a test pass.**

Runbook: `docs/artifacts/.work/verification-env/RUNBOOK.md`.

---

## How to Run Checks

```bash
# Full acceptance suite (8 stages) — expect: Acceptance suite: PASSED
python3 docs/artifacts/tools/corpus.py check

# Schema + link + semantic validation — expect: errors=0
python3 docs/artifacts/tools/corpus.py validate

# The 15 coverage dimensions
python3 docs/artifacts/tools/corpus.py coverage

# Toolchain self-tests — expect: 22 PASS, 0 FAIL
python3 docs/artifacts/tools/corpus.py selftest

# Source/feature/variant inventory — expect: 612/612, 24 modules, 22 features, 23 variants
python3 docs/artifacts/tools/corpus.py inventory

# Mutation + change-lifecycle scenarios — expect: 20/20 and 3/3.
# Each mutation line names the detector rule it declares; a scenario passes only when
# THAT rule fires, never on a neighbouring finding.
python3 docs/artifacts/tools/corpus.py scenario-test

# Traceability query
python3 docs/artifacts/tools/corpus.py trace FB2-SAF-HAZ-000001

# Impact analysis
python3 docs/artifacts/tools/corpus.py impact FB2-PRM-000001

# Spec-document integrity and determinism — expect: INTEGRITY CHECK PASSED
python3 docs/artifacts/tools/render_spec_documents.py --check
```

## How to Regenerate Derived Outputs

Everything in `views/`, `exports/`, `spec-documents/` and the machine-generated
report JSONs is derived and regenerable. The canonical records are the JSON files
under `corpus/`, `reviews/`, `traceability/` and `scenarios/`.

```bash
# Regenerate all 11 views, including the canonical traceability document
# (~15 s; dominated by Mermaid validation)
python3 docs/artifacts/tools/corpus.py render

# Regenerate exports
python3 docs/artifacts/tools/corpus.py export

# Regenerate machine-verified coverage JSON
python3 docs/artifacts/tools/corpus.py coverage

# Regenerate scenario-validation JSON
python3 docs/artifacts/tools/corpus.py scenario-test

# Regenerate the 10 spec documents
python3 docs/artifacts/tools/render_spec_documents.py
```

**Determinism:** rendering twice produces byte-identical output apart from the
`Generated:` line in each view's preamble and the `generated_at` field in
`exports/manifest.json`. Verified by `diff -r -I '^Generated:'`. No other line is
excluded.

**Anti-drift:** generated prose reads `governance/coverage-plan.json` **live at
render time** rather than quoting a frozen literal, so correcting the plan
corrects the views. This was verified empirically by temporarily flipping a
disposition and observing the view follow it.

The `.md` reports in `reports/` are hand-authored but every number in them is
taken from a live tool run, and each report states which command produced which
figure.

---

## How to Resume

Corpus state is checkpointed in `_control/`.

```bash
cat docs/artifacts/_control/progress.json    # machine-readable state
cat docs/artifacts/_control/resume.md        # human-readable checkpoint
cat docs/artifacts/_control/work-queue.json  # 96 work-queue entries, all completed
```

**Resumability guarantees:** no recreated or renumbered artifacts; exact
completed/remaining IDs tracked; environment state preserved in `.work/`;
source baseline validated on resume (commit `308028fb`).

**Never run `git checkout`, `git restore`, `git stash`, `git reset` or
`git clean` on this repository while corpus work is in progress.** Two agents in
this series lost uncommitted work that way, one of them 26 source anchors. Use
`git diff` and `git show HEAD:<path>` to read history instead.

---

## How Changes Invalidate Links/Reviews/Evidence

| Change type | Invalidated |
|-------------|-------------|
| Content change (artifact) | outgoing/incoming links suspect, reviews stale, evidence stale |
| Link change | endpoint reviews suspect |
| Parameter change | all dependent artifacts suspect (`constrained_by`) |
| Assumption invalidation | all `affected_scope` artifacts suspect |
| Baseline change | new baseline ID; `supersedes` links created |

**Process:** changes go through the change lifecycle (3 demos in
`scenarios/change-lifecycles/`). Impact analysis → decision → new revisions →
suspect links → required updates → reverification → clean post-change baseline.

---

## Standards Baseline

| Standard | Version | Status |
|----------|---------|--------|
| ISO 26262 | 2018 (Parts 1–12) | Locked in `governance/standards-lock.json` |
| ASPICE PAM | 4.1 | Locked in `governance/standards-lock.json` |

**IEC 61508 is not locked and no corpus record was authored against it.** The
pinned source does list it as a candidate standard (`docs/general/safety/safety.rst:60`)
and cite IEC 61508-3:2010 in `docs/references.bib`, so the standard is a
legitimate consideration for the product; the corpus simply never engaged it.

**Coverage:** 32 ASPICE processes (28 applicable, 4 `not_applicable`), 12 ISO
parts. The acceptance gate verifies 44/44 mapping items — meaning every item has
an explicit disposition, **not** that the dispositions are favourable:

- ASPICE: 12 `mapped`, 10 `partially_mapped`, **6 `gap`** across the 28 applicable
- ISO parts: 2 `mapped`, 4 `partially_mapped`, **2 `gap`**, 2 `referenced`, 2 `not_applicable`

**No process in this corpus is assessed at any ASPICE capability level.**

---

## Known Gaps and Defects

### Governance gaps (verified against disk, corrected 2026-09-29)

| Process / part | Status | What is missing |
|---|---|---|
| `SYS.1` Requirements Elicitation | `gap` | no stakeholder-needs, use-case or operational-scenario record |
| `SYS.2` System Requirements Analysis | `gap` | no system requirements record in either profile |
| `HWE.4` Hardware Integration and Test | `gap` | no `as_is` HW test record |
| `MAN.3` Project Management | `gap` | only a scope statement; no plan, schedule, resource plan or progress report |
| `MAN.5` Risk Management | `gap` | only a TARA threat table; no project risk register |
| `MAN.6` Measurement | `partially_mapped` | 100 acceptance criteria exist on 26 records, but no measurement plan |
| `PIM.3` Process Improvement | `gap` | no improvement proposal, record or effectiveness evaluation |
| ISO Part 3 Concept | `partially_mapped` | no functional safety concept, no technical safety concept |
| ISO Part 6 Software | `partially_mapped` | unit verification only partially mapped |
| ISO Part 7 Production | `gap` | no production, operation, service or decommissioning record |
| ISO Part 8 Supporting | `gap` | no supporting-domain process-definition record |

### Reported defects

| Defect | Severity | Disposition |
|---|---|---|
| `TRACEABILITY_DOCUMENT.md` at repository root claimed ISO 26262 + IEC 61508 compliance, an ASIL-D/ASIL-B capability, and carried a fabricated human-approval sign-off; outside the write boundary | high | **accepted** — `FB2-REV-FND-000022` rev 4; corrected under explicit owner authorisation, then made **tool-owned**: the document is generated at `views/traceability/traceability-document.md` and the root path is a content-free pointer, so the drift risk is closed by construction |
| `FB2-REV-000001` exists in two files with identical content | medium | accepted, reported; index de-duplicates, validator does not flag it |
| Redundant link-registry copy under `corpus/` (51 of 172 links) | low | accepted, reported; de-duplicated by the tool |
| `feature-inventory.json` `summary.total_features` says 20, holds 22 | low | accepted, reported; the tool counts records and reports 22 |
| 7 FSRs carry no `fault_reaction` field | medium | 7 findings open; schema change needed |
| 5 security requirements have no verification link in either direction | medium | 5 findings open; real gap |
| ASIL assignment with no justification | medium | 2 findings open; needs an engineering determination |
| `verifies`-direction rule fires on correctly verified requirements | medium | not resolved by design; convention decision owed |

---

## Reports

| Report | Description |
|--------|-------------|
| `reports/final-acceptance-report.md` + `.json` | All gates, 15 dimensions, 5 walkthroughs, final status |
| `reports/coverage-report.md` + `.json` | Population, three-count explanation, census, gaps |
| `reports/standards-mapping-report.md` | ISO part and ASPICE process dispositions, 15 corrections |
| `reports/traceability-report.md` | Link statistics, direction convention, worked chains |
| `reports/consistency-report.md` | 10 check categories, 4 finding families, structure defects |
| `reports/review-summary.md` | Review coverage, types, findings, limitations |
| `reports/source-vs-synthetic-gap-report.md` | `as_is` vs `synthetic_reference` gaps by category |
| `reports/verification-evidence-report.md` | The real macOS host run, 5 failures root-caused, 177 blocked |
| `reports/scenario-validation-report.md` + `.json` | 20 mutations, 3 change lifecycles, baseline-firing detectors |
| `reports/reproducibility-report.md` | Determinism measured by rendering twice and diffing |
| `reports/TRACEABILITY_DOCUMENT.md` + `.docx` | **Pointer** to the generated traceability document, plus a pandoc conversion of that pointer. Neither carries engineering content |
| `reports/traceability-chain-map.md` | Cross-domain chain map |
| `reports/aspice-process-map.md` | ASPICE process-to-artifact map |
| `reports/aspice-mock-audit-report.md` | ASPICE PAM 4.1 mock audit, per-process verdicts |

> There is exactly **one** traceability document with engineering content,
> and it is generated: `views/traceability/traceability-document.md`, emitted by
> `python3 docs/artifacts/tools/corpus.py render` from the canonical records
> with the same provenance header and guard-field contract as every other
> generated view. `TRACEABILITY_DOCUMENT.md` at the **repository root** and
> `reports/TRACEABILITY_DOCUMENT.md` are short pointers to it and contain no
> engineering content. The root file was the one that carried the unsupported
> conformity and ASIL claim recorded as `FB2-REV-FND-000022`; it was corrected
> by hand on 2026-09-29 under explicit owner authorisation and then made
> tool-owned, so that condition cannot recur.

---

## Support & Sponsorship

If this corpus saved you time, consider supporting the graphify project that
enabled the knowledge graph foundation:

**Graphify Sponsors:** https://github.com/sponsors/safishamsi

---

*All artifacts under `docs/artifacts/` preserve the foxBMS existing documentation
structure. No foxBMS source code, hardware files or tests were modified. Writes
are confined to `docs/artifacts/`; `src/`, `tests/`, `conf/`, `tools/`, `cli/`,
`gui/`, `hardware/`, `wscript`, `fox.py`, `fox.sh` and `.gitignore` are
untouched.*
