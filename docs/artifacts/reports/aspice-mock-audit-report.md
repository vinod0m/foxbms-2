# foxBMS 2 — ASPICE PAM 4.1 Mock Audit Report

**Audit date:** 2026-09-20 — **verdicts and counts refreshed 2026-10-01 from a live `corpus.py` run**
**Baseline:** BAS-REF-001 — source pinned to commit `308028fb` (tag `v1.11.0`); corpus authored at `2a408d5`. The original audit also cited corpus branch `foxbms-2-synthetic-data` at `83d2381a`, which is neither of those two and is not the tree these figures come from.
**Reference model:** Automotive SPICE PAM 4.1 (process reference: SYS.1–SYS.5, SWE.1–SWE.6, HWE.1–HWE.4, SUP, MAN, VAL, PIM, REU)
**Audited corpus (live, 2026-10-01):** **286** validated artefact files, **263** unique `(profile, id)` records, **489** links (0 dangling), **33** test measures, **44** execution records, 4 findings / **0** errors (`corpus.py validate`/`check` PASSED, **selftest 48/48**)
**Audit scope:** document/work-product level — this is a MOCK audit of the artefact corpus, not a process-capability assessment of an organization. No live interviews, no tool qualification, no assessor judgment.

> **This report's verdicts were wrong and are corrected here.** The 2026-09-20
> version marked **14 of 15** process groups `PASS` at document level. The
> 2026-10-01 substantive audit (`CORR-COV-016`), which derived every process's
> backing set from each artefact's own `standards_mappings[].reference` rather
> than from the presence of a document, demoted **23 of 28** applicable ASPICE
> processes and **8 of 10** applicable ISO parts. Only **4 ASPICE processes are
> `mapped`** and **no ISO part is**. Three processes — `SWE.3`, `HWE.3`,
> `HWE.4` — have **no backing artefact at all**. "A document exists that names the
> process" was the standard this report applied, and it is not a sufficient one.

## 1. Audit Verdict Summary

| Assessment | Verdict |
|---|---|
| Work products present **and** carrying the engineering the process defines | **4 of 28** applicable ASPICE processes; **0 of 10** applicable ISO parts |
| Work products present but the activity not performed, or one expected family absent | **21** ASPICE processes `partially_mapped` |
| No backing artefact of any kind | **3** ASPICE processes `gap` (`SWE.3`, `HWE.3`, `HWE.4`) |
| Work products recorded blocked with disposition | ⚠️ 23 of 44 execution records are `execution_kind: none` / `outcome: blocked` |
| Fabricated evidence | ⚠️ **6 `synthetic_fixture` executions record `pass` with no retained evidence** — the fixture never existed (`evidence/synthetic-fixtures/` holds no fixture artefact, only a `MANIFEST.md` documenting the gap — and that file cites finding `FB2-REV-FND-000143`, which does not exist in the corpus). Not fabrication of a number, but an unverifiable pass. |
| Process capability (PA levels) | ⚠️ synthetic examples only — no real organizational capability, no assessor evidence |

**Overall: NOT AUDIT-READY for a real ASPICE assessment, by a wider margin than
the 2026-09-20 version stated.** Document presence is not process coverage;
21 of 28 processes have at least one expected artefact family with no record,
and 3 have no backing record at all.

## 2. Per-Process Audit (SYS flow)

| Process | Required work products (BP-level) | Corpus state | Verdict |
|---|---|---|---|
| SYS.1 Requirements Elicitation | Stakeholder needs, use cases, **operational scenarios** | 5 stakeholder needs + 4 use cases + item definition exist. Each need carries `is_a_real_elicitation = false`; no workshop/interview/questionnaire was held. **No operational-scenario record exists** — the 5 `SCN-*` records are mutation/change-lifecycle harness scenarios | ⚠️ **PARTIAL** — declared, not elicited; one family absent |
| SYS.2 System Requirements Analysis | System reqs spec, **modes/states**, **interface reqs** | 8 system requirement records (`FB2-SYS-SYR-000001..000008`) with statement, rationale, acceptance criteria. **No system modes/states record exists.** **No system-level interface requirement record exists.** The requirements are `origin: derived` and back-inferred from code | ⚠️ **PARTIAL** — two families absent; analysis not evidenced |
| SYS.3 System Architectural Design | **System architecture**, HW/SW allocation, HSI | `FB2-SYS-HSI-000001` is `design_level: interface_specification` — one interface, not the architecture. HW/SW allocation exists only inside `FB2-SAF-FSC-000001` and `FB2-SAF-TSC-000001`. **No system-architecture record exists in either profile** | ⚠️ **PARTIAL** — architecture absent |
| SYS.4 System Integration + Integration Test | Integration plan, integration test spec, integration test results | Plan: doc 07 ✅; spec: `FB2-VER-TMS-000007` ✅; results: `FB2-VER-EXE-000007` recorded `blocked` ⚠️ | ⚠️ PARTIAL (results blocked, not fabricated) |
| SYS.5 System Qualification Test | Qualification plan, spec, results | Spec: `FB2-VER-TMS-000008`/`000011` ✅; results: `FB2-VER-EXE-000008`/`000011` recorded `blocked` ⚠️ | ⚠️ PARTIAL (results blocked, not fabricated) |

## 3. Per-Process Audit (SWE flow)

| Process | Required work products | Corpus state | Verdict |
|---|---|---|---|
| SWE.1 Software Requirements Analysis | SW reqs spec, **interface reqs** | `FB2-SW-SWR-000001..000003` in both profiles carry statement, rationale, acceptance criteria, ASIL allocation scope and conditions/modes. **No software interface requirement record exists** — the requirements state database-publish targets but there is no interface-requirement artefact. The requirements are `origin: derived` and back-inferred from the implementation, which is the opposite direction to requirements analysis | ⚠️ **PARTIAL** — specification present, interface requirements absent, analysis not evidenced |
| SWE.2 Software Architectural Design | SW arch, component designs, **interface specifications** | `FB2-SW-DSN-000001..000003` carry `design_level: architecture`, responsibilities, decomposition, a behaviour model with guards, budgets, failure response, recorded decisions and `implementation_mapping`. **The `interfaces` field is a signal table (name/type/unit/range/rate), not an interface specification** — no protocol, ownership or agreement, and no separate interface-specification record exists | ⚠️ **PARTIAL** — architecture present, interface specifications absent |
| SWE.3 Detailed Design + Unit Construction | Detailed design, source code, unit test specs | **Zero corpus artefacts reference SWE.3 in any `standards_mappings[].reference` string.** The nearest content is `06-detailed-design-specification.md` and the `implementation_mapping` on the 6 `design` records (9 distinct source files, 24 symbol entries), which name **SWE.2**, not SWE.3. The repository holds **318** `test_*.c` files under `tests/`; the SIL harness attempted **313** of them. No source-code record and no unit-test specification exists | ❌ **GAP** — recorded `mapped` until 2026-10-01; see `CORR-COV-016` |
| SWE.4 Software Unit Verification | Unit verification measures, specs, results | **33** measures carry SWE.4 in their mappings. **15 real host-run executions** exist (`actual_host_run`), carrying environment, input/output hashes, per-test log digests and assertion counts. But the upstream Unity/CMock unit suite was never executed by this corpus, and **6 `synthetic_fixture` executions record `pass` with NO retained evidence** — `evidence/synthetic-fixtures/` holds no fixture artefact, only a `MANIFEST.md` documenting the gap. No unit-test specification record exists | ⚠️ **PARTIAL** — no specification; the only results are the SIL host harness, and 6 of them are unverifiable |
| SWE.5 Software Integration + Integration Test | Integration **plan**, integration spec, results | `FB2-VER-TMS-000007` is a planning **stub**, not a specification. **No SW integration plan record exists** — the earlier claim that the approach is "documented (database/task model, build system)" rests on `FB2-SW-DSN-000001..000003`, which belong to SWE.2. `FB2-VER-EXE-000007` is `execution_kind: none` / `outcome: blocked` | ⚠️ **PARTIAL** — all three families absent or blocked |
| SWE.6 Software Qualification Test | Qualification **plan**, spec, results | `FB2-VER-TMS-000008` is a stub, plus five substantive network-security measures `FB2-VER-TMS-000016..000020` that state what a passing run would have to observe and what the oracle cannot see. **No qualification plan or specification exists**; `FB2-VER-EXE-000008` is `none`/`blocked` | ⚠️ **PARTIAL** — plan and spec absent, no result |

## 4. Per-Process Audit (HWE / VAL / supporting)

| Process | Required work products | Corpus state | Verdict |
|---|---|---|---|
| HWE.1 HW Requirements Analysis | HW reqs spec, **interface reqs** | 7 hardware requirement records with statement, acceptance criteria and safety allocation. **No hardware interface requirement record exists** — the only interface specification is a system-domain record. Requirements were derived from design packages, not analysed from higher-level requirements | ⚠️ **PARTIAL** — interface reqs absent |
| HWE.2 HW Architectural Design | HW architecture, block diagrams, interface schematics | **No hardware architecture record, no block diagram, no interface schematic exists in this corpus.** The schematic sources are Altium `.SchDoc` files in the **separate `foxBMS2_hw` repository**; anchors `FB2-SRC-HW-000001..000003` read `content_hash: unresolved`. **10 non-review records cite those anchors** | ⚠️ **PARTIAL** — all three families absent; external-repository limitation |
| HWE.3 HW Detailed Design | Schematics, PCB layout, BOM, component specs | **Zero corpus artefacts reference HWE.3 in any `standards_mappings[].reference` string.** No schematic, PCB layout, BOM or component specification exists. The superseded text read `partially_mapped - design packages referenced; detailed analysis limited by CAD format` and named no record | ❌ **GAP** |
| HWE.4 HW Integration + Test | HW integration plan, test spec, results | **Zero corpus artefacts reference HWE.4.** No hardware integration plan, no hardware test specification and no hardware test result exists in either profile. The earlier text claimed "synthetic test specs created" — those test measures do not name HWE.4 and there is no hardware integration or test record at all | ❌ **GAP** |
| VAL.1 Validation | Validation **plan**, spec, **results** | 4 substantive measures `FB2-VER-TMS-000012..000015` (no false reaction over a full charge; driver-facing outcome under traction; degraded operation usable and announced; technician commissioning without incorrect energising), each validating a need or use case against a named scenario, each stating its oracle basis **and what the oracle cannot see**, plus the `FB2-VER-TMS-000009` stub. **No validation plan exists and no validation was executed** — every execution is `none`/`blocked` | ⚠️ **PARTIAL** — plan absent, zero results |
| SUP.1 Quality Assurance | QA plan, review records, **audit records** | `FB2-SUP-QAP-000001` defines the process; **15** review records carry **49** embedded findings; coverage **144/224 = 64%**. **No audit record exists**, and the record's own `accountable_role.independence` field states the independence is **not** achieved — every review is an automated review by the runtime that wrote the artefacts | ⚠️ **PARTIAL** — no audit; independence not achieved |
| SUP.8 Configuration Management | CM plan, config items, baselines, **change control** | `FB2-SUP-CFM-000001` defines the process and establishes BAS-REF-001 rev 2. **Change control is deferred to `FB2-SUP-CHC-000001`** — this record discharges none of its own. **Status accounting is not performed:** measured, 326 of 489 links carry a stale endpoint revision and all 489 are marked `change_suspect_status: false` | ⚠️ **PARTIAL** — change control deferred; currency not enforced |
| SUP.9 Problem Resolution | Problem reports, resolution records, **trends** | **13** `finding` records mapped to SUP.9, each with root cause and resolution; **42** finding artefacts exist in total. **No trend analysis exists** — `FB2-SUP-PRB-000001` states in its own `limitations`: *"The trend this process is supposed to produce cannot be produced from a corpus of one intake cycle."* | ⚠️ **PARTIAL** — trend absent |
| SUP.10 Change Request Management | Change requests, impact analyses, decisions | 3 full change records (32–41 KB each) with trigger, impact analysis + rationale, decision, new_revisions, suspect_links, required_updates and reverification selection; SCN-CHG-001..003 content-validate 19/19 checks each. **All three are fictional changes to the hypothetical project; none was raised against the real product** | ⚠️ **PARTIAL** — families present, product untouched |
| SUP.11 Traceability Management | Traceability matrix, links, coverage reports | **489** links / **0 dangling**, `exports/trace-matrix.csv`, coverage reports, chain maps. **Link currency is not maintained:** 326 of 489 links record a stale endpoint revision and **none** is marked suspect; `change_suspect_status` is a blanket `false`, not a derived value | ⚠️ **PARTIAL** — resolution verified, currency not |
| MAN.3 Project Management | Project plan, schedule, resource plan, progress reports | `FB2-MAN-PLN-000001` (`project_plan`, 24,465 B): six-phase lifecycle, eight-package WBS with accountable roles, dated schedule with critical path and float, six gates with entry/exit criteria, resource assignment, five progress records, three communication records. All four families present | ✅ **MAPPED** (the only management process that survives the audit) |
| MAN.5 Risk Management | Risk register, analyses, mitigations | `FB2-MAN-RSK-000001` (`risk_register`): eight entries across eight categories, each with ordinal-pair exposure on a stated scale, an owner, dated mitigation actions and a residual exposure with its argument; two residuals equal their inherent because no action was taken, recorded rather than presented as progress | ✅ **MAPPED** |
| MAN.6 Measurement | Measurement plan, metrics definitions, measurement results | `FB2-MAN-MSM-000001` (`measurement_plan`): named population with exclusions and known bias, six collection rules with cadence and collector role, six metrics each with definition/unit/formula/baseline/target/control limit/action on breach, analysis method requiring every charted point to be an observation record, six observations with derivations | ✅ **MAPPED** |
| PIM.3 Process Improvement | Improvement proposals, improvement records, effectiveness evaluation | `FB2-PIM-IMP-000001`/`000002` (`process_improvement`): baseline, hypothesis with falsification condition, the change made, effectiveness evaluation with the arithmetic written out, counter-evidence and a verdict. Verdicts: one `partially_effective`, one `insufficient_evidence`, **none `effective`** — left as it is | ✅ **MAPPED** |
| REU.2 Reuse Program Management | Reuse strategy, **reuse assessments**, records | `FB2-SUP-RUS-000001`: reuse inventory of four elements with upstream, version and modification state. **No reuse assessment is completed for any element** — the record states it, and states the independence `cannot hold` for the modified vendor drivers | ⚠️ **PARTIAL** — assessments absent |
| MLE.1–MLE.4 Machine Learning | — | Explicit non-applicability artifact (`APP-MLE-ALL`) | ✅ N/A justified |

## 5. Audit Findings

| # | Finding | Severity | Evidence |
|---|---|---|---|
| A-1 | **23 of 44 execution records are `blocked`** (`outcome: blocked`, `execution_kind: none`): 22 `synthetic_reference` + 1 `as_is`. Unblocking conditions are documented on each | Medium (audit-readiness) | `FB2-VER-EXE-000007..000011` and the 22 synthetic ones |
| A-2 | **`SWE.3` recorded `mapped` with zero referencing artefacts.** The worst case in the file | **High** | 0 occurrences of `SWE.3` across the 106 distinct `standards_mappings[].reference` strings; `CORR-COV-016` |
| A-3 | **6 `synthetic_fixture` executions record `outcome: pass` with NO retained evidence.** `docs/artifacts/evidence/synthetic-fixtures/` holds **no fixture artefact** — only a hand-written `MANIFEST.md` stating the fixture was never captured and that the file "must never be counted as captured evidence for any test". **That file records the gap against `FB2-REV-FND-000143`, and no such record exists**: 42 `finding` records exist, numbered to `FB2-REV-FND-000042`. The gap is in no canonical record | **High** | `FB2-VER-EXE-000001..000006`, profile `synthetic_reference` |
| A-4 | **326 of 489 links carry a stale endpoint revision and all 489 are marked `change_suspect_status: false`** | **High** | measured over `load_links`; `FB2-SUP-CFM-000001` `limitations` says the same |
| A-5 | **10 records' hardware provenance rests on an external repository.** Altium `.SchDoc` files in `foxBMS2_hw`, `content_hash: unresolved`, `hash_status: external_design_file_unverifiable_from_this_repository` | Medium | anchors `FB2-SRC-HW-000001..000003` |
| A-6 | **4 anchors have no machine-checkable symbol** (whole `rtc.c` module body, the FreeRTOS markdown README, `requirements.txt`, a licence header). Content hashes and line ranges verified; symbol occurrence is not | Low (documented) | `symbol_unverifiable_prose` in the provenance tally |
| A-7 | **5 execution records carry an `output_hashes` digest resolving into the gitignored `.work/` tree** rather than the evidence file they name | Medium | `FB2-VER-EXE-000008..000012`; `FB2-VER-EXE-000015` names eight `.work/` paths in `logs[]` |
| A-8 | **Process capability examples are synthetic** — no real organizational capability, no assessor evidence, no tool qualification | High (for a real audit) | `coverage-plan.json` `capability_dimension` note; `CORR-COV-015` sets `level_1_performed` to `not_met` |
| A-9 | **Automated review coverage 64%** (144/224). **80 distinct IDs are unreviewed**, and the unreviewed set includes every `post_development_record`, `process_record`, `measurement_plan`, `risk_register`, `project_plan`, `stakeholder_need`, `use_case` and `safety_concept` record — the records the process claims rest on | Medium | `corpus.py coverage`; `reviews/records/*.json` |
| A-10 | **Human approval `pending` and `production_authorized: false` on all 263 records** — no human has approved anything | High (for a real audit) | `corpus.py coverage` → `human_approval 0/263`, `production_authorization 0/263` |
| A-11 | **4 findings, 0 errors from validation** — 3 anchors whose design files are external and cannot be hashed, plus 4 anchors recorded as prose-only | Low | provenance tally |
| A-12 | **`render_e2e_html.py --check` exits 1** on 14 `implementation` records with no owning section in the renderer | Medium (tool-side) | renderer output |

**No critical finding.** That is the only unambiguously good result in this
table, and it is reported as a count, not as a claim that nothing serious
remains — A-2 through A-4 are `high`.

## 6. What a Real ASPICE Assessment Would Require (gap to audit-ready)

1. **Real execution evidence** — run the blocked tests on a supported environment (Linux/Windows + HALCoGen codegen + gdb for unit; harnesses for integration/component; target + HIL bench for SYS.5/HWE.4; validation environment for VAL.1), with retained logs and coverage hashes.
2. **Independent human review** — assessor-qualified review records with human sign-off (`human_approval_status: approved`).
3. **Process capability assessment** — real PA1.1–PA2.2 evidence per process (interviews, work-product audits, not synthetic examples).
4. **Tool qualification** — qualification of the Ceedling/Unity/waf toolchain per ASPICE SWE.5/SYS.4 expectations.
5. **HWE.2/HWE.3 depth** — real hardware architecture/detailed design analysis of the CAD packages.
6. **FTTI budget closure in as_is** — resolve the 135 ms > 100 ms violation (synthetic resolves it via independent monitor; as_is remains as-is platform fact).

## 7. Audit Method and Limits

- Work-product presence verified by `corpus.py validate` (**286** artefact files, 4 findings, 0 errors), `check` (acceptance suite PASSED, 8/8 stages, **14 gate lines**), `selftest` (**48/48 PASS**), and direct reads of every artefact family referenced above.
- **Verdicts are no longer document-level presence.** The 2026-09-20 standard was "PASS = required work products exist with typed traceability", and that standard passed processes whose expected artefact families do not exist and whose activities were never performed. It is replaced by: **MAPPED** = a backing record carries the engineering the process defines and every family in its `expected_artifacts` is represented; **PARTIAL** = at least one family is represented and at least one is not, or the activity was not performed, with the shortfall named; **GAP** = no backing artefact of any kind.
- Backing sets are derived from each artefact's **own** `standards_mappings[].reference`, not from the disposition text. This is what surfaced `SWE.3`.
- This is a MOCK audit. No live process interviews, no organizational assessment, no normative ASPICE text reproduction — the reference model is applied at work-product level only. **No verdict here claims process capability, conformity, or ASPICE capability at any level.**

---

*Generated: 2026-09-20; verdicts, counts and the audit-findings table refreshed 2026-10-01 from a live `corpus.py` run and the `CORR-COV-016` substantive audit — hand-maintained mock audit of the machine-verifiable corpus.*
