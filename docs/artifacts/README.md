# foxBMS 2 Lifecycle Artifact Corpus

**Repository:** `/Users/vinod/Downloads/SoftwareDevLabs/foxbms-2`
**Source registry pinned to commit:** `308028fb13d046ba29b98886895c2e17937b1437` (foxBMS 2 v1.11.0, 2026-04-20)
**Corpus authored at commit:** `2a408d573b41c2f3ab75edccb31f28768adcf9f2` (2026-10-01) — the two are different things and neither is the other; see "Two commits, not one" below
**Figures refreshed:** 2026-10-01
**Status:** `synthetic_ready_with_limitations`

---

## ⚠️ Critical Warning Labels

| Label | Meaning |
|-------|---------|
| **SYNTHETIC** | This is a synthetic development corpus, NOT a certification package. foxBMS, SoftwareDevLabs and this corpus are NOT ISO 26262 compliant and NOT ASIL certified. The corpus holds a **structural mapping** to clause references; that is not conformity. |
| **HUMAN_APPROVAL_PENDING** | All 298 indexed records have `human_approval_status: pending`. **No human has approved anything in this corpus.** AI reviews are automated; distinct agent sessions are NOT organisational independence or human confirmation. |
| **PRODUCTION_UNAUTHORIZED** | All 298 indexed records have `production_authorized: false` and `product_verification_credit: false`. No generated record grants production authority. |
| **NO_TARGET_HARDWARE_EVIDENCE** | 0 of 33 required target-hardware executions exist. A real macOS **host** run exists (SIL harness, 313 CeeDling targets attempted, 222 passed) but macOS is **not an upstream-supported foxBMS platform** and a host run is **not** target-hardware evidence. It carries no verification credit. |
| **AS_IS vs SYNTHETIC_REFERENCE** | Two profiles: `as_is` (faithful reconstruction of pinned sources, 90 records) and `synthetic_reference` (hypothetical automotive BMS project, 173 records). Field-level provenance distinguishes `source_observed` (63), `derived` (53) and `synthetic` (147). |
| **NO NORMATIVE TEXT** | ISO 26262 and ASPICE PAM normative text NOT reproduced. Only metadata, methodology mappings and clause/process references are used, per rights policy. |
| **KNOWN_GOVERNANCE_CORRECTIONS** | **16** status claims in `governance/coverage-plan.json` are recorded as corrections. `CORR-COV-001`…`CORR-COV-015` (2026-09-29) verified each disposition against disk. `CORR-COV-016` (2026-10-01) went further: it ignored the disposition text, derived every process's backing set from each artefact's own `standards_mappings[].reference`, and asked whether those records carry the engineering the process defines. That pass demoted 23 of the 28 applicable ASPICE processes and 8 of the 10 applicable ISO parts. Nothing was upgraded; no expectation was deleted or narrowed; no artefact was fabricated to make a status true. |
| **TRACEABILITY_DOCUMENT_IS_TOOL_OWNED** | `TRACEABILITY_DOCUMENT.md` at the **repository root** claimed ISO 26262 and IEC 61508 compliance evidence and an ASIL-D/ASIL-B capability, and carried a fabricated `Status: APPROVED` sign-off block. The repository owner **explicitly authorised amending it**, and it was corrected by hand on 2026-09-29 (finding `FB2-REV-FND-000022` revision 3). **The durable fix has since been implemented, at revision 4 of that finding:** the document is now **generated** at `views/traceability/traceability-document.md` by `corpus.py render` from the canonical records, carrying the same provenance header and guard-field contract as every other generated view, with every figure computed at render time. The repository-root path and `reports/TRACEABILITY_DOCUMENT.md` are now content-free pointers to it. The drift risk is closed by construction rather than by human discipline. |
| **KNOWN_EVIDENCE_LIMITATIONS** | Four measured limitations of the evidence base. They are stated here and in full in the *Known Limitations* section of `reports/final-acceptance-report.md`, not only in agent handovers. See that section. |

---

## Two commits, not one

The corpus quotes two different commits and conflating them would be a false
statement in either direction.

| Field | Value | What it is |
|---|---|---|
| Source registry pin | `308028fb13d046ba29b98886895c2e17937b1437` | foxBMS 2 v1.11.0, dated 2026-04-20. This is what `as_is` records cite: every `as_is` source anchor resolves to a blob at *this* commit. `git merge-base --is-ancestor 308028fb HEAD` returns true. |
| Corpus authored at | `2a408d573b41c2f3ab75edccb31f28768adcf9f2` | dated 2026-10-01. This is the tree every number in every report was measured against. 74 commits touch `docs/artifacts/`. |

The corpus content **does not exist at** `308028fb` (`git ls-tree -r 308028fb`
has no `docs/artifacts` entry), and the pinned source at `308028fb` was not
re-audited on every pass. Both facts are recorded in
`governance/coverage-plan.json` as `repository_commit` (source pin, matching
`sources/source-registry.json` and `exports/manifest.json`) and
`corpus_authored_at_commit` (authoring head), each with a `_meaning` field.

---

## Current State at a Glance

All figures from a live `python3 docs/artifacts/tools/corpus.py` run on
2026-10-01. Every figure below is labelled with the population it counts,
because three different populations are legitimately in play.

| Measure | Value | Counts which population |
|---|---|---|
| Acceptance suite | **PASSED** — 8 stages, 10 gate lines, 0 FAIL | — |
| Schema-validated artifact files | **321** | population **A** — `validate`: every record carrying an `id`. `scenarios/` is walked, so this now equals population **B**; it did not before 2026-10-03. |
| Unique `(profile, id)` records | **321** | population **B** — the tool's `load_artifact_index` |
| Distinct artifact IDs across both profiles | **282** | population **C** — the `automated_review_coverage` denominator. 321 records carry 282 distinct ids: **39 ids appear in both profiles**. Those 39 pairs are different subjects (`origin` disagrees on every pair). Since amendment **ID-RULE-004-A1** (2026-10-04) an identifier is unique **within its profile**, so all 39 are **conformant**: no rename is required or permitted. See ITEM 2 below. |
| Traceability links | **585, 0 dangling** | de-duplicated by `(profile, link_id)` |
| Validator findings / errors | **5 / 0** | findings are provenance observations plus one ambiguity report, all `medium`, none is an error. `unqualified_reference_ambiguity` is the fifth: it reports artefact identifiers that are each carried by more than one live record **and** are referenced in prose without a profile qualifier. It is **not** an identifier-collision finding — under ID-RULE-004 as amended on 2026-10-04 the sharing is conformant. It is reported rather than raised to an error because every id-keyed lookup resolves `(profile, id)`, so no machine-read path is ambiguous; see ITEM 2 below. |
| Finding artifacts recorded | **42** | population **B**, `artifact_type: finding` |
| Coverage dimensions | 15 | — |
| Mutation scenarios | **20 / 20** detected | executed, each by the rule it declares |
| Change lifecycles | **3 / 3** content-validated | 19/19 required checks each |
| Toolchain self-tests | **95 PASS, 0 FAIL** | — |
| Source inventory | 612/612 files, 24 modules, 22 features, 23 variants | `src/**/*.c` and `*.h` |
| Export | **321 nodes, 585 edges**, 3 content hashes | population **B** and the link registry |
| Review records / unique IDs covered | **18 / 172 of 282 (61%)** | population **C** denominator. `reviewed_by_attribution_agrees_per_review` is **true**: every review's `reviewed_ids` set equals the set its own `reviewed_by` links name. |
| Target-hardware executions | **0 / 33** | 33 test measures; 44 execution records exist, none on target hardware |
| Human approval | **0 / 321** — all pending | population **B** |
| Production authorization | **0 / 321** — all false | population **B** |

### Records by type and domain — population **B** (318 unique `(profile, id)` records)

| By type | | By domain | | By profile | |
|---|---|---|---|---|---|
| execution | 44 | verification | 111 | `synthetic_reference` | 173 |
| finding | 42 | software | 54 | `as_is` | 90 |
| requirement | 34 | safety | 38 | | |
| test_measure | 33 | system | 21 | **By lifecycle** | |
| deviation | 26 | management | 14 | draft | 126 |
| review | 15 | supporting | 12 | reviewed | 73 |
| implementation | 14 | hardware | 7 | baselined | 64 |
| design | 8 | production | 2 | | |
| post_development_record | 6 | decommissioning | 1 | **By origin** | |
| process_record | 6 | operation | 1 | synthetic | 147 |
| stakeholder_need | 5 | release | 1 | source_observed | 63 |
| scenario | 5 | service | 1 | derived | 53 |
| safety_analysis | 4 | **Total** | **263** | | |
| use_case | 4 | | | | |
| change | 3 | | | | |
| hazard | 2 | | | | |
| safety_goal | 2 | | | | |
| safety_concept | 2 | | | | |
| process_improvement | 2 | | | | |
| project_plan, risk_register, item_definition, safety_case, tara, measurement_plan | 1 each | | | | |
| **Total** | **263** | | | | |

### The 15 coverage dimensions

Exactly as printed by `corpus.py coverage` on 2026-10-01. Each row names the
population its denominator counts, because they differ.

| Dimension | Ratio | % | Denominator counts |
|---|---|---|---|
| scope_accounting | 1/1 | 100% | presence of the three inventories |
| artifact_population | 13/13 | 100% | 13 declared artefact families |
| standards_mapping | **33/38** | 87% | 28 applicable ASPICE processes + 10 applicable ISO parts; ASPICE 25/28, ISO 8/10 |
| source_grounding | **99/263** | 38% | population **B**; 130 anchors available |
| traceability_integrity | **489/489** | 100% | every link in the registry |
| semantic_consistency_checks | 10/10 | 100% | declared count of check categories, not a measurement |
| automated_review_coverage | **144/259** | 64% | population **C**; 15 review records |
| verification_planning | **33/7** | 471% (ratio, not a score) | 33 test measures for 7 distinct FSR ids |
| actual_product_evidence | **0/33** | **0%** | population **B** execution records; `execution_kind` has no target-hardware member |
| synthetic_fixture_coverage | **173/43** | 402% (ratio, not a score) | `synthetic_reference` records against a declared target |
| negative_scenario_validation | 20/20 | 100% | **measured**: 20 scenarios executed, 20 detected by their own declared rule |
| export_reproducibility | 1/1 | 100% | presence of the manifest |
| human_approval | **0/263** | **0%** | population **B**. **Measured** since 2026-10-04, was a `{"numerator": 0}` literal. Counts records whose `human_approval_status` is a human decision **and** whose `approval_evidence` carries all six required elements. Reads 0 because nothing is approved |
| production_authorization | **0/263** | **0%** | population **B**. **Measured** since 2026-10-04, was a `{"numerator": 0}` literal. Same computation with a **strictly higher** bar: an approving role holding production authority, and a record family human approval is required for. Reads 0 because nothing is authorised |
| final_status | `synthetic_ready_with_limitations` | — | — |

`standards_mapping` measures **whether a disposition names an artefact that
resolves**, not whether the status is favourable. The figure rose from 16/38 to
33/38 in this pass because `CORR-COV-016` rewrote each disposition to name the
record it rests on, which is what recording evidence for a decision means. The
number that reflects substance went the other way: the ASPICE disposition tally
moved from **12 `mapped` / 10 `partially_mapped` / 6 `gap`** to
**4 `mapped` / 21 `partially_mapped` / 3 `gap`**, and the applicable ISO tally
from 6 `mapped` to **0**.

### The three population counts — deliberately not harmonised

| Count | Tool that produces it | What it measures | Why it differs |
|---|---|---|---|
| **318** | `validate` | schema-validated artefact **files** carrying an `id` | Walks `corpus/`, `reviews/` and `scenarios/`. It walked `scenarios/` separately until 2026-10-03 while the index did not, so it used to report 323 for a 300-record tree. |
| **318** | `load_artifact_index` | unique `(profile, id)` records | Same roots, same record set: all 318 `(profile, id)` pairs are unique, so nothing collapses. The index now walks `scenarios/`, which its own docstring always claimed it did. |
| **279** | `automated_review_coverage` | distinct artifact **IDs** across both profiles | 318 − 279 = **39** ids appear in both `as_is` and `synthetic_reference`. Profile isolation permits this; whether it should is the subject of the id migration in `coverage-plan.json` corrections. |

> **The split-brain that made populations A and B disagree, and is now closed.**
> `load_artifact_index` walked `corpus/` and `reviews/` only. Its docstring named
> three roots including `scenarios/`, and `cmd_validate` walked all three — which
> is why `validate` reported 323 artefacts while `check` counted 300 records for
> the same tree. The mutation harness read `scenarios/`. Five scenario fixtures
> existed twice under one id: a revision-1 copy under `corpus/scenarios/` that the
> index resolved to, and the live copy under `scenarios/` that the harness
> executed. The corpus therefore reported on different bytes than the harness
> validated, and the duplicate-id detector could not see it because it only ever
> saw one copy. Fixed on 2026-10-03: the duplicate tree was deleted and the index
> now walks `scenarios/`. Two self-tests hold it —
> `the index and the scenario harness resolve every scenario to the SAME bytes`
> and `a duplicate scenario id under any root FAILS validate`.

Nothing here is a rounding difference and none of the three is wrong. A report
that quotes one of them without saying which is the defect this section exists
to prevent.

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
│   ├── work-queue.json                 # 96 work-queue entries, all completed
│   └── resume.md
├── governance/                         # Corpus governance
│   ├── corpus-policy.json
│   ├── standards-lock.json             # ISO 26262:2018, ASPICE PAM 4.1
│   ├── scope-and-applicability.json
│   ├── coverage-plan.json              # 32 processes, 16 corrections
│   ├── role-and-review-policy.json
│   └── finding-disposition-vocabulary.md
├── sources/                            # Source registry + inventories
│   ├── source-registry.json            # 130 anchors, pinned to 308028fb
│   ├── source-inventory.json           # 612 source files, 24 modules
│   ├── feature-inventory.json          # 22 feature records
│   ├── variant-matrix.json             # 23 variants
│   └── permitted-extracts/
├── schemas/                            # JSON Schemas (draft 2020-12) — 26 files
│   ├── artifact-base.schema.json
│   ├── assumption.schema.json
│   ├── change.schema.json
│   ├── design.schema.json
│   ├── deviation.schema.json
│   ├── execution.schema.json
│   ├── finding.schema.json
│   ├── implementation.schema.json
│   ├── item_definition.schema.json
│   ├── link.schema.json
│   ├── measurement_plan.schema.json
│   ├── parameter.schema.json
│   ├── post_development_record.schema.json
│   ├── process_improvement.schema.json
│   ├── process_record.schema.json
│   ├── project_plan.schema.json
│   ├── requirement.schema.json
│   ├── review.schema.json
│   ├── risk_register.schema.json
│   ├── safety_concept.schema.json
│   ├── scenario.schema.json
│   ├── source_anchor.schema.json
│   ├── stakeholder_need.schema.json
│   ├── tara.schema.json
│   ├── test_measure.schema.json
│   └── use_case.schema.json
├── corpus/                             # 238 records (72 as_is + 166 synthetic_reference) + registry containers
│   ├── shared/
│   ├── as_is/                          # 72 records
│   ├── synthetic_reference/            # 166 records
│   └── (no scenarios/ subdirectory — the duplicate revision-1 tree was removed 2026-10-03;
│                                        the 23 live scenario records live under scenarios/ below,
│                                        and the index resolves them from there)
├── traceability/                       # Canonical typed links — 553 links after de-duplication
│   ├── link-registry/
│   │   ├── as_is/                      # 124 links across 2 files
│   │   └── synthetic_reference/        # 429 links across 6 files
│   ├── rules/
│   └── queries/
├── reviews/                            # Review records and findings
│   ├── records/                        # 15 review records, 49 embedded findings
│   ├── findings/                       # 42 finding artefacts
│   └── closure/
├── views/                              # Generated human-readable views — 11 files
│   ├── concept-and-safety/vertical-slice.md
│   ├── hardware/hardware.md
│   ├── management/management.md
│   ├── production-operation-service/lifecycle-continuation.md
│   ├── software/software.md
│   ├── verification-validation/verification-validation.md
│   ├── supporting-processes/supporting-processes.md
│   ├── standards-mapping/standards-mapping.md
│   ├── system/system.md
│   ├── traceability/traceability.md
│   └── traceability/traceability-document.md   # the canonical traceability doc
├── exports/                            # Portable exports — 4 files
│   ├── manifest.json                   # 318 nodes, 553 edges, 3 content hashes
│   ├── nodes.jsonl                     # 318 nodes
│   ├── edges.jsonl                     # 553 edges
│   └── trace-matrix.csv
├── evidence/
│   ├── actual-runs/                    # TRACKED host-run evidence, sha256-verified
│   └── synthetic-fixtures/             # EMPTY: no synthetic fixture was ever retained
├── spec-documents/                     # 10 generated spec documents (.md + .docx)
├── tools/                              # Validation tooling
│   ├── corpus.py                       # main CLI
│   ├── render_spec_documents.py        # spec-document generator
│   ├── render_e2e_html.py              # HTML deliverable generator
│   ├── check_references.py
│   ├── verify_traceability_document.py
│   ├── make_review_packets.py         # review packet generator + `--transcribe`
│   ├── verify_approval_ledger_independently.py
│   │                                   # from-scratch check of the approval
│   │                                   # ledger: chain, anchors, emptiness,
│   │                                   # packet digests, empty signatures
│   ├── verify_approval_evidence_independently.py
│   │                                   # from-scratch check of the approval
│   │                                   # amendment; imports NO tool in this repo
│   └── repo_model.py
├── tests/                              # Corpus toolchain tests
├── reports/                            # Reports (see table below)
├── diagrams/                           # Interactive diagrams (archify)
└── .work/                              # Temporary (gitignored, NOT in the distribution)
    ├── verification-env/               # SIL harness + runbook for the first host run
    └── verification-env/sil/           # SIL harness + logs for the 313-target run
```

### The tracked evidence base, and what is not in it

`docs/artifacts/evidence/actual-runs/` **is** tracked and every file in it is
sha256-verified against the execution records that cite it: 46 log entries,
46 hashes verified, 0 mismatched, 0 missing; plus 34 `evidence_files` entries,
0 missing. The SIL headline figures in this README are read directly from
`docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json`.

`docs/artifacts/.work/` is **gitignored and untracked**. Two consequences are
stated wherever a published number depends on it, rather than implied:

1. `FB2-VER-EXE-000008`…`FB2-VER-EXE-000012` each carry an
   `output_hashes.sil_suite_results_all` digest of
   `sha256:cbbdebeecd54720561753562f7c7dd3ca105e04ca36494f52b674d9fd5a00f67`,
   which resolves to
   `docs/artifacts/.work/verification-env/sil/logs/RESULTS-POST-fix.json` — a
   gitignored scratch file — and **not** to the `results-sil-all.json` the same
   records name in their `logs[]` (`sha256:edd3e70888c75ba075db2dadb17cd9cfb369adfce4b8ac4a05aaefada3c64589`).
   `FB2-VER-EXE-000015` goes further and names eight `.work/` paths directly in
   its `logs[]`.
2. The first host run's `docs/artifacts/.work/verification-env/RUNBOOK.md` is a
   local artefact, not a distributed one.

Reproducing the SIL run from a fresh clone: see
`evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/RUNBOOK.md`,
which **is** tracked.

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

### ID-RULE-004 — uniqueness is per profile (amended 2026-10-04)

**ID-RULE-004-A1.** An artefact identifier is unique **WITHIN ITS PROFILE**. Two
records of different profiles may legitimately carry the same identifier string,
and doing so is **conformant, not a collision and not a defect**.

| | |
|---|---|
| **Supersedes** | the corpus-wide-uniqueness reading of ID-RULE-004 as previously written ("IDs must be globally unique across profiles"), in its entirety |
| **Does not supersede** | ID-RULE-001, ID-RULE-002, ID-RULE-003 — all unchanged |
| **ID-RULE-003 invoked?** | **No.** No supersession, deletion or migration is performed, so that instrument is not the one in play |
| **The 39 shared ids** | **No rename is required, and none is permitted.** They are conformant. No string is carried by two records of the *same* profile — that is the condition the duplicate check reports as an error, and it has never fired |
| **Why this route** | Route (b) of the two `FB2-SAF-VOC-000001` put forward. The tool has always enforced per-profile uniqueness, so the corpus was previously in permanent declared non-conformance with its own policy. Route (a) — migrating under ID-RULE-003 — was measured and declined: renaming would make ~900 unqualified prose references *confidently wrong* with no validator able to detect it |

**The corpus's primary key is `(profile, id)`.** An unqualified reference does
not supply a profile, so it does not resolve. The corpus resolves the remainder
by an adopted convention — *an unqualified id reads as the `synthetic_reference`
copy* — which is now **load-bearing** under this rule.

**The residual risk, which the amendment relocates rather than removes:** where
the named id is carried by more than one live record, the convention supplies the
answer and a reader who does not hold it has two live candidates and no way to
choose. `corpus.py` reports exactly this, under rule
`unqualified_reference_ambiguity`: 39 shared strings, **34** referenced
unqualified, **610** prose mentions across **527** referring locations, plus 785
mentions in profile-scoped id slots (excluded by design, counted separately). All
four figures are over **records**; every one was independently reproduced by a
from-scratch enumeration that does not import `corpus.py`.
**23** of the 34 are also referenced unqualified from an `as_is` record, where the
enclosing record's own profile points away from the `synthetic_reference` default.

That figure is an **upper bound, not an exact count**: a pattern match cannot see
a qualifier stated in words, so some counted references are qualified for a human
reader. It does not under-report — a qualified reference being counted is noise,
whereas a missed ambiguous reference would be a hole. Severity is **report-only,
not gated**: every id-keyed lookup resolves `(profile, id)`, so no machine-read
path is ambiguous.

**Reconciliation.** `FB2-SAF-VOC-000001` said "Do not renumber … so a rename is
not available as a repair" (citing ID-RULE-001) while `CORR-COV-021` treated
ID-RULE-003 as the sanctioned instrument. Both asserted the corpus was
non-conformant; they disagreed about whether a repair existed, and neither was
subordinate to the policy. **The amended rule now governs**, and the two documents
agree. The ID-RULE-001 reasoning is *withdrawn as reasoning* — it was never the
bar — while the conclusion survives as a settled state rather than a deferral.
Recorded in full at `FB2-SAF-VOC-000001`
`identifier_vocabulary.supersession_reconciliation_2026_10_04`.

---

### APPROVAL-RULE-A1 — an approval needs evidence, not a ban (2026-10-04)

**The problem.** Three rules — `human_approval_rejected`,
`production_authorized_rejected`, `verification_credit_rejected` — failed
validation on the approval field's **value alone**. A rule that fails on the
value never inspects an approval, so it cannot tell a fabricated one from a real
one: it could say only "no", never "this one is unsigned". The corpus therefore
had two reachable states for approval, *absent* and *forbidden*, and no way to
represent the legitimate middle. A reviewer who had done the work had nowhere to
record it, and the first signature would have turned `check` red and been blamed
for it.

**The change.** An approval value is **necessary and not sufficient**. It passes
only if the record carries, under `approval_evidence.<kind>`, all six elements
below. The contract is machine-readable at
`governance/role-and-review-policy.json#/approval_evidence_contract` and the
validator **reads it from there** rather than restating it, so policy and code
cannot drift.

| # | element | what is checked |
|---|---|---|
| 1 | the grant value | present. Never sufficient on its own |
| 2 | `approved_by` | a named **person**: ≥2 tokens, not a declared `role_id` or role name, no token a `role_id`, no token from the team vocabulary |
| 3 | `role` + `independence` | `role` is a declared `role_id`; `independence{owner_role, satisfied, evidence, policy_ref}` with `owner_role` equal to **this record's own**. Independence is then **enforced**: the role must differ from `owner_role` **and** from the author of the last content revision |
| 4 | `date` | ISO-8601, grammar- **and** parse-checked |
| 5 | `review_packet` | `{path, sha256, record_sha256_at_signing}`. The path resolves to a `packet.json` on disk **under `reviews/signed/` and nowhere else** (a `reviews/packets/` citation is rejected — see `APPROVAL-LEDGER-A1`); `sha256` equals that file's bytes **now**; `record_sha256_at_signing` equals **the packet's own** `integrity.record_sha256`; the packet's `target.record_id` **and** `target.profile` name this record |
| 6 | `approval_ledger_ref` | superseded 2026-10-04 — see `APPROVAL-LEDGER-A1` below. It used to require a `revision_history` entry, which made an approval a content change and therefore unsatisfiable in practice |

Every finding names **which** element is unmet, numbered, so a reviewer can fix
it in one pass. `production_authorization` adds two conditions on top, so its
bar is **strictly higher**: the approving role must hold production authority
(`architect` or `safety_manager`) and the record's family must be one human
approval is required for (`safety_case`, `post_development_record`, `change`).

**`human_approval` and `production_authorization` are now measured.** Both were
the literal `{"numerator": 0}`, which reads 0/321 before any signature exists and
would read 0/321 after three hundred. Both are now computed from the records by
**the same predicate the validator enforces**, so neither can read higher than
the gate permits. They read 0/321 because **no approval exists**, and the detail
text says so as a measurement.

**What it did NOT do.** It did **not** produce an approval: every record is still
`pending` and this repository may not write one. It did **not** add authority to
anyone. It did **not** relax `human_approval_status: "not_required"`. It did
**not** touch the recursive authority-key scan, the ASIL/conformity/certification
claim classes, gate `[7/8]`, the provenance gate, or the packet generator's rule
that no code path writes a signature.

**Honest residual risk.** Before the amendment *any* approval failed, so the
mechanical guard was total; now a fully evidenced approval passes and the guard
is the attribution requirement. A determined person can still forge all six
elements — the digest chain proves a packet exists and pins which record state it
was generated against, but it does not prove anybody read anything. Four
residual risks are recorded rather than dropped, at
`governance/corpus-policy.json` `review_policy.approval_rule_amendment`
(`.residual_risks_recorded_here_not_silently_dropped`) and in
`governance/closing-list.md` §3.1.

**A reviewer can now transcribe a correct approval first time:**

```bash
python3 docs/artifacts/tools/make_review_packets.py --transcribe FB2-HW-TSR-000001 --profile as_is
```

It prints the exact `approval_evidence` block and the exact ledger entry, writes
nothing, appends nothing, and fills no decision. Section 8 of all 321 generated
packets states the same rule. **Run it twice** — see below.

Recorded in full at `governance/corpus-policy.json`
`review_policy.approval_rule_amendment` and `coverage-plan.json` `CORR-COV-022`.

---

### APPROVAL-LEDGER-A1 — an approval is an event, not a change (2026-10-04)

**The problem.** `APPROVAL-RULE-A1` made a properly evidenced approval *expressible*
but not *satisfiable*. Element 6 required the approval to be recorded as a
`revision_history` entry, and a `revision_history` entry **is** a content change,
so the record's `revision` had to bump. A bumped revision makes every link pinning
that record's revision stale, and invalidates the `sha256` that every review
record stores for it. So recording a legitimate approval broke two controls nobody
had authorised breaking, and the corpus worked around it by recording the approval
against the **current** revision — an unratified convention.

The tell was the tool's own happy-path self-test: it had to pick a record that
**no review record covers**, purely so the approval would not invalidate a stored
digest. A test that must choose an uncovered record to demonstrate its own happy
path is demonstrating an unsatisfiable requirement.

**The change.** An approval is an **event about** a record, not a change **to** it.
It is recorded in an append-only ledger and the record keeps only a reference:

```
governance/approval-ledger.jsonl        one JSON object per line, APPEND-ONLY, 0 bytes today
  ledger_id, record_id, profile, kind,
  approved_record_sha256, approved_content_revision,
  approved_by, role, independence, date,
  signed_packet{path, sha256},
  packet_first_commit,        the commit that first held that packet
  previous_entry_sha256       the preceding entry's digest, or 64 zeros

the record gains exactly one thing:
  approval_ledger_ref: {ledger_id, entry_sha256}
```

**The mechanism is a CONTENT DIGEST**, and it is what makes recording an approval
free. A record's content digest is its bytes projected through a view in which
approval evidence is removed and approval state is reset to the no-claim values
every record already carries. So a record nobody approved projects to **its own
bytes** — all 261 stored review digests still verify, unchanged — and an approved
record projects back to **the file it had before the approval**, rendered in that
file's own detected layout (the records are a mix of 1- and 2-space indent, so the
layout is probed and verified, never assumed). The review-digest check compares
the content digest.

**Therefore, proved by self-test on a record a review record already covers:**

```
FB2-HW-TSR-000001/as_is: revision 2 -> 2
  stale-link observations  122/1170 -> 122/1170
  review digests verified      261 -> 261   (0 mismatches before and after)
  approval landed in revision_history = False
  content digest unchanged = True
```

**Two further changes.**

| risk | before | now |
|---|---|---|
| staleness was **invisible** | the approval just stopped counting; no finding, no count | an entry whose `approved_record_sha256` no longer matches is **STALE, not invalid**: it does **not** fail validation, it is counted as `approval_staleness` `stale / total`, and it is reported in a finding naming the record, the ledger entry and **the fields that changed** — recoverable because every signed packet embeds the approved record verbatim. A stale approval is excluded from the `human_approval` numerator and not discarded: `human_approval` and `approval_staleness` together account for every approval |
| `reviews/signed/` was an **ordinary directory** | a `packets/` citation resolved, so nothing stopped a reviewer parking evidence in the regenerated tree | a signed packet is admissible **only** from `reviews/signed/`. A `packets/` citation fails with a message naming the archive and saying to archive first |

`approval_staleness` is a **counted metric reported beside the fifteen coverage
dimensions**, not a sixteenth dimension: "this corpus has fifteen coverage
dimensions" is a claim the audit trail relies on, and inflating the count to
advertise a new measurement would make it false. It is printed by `coverage` and by
`check` on every run. Current value **0/0** — the ledger holds no entry, so there
is nothing to go stale.

**What forgery resistance this does and does not give.** Each entry binds to its
predecessor's digest, so deleting, reordering or editing any entry breaks the chain
from that point on and the validator reports the **first** break. Each entry cites
the git commit that first contained the signed packet, and the validator confirms
that commit exists **and** holds the blob.

> **Neither proves that a human read anything, and none of this makes an approval
> unforgeable.** A determined person can write all six elements, archive a packet,
> cite a real commit and maintain the chain correctly, and nothing in this
> repository can tell that from a real approval. That limit is **irreducible** —
> any attestation can be forged by someone determined to lie. What was added is
> **cost** and **detectability**, not prevention. Recorded in four places:
> `governance/corpus-policy.json`
> `review_policy.approval_ledger_amendment`, `governance/approval-ledger.md`, the
> docstring of `CorpusTool._check_ledger_git_anchor`, and
> `tools/verify_approval_ledger_independently.py`. **Do not describe any of it as
> making approval unforgeable.**

**What it did NOT do.** It recorded **no** approval and appended **no** ledger
entry: the file is 0 bytes and every record is still `pending`. It added no
authority. It moved **no** coverage dimension — `human_approval` 0/321,
`production_authorization` 0/321, `actual_product_evidence` 0/33, all unchanged —
and it added two new obstacles rather than removing any: a forged `ledger_id` and
a forged `entry_sha256` are both rejected by name. Element 5 got **tighter**, not
looser.

**A reviewer can now record a correct approval first time** — and must run the
command **twice**, because the digest an approval must cite is the digest of the
*archived signed copy*, which has their signature in it and so cannot be known
before they have signed:

```bash
python3 docs/artifacts/tools/make_review_packets.py --transcribe FB2-HW-TSR-000001 --profile as_is
# 1. fill section 9 in your own copy;  2. archive at reviews/signed/<profile>/<id>.json
python3 docs/artifacts/tools/make_review_packets.py --transcribe FB2-HW-TSR-000001 --profile as_is
# 3. resolves both digests; 4. append the printed line to the ledger; 5. merge the block + approval_ledger_ref
```

**An independent checker that shares no code with the tool it checks:**

```bash
python3 docs/artifacts/tools/verify_approval_ledger_independently.py
```

It re-derives the chain, the approvals count, the packet digests, the cited paths,
the empty signature blocks and the single-append-site fact from bytes on disk, and
states its own limits in its own output.

Recorded in full at `governance/corpus-policy.json`
`review_policy.approval_ledger_amendment`,
`governance/role-and-review-policy.json#/approval_ledger_contract` and
`coverage-plan.json` `CORR-COV-023`.

---

## Link Semantics

**Eleven** relation types are in use across **489** links. Counts below are from
`load_links`, which de-duplicates on `(profile, link_id)`.

| Relation | Count | Direction |
|----------|------:|-----------|
| `reviewed_by` | 229 | artifact → review record |
| `verifies` | 55 | test measure → requirement (**test measure is the source**) |
| `allocated_to` | 46 | HW/SW/system requirement → FSR it satisfies |
| `refines` | 41 | FSR → safety goal; scenario → parent scenario |
| `result_of` | 33 | execution → the measure it resulted from |
| `supports` | 29 | analysis / TARA → requirement or goal |
| `changes` | 16 | change record → artefact it revises |
| `implements` | 13 | design → requirement it implements |
| `validates` | 12 | test measure → requirement (validation direction) |
| `depends_on` | 12 | artefact → artefact it depends on |
| `mitigates` | 3 | safety goal → hazard |
| **Total** | **489** | |

By profile: `as_is` 117, `synthetic_reference` 372.
By review state: reviewed 414, pending 75.

> **Link currency is now maintained, and 332 links await re-examination.** Every
> link carries both endpoint revisions. 423 of them had drifted from the current
> revision of the artefact they name; **all 423 have been advanced to current**,
> each with a per-link `provenance_repair` record naming the previous value, the
> revisions skipped, and their date, author and description — so a reader can
> see exactly what content a link now names that it did not name when authored.
> **332 of 553 links are now marked `change_suspect_status: true`.** That flag
> means *an endpoint was advanced past the revision this link was authored
> against, and no re-examination of the link is recorded* — it is a statement
> about re-examination, not a claim that the link is wrong. Link *resolution* is
> verified (0 dangling) and link *currency* is machine-enforced by two validator
> rules, `link_endpoint_revision_stale` and `link_derived_field_contradiction`.
> The 326 awaiting re-examination are themselves why `SUP.11 Traceability
> Management` stays `partially_mapped` rather than `mapped`.

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

44 `execution` records exist in population **B**. Measured distribution:

| Execution kind | Description | Records |
|----------------|-------------|--------:|
| `actual_host_run` | Executed on a development host — **not target hardware** | **15** (all `as_is`) |
| `none` | Planned or attempted but nothing ran | **23** (1 `as_is`, 22 `synthetic_reference`) |
| `synthetic_fixture` | Synthetic test data for corpus validation | **6** (all `synthetic_reference`) |
| `actual_simulation_run` | Simulator with captured logs | **0** |
| **target hardware** | — | **no such member exists in the enum** |

| Outcome | Records |
|---------|--------:|
| `pass` | 11 (5 `as_is` host runs, 6 `synthetic_fixture`) |
| `fail` | 10 (all `as_is` host runs) |
| `blocked` | 23 (1 `as_is`, 22 `synthetic_reference`) |
| `inconclusive` / `not_run` | 0 |

**Orthogonal:** execution kind ≠ outcome. Planning is not execution.
`actual_product_evidence` is **0/33** because `execution_kind` has no
target-hardware member, so none can be claimed without fabricating one.

> **The 6 `synthetic_fixture` executions retain no evidence at all.** Each of
> `FB2-VER-EXE-000001`…`FB2-VER-EXE-000006` (profile `synthetic_reference`)
> records `outcome: pass` with `logs: []` and no evidence file, and
> `docs/artifacts/evidence/synthetic-fixtures/` holds **no fixture artefact** — its
> only file is a hand-written `MANIFEST.md` documenting the absence, which states in
> its own header that it "must never be counted as captured evidence for any test".
> The fixture they claim
> to have run was never retained, so the `pass` cannot be checked by anyone,
> including this corpus. That is why the denominator of
> `actual_product_evidence` counts all 44 execution records and the tool's own
> detail string separates host/simulation (15) from `synthetic_fixture`/`none`
> (29).

---

## The macOS Host Runs

**This section supersedes the earlier claim that "177 of 313 repository tests
are blocked on HALCoGen."** That was true of the *first* host run, which selected
only the 136 test suites whose quoted-`#include` closure reaches no
HALCoGen-generated header. A **SIL harness** now runs all 313. Both runs are
reported because the first is the one the older reports describe.

### Run 1 — pre-SIL host run, selection `no_halcogen_dependency`

Source (tracked): `evidence/actual-runs/foxbms2-host-unit-test-macos-2026-09-29/results-strict.json`,
generated 2026-09-29T10:30:52+0200.

| Measure | Strict | Relaxed (`results-relaxed.json`) |
|---|---:|---:|
| Tests in scope | 136 | 136 |
| Passed | 94 | 98 |
| Failed | 5 | 7 |
| Build failures | 37 | 31 |
| Assertions tested | 332 | 391 |
| Assertions passed | 323 | 380 |
| Assertions failed | 8 | 10 |

The 177 tests outside this selection were blocked on proprietary TI HALCoGen
output reaching **34 distinct `HL_*.h` headers** (`halcogen-dependency-closure.json`).
That blocker is now *worked around by a SIL harness*, not by faking TI register
maps, and it is no longer the reason those 177 suites do not run.

### Run 2 — SIL host run, selection `all` (**the current headline**)

Source (tracked): `evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json`,
generated 2026-09-30T01:24:18+0200. Harness: "SIL host unit tests (CMock mocks of
host-declared `HL_*.h` interface headers)".

| Measure | Value |
|---|---:|
| CeeDling targets attempted | **313** |
| **Passed** | **222** |
| **Failed** | **7** |
| Build failures | **84** |
| Assertions tested / passed / failed | 988 / 950 / 35 |

The 84 build failures are classified by the harness, order-independently, on the
**set of distinct diagnostic codes** — not on any single message:

| Class | n | | Class | n |
|---|---:|---|---|---:|
| `excluded:upstream_config` | 28 | | `build:real_defect_macro_arity` | 4 |
| `build:clang_only_diagnostic` | 22 | | `build:sil_interface_header_mismatch` | 3 |
| `build:undeclared_identifier` | 8 | | `build:real_defect_implicit_function_declaration` | 2 |
| `build:real_defect_out_of_bounds_array_index` | 6 | | `build:real_defect_implicit_int` | 2 |
| `build:strict_diagnostic_both_compilers` | 5 | | 4 more classes, 1 each | 4 |
| | | | **Sum** | **84** |

313 = 222 passed + 7 failed + 84 build failures, exactly.

**Two populations that must not be conflated.** The harness *attempted 313*
CeeDling targets. The repository today contains **318** `test_*.c` files under
`tests/`; the 5 not attempted are `tests/unit-hw/test_tms570_{boot,crc,flash,main}.c`
— the TMS570 **target-hardware** tests, which is precisely the evidence class
this corpus cannot produce — plus
`tests/cli/pre_commit_scripts/test_check_include_guard/test_file.c`, a C sample
for a Python linter. "313 tests" is the harness's enumeration, not a count of
every `test_*.c` file in the tree.

**macOS is not an upstream-supported foxBMS platform.** This is a host run and
carries no target-hardware verification credit.

**The 5 failures of the first run are a real defect in the product's test setup, not a harness
artefact** — a statement that still holds, and it is why
`FB2-REV-FND-000042` exists: **53 of the 245 green tests in the SIL host run
assert nothing**, which is a separate and worse finding, recorded against the
SIL run rather than hidden by it.

Runbook: `evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/RUNBOOK.md` (tracked).

**The root cause of the first run's failures, in full.** `src/app/engine/database/database.h:209` declares the database
access API with untyped `void *` parameters; the shipped Ceedling config sets
`:cmock: :when_ptr: :compare_data`, so CMock cannot learn the pointed-to size
and emits a pointer-**identity** check. The tests pass a pointer to their own
`static` copy while the code under test passes a different one. This is
compiler- and platform-independent, so the same five tests are expected to fail
under GNU gcc on Linux. **No result was adjusted to make a test pass.**

---

## How to Run Checks

### Before anything else — `jsonschema` (P-a)

This corpus **will not run** without `jsonschema`, and it refuses to run rather
than reporting a pass it did not earn. The dependency has gone missing three
times, with a different failure mode each time (once *silently*, with
`corpus.py` exiting 0 having validated nothing), and the cause was never the
corpus: **`jsonschema>=4.18` being pinned in `requirements.txt` does not install
it.** A pin is a statement in a file; what an interpreter holds is a fact on
that interpreter's disk. Nothing reconciles the two, which is why the same
failure kept returning.

On a fresh checkout, or on a machine that has just been restarted, run this
first:

```bash
docs/artifacts/tools/bootstrap.sh
```

It creates a virtualenv **outside** the repository (default
`~/.cache/foxbms-corpus-venv`, override with `FOXBMS_CORPUS_VENV`), installs the
pinned requirements, and prints the command to run the suite with it. It creates
nothing inside the tree and refuses to run if `FOXBMS_CORPUS_VENV` resolves
inside it.

If you would rather install into an existing interpreter:

```bash
# PEP 668 managed Python (macOS/Debian) refuses without the flag:
python3 -m pip install --user --break-system-packages -r docs/artifacts/tools/requirements.txt

# then confirm by IMPORTING, not by trusting pip's output:
python3 -c "import jsonschema, referencing; print(jsonschema.__version__)"
```

If `jsonschema` is absent, `corpus.py` prints a preflight naming the missing
distribution, the interpreter actually running, the requirement file, both
install commands and the `bootstrap.sh` route — and still exits 2. That is
deliberate. See `governance/closing-list.md` §4 P-a.

### The commands

```bash
# Full acceptance suite (8 stages) — expect: Acceptance suite: PASSED
python3 docs/artifacts/tools/corpus.py check

# Schema + link + semantic + provenance validation — expect: errors=0
python3 docs/artifacts/tools/corpus.py validate

# The 15 coverage dimensions
python3 docs/artifacts/tools/corpus.py coverage

# Toolchain self-tests — expect: 48 PASS, 0 FAIL
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

# HTML deliverable integrity — expect: exit 0. IT CURRENTLY EXITS 1, see the
# note under "Known Gaps and Defects".
python3 docs/artifacts/tools/render_e2e_html.py --check
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

# Regenerate the HTML deliverable (tracked; see the note on its --check below)
python3 docs/artifacts/tools/render_e2e_html.py
```

**Determinism:** rendering twice produces byte-identical output apart from the
`Generated:` line in each view's preamble and the `generated_at` field in
`exports/manifest.json`. Verified by `diff -r -I '^Generated:'`. No other line is
excluded. Re-verified on 2026-10-01 after the coverage-plan change: two renders,
zero differences across all 11 views.

**Anti-drift:** generated prose reads `governance/coverage-plan.json` **live at
render time** rather than quoting a frozen literal, so correcting the plan
corrects the views. Verified twice: once on 2026-09-29 by temporarily flipping a
disposition and observing the view follow it, and again on 2026-10-01 when the
`CORR-COV-016` demotions propagated — `views/standards-mapping/standards-mapping.md`
moved from 12/10/6 to 4/21/3 without any view being edited.

The `.md` reports in `reports/` are hand-authored but every number in them is
taken from a live tool run, and each report states which command produced which
figure. **Where a report's figure and the live figure disagreed, the report was
corrected rather than the live figure — except where the live figure itself was
the defect, which is recorded as a finding and named in the report.**

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
parts. Two different figures must not be conflated:

| Figure | Value | What it measures |
|---|---|---|
| `standards_mapping` (acceptance gate) | **33/38** | how many of the 38 applicable entries name an artefact that resolves — ASPICE 25/28, ISO 8/10. **Not** a statement about favourability. |
| Disposition tally | **ASPICE: 4 `mapped`, 21 `partially_mapped`, 3 `gap`** over the 28 applicable; **ISO: 0 `mapped`, 8 `partially_mapped`, 2 `referenced`** over the 10 applicable | whether the backing records carry the engineering the process defines. **This is the honest figure.** |

The old `44/44` was the number of keys in the inventory file divided by itself.
It was replaced by `16/38` on 2026-09-29 (measured by backing) and then rose to
`33/38` on 2026-10-01, because `CORR-COV-016` rewrote each disposition to name
the record it rests on. The number that reflects substance moved the other way,
from 12 `mapped` to 4.

**Only 4 of 28 applicable ASPICE processes survive the audit:** `MAN.3`
(`FB2-MAN-PLN-000001`), `MAN.5` (`FB2-MAN-RSK-000001`), `MAN.6`
(`FB2-MAN-MSM-000001`) and `PIM.3` (`FB2-PIM-IMP-000001`/`000002`). Three
processes are honest `gap`: **`SWE.3` and `HWE.3` and `HWE.4`, none of which any
artefact in the corpus references in any `standards_mappings[].reference` string.**
No ISO 26262 part is `mapped`.

**No process in this corpus is assessed at any ASPICE capability level.**

---

## Known Gaps and Defects

### Process-coverage gaps after the substantive audit (`CORR-COV-016`, 2026-10-01)

Every row below is measured from the corpus, not asserted. "Backing records"
means artefacts whose own `standards_mappings[].reference` names the process.

| Process | Status | Backing records | What is actually missing |
|---|---|---|---|
| **`SWE.3`** Software Detailed Design and Unit Construction | **`gap`** | **ZERO** | Recorded `mapped` until 2026-10-01 while **no artefact in the corpus referenced it at all**. No detailed-design record (the 8 `design` records are `design_level: architecture` and name SWE.2), no source-code record, no unit-test specification. |
| **`HWE.3`** Hardware Detailed Design | **`gap`** | **ZERO** | No schematics, PCB layout, BOM or component specification. The Altium design files live in the external `foxBMS2_hw` repository and are unverifiable from here. |
| `HWE.4` Hardware Integration and Test | **`gap`** | **ZERO** | No HW integration plan, test specification or test result. |
| `SYS.1` Requirements Elicitation | `partially_mapped` | 5 stakeholder needs, 4 use cases, item definition, project plan | No operational scenario; every need carries `is_a_real_elicitation = false`; `as_is` remains at gap. |
| `SYS.2` System Requirements Analysis | `partially_mapped` | 8 system requirements | No system modes/states; no system-level interface requirements; requirements back-inferred from code, not analysed. |
| `SYS.3` System Architectural Design | `partially_mapped` | HSI interface spec, 2 safety concepts, project plan | **No system-architecture record exists.** Allocation lives only inside the safety concepts. |
| `SWE.1` Software Requirements Analysis | `partially_mapped` | 6 software requirements | No software interface requirements; requirements back-inferred, not analysed. |
| `SWE.2` Software Architectural Design | `partially_mapped` | 6 design records | Interfaces are signal tables, not interface specifications; records extracted from existing code. |
| `SWE.4` / `SWE.5` / `SWE.6` | `partially_mapped` | 33 test measures, 15 host-run executions | No unit/integration/qualification **specification**, no **plan** for SWE.5, and the only unit results are from the SIL host harness, not the upstream Unity/CMock suite. |
| `SYS.4` / `SYS.5` | `partially_mapped` | 23 test measures, 8 executions | No integration or qualification plan or specification; all results blocked. |
| `HWE.1` / `HWE.2` | `partially_mapped` | 7 hardware requirements | No hardware interface requirements, no hardware architecture, no block diagram, no interface schematic. |
| `ACQ.4` Supplier Monitoring | `partially_mapped` | 1 process record, 1 post-development record | No supplier assessment — the record states no supplier is under contract and no advisory source was consulted. |
| `REU.2` Reuse Program Management | `partially_mapped` | 1 process record | No reuse assessment completed for any element; independence unachievable for the modified vendor drivers. |
| `SPL.2` Release Management | `partially_mapped` | 4 records | No release notes; nothing released — `any_step_executed: false`. |
| `SUP.1` Quality Assurance | `partially_mapped` | 1 process record, 15 review records | No audit record; independence stated and explicitly not achieved (RSK-003). |
| `SUP.8` Configuration Management | `partially_mapped` | 1 process record, 4 records | Change control deferred to another record; status accounting not performed. |
| `SUP.9` Problem Resolution Management | `partially_mapped` | 13 findings, 1 process record | No trend analysis — the record itself says one intake cycle cannot produce one. |
| `SUP.10` Change Request Management | `partially_mapped` | 3 change records, 1 process record | All three changes are fictional; nothing was raised against the real product. |
| `SUP.11` Traceability Management | `partially_mapped` | 3 change records, 547 links, coverage reports | Link currency not maintained: **326 of 547 links carry a stale endpoint revision and none is marked suspect.** |
| `VAL.1` Validation | `partially_mapped` | 5 test measures, 4 use cases, 2 post-development records | No validation plan; **zero validations executed** — all executions blocked. |
| ISO Part 2 Management | `partially_mapped` | `FB2-MAN-SPL-000001` only | That record has `artifact_type: design`, six empty structural fields, no roles assigned and no tailoring. It is not a safety plan. |
| ISO Parts 3, 4 | `partially_mapped` | Item definition, FSC, TSC, HSI, 8 system requirements | Concept timing budget does not close (FND-000025); contactor reaction requirement contradicts itself (FND-000024); no system architecture; no modes/states. |
| ISO Part 7 Production | `partially_mapped` | 6 post-development records | All six carry `any_step_executed: false`. Documented, not performed. |
| ISO Part 8 Supporting | `partially_mapped` | 6 supporting-process records | Rests entirely on records whose own processes are `partially_mapped`; QA independence not achieved. |
| ISO Part 9 ASIL | `partially_mapped` | 4 safety analyses, 2 ASIL field values | No ASIL methodology; `FB2-SAF-SGO-000001` carries `ASIL_D` with no justification field at all. |

### Known limitations of the evidence base

These four are true, measured, and belong in the reports rather than only in an
agent handover.

| # | Limitation | Measured extent |
|---|---|---|
| 1 | **10 records' hardware provenance rests on Altium design files in an external repository.** Anchors `FB2-SRC-HW-000001..000003` name `.SchDoc` files that live in `foxBMS2_hw`, present neither in this working tree nor in any commit of it. Their `content_hash` and `location.file_hash` both read `unresolved` and their `hash_status` is `external_design_file_unverifiable_from_this_repository`. | **14** records cite them; **10** are non-review records (6 hardware requirements, `FB2-SAF-ANL-000003`, `FB2-SAF-ITE-000001`, `FB2-SAF-TSC-000001`, `FB2-SYS-HSI-000001`) and 4 are the review records that review them. |
| 2 | **4 anchors have no single machine-checkable symbol.** The provenance checker records `symbol_unverifiable_prose` for these and cannot verify them by symbol match. Their content hashes and line ranges *are* verified. | `FB2-SRC-COD-000044` whole `rtc.c` module body (lines 70–653); `FB2-SRC-COD-000076` the 12-line FreeRTOS **markdown README**; `FB2-SRC-COD-000077` the whole 114-line **`requirements.txt`**; `FB2-SRC-COD-000088` the **licence/copyright header** of `dp83869.c` (lines 1–59). |
| 3 | **5 execution records carry a suite-results digest belonging to a `.work` scratch file** rather than the evidence file they name. | `FB2-VER-EXE-000008`…`000012`: `output_hashes.sil_suite_results_all = sha256:cbbdee…` resolves to `.work/verification-env/sil/logs/RESULTS-POST-fix.json`, not to the `results-sil-all.json` (`sha256:edd3e70…`) those records cite. `FB2-VER-EXE-000015` additionally names eight `.work/` paths directly in its `logs[]`. |
| 4 | **6 synthetic executions describe a `synthetic_fixture` run with NO retained evidence.** The fixture never existed. | `FB2-VER-EXE-000001`…`000006` (profile `synthetic_reference`): each records `outcome: pass` with `logs: []` and no evidence file, and each carries a `provenance_repair.unretained_evidence` entry recording that the previous `build/synthetic/*.log` reference was removed rather than replaced. `docs/artifacts/evidence/synthetic-fixtures/` holds **no fixture artefact** — only a `MANIFEST.md` documenting the gap. **That `MANIFEST.md` cites finding `FB2-REV-FND-000143`, and no such record exists in the corpus**: 42 `finding` records exist, numbered up to `FB2-REV-FND-000042`. The gap is therefore recorded only in a hand-written statement, not in a canonical record. |

### Reported defects

| Defect | Severity | Disposition |
|---|---|---|
| `TRACEABILITY_DOCUMENT.md` at repository root claimed ISO 26262 + IEC 61508 compliance, an ASIL-D/ASIL-B capability, and carried a fabricated human-approval sign-off; outside the write boundary | high | **accepted** — `FB2-REV-FND-000022` rev 4; corrected under explicit owner authorisation, then made **tool-owned**: the document is generated at `views/traceability/traceability-document.md` and the root path is a content-free pointer, so the drift risk is closed by construction |
| **`render_e2e_html.py --check` fails on 14 records** | medium | **open, tool-side.** Every `artifact_type: implementation` record (10 `as_is`, 4 `synthetic_reference`) has no owning section in the renderer, so its integrity check exits 1 with `UNMAPPED artifact type … has no owning section`. The HTML deliverable itself is regenerated, tracked (the path-specific negation in `docs/artifacts/.gitignore` works: `git check-ignore` returns 1) and passes `--audit-guard` with no affirmative conformity claim. The fix is an owning section in `render_e2e_html.py`, which is outside the write boundary of this workstream. |
| **326 of 547 links carry a stale endpoint revision and none is marked suspect** | medium | **open.** `SUP.11` demoted to `partially_mapped` for it. |
| **53 of the 245 green tests in the SIL host run assert nothing** | high | **recorded** — `FB2-REV-FND-000042`, against the SIL run rather than hidden by it |
| **`FB2-SW-IFS-000007` records the `FAS_DisableInterrupts` implementation at `fassert.h:112`, which is a doc-comment line; the pragma is at 116 and the declaration at 117** | medium | **open, not repaired.** `FB2-REV-FND-000193`, raised 2026-10-04. 1 wrong structured line reference out of 61 across the 16 interface specifications; the other 60 are exact. Four prose references in the same record carry the same wrong line. Repairing it is the record owner's edit, not a reviewer's. |
| **Same record asserts the pragma is both "on the line above" the declaration at 117 and "at L112"** | low | **open.** `FB2-REV-FND-000194`. An absolute and a relative claim for one construct, the absolute one wrong; correcting the number alone does not resolve the contradiction. |
| **`FB2-SW-IFS-000007` grounds its assembler-boundary claim in a doc comment naming a path that does not exist at the pinned commit** | low | **open, referred.** `FB2-REV-FND-000195`. The comment names `src\os\freertos\portable\ccs\arm_cortex-r5\portasm.asm`; the real file at `308028fb` is `src/os/freertos/freertos/portable/ccs/…` (extra `freertos` segment), and the routine *is* locatable there at line 313. The record makes no false statement, so there is nothing to correct — what is missing is the recorded discrepancy. |
| **`FB2-SW-IFS-000011` names the shared id `FB2-SW-DSN-000002` without a profile qualifier** | low | **accepted, conformant.** `FB2-REV-FND-000196`. Not a violation under the amended rule; the only one of the 16 that exhibits reference ambiguity. Reported by `unqualified_reference_ambiguity`, not gated. |
| **10 `reviewed_by` links attributed to the wrong review** | medium | **closed 2026-10-04.** `reviewed_by_attribution_agrees_per_review` was **false**: 10 links ran from `FB2-REV-000013`, which does not claim those artefacts, while `FB2-REV-000015` claimed them in `reviewed_ids`. The corpus-wide union was equal, so the weaker field never saw it. Source endpoints corrected, previous source and rationale preserved on each link. Now **true**. |
| `feature-inventory.json` `summary.total_features` says 20, holds 22 | low | accepted, reported; the tool counts records and reports 22 |
| FSRs carry no `fault_reaction` field | medium | findings open; schema change needed |
| Security requirements have no verification link in either direction | high | `FB2-REV-FND-000041`, open; the measures now exist but the executions are blocked |
| ASIL assignment with no justification | medium | open on `FB2-SAF-SGO-000001`; needs an engineering determination, not a corpus edit |
| `verifies`-direction rule fires on correctly verified requirements | medium | not resolved by design; convention decision owed |
| Link-registry layout: `corpus/synthetic_reference/.../links-cell-voltage.json` duplicates 51 of the 195 links in the canonical registry | low | accepted, reported; de-duplicated by the tool. **The sibling `links-concept-lifecycle.json` (177 links) is NOT a duplicate** — it is the only copy of the concept-lifecycle links and is load-bearing. |

---

## Reports

| Report | Description |
|--------|-------------|
| `reports/final-acceptance-report.md` + `.json` | All gates, 15 dimensions, 5 walkthroughs, final status |
| `reports/coverage-report.md` + `.json` | Population, three-count explanation, census, gaps |
| `reports/standards-mapping-report.md` | ISO part and ASPICE process dispositions, 16 corrections |
| `reports/traceability-report.md` | Link statistics, direction convention, worked chains |
| `reports/consistency-report.md` | 10 check categories, 4 finding families, structure defects |
| `reports/review-summary.md` | Review coverage, types, findings, limitations |
| `reports/source-vs-synthetic-gap-report.md` | `as_is` vs `synthetic_reference` gaps by category |
| `reports/verification-evidence-report.md` | Both macOS host runs: 313 SIL targets, and the 5 failures root-caused |
| `reports/e2e-engineering-document.html` | Single-file HTML deliverable; generated, tracked, guard-audited |
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
