# foxBMS 2 Lifecycle Artifact Corpus

**Repository:** `/Users/vinod/Downloads/SoftwareDevLabs/foxbms-2`  
**Commit:** `308028fb` (v1.11.0, 2026-04-20)  
**Generated:** 2026-09-08  
**Runtime:** OpenCode with nvidia/nemotron-3-ultra-550b-a55b  
**Status:** `synthetic_ready_with_limitations`

---

## ⚠️ Critical Warning Labels

| Label | Meaning |
|-------|---------|
| **SYNTHETIC** | This is a synthetic development corpus, NOT a certification package. foxBMS, Fraunhofer, SoftwareDevLabs are NOT ISO 26262 compliant or ASIL certified. |
| **HUMAN_APPROVAL_PENDING** | All artifacts have `human_approval_status: pending`. AI reviews are automated - distinct agent sessions are NOT organizational independence or human confirmation. |
| **PRODUCTION_UNAUTHORIZED** | All artifacts have `production_authorized: false` and `product_verification_credit: false`. No generated record grants production authority. |
| **AS_IS vs SYNTHETIC_REFERENCE** | Two profiles: `as_is` (faithful reconstruction of pinned sources) and `synthetic_reference` (hypothetical automotive BMS project grounded in foxBMS). Field-level provenance distinguishes `source_observed`, `derived`, `synthetic`. |
| **NO NORMATIVE TEXT** | ISO 26262 and ASPICE PAM normative text NOT reproduced. Only metadata, methodology mappings, and clause/process references used per rights policy. |

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
│   ├── standards-lock.json
│   ├── scope-and-applicability.json
│   ├── coverage-plan.json
│   ├── source-inventory.json
│   ├── feature-inventory.json
│   ├── variant-matrix.json
│   └── role-and-review-policy.json
├── schemas/                            # JSON Schemas (draft 2020-12)
│   ├── artifact-base.schema.json
│   ├── requirement.schema.json
│   ├── design.schema.json
│   ├── test_measure.schema.json
│   ├── execution.schema.json
│   ├── review.schema.json
│   ├── assumption.schema.json
│   ├── parameter.schema.json
│   ├── link.schema.json
│   ├── source_anchor.schema.json
│   ├── change.schema.json
│   ├── finding.schema.json
│   └── scenario.schema.json
├── sources/                            # Source registry
│   ├── source-registry.json
│   └── permitted-extracts/
├── corpus/                             # Canonical engineering records
│   ├── shared/                         # Authoritative shared identities
│   ├── as_is/                          # Observed/reconstructed records
│   │   ├── safety/
│   │   ├── system/
│   │   ├── hardware/
│   │   ├── software/
│   │   └── verification/
│   └── synthetic_reference/            # Hypothetical engineering records
│       ├── shared/
│       ├── safety/
│       ├── system/
│       ├── hardware/
│       ├── software/
│       ├── verification/
│       └── management/
├── traceability/                       # Canonical typed links
│   ├── link-registry/
│   │   ├── as_is/
│   │   └── synthetic_reference/
│   ├── rules/
│   └── queries/
├── views/                              # Derived human-readable work products
│   ├── management/
│   ├── concept-and-safety/
│   ├── system/
│   ├── hardware/
│   ├── software/
│   ├── verification-validation/
│   ├── production-operation-service/
│   ├── supporting-processes/
│   ├── standards-mapping/
│   └── traceability/
├── evidence/                           # Execution evidence
│   ├── actual-runs/
│   └── synthetic-fixtures/
├── reviews/                            # Review records
│   ├── records/
│   ├── findings/
│   └── closure/
├── scenarios/                          # Mutation & change scenarios
│   ├── mutations/
│   ├── change-lifecycles/
│   └── evaluator-only/
├── exports/                            # Portable exports
├── tools/                              # Validation tooling
├── tests/                              # Corpus toolchain tests
├── reports/                            # Final reports
│   ├── coverage-report.md + .json
│   ├── standards-mapping-report.md
│   ├── traceability-report.md
│   ├── consistency-report.md
│   ├── review-summary.md
│   ├── source-vs-synthetic-gap-report.md
│   ├── verification-evidence-report.md
│   ├── scenario-validation-report.md + .json
│   ├── reproducibility-report.md
│   ├── final-acceptance-report.md + .json
│   ├── TRACEABILITY_DOCUMENT.md + .docx (end-to-end walkthrough)
│   ├── traceability-chain-map.md (system↔software↔hardware↔system)
│   ├── aspice-process-map.md (SYS.1-5, SWE.1-6, artifact-level chains)
│   └── aspice-mock-audit-report.md (PAM 4.1 per-process verdicts)
└── diagrams/                           # Interactive diagrams (archify)
    ├── foxbms-architecture.json + .html
    ├── foxbms-dataflow.json + .html
    ├── foxbms-lifecycle.json + .html
    ├── foxbms-sequence.json + .html
    └── foxbms-workflow.json + .html
└── .work/                              # Temporary (gitignored)
```

---

## Two Profiles

### `as_is` — Faithful Reconstruction
- **What it is:** Reconstruction of what the pinned foxBMS sources (commit 308028fb) demonstrate
- **Content:** Observed behavior, existing artifacts/tests, justified inferences, evidence gaps, contradictions, proposed changes
- **Provenance:** `source_observed` (direct from source), `derived` (logical inference)
- **Does NOT:** Rewrite inconvenient facts, assert undocumented stakeholder intent, back-infer requirements as historical specifications

### `synthetic_reference` — Hypothetical Automotive BMS Project
- **What it is:** Complete, coherent hypothetical automotive BMS development project grounded in foxBMS
- **Content:** Fictional item, vehicle context, stakeholders, lifecycle, parameter set. Reuses source-grounded behavior where justified. Fills gaps with labeled synthetic content.
- **Provenance:** `source_observed`, `derived`, `synthetic` (field-level)
- **Key additions over as_is:** Independent HW monitor (FSR-0004), timing budgets, parameter registry, assumption registry, change lifecycles, mutation scenarios

**Both profiles share:** Source registry, schemas, link semantics, ID scheme, variant matrix, coverage plan.

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
| SAF (Safety) | HAZ, SGO, FSR, TSR, SSM, TMS, EXE, REV, ASM, PRM, LNK, CHG, FND, SCN |
| VER (Verification) | TMS, EXE, REV, ASM, PRM, LNK, CHG, FND, SCN |
| MAN (Management) | SCO, SPL, PRM, LNK, CHG, FND, SCN |
| CFG (Configuration) | PRM, LNK, CHG, FND, SCN |

**Rules:** Never renumber established IDs. Exact revisions on baseline-controlled links. Supersession/deletion/tombstones defined in schemas.

---

## Link Semantics (17 Types)

| Relation | Direction | Domain → Range |
|----------|-----------|----------------|
| `refines` | lower req → parent req/goal | requirement → requirement |
| `allocated_to` | req → arch/design | requirement → design |
| `implements` | impl → design/req | implementation → design/requirement |
| `verifies` | test → req/design | test_measure → requirement/design |
| `validates` | validation → stakeholder need | test_measure → stakeholder_need |
| `result_of` | execution → test | execution → test_measure |
| `supports` | evidence → claim | evidence → claim |
| `mitigates` | mechanism → fault/hazard | safety_mechanism → fault/hazard/failure_mode |
| `specified_by` | element → spec | interface/element → specification |
| `consumes` | element → signal | element → signal |
| `produces` | element → signal | element → signal |
| `depends_on` | dependent → prerequisite | artifact → artifact |
| `constrained_by` | artifact → param/assumption | artifact → parameter/assumption |
| `reviewed_by` | artifact → review | artifact → review |
| `changes` | change → affected | change → artifact |
| `supersedes` | new rev → prior rev | artifact → artifact |

**Every link has:** ID, endpoints with revisions, relation type, profile/scenario/variant context, rationale, provenance, review state, change suspect status.

---

## Evidence Classification

| Execution Kind | Description |
|----------------|-------------|
| `none` | No execution planned/performed |
| `actual_host_run` | Executed on dev host (x86_64 Linux) |
| `actual_simulation_run` | Simulator with captured logs |
| `synthetic_fixture` | Synthetic test data for corpus validation |

| Outcome | Description |
|---------|-------------|
| `pass` | All acceptance criteria met |
| `fail` | Criteria not met |
| `inconclusive` | Incomplete/ambiguous |
| `not_run` | Planned but not executed |
| `blocked` | Cannot execute (missing HW/tools) |

**Orthogonal:** Execution kind ≠ Outcome. Planning is not execution. Fabricated numbers = `synthetic_fixture`.

---

## How to Explore/Query

### By Artifact ID
```bash
# Find artifact
find docs/artifacts/corpus -name "FB2-SAF-FSR-000001*"
```

### By Traceability Path
```bash
# Vertical chain: Hazard → Safety Goal → FSR → TSR/SWR → Design → Test → Execution → Review
cat docs/artifacts/traceability/link-registry/synthetic_reference/links-cell-voltage.json | jq '.links[] | select(.source_id=="FB2-SAF-HAZ-000001")'
```

### By Lateral Query
```bash
# HW/SW interface for cell voltage
cat docs/artifacts/traceability/link-registry/synthetic_reference/links-cell-voltage.json | jq '.links[] | select(.relation_type=="specified_by")'
```

### By Review
```bash
# All findings for vertical slice
cat docs/artifacts/reviews/records/review-vertical-slice.json | jq '.findings[]'
```

---

## How to Run Checks

### Schema Validation
```bash
python3 -m jsonschema -i docs/artifacts/corpus/synthetic_reference/safety/fsr-cell-voltage.json docs/artifacts/schemas/requirement.schema.json
```

### Full Corpus Validation
```bash
python3 docs/artifacts/tools/corpus.py validate
```

### Coverage Report
```bash
python3 docs/artifacts/tools/corpus.py coverage
```

### Traceability Query
```bash
python3 docs/artifacts/tools/corpus.py trace FB2-SAF-HAZ-000001
```

### Impact Analysis
```bash
python3 docs/artifacts/tools/corpus.py impact FB2-PRM-000001
```

### Export
```bash
python3 docs/artifacts/tools/corpus.py export --format jsonl --output exports/
```

---

## How to Regenerate/Export

The corpus is generated from canonical JSON records in `corpus/`. Views in `views/`, exports in `exports/`, and reports in `reports/` are derived and can be regenerated:

```bash
# Regenerate all views from canonical data
python3 docs/artifacts/tools/corpus.py render

# Regenerate all exports
python3 docs/artifacts/tools/corpus.py export

# Regenerate machine-verified coverage JSON
python3 docs/artifacts/tools/corpus.py coverage

# Regenerate the 10 spec documents (Markdown + DOCX)
python3 docs/artifacts/tools/render_spec_documents.py

# Markdown reports are hand-maintained but data-verified against the
# canonical corpus (validate/check/scenario-test outputs above)
```

**Invariants:**
- Unchanged canonical baseline → unchanged exports/digests (apart from run metadata)
- Content hashes in `sources/source-registry.json` provide integrity checking
- Run metadata separated from engineering payloads

---

## How to Resume

If interrupted, the corpus state is saved in `_control/`:

```bash
# Check progress
cat docs/artifacts/_control/progress.json

# See work queue
cat docs/artifacts/_control/work-queue.json

# Resume from last checkpoint
cat docs/artifacts/_control/resume.md
```

**Resumability guarantees:**
- No recreated/renumbered artifacts
- Exact completed/remaining IDs tracked
- Environment state preserved in `.work/`
- Source baseline validated on resume (commit 308028fb)

---

## How Changes Invalidate Links/Reviews/Evidence

| Change Type | Invalidated |
|-------------|-------------|
| Content change (artifact) | Outgoing/incoming links suspect, reviews stale, evidence stale |
| Link change | Endpoint reviews suspect |
| Parameter change | All dependent artifacts suspect (constrained_by links) |
| Assumption invalidation | All affected_scope artifacts suspect |
| Baseline change | New baseline ID; supersedes links created |

**Process:** Changes go through change lifecycle (3 demos in `scenarios/change-lifecycles/`). Impact analysis → Decision → New revisions → Suspect links → Required updates → Reverification → Clean post-change baseline.

---

## Standards Baseline

| Standard | Version | Status |
|----------|---------|--------|
| ISO 26262 | 2018 (Parts 1-12) | Locked in `governance/standards-lock.json` |
| ASPICE PAM | 4.1 (VDA QMC English 2026-08-24) | Locked in `governance/standards-lock.json` |

**Coverage:** 32 ASPICE processes (28 applicable, 4 not_applicable), 12 ISO parts (see `governance/coverage-plan.json`); acceptance gate verifies 44/44 mapping items.

---

## Final Reports

| Report | Description |
|--------|-------------|
| `reports/coverage-report.md` | Scope, artifact, feature, process coverage |
| `reports/standards-mapping-report.md` | ISO/ASPICE clause/process mapping |
| `reports/traceability-report.md` | Vertical/lateral chains, change impact |
| `reports/consistency-report.md` | 10 semantic consistency check categories |
| `reports/review-summary.md` | Review coverage, findings, limitations |
| `reports/source-vs-synthetic-gap-report.md` | as_is vs synthetic_reference gaps |
| `reports/verification-evidence-report.md` | Execution kinds, outcomes, oracle basis |
| `reports/scenario-validation-report.md` | Mutation scenarios, change lifecycles |
| `reports/reproducibility-report.md` | Round-trip, determinism, tool versions |
| `reports/final-acceptance-report.md` | All gates, final status, walkthroughs |
| `reports/TRACEABILITY_DOCUMENT.md` (+ `.docx`) | End-to-end traceability, completeness review |
| `reports/traceability-chain-map.md` | Cross-domain chain map (system↔software↔hardware↔system) |
| `reports/aspice-process-map.md` | ASPICE process-to-artifact map (SYS.1-5, SWE.1-6, artifact-level chains) |
| `reports/aspice-mock-audit-report.md` | ASPICE PAM 4.1 mock audit (per-process work-product verdicts) |

---

## Support & Sponsorship

If this corpus saved you time, consider supporting the graphify project that enabled the knowledge graph foundation:

**Graphify Sponsors:** https://github.com/sponsors/safishamsi

---

*Generated by OpenCode orchestration following the foxBMS 2 Lifecycle Artifact Corpus Master Prompt. All artifacts under `docs/artifacts/` preserve foxBMS existing documentation structure. No foxBMS source code, hardware files, or tests were modified.*
