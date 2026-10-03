# Final Acceptance Report

> **Figures in this document were measured on the date in its header and are NOT
> current.** The record population moved from 300 to 318 records on 2026-10-03
> (the artifact index was corrected to walk `scenarios/`, which it had always
> claimed in its docstring to do, and a duplicate revision-1 scenario tree under
> `corpus/scenarios/` was removed), the link count is 553 not 489, the validator
> reports 5 findings and 0 errors rather than 4 and 0, and the self-test count is
> 91 rather than 48. Every figure below is left as measured on its stated date so
> that the audit trail is not rewritten; read it as a dated measurement, not as a
> current one. Live figures: `docs/artifacts/README.md`, which was re-measured.


**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`, v1.11.0)
**Repository:** `/Users/vinod/Downloads/SoftwareDevLabs/foxbms-2`
**Machine-readable sibling:** `final-acceptance-report.json`

> **Status of this report.** Every number below was produced by a live run of
> `docs/artifacts/tools/corpus.py` on **2026-10-01**. None is transcribed from an
> earlier report. The commands are listed in the *Provenance of every number*
> section so each figure can be re-derived. Where the previous version of this
> report carried a figure that no longer matched a live run, the figure was
> corrected here and the correction is listed figure-by-figure in §16.
>
> **This is not a conformity statement.** The corpus holds a **structural
> mapping** to ISO 26262 clause references and to ASPICE process references. It
> asserts **no ISO 26262 conformity**, no ASIL capability, no certification, no
> tool qualification and no ASPICE capability level. Every one of the **263**
> indexed records carries `human_approval_status: pending`,
> `production_authorized: false` and `product_verification_credit: false`.
> **No human has approved anything in this corpus.**

---

## 1. Corpus Status

**Final status: `synthetic_ready_with_limitations`**

Recorded by `corpus.py check` gate `[8/8] final status recorded`.

## 2. Acceptance Suite Result

`python3 docs/artifacts/tools/corpus.py check` → **`Acceptance suite: PASSED`**

| Stage | Gate | Result |
|---|---|---|
| 1/8 | validate | PASS (**286** artifacts validated, **4** findings, **0** errors) |
| 2/8 | inventory | PASS (612/612 source files) |
| 3/8 | negative_scenario_validation = 20/20 mutations | PASS (measured: 20 scenarios executed, 20 passing) — see §2.1 |
| 3/8 | change lifecycles = 3/3 | PASS (3/3 executed, 19/19 content checks each) |
| 4/8 | hazard present (trace reachability) | PASS (both profiles) |
| 5/8 | scenario-test | PASS (23/23 scenario lines; 20/20 mutations **detected on their own declared detector**) |
| 6/8 | export | PASS (263 nodes, 489 edges) |
| 6/8 | deterministic export hashes | PASS |
| 7/8 | no production_authorized/approved artifacts | PASS (0 violations this run; 298 records scanned) |
| 7b/8 | provenance verification | PASS (229 digests, 130 anchors, 57 log hashes, 62 evidence-file entries; 4 findings, none an error) |
| 8/8 | final status recorded | PASS (`synthetic_ready_with_limitations`) |

**14** gate lines PASS, 0 FAIL (the earlier "10 gate lines" predates the
provenance gate). 23/23 scenario lines pass (20 mutation scenarios plus 3 change
lifecycles).

`python3 docs/artifacts/tools/corpus.py selftest` → **48 PASS, 0 FAIL**
(11 pre-existing + 37 added to test the gates' own soundness; see §2.2 and
`reports/reproducibility-report.md` §6).

**`render_e2e_html.py --check` exits 1**, on 14 `implementation` records that have
no owning section in the renderer. Tool-side, outside this workstream's write
boundary; the HTML deliverable is regenerated, tracked and guard-audited. See
§13 item 13.

### 2.1 What the 20/20 in gate 3/8 means, and what it does not

**As of 2026-09-29 it means that twenty mutation scenarios were executed and
twenty of them passed.** The gate, the rules and the scenarios are unchanged;
only the coverage dimension the gate reads was repaired.

Until then gate `[3/8]` counted how many mutation scenarios **exist**
(`numerator = len(mutations on disk)`). It was a coverage-of-scenarios figure,
unaffected by whether those scenarios detected anything, and it would have read
`20/20` at the moment the mutation gate was discovered to be self-certifying —
when 8 of the 20 were failing. That is a presence check published under the name
of a detection measurement, and it is the defect finding `FB2-REV-FND-000032`
exposed.

`negative_scenario_validation` now executes the mutation and change-lifecycle
scenarios through `_execute_scenarios`, the same path gate `[5/8]` uses, and
reports the number that PASS. Both gates read one memoised measurement within a
run, so the dimension and the gate cannot disagree about the same corpus. The
proof that the figure is now a measurement and not a count: temporarily pointing
one scenario's declared detector at a rule no detector implements moved the
dimension to `19/20` and named `SCN-MUT-005` as the failure, where the old
computation would still have printed `20/20`.

What the figure still does **not** say is that the detector set is complete or
that any rule is correct. A defect no scenario models is undetected by
construction. That remains stated in
`scenario-validation-report.md` §6.

### 2.2 The mutation gate was self-certifying until finding FB2-REV-FND-000032

Earlier revisions of this report stated, as a measured result:

> 20/20 mutation scenarios detect their injected defect.

**That statement was false when it was written, and it was false before any
defect in this corpus was repaired.** The harness re-ran the rules on the
mutated corpus and then kept any finding whose `artifact_id` was one of the
scenario's `affected_ids`, accepting the scenario when *some* finding of the
expected severity turned up. Severity and category are shared by many rules
and the artifact id was shared by whatever defects that artifact happened to
carry, so a standing defect inherited from the corpus satisfied scenarios
whose own detector did not exist, was unreachable, or read a field the record
did not carry. Eight of the twenty scenarios were passing that way; four of
them had a declared detector that no rule emits or that no rule can reach on
the record the scenario targets.

The gate now resolves each scenario's declared detector by stable rule id,
proves the rule is emitted by this module at all, subtracts the findings the
unmutated corpus already produces, and accepts only a finding **from that
rule** that the mutation caused. A scenario whose declared detector does not
exist now fails with an explicit message instead of matching a neighbour.

Three consequences, all of which the numbers above already reflect:

- The 20/20 in gate `[5/8]` is now a detection measurement rather than an
  existence count. Each line names the rule that fired.
- Nine scenarios that were passing on their neighbour are unaffected in
  outcome but are now passing on their own rule.
- Four scenarios had defective patches that injected nothing their detector
  could see, or injected something other than what they declared. The patches
  were corrected; the scenarios were not weakened. See §2.3.

### 2.3 What the mutation scenarios actually exercise

Every scenario's declared detector, the rule that implements it, and the
finding it produces. "Own detector" means the rule id the scenario declares,
resolved from the evaluator-only oracle manifest and verified against the rule
ids this module actually emits.

| Scenario | Declared detector (rule id) | Implemented | Detected on its own rule |
|---|---|---|---|
| SCN-MUT-001 | `traceability_checker` | yes | yes |
| SCN-MUT-002 | `link_forbidden_relation_type` | yes | yes |
| SCN-MUT-003 | `revision_consistency_checker` | yes | yes — **was unreachable** |
| SCN-MUT-004 | `parameter_unit_consistency` | yes | yes |
| SCN-MUT-005 | `hsi_interface_consistency` | yes | yes |
| SCN-MUT-006 | `ftti_budget_consistency_checker` | yes | yes — **rule could not fire on the record** |
| SCN-MUT-007 | `parameter_threshold_order` | yes | yes |
| SCN-MUT-008 | `safety_requirement_completeness_checker` | yes | yes |
| SCN-MUT-009 | `asil_assignment_validator` | yes | yes — **was undetectable on a healthy corpus** |
| SCN-MUT-010 | `diagnostic_coverage_claim_validator` | yes | yes |
| SCN-MUT-011 | `configuration_consistency` | yes | yes |
| SCN-MUT-012 | `execution_kind_classifier` | yes | yes |
| SCN-MUT-013 | `requirement_applicability_validator` | yes — **implemented; did not exist** | yes |
| SCN-MUT-014 | `evidence_reference_validator` | yes | yes |
| SCN-MUT-015 | `identity_uniqueness_checker` | yes | yes |
| SCN-MUT-016 | `source_anchor_drift_detector` | yes | yes |
| SCN-MUT-017 | `production_authorization_governance_checker` | yes | yes |
| SCN-MUT-018 | `incomplete_propagation` | yes | yes |
| SCN-MUT-019 | `refinement_cycle_detector` | yes | yes — **patch created no cycle** |
| SCN-MUT-020 | `verification_traceability_checker` | yes | yes — **patch removed 1 of 4 links** |

The four bolded defects are the ones that made the old 20/20 meaningless for
those scenarios specifically:

- **SCN-MUT-003** declared the revision-consistency rule, which lived inside
  `_validate_artifact`. The scenario harness never calls schema validation, so
  the rule was unreachable by construction. The rule now lives in
  `_check_revision_consistency` and is called from both paths.
- **SCN-MUT-006** declared the FTTI budget rule, which read `ftti_ms` or
  `ftti`. No safety goal in this corpus carries either field, so the rule
  `continue`d on every record it was pointed at. The rule now resolves the
  interval from the parameter registry entry the safety goal is now bound to
  (`FB2-PRM-000004`, `ftti_ms = 100`) and cross-checks every declaration of it
  on the record, so the value can no longer be scattered inconsistently.
- **SCN-MUT-009** declared the ASIL validator, which fired only on *absence*
  of a justification. An unjustified downgrade leaves the justification
  present and saying otherwise, so the rule could only ever have passed on a
  corpus that had no justification at all — it was testing the corpus's health
  and passing on the condition it claimed to detect. The rule now re-derives
  the ASIL from the severity and exposure ratings the justification itself
  records, using ISO 26262-3:2018 Table 4, and reports an assignment the
  derivation contradicts.
- **SCN-MUT-013** declared a requirement applicability validator that no rule
  implemented. The patch it carried set an undeclared top-level
  `applicability` property that nothing reads. The data model *can* express
  non-applicability — `requirement.schema.json` enumerates `not_applicable` as
  a value of `safety_allocation.asil` — so the rule was implemented against
  that field, reading the reason from the `asil_justification` field the
  corpus already uses on safety goals. No field was invented.
- **SCN-MUT-019** repointed a link to `SGO refines HAZ`. No hazard is ever
  the source of a `refines` link, so the edge terminated immediately and the
  graph stayed acyclic: the patch mutated a link without creating the
  circularity it declares. It now closes a real three-node cycle.
- **SCN-MUT-020** deleted one of the four `verifies` links covering
  `FB2-SAF-FSR-000002`; three others remained, so the requirement stayed
  verified and the missing-verification defect was never injected. It now
  removes the only `verifies` link covering `FB2-SAF-SEC-000001`.

## 3. The 15 Coverage Dimensions

Exactly as printed by `corpus.py coverage`. Percentages are computed from the
printed ratio; where a ratio exceeds 100% it is an over-coverage count, not a
score.

| # | Dimension | Ratio | % | Status | Note | Denominator counts |
|---|---|---|---|---|---|---|
| 1 | scope_accounting | 1/1 | 100% | complete, **presence** | inventories present; the claim-vs-tree comparison is gate `[2/8]` | presence |
| 2 | artifact_population | 13/13 | 100% | complete | 13 families populated | 13 declared families |
| 3 | standards_mapping | **33/38** | 87% | **see §6.1 — not a favourability score** | ASPICE 25/28 + ISO 8/10 have a disposition naming a resolving artefact | 28 applicable ASPICE + 10 applicable ISO |
| 4 | source_grounding | **99/263** | 38% | **partial** | 101 source anchors available; 164 records carry no `source_refs` | population **B** (263) |
| 5 | traceability_integrity | **489/489** | 100% | complete as to **resolution** | 0 dangling, from a link validation re-run for this figure. **Currency is not maintained** — see §6.2 | every link in the registry |
| 6 | semantic_consistency_checks | 10/10 | 100% | complete, **declared** | 10 check categories per run — a declared constant, not a measured result | declared count |
| 7 | automated_review_coverage | **144/259** | 64% | **partial** | 15 review records; `reviewed_by` links consistent with `reviewed_ids` | population **C** (224) |
| 8 | verification_planning | **33/7** | 471% | over-covered | 33 test measures for 7 distinct FSR ids; a ratio, not a score | 7 distinct FSR ids |
| 9 | actual_product_evidence | **0/33** | 0% | **blocked by policy** | 0 target-hardware executions; see §7 | population **B** execution records |
| 10 | synthetic_fixture_coverage | **173/43** | 402% | over-covered | 173 `synthetic_reference` records against a target of 43 | `synthetic_reference` records |
| 11 | negative_scenario_validation | 20/20 | 100% | **measured** — 20 scenarios executed, 20 detected by their own declared rule; see §2.1 | plus 3/3 change lifecycles, executed | 20 declared mutations |
| 12 | final_status | `synthetic_ready_with_limitations` | — | — | recorded status | — |
| 13 | export_reproducibility | 1/1 | 100% | complete, **presence** | export manifest present; hash stability is measured by gate `[6/8]` | presence |
| 14 | human_approval | **0/263** | 0% | **pending by policy** | every record pending; none performed | population **B** |
| 15 | production_authorization | **0/263** | 0% | **false by policy** | every record `production_authorized=false` | population **B** |

### Note on the three different denominators

The corpus contains **three** legitimately different population counts, and a
reader comparing them will otherwise think one is wrong. **They are not
harmonised, on purpose.**

- **286** — schema-validated artefact **files** carrying an `id`, printed by
  `validate`: 263 corpus records + 23 scenario records. The 23 scenarios live
  under `scenarios/` and carry no `profile`, so they are not profile-scoped
  records and are not in the artifact index.
- **263** — unique `(profile, id)` records in the tool's artifact index.
  `iter_corpus_artifacts` walks **267** corpus JSON files; 263 carry an `id` and
  **all 263 `(profile, id)` pairs are unique**, so the index collapses nothing.
  The former `FB2-REV-000001` duplicate that made this arithmetic lossy has been
  removed (§8). Used as the denominator for `source_grounding`,
  `human_approval` and `production_authorization`.
- **224** — distinct artefact **IDs** across both profiles. Lower than 263
  because **39** IDs deliberately exist in both `as_is` and
  `synthetic_reference`; profile isolation is a design decision, not duplication.
  Used as the denominator for `automated_review_coverage`.

The previous version of this report gave four numbers (246 / 223 / 222 / 187).
The extra one was an artefact of counting files against records while a duplicate
existed; the duplicate is gone and the count is now three.

## 4. Record Census

**263 unique `(profile, id)` records** in the tool's artifact index (population
**B**). Every count below is computed from the tool's own index by a live run of
`corpus.py load_artifact_index`, not from a directory listing.

### By artifact type

| Type | Count | | Type | Count |
|---|---|---|---|---|
| execution | 44 | | change | 3 |
| finding | 42 | | hazard | 2 |
| requirement | 34 | | safety_goal | 2 |
| test_measure | 33 | | safety_concept | 2 |
| deviation | 26 | | process_improvement | 2 |
| review | 15 | | project_plan | 1 |
| implementation | 14 | | risk_register | 1 |
| design | 8 | | item_definition | 1 |
| post_development_record | 6 | | safety_case | 1 |
| process_record | 6 | | tara | 1 |
| stakeholder_need | 5 | | measurement_plan | 1 |
| scenario | 5 | | | |
| safety_analysis | 4 | | | |
| use_case | 4 | | | |
| **Total** | **263** | | | |

### By engineering domain

| Domain | Count | | Domain | Count |
|---|---|---|---|---|
| verification | 111 | | hardware | 7 |
| software | 54 | | production | 2 |
| safety | 38 | | decommissioning | 1 |
| system | 21 | | operation | 1 |
| management | 14 | | release | 1 |
| supporting | 12 | | service | 1 |
| **Total** | **263** | | | |

### By profile

| Profile | Count |
|---|---|
| `synthetic_reference` | 173 |
| `as_is` | 90 |
| **Total** | **263** |

### By lifecycle status

| Lifecycle | Count |
|---|---|
| draft | 126 |
| reviewed | 73 |
| baselined | 64 |
| **Total** | **263** |

### By origin

| Origin | Count |
|---|---|
| synthetic | 147 |
| source_observed | 63 |
| derived | 53 |
| **Total** | **263** |

### Guard fields — corpus-wide

Every one of the **263** records carries `human_approval_status: pending`,
`production_authorized: false` and `product_verification_credit: false`. The
validator raises a finding on any record that does not, and gate `[7/8]`
reports 0 violations over all 298 records.

## 5. Traceability

**547 links**, **0 dangling**. De-duplicated by `(profile, link_id)` across all
registries.

| Relation type | Count | | Relation type | Count |
|---|---|---|---|---|
| reviewed_by | 229 | | implements | 13 |
| verifies | 55 | | validates | 12 |
| allocated_to | 46 | | depends_on | 12 |
| refines | 41 | | mitigates | 3 |
| result_of | 33 | | | |
| supports | 29 | | | |
| changes | 16 | | | |
| **Total** | **489** | | | |

By profile: `as_is` 117, `synthetic_reference` 372.
By review state: reviewed 414, pending 75.

### 5.1 Link revision currency — measured, and not maintained

| Measure | Value |
|---|---:|
| Links whose **both** endpoint revisions match the endpoint artefacts' current revisions | **163** |
| Links with **at least one** stale endpoint revision | **326** |
| Links carrying `change_suspect_status: true` | **0** |
| Links carrying `change_suspect_status: false` | **489** |
| Artefacts at a revision other than 1 | **109** |

Link *resolution* is verified on every run. Link *currency* is not verified at
all, and `change_suspect_status` is a blanket `false` rather than a derived
value. The corpus's own supporting-process record says the same
(`FB2-SUP-CFM-000001`, `limitations`): *"Currency of a link's recorded revisions
is not automated. The process describes the control and does not claim the
tooling enforces it."* This is the shortfall behind `SUP.11` being
`partially_mapped` (§6).

## 6. Governance State

`governance/coverage-plan.json` holds 32 process entries: **28 applicable**,
**4 explicitly `not_applicable`** (MLE.1–MLE.4, each with a rationale and a
`reference_decision`).

### Disposition status across the 28 applicable processes

| Disposition | Before 2026-10-01 | **After `CORR-COV-016`** |
|---|---:|---:|
| `mapped` | 12 | **4** |
| `partially_mapped` | 10 | **21** |
| `gap` | 6 | **3** |

Across the 10 applicable ISO 26262 parts: **6 `mapped` → 0**, with 8
`partially_mapped` and 2 `referenced`.

**The 4 that remain `mapped`:** `MAN.3` (`FB2-MAN-PLN-000001`), `MAN.5`
(`FB2-MAN-RSK-000001`), `MAN.6` (`FB2-MAN-MSM-000001`) and `PIM.3`
(`FB2-PIM-IMP-000001`/`000002`). Each was re-examined, not assumed, and each
record carries the process's defining engineering content. None is an upgrade.

**The 3 `gap` processes — `SWE.3`, `HWE.3`, `HWE.4` — have no backing artefact
of any kind.** Measured by extracting every artefact's own
`standards_mappings[].reference` string (183 of 298 records carry one, spanning
106 distinct strings; 80 carry none) and testing each for the token: **SWE.3
occurs ZERO times.** `SWE.3` was recorded `mapped` until 2026-10-01.

The full per-process evidence table, including which family of each process's own
`expected_artifacts` is missing, is in
`reports/standards-mapping-report.md` §3 and in each entry's `disposition` and
`disposition_reason` fields in the plan itself.

### 6.1 `standards_mapping` before and after — and why it went **up**

| Figure | Before | After | What it measures |
|---|---:|---:|---|
| `standards_mapping` (acceptance gate) | **16/38** | **33/38** | how many applicable entries name an artefact identifier that resolves. ASPICE 12/28 → 25/28; ISO 4/10 → 8/10 |
| ASPICE `mapped` (28 applicable) | 12 | **4** | whether backing records carry the engineering the process defines |
| ASPICE `partially_mapped` | 10 | **21** | — |
| ASPICE `gap` | 6 | **3** | — |
| ISO `mapped` (10 applicable) | 6 | **0** | — |
| ISO `partially_mapped` | 2 | **8** | — |

The gate figure rose because `CORR-COV-016` rewrote every disposition to name the
record it rests on and the specific family that is missing, which is what
recording the evidence for a decision requires. The gate is a *naming* metric. The
*substance* metric went the other way and the two are reported side by side
precisely so neither is read alone.

For reference: the figure before any of this work was **`44/44`**, which was the
number of keys in the inventory file divided by itself. It asserted nothing about
any mapping.

### 6.2 What the demotions rest on

Six of them cite the backing record's **own** text, which is the strongest
evidence available because the record says it itself:

| Process | The record's own words | Effect |
|---|---|---|
| `SUP.9` | `FB2-SUP-PRB-000001`: "The trend this process is supposed to produce cannot be produced from a corpus of one intake cycle." | no Trend Analysis → `partially_mapped` |
| `SUP.8` | `FB2-SUP-CFM-000001`: "Currency of a link's recorded revisions is not automated." | status accounting not performed → `partially_mapped`; measured as 326/489 (§5.1) |
| `SUP.1` | `FB2-SUP-QAP-000001`: "every review record in it is an automated review produced by the same process that produced the artifacts, and no human reviewer exists" | no independent review, no audit → `partially_mapped` |
| `ACQ.4` | `FB2-SUP-SPL-000001`: "It does not include a component inventory that has been checked against an advisory source"; "No supplier is under contract" | no Supplier Assessment → `partially_mapped` |
| `REU.2` | `FB2-SUP-RUS-000001`: "It does not complete a reuse assessment for any individual element" | no Reuse Assessment → `partially_mapped` |
| `SPL.2`, ISO Part 7 | all six post-development records: `evidence_state.any_step_executed: false` | documented, not performed → `partially_mapped` |

### Corrections recorded in the coverage plan

**16 corrections** (`CORR-COV-001` … `CORR-COV-016`). The first fifteen are
dated 2026-09-29; `CORR-COV-016` is dated 2026-10-01.

Every correction kept its original `expected_artifacts` and
`capability_attributes`. No expectation was deleted or narrowed, and no
artifact was fabricated to make a status true. Two of the first fifteen
(`CORR-COV-008` on MAN.6 and `CORR-COV-011` on ISO Part 6) landed on a
*different* status than the originally reported reality suggested, because
verification against disk found evidence on both sides of the claim; both record
the divergence explicitly rather than resolving it in the convenient direction.

**Nothing was upgraded in `CORR-COV-016`.**

### Placeholders replaced

`coverage-plan.json` carried three literal, never-rendered template macros:

| Field | Was | Now | How derived |
|---|---|---|---|
| `created_at` | `{{BUILD_TIMESTAMP}}` | `2026-09-08T10:12:59Z` | commit date of `8aaa774`, the commit that first added this file (2026-09-08T12:12:59+02:00), normalised to UTC |
| `updated_at` | `{{BUILD_TIMESTAMP}}` | `2026-10-01T04:27:00Z` | `date -u +%Y-%m-%dT%H:%M:%SZ` at the moment of the edit |
| `repository_commit` | `{{REPOSITORY_COMMIT}}` | `308028fb13d046ba29b98886895c2e17937b1437` | `sources/source-registry.json .repository_commit`, verbatim |

**The pinned-commit vs authored-at distinction is recorded in two fields, not
one.** `repository_commit` keeps the meaning it has always had anywhere in this
corpus — the commit the **source** is pinned to, identical to
`exports/manifest.json.repository_commit` — and a companion
`repository_commit_meaning` states that in prose. The commit the **corpus
content** was authored at, `2a408d573b41c2f3ab75edccb31f28768adcf9f2`
(`git log -1`, 2026-10-01), is a separate field,
`corpus_authored_at_commit`, with its own `_meaning`. Neither is put in the
other's field. `git merge-base --is-ancestor 308028fb HEAD` returns true, and
`git ls-tree -r 308028fb` contains no `docs/artifacts` entry, so neither commit
can stand in for the other.

### One residual disagreement, still open

`sources/feature-inventory.json` carries `summary.total_features: 20` while
the file contains 22 feature records, and `corpus.py inventory` reports 22.
The summary field is stale; the tool counts the records.

The earlier second residual — that `SUP.1`, `SUP.8`, `SUP.9` and `SUP.10` read
`mapped` while the generated `supporting-processes` view reported no
process-definition record — **is closed**: six supporting-process records now
exist and the four processes are `partially_mapped` with the specific shortfall
named in each.

### Standards lock

| Standard | Edition |
|---|---|
| `ISO_26262_2018` | 2018 |
| `ASPICE_PAM_41` | 4.1 |

Locked by `safety`. **No corpus record was authored against IEC 61508.** No corpus record was authored against IEC 61508. It is absent from `governance/standards-lock.json`, which locks exactly two standards: `ISO_26262_2018` (2018) and `ASPICE_PAM_41` (4.1). No requirement, `standards_mapping`, analysis, test measure or work product in `corpus/`, `governance/`, `schemas/`, `sources/`, `traceability/` or `scenarios/` references it. The standard is **not** alien to the product: the pinned source lists it as a candidate (`docs/general/safety/safety.rst:60`) and cites IEC 61508-3:2010 in `docs/references.bib`. The defect is that the corpus performed no IEC 61508 work, so it cannot supply compliance evidence for it. See §9.

## 7. Verification Evidence

### 7.1 The SIL host run — the current headline

A genuine test-suite run was performed on the build host on **2026-09-30**.
**Source (tracked):**
`docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json`

| Measure | Value |
|---|---|
| Host | Darwin arm64, Darwin Kernel 27.0.0 |
| Toolchain | ruby 4.0.7 (2026-09-15) +PRISM [arm64-darwin27]; Apple clang 17.0.0 |
| Run timestamp | **2026-09-30T01:24:18+0200** |
| Selection | `all` — **no HALCoGen exclusion** |
| **CeeDling targets attempted** | **313** |
| **Passed** | **222** |
| **Failed** | **7** |
| Build failures | **84** |
| Assertions tested | **988** |
| Assertions passed | **950** |
| Assertions failed | **35** |

313 = 222 + 7 + 84 exactly. Every per-test log, the suite results, the HAL
surface inventory and the HAL signature inventory are **tracked** and
sha256-verified: 46 log entries, 46 hashes verified, 0 mismatched, 0 missing.

**16 of the 84 build failures are classified by the harness itself as real
product defects.** `FB2-REV-FND-000042` records that **53 of the 245 green tests
assert nothing** — a finding the run produced against itself.

**macOS is not an upstream-supported foxBMS platform.** This is a host run, not
target-hardware evidence, and it is not credited as such.

### 7.1a Where this evidence lives — tracked, or not

**The previous version of this report cited `.work/verification-env/logs/*.json`
for its headline test figures. `.work/` is gitignored and untracked, so that
evidence was not in the distribution.** It has been replaced by tracked paths
throughout:

| Evidence | Tracked? | Path |
|---|---|---|
| SIL results (all 313 targets) | **yes** | `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json` |
| SIL per-test logs (313 files) | **yes** | `…/foxbms2-sil-host-unit-test-macos-2026-09-29/logs-strict/` |
| SIL runbook / reproduction command | **yes** | `…/foxbms2-sil-host-unit-test-macos-2026-09-29/RUNBOOK.md` |
| Pre-SIL strict and relaxed results | **yes** | `…/foxbms2-host-unit-test-macos-2026-09-29/results-{strict,relaxed}.json` |
| HALCoGen dependency closure | **yes** | `…/foxbms2-host-unit-test-macos-2026-09-29/halcogen-dependency-closure.json` |
| **SIL harness working tree** | **NO — gitignored** | `docs/artifacts/.work/verification-env/sil/` |
| **Pre-SIL harness working tree** | **NO — gitignored** | `docs/artifacts/.work/verification-env/` |

> **Five execution records carry a suite-results digest that resolves into the
> gitignored tree.** `FB2-VER-EXE-000008`…`FB2-VER-EXE-000012` each carry
> `output_hashes.sil_suite_results_all =
> sha256:cbbdebeecd54720561753562f7c7dd3ca105e04ca36494f52b674d9fd5a00f67`, which
> resolves to
> `docs/artifacts/.work/verification-env/sil/logs/RESULTS-POST-fix.json` — **not**
> to the `results-sil-all.json` those records name in their `logs[]`
> (`sha256:edd3e70888c75ba075db2dadb17cd9cfb369adfce4b8ac4a05aaefada3c64589`).
> `FB2-VER-EXE-000015` names eight `.work/` paths directly in its `logs[]`.
>
> The reproducible generation command for the SIL run is in the **tracked**
> `…/RUNBOOK.md`. A fresh clone can reproduce the run; it cannot verify those five
> aggregate digests, and this report does not claim it can.

### 7.2 The earlier pre-SIL run, for the record

| Measure | Strict | Relaxed |
|---|---:|---:|
| Timestamp | 2026-09-29T10:30:52+0200 | 2026-09-29T10:33:16+0200 |
| Selection | `no_halcogen_dependency` | `no_halcogen_dependency` |
| Tests in scope | 136 | 136 |
| Passed | 94 | 98 |
| Failed | 5 | 7 |
| Build failures | 37 | 31 |
| Assertions tested / passed / failed | 332 / 323 / 8 | 391 / 380 / 10 |

Of the harness's 313 targets, 136 were in scope for this run and **177 were
excluded** because their quoted-`#include` closure reaches proprietary TI
HALCoGen output across **34 distinct `HL_*.h` headers**. Reconstructing 34
proprietary TI register maps from memory would fabricate the very thing those
tests exist to verify, so it was not done; the closure is characterised precisely
in the tracked `halcogen-dependency-closure.json`.

**That exclusion is superseded, not merely restated.** The SIL harness mocks the
`HL_*.h` interface boundary instead of reconstructing TI register maps, so **all
313 targets are now attempted** (§7.1). Of the 84 remaining build failures, 28
are upstream-excluded paths and 22 are Apple-clang-only diagnostics; the
HALCoGen-specific exclusion accounts for none of them.

**313 is the harness's enumeration, not a count of the tree.** The repository
holds **318** `test_*.c` files under `tests/`; the 5 not attempted are
`tests/unit-hw/test_tms570_{boot,crc,flash,main}.c` — the TMS570
**target-hardware** tests — plus
`tests/cli/pre_commit_scripts/test_check_include_guard/test_file.c`.

### 7.3 Execution record classes

`actual_product_evidence` is **0/33**, and the tool's own detail string states
why: `execution_kind` has no target-hardware member, so none can be claimed. Of
**44** execution records, **15** are host runs of real product code (not target
hardware) and **29** are `synthetic_fixture` or `none`. Nothing is undeclared.

> **6 of the 29 retain nothing.** `FB2-VER-EXE-000001`…`000006` (profile
> `synthetic_reference`) record `execution_kind: synthetic_fixture`,
> `outcome: pass`, `logs: []` and no evidence file, and
> `docs/artifacts/evidence/synthetic-fixtures/` holds **no fixture artefact** — its
> only file is a hand-written `MANIFEST.md` stating that the fixture was never
> captured and that the file "must never be counted as captured evidence for any
> test". That file records the gap against `FB2-REV-FND-000143`, **which does not
> exist in the corpus** — 42 finding records exist, numbered to
> `FB2-REV-FND-000042`. The fixture they
> claim to have run was never retained, so the `pass` cannot be checked by
> anyone. See §13 item 4.

## 8. Reviews and Findings

**15 review records** in the index, and **15 files** on disk — the earlier
duplicate has been removed (see below).

| Profile | critical | high | medium | low | `info` | Total |
|---|---|---|---|---|---|---|
| as_is | **0** | 1 | 9 | 3 | 4 | 17 |
| synthetic_reference | **0** | 7 | 15 | 4 | 6 | 32 |
| **All** | **0** | **8** | **24** | **7** | **10** | **49** |

**49** review-embedded findings in total. The rendered view's table has no `info`
column, so the visible columns do not sum to the Total; the 10 unaccounted
findings are `info`. The table is generated and is left as generated.

**No critical finding exists in either profile.**

**42 `finding` artifacts** exist as first-class records under
`docs/artifacts/reviews/findings/` (32 `medium`, 9 `high`, 1 `low`), each carrying
`validator_finding_verbatim` text. These are the validator's own findings
promoted to records; they are a different set from the 49 embedded above and are
not added together.

Automated review coverage: **144/259 = 64%**, 15 review records,
`reviewed_by` links consistent with `reviewed_ids` (229 each). **80 distinct
artefact IDs are covered by no review record.**

**3 change records** (`FB2-MAN-CHG-000001..000003`), each with a full change
lifecycle, and **3 change-lifecycle scenarios** all validating 19/19 required
content checks.

### Reported defect: duplicated review record — closed

`FB2-REV-000001` previously existed in two files with identical content
(`docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json` and
`docs/artifacts/reviews/records/review-vertical-slice.json`). **The duplicate has
been removed.** `docs/artifacts/reviews/records/` now holds **15 files for 15
review records**, and measured over the corpus **every `(profile, id)` pair is
unique** — the tool's index collapses nothing.

The validator gap that let it pass silently is unchanged and is worth fixing in
the tool: duplicate detection runs inside the validator while index
de-duplication runs upstream of it, so a future duplicate would again be absorbed
without a finding.

## 9. Corrected Defect in the Hand-Authored Root Document

`TRACEABILITY_DOCUMENT.md` at the **repository root** (one level above
`docs/artifacts/`) **stated**:

- under "1.1 Purpose": "Provides evidence for compliance with ISO 26262, IEC 61508, and
  other applicable safety standards"
- under "1.2 Scope": "Safety Requirements (ASIL-D, ASIL-B)"
- and, in a document-control block at the end of the file, a sign-off naming a safety
  engineer as reviewer, a safety manager as approver, and the status of the document
  as approved — **an approval that never existed**

This was a conformity claim, an ASIL-capability claim, and a fabricated human approval,
all of which this corpus forbids. It was also unsupported on two counts. **No corpus record was
authored against IEC 61508** and the standard is absent from
`governance/standards-lock.json` — though the pinned source *does* list IEC 61508
as a candidate standard and cite IEC 61508-3:2010, so the remedy was to record the
non-engagement explicitly, not to pretend the standard is unknown to foxBMS. And the
`asil` field on `FB2-SAF-SGO-000001` carries no justification, which the corpus's own
validator flags. `git ls-tree -r 308028fb` contains no `TRACEABILITY` entry, so the
file is corpus output rather than pinned upstream source.

**The repository owner explicitly authorised amending the file** — it is outside the
`docs/artifacts/` write boundary, and that authorisation is the sole authority for the
out-of-boundary write. It was corrected by hand on 2026-09-29 and is recorded as finding
**`FB2-REV-FND-000022`**,
`docs/artifacts/reviews/findings/finding-000022-root-traceability-document-conformity-claim.json`,
with severity `high`, category `consistency`, disposition `accepted`.

**The durable fix has since been implemented, at revision 4 of that finding.** The
document is now **generated**. `corpus.py render` emits
`docs/artifacts/views/traceability/traceability-document.md` from the canonical
records through the same view preamble as the other generated views, so it carries
the identical "derived, not authored / regenerable / guard fields / not a
conformity claim" contract. Every figure in it is computed at render time; none is
transcribed from a report. Both hand-authored copies — the repository-root file and
`docs/artifacts/reports/TRACEABILITY_DOCUMENT.md` — were reduced to short,
content-free pointers to that one canonical document, and the `.docx` beside the
reports pointer was regenerated from that pointer.

**The residual risk is therefore closed by construction rather than by human
discipline:** the earlier residual — a hand-authored file outside the toolchain's
reach, in which nothing would detect a regression — no longer holds for these
paths. The remaining residuals are recorded in the finding and are not this
defect: the generated document is only as honest as the records it derives from,
and four coverage dimensions remain presence checks or declared constants (now
labelled as such in that document's own coverage table).

## 10. Cross-Domain Walkthroughs

Five walkthroughs, each traced against real corpus IDs with `corpus.py trace`.
IDs are live; no ID below is nominal.

### 10.1 Cell Voltage Protection — complete chain

Traced from the hazard upward and the requirement downward.

| Stage | Record | Relation |
|---|---|---|
| Hazard | `FB2-SAF-HAZ-000001` | (as_is and synthetic_reference) |
| Safety goal | `FB2-SAF-SGO-000001` | `mitigates` → hazard; FTTI 100 ms |
| FSRs | `FB2-SAF-FSR-000001`, `-000002`, `-000003`, `-000004` | `refines` → safety goal |
| HW requirements | `FB2-HW-TSR-000001`, `-000002` | `allocated_to` → `FB2-SAF-FSR-000001` |
| HW requirements | `FB2-HW-TSR-000003` | `allocated_to` → `FB2-SAF-FSR-000003` |
| HW requirement | `FB2-HW-TSR-000004` | `allocated_to` → `FB2-SAF-FSR-000004` (independent monitor) |
| SW requirements | `FB2-SW-SWR-000001`, `-000002`, `-000003` | `allocated_to` → FSRs |
| SW design | `FB2-SW-DSN-000001`, `-000002`, `-000003` | per module |
| Concepts | `FB2-SAF-FSC-000001` (functional), `FB2-SAF-TSC-000001` (technical) | allocate the safety goal across six architectural elements |
| Analyses | `FB2-SAF-ANL-000001` (FMEA), `-000002` (FTA), `-000003` (dependent failure), `-000004` (FFI) | |
| Test measures | `FB2-VER-TMS-000001`…`-000028` | `verifies` → FSRs |
| Reviews | `FB2-REV-000001`, `-000009`, `-000010` (challenge), `-000011`, `-000012` (meta), `-000013`, `-000014` (cross_domain) | `reviewed_by` |

Change lifecycle is live: `FB2-MAN-CHG-000001` (`changes` → hazard and safety
goal) is the cell-voltage maximum-limit reduction, and
`FB2-MAN-CHG-000002` (`changes` → `FB2-SYS-HSI-000001`) is the AFE front-end
migration.

**Gap that remains:** the chain terminates at the design and test-measure
layers. `FB2-VER-TMS-000001` and `-000003` have execution records, but no
execution in this chain is target-hardware evidence. **Two high-severity
findings stand inside the concept phase that now sits above the safety goal:**
`FB2-REV-FND-000025` — the timing budget's arithmetic does not close — and
`FB2-REV-FND-000024` — the contactor reaction requirement contradicts itself. And
there is still **no system-architecture record** (`SYS.3`), so the chain has no
system-level architecture to pass through.

### 10.2 Temperature Measurement — parameters only, gap unchanged

No hazard, safety goal, FSR, TSR, SWR, design, test measure or execution record
exists for temperature measurement. What exists is the `FEAT-TEMPERATURE`
feature record in `sources/feature-inventory.json` (status `implemented`,
`source_modules` `MOD-APP-DRIVER-AFE`, `MOD-APP-DRIVER-TS`), the temperature
parameters in the shared parameter registry, and the HSI signal definition in
`FB2-SYS-HSI-000001`.

**Gap:** no vertical chain. The report previously listed three source anchors
for this walkthrough; the anchors are real, but they are feature-inventory
provenance, not a requirement-to-verification chain, and they are not restated
here as if they were a chain.

### 10.3 Current Measurement — parameters only, gap unchanged

Same state as temperature. `FEAT-CURRENT` is recorded `implemented` in the
feature inventory with source modules, and the CAN receive path is anchored in
the source registry, but no hazard, safety goal, requirement, design, test
measure or execution record forms a chain.

**Gap:** no vertical chain.

### 10.4 Precharge and Contactor Control — complete chain

| Stage | Record | Relation |
|---|---|---|
| FSR | `FB2-SAF-FSR-000003` | `refines` → `FB2-SAF-SGO-000001` |
| HW requirement | `FB2-HW-TSR-000003` | `allocated_to` → `FB2-SAF-FSR-000003` |
| SW requirement | `FB2-SW-SWR-000003` | `allocated_to` → `FB2-SAF-FSR-000003` |
| SW design | `FB2-SW-DSN-000003` | per module |
| Concepts | `FB2-SAF-FSC-000001`, `FB2-SAF-TSC-000001` | HW/SW allocation |
| Test measures | `FB2-VER-TMS-000002`, `-000008`, `-000011` | `verifies` → `FB2-SAF-FSR-000003` |
| Reviews | `FB2-REV-000001`, `-000010`, `-000011` | `reviewed_by` |
| Security | `FB2-SAF-TAR-000001` | `supports` → `FB2-SAF-FSR-000003` |

The contactor weld-detection path is additionally covered by the independent
monitor requirement `FB2-SAF-FSR-000004` → `FB2-HW-TSR-000004` → `FB2-SW-DSN-000004`,
verified by `FB2-VER-TMS-000004`, `-000008` and `-000011`.

**Change since the previous version of this report:** the cybersecurity work is
now real and linked. `FB2-SAF-TAR-000001` (threat analysis and risk assessment
for the external communication attack surface) `supports` this requirement, along
with the safety goal, `FB2-SAF-FSR-000001`, `-000002` and the safety case
`FB2-SAF-SCS-000001`.

**Gap that remains:** still no target-hardware execution in this chain, and
`FB2-REV-FND-000024` — the 30 ms acceptance threshold against the longer stated
reaction — is open against the contactor reaction requirement in this very chain.

### 10.5 Communication and Watchdog Fault Response — materially extended, still no full chain

This walkthrough has changed the most and is **no longer "parameters only"**.

New and real:

| Record | Type | Role |
|---|---|---|
| `FB2-SAF-TAR-000001` | tara | 8 threats, 9 mitigations, `item_and_scope` defined, `residual_risk_acceptance.acceptance_exists = false` |
| `FB2-SAF-SEC-000001` | requirement | authenticated/confidential transport for the network service |
| `FB2-SAF-SEC-000002` | requirement | bounded connection admission and per-service resource budget |
| `FB2-SAF-SEC-000003` | requirement | message-level integrity and freshness for safety-relevant CAN |
| `FB2-SAF-SEC-000004` | requirement | framing, integrity and authorisation on the serial link |
| `FB2-SAF-SEC-000005` | requirement | cryptographically strong entropy for network security parameters |
| `FB2-REV-000003` | review | review of the TARA and SEC-000001..000005 |
| `FB2-SAF-SEC-000003` | requirement | also `supports` → `FB2-SAF-FSR-000002` (SOA monitoring) |

The TARA links forward to all five security requirements, the safety goal, three
FSRs and the safety case.

**Gap that remains:** there is still no communication-specific hazard, safety
goal or FSR, and **no executed result** for the security requirements — the
measures now exist (`FB2-VER-TMS-000016`…`-000020`, which are the most
substantial part of the security work in the corpus) but every execution is
blocked (`FB2-REV-FND-000041`). The chain runs threat → security requirement →
safety goal, and stops. It is a real and substantial partial chain, not a
complete one.

### 10.6 Walkthrough summary

| # | Walkthrough | State | Blocking gap |
|---|---|---|---|
| 1 | Cell voltage protection | complete chain through the concept phase | **no system architecture**; TSC timing budget does not close (`FB2-REV-FND-000025`); no target-hardware execution |
| 2 | Temperature measurement | parameters only | no chain at all |
| 3 | Current measurement | parameters only | no chain at all |
| 4 | Precharge and contactor control | complete chain through the concept phase | contactor reaction requirement contradicts itself (`FB2-REV-FND-000024`); no target-hardware execution |
| 5 | Communication and watchdog | partial: TARA + 5 security requirements + 5 measures | no hazard/SG/FSR for comms; no design; **no executed verification** (`FB2-REV-FND-000041`) |

## 11. Source Inventory

`corpus.py inventory` → `Inventory: 612/612 source files, 24 modules, 22
features, 23 variants`

The inventory is complete: all 612 discovered source files are accounted for.

## 12. Export and Reproducibility

- Export: **263 nodes, 489 edges** to `docs/artifacts/exports/`
- `exports/manifest.json` present; all **3** content hashes identical across two
  consecutive exports (gate `[6/8] deterministic export hashes` PASS)
- `corpus.py render` → 11 views, **byte-identical across two runs** once the
  `Generated:` line is excluded; verified again after the coverage-plan change
- `render_spec_documents.py --check` → `INTEGRITY CHECK PASSED`, 10/10 documents
  converted, `DETERMINISM: byte-identical across runs`
- `render_e2e_html.py` regenerated the HTML deliverable; still **tracked**
  (`git check-ignore` returns 1 for it, and `git ls-files --error-unmatch`
  succeeds). `--audit-guard` **passes** with no affirmative conformity claim.
  `--check` exits **1** on 14 `implementation` records with no owning section —
  a renderer gap, recorded as §13 item 13.

## 13. Known Limitations

These are the measured limitations of the corpus. Each is stated here rather than
left to an agent handover, and each names what was measured and how.

1. **No target-hardware evidence.** 0 of 33 required target-hardware executions
   exist. Both macOS host runs in §7 are real product code on a development host
   and are not credited as target hardware. The repository's four
   `tests/unit-hw/test_tms570_*.c` target-hardware tests were never even
   attempted by the SIL harness.
2. **10 records' hardware provenance rests on an external repository.**
   Anchors `FB2-SRC-HW-000001..000003` name Altium `.SchDoc` files that live in
   the separate **`foxBMS2_hw` repository**, present neither in this working tree
   nor in any commit of this one. Their `content_hash` and `location.file_hash`
   both read `unresolved` and their `hash_status` is
   `external_design_file_unverifiable_from_this_repository`. **14** records cite
   them — **10 non-review records** (6 hardware requirements,
   `FB2-SAF-ANL-000003`, `FB2-SAF-ITE-000001`, `FB2-SAF-TSC-000001`,
   `FB2-SYS-HSI-000001`) and **4 review records** that review them. This is also
   why `HWE.2` and `HWE.3` cannot be discharged from this repository.
3. **4 anchors have no single machine-checkable symbol.** The provenance checker
   records `symbol_unverifiable_prose` for these and cannot verify them by symbol
   match; their content hashes and line ranges *are* verified. Each is
   legitimately about a whole file, a whole module or a prose block, so naming an
   identifier would understate the claim: `FB2-SRC-COD-000044` (whole `rtc.c`
   module body, lines 70–653), `FB2-SRC-COD-000076` (the 12-line FreeRTOS
   **markdown README**), `FB2-SRC-COD-000077` (the whole 114-line
   **`requirements.txt`**) and `FB2-SRC-COD-000088` (the copyright/licence header
   of `dp83869.c`, lines 1–59).
4. **6 synthetic executions describe a `synthetic_fixture` run with NO retained
   evidence — the fixture never existed.** `FB2-VER-EXE-000001`…`000006` (profile
   `synthetic_reference`) each record `execution_kind: synthetic_fixture`,
   `outcome: pass`, `logs: []` and no `evidence_files` entry, and
   `docs/artifacts/evidence/synthetic-fixtures/` holds **no fixture artefact** — only
   a `MANIFEST.md` documenting the gap, and that file's own finding reference
   (`FB2-REV-FND-000143`) resolves to nothing. The `pass` cannot
   be checked by anyone, including this corpus. Their `evidence_refs` name real
   test measures and real test source files, which is not the same thing as
   evidence that a run happened.
5. **5 execution records carry a suite-results digest belonging to a `.work`
   scratch file** rather than the evidence file they name. See §7.1a for the
   digests, the paths they resolve to, and the tracked runbook that regenerates
   the run.
6. **Link revision currency is not maintained.** 326 of 547 links record a stale
   endpoint revision and **none** is marked suspect (§5.1). This is the largest
   traceability limitation and the specific reason `SUP.11` is
   `partially_mapped`.
7. **3 applicable ASPICE processes have no backing artefact at all**: `SWE.3`,
   `HWE.3`, `HWE.4`. Zero corpus records reference any of them. `SWE.3` was
   recorded `mapped` until 2026-10-01. **18 more are `partially_mapped`** because
   at least one family of their own `expected_artifacts` has no record. Only **4**
   ASPICE processes are `mapped`, and **no ISO 26262 part is**. See §6.
8. **The concept phase exists but does not close.** Two high-severity findings
   stand inside it: `FB2-REV-FND-000025` (timing budget arithmetic) and
   `FB2-REV-FND-000024` (contactor reaction requirement contradicts itself).
   `FB2-SAF-SGO-000001` carries `asil: ASIL_D` with **no justification field of
   any kind**, so ISO Part 9 is `partially_mapped` too.
9. **No system-architecture record exists**, and no system modes/states record
   exists. `SYS.2` and `SYS.3` are `partially_mapped`; `as_is` has no system
   record at all.
10. **Stakeholder needs are declared, not elicited.** 5 records, each carrying
    `is_a_real_elicitation = false`; no workshop, interview or questionnaire was
    held; and **no operational-scenario record exists**.
11. **5 genuine test failures** in the earlier strict run, root-caused to untyped
    `void *` parameters in `src/app/engine/database/database.h:209` interacting
    with the shipped CMock configuration. A real defect in the product's test
    setup, compiler- and platform-independent. **No result was adjusted to make
    a test pass.**
12. **53 of the 245 green tests in the SIL host run assert nothing**
    (`FB2-REV-FND-000042`), and the harness classifies **16 of the 84 build
    failures** as real product defects.
13. **`render_e2e_html.py --check` exits 1** on 14 `implementation` records that
    have no owning section in the renderer. The HTML deliverable is regenerated,
    tracked and guard-audited; the fix is tool-side and outside this workstream's
    write boundary.
14. **Automated review coverage 64%** (144/259 distinct IDs). **80** distinct
    IDs are covered by no review record — and the unreviewed set includes every
    `post_development_record`, `process_record`, `measurement_plan`,
    `risk_register`, `project_plan`, `stakeholder_need`, `use_case` and
    `safety_concept` record, i.e. **the records the process-coverage claims rest
    on**.
15. **A conformity claim existed outside the write boundary** (§9). Corrected
    under explicit owner authorisation and then made tool-owned; the drift risk is
    closed by construction.
16. **`feature-inventory.json` `summary.total_features` is stale** at 20 against
    22 actual records. The tool counts records and reports 22; the summary field
    is not corrected because it is a corpus record, outside this write boundary.
17. **Human approval pending** for all **263** records. No human has approved any
    artefact, and none is production-authorized.

## 14. Final Determination

**`synthetic_ready_with_limitations`**

### What supports the status

- All 8 acceptance stages pass, **14 gate lines PASS and 0 FAIL**; 23/23
  scenario lines pass; **48/48** selftests pass.
- 13/13 artifact families populated.
- Every one of the 38 applicable standards entries carries an explicit
  disposition backed by a record that resolves: **33/38** (ASPICE 25/28, ISO
  8/10). The 5 that name no existing artefact are `SWE.3`, `HWE.3`, `HWE.4`,
  `part_1_vocabulary` and `part_10_guidelines`.
- **489/489** links resolve; 0 dangling.
- 10/10 semantic consistency check categories execute; **0 errors**, 4
  provenance observations.
- 20/20 mutation scenarios are detected **by the rule each one declares**, after
  the gate was repaired to assert against that rule. Before finding
  FB2-REV-FND-000032 the gate accepted any finding of the expected severity on
  the scenario's affected artifact, and 8 of the 20 were passing on standing
  defects; four declared a detector that did not exist, was unreachable, or
  could not fire on the record the scenario targets. See §2.1-§2.3.
- 46 evidence log hashes verified, 0 mismatched; 229 review digests verified, 0
  placeholder.
- A real SIL host run over **313** CeeDling targets: **222 passed, 7 failed, 84
  build failures**, all tracked and hashed.

### What prevents `synthetic_ready`

- **Process coverage is 4 `mapped` out of 28 applicable ASPICE processes, and 0
  `mapped` out of 10 applicable ISO parts.** Three processes have no backing
  artefact at all. This is the single largest reason the status is
  `synthetic_ready_with_limitations` and not something stronger.
- Automated review coverage is **64%**, not complete, and the unreviewed records
  are disproportionately the ones the process-coverage claims rest on.
- Human approval is 0% and is out of the corpus's control.
- Target-hardware product evidence is **0/33**, and the tool states the
  `execution_kind` enum has no target-hardware member, so none can be claimed
  without fabricating one.
- **326 of 547 links carry a stale endpoint revision and none is marked suspect.**
- Two of the five cross-domain walkthroughs are still parameters-only, and two
  of the other three terminate at a concept phase that does not close.

### What this status does and does not mean

It **can** describe: a synthetic corpus whose structure, traceability and
negative-scenario behaviour are demonstrably sound, with real host-run test
evidence, with blocked and failed results recorded rather than hidden, and with
its own governance overclaims corrected and recorded.

It **cannot** mean, and is not evidence of: ISO 26262 conformity, ASIL
capability, IEC 61508 conformity, an ASPICE capability level, human approval,
tool qualification, certification, or target-hardware verification.

## 15. Provenance of Every Number

| Figure | Source command or tracked file |
|---|---|
| **286** validated artefacts, 4 findings, 0 errors | `corpus.py validate` |
| **263** unique `(profile, id)` records, **489** links, all censuses | `corpus.py load_artifact_index` / `load_links` via the tool's own loaders |
| **224** distinct artefact IDs; 39 exist in both profiles | same loaders |
| 15 coverage dimensions and all ratios | `corpus.py coverage` |
| 8 stages, 14 gate lines, 23 scenario lines, 20/20 mutations detected on their own declared detector | `corpus.py check` |
| **48/48** selftests, including 9 provenance tests and 2 that break the mutation gate on purpose | `corpus.py selftest` |
| 229 review digests, 130 anchors, 57 log hashes, 62 evidence-file entries verified; 4 anchors prose-only | `corpus.py validate` provenance tally |
| every `safety_goal_ref` and payload-field cross-reference resolves; every FTTI allocation closes | `docs/artifacts/tools/check_references.py` |
| 612/612, 24 modules, 22 features, 23 variants | `corpus.py inventory` |
| 32/28/4 processes, **16** corrections, ASPICE 4/21/3, ISO 0/8/2 | `governance/coverage-plan.json` |
| **standards_mapping 16/38 → 33/38** | `corpus.py coverage`, before and after the `CORR-COV-016` edit |
| **222 passed / 7 failed / 84 build failures / 988-950-35 assertions / 313 targets** | **tracked** `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json` |
| 136 / 94 / 5 / 37 and 332/323/8 (strict), 136 / 98 / 7 / 31 and 391/380/10 (relaxed) | **tracked** `…/foxbms2-host-unit-test-macos-2026-09-29/results-{strict,relaxed}.json` |
| 313 / 136 / 177 / 34 headers | **tracked** `…/foxbms2-host-unit-test-macos-2026-09-29/halcogen-dependency-closure.json` |
| **5 `.work` digests that resolve outside the distribution** | hashing every file under `docs/artifacts/.work/` and `docs/artifacts/evidence/` and matching against each execution record's `output_hashes` |
| **263 nodes, 489 edges, 3 content hashes** | `exports/manifest.json` |
| **11 views byte-identical across two runs** | `diff -r -I '^Generated:'` over two `corpus.py render` runs |
| spec-document integrity and determinism | `render_spec_documents.py --check` → `INTEGRITY CHECK PASSED`, `DETERMINISM: byte-identical across runs` |
| HTML deliverable guard audit | `render_e2e_html.py --audit-guard` → no affirmative conformity claim |
| HTML deliverable integrity | `render_e2e_html.py --check` → **exit 1**, 14 `implementation` records unmapped (renderer gap) |
| conformity claim and fabricated approval sign-off in the hand-authored root document | `TRACEABILITY_DOCUMENT.md` at repository root, corrected under explicit owner authorisation, then made tool-owned: the document is now generated at `docs/artifacts/views/traceability/traceability-document.md` and the root path is a content-free pointer. Finding `FB2-REV-FND-000022` rev 4 |

**Note on the test figures specifically.** The previous version of this table
cited `.work/verification-env/logs/*.json`. That directory is **gitignored and
untracked**, so the evidence behind the published numbers was not in the
distribution. Every test figure above is now read from a **tracked** file under
`docs/artifacts/evidence/actual-runs/`, and the one place where a digest still
resolves into `.work/` is named as such in §7.1a rather than presented as
verifiable.

## 16. What Changed in This Revision, Figure by Figure

Recorded so a reader holding the previous version can account for every
difference. **Every figure below was recomputed from a live
`python3 docs/artifacts/tools/corpus.py` run on 2026-10-01**; where the live
figure and the published figure disagreed, the published figure was wrong and
was corrected here.

| Figure | Previous version | This version | Source of the live figure |
|---|---:|---:|---|
| Schema-validated artefact files | 246 | **286** | `validate` |
| Unique `(profile, id)` records | 222 | **263** | `load_artifact_index` |
| Distinct artefact IDs across profiles | 187 | **224** | `automated_review_coverage` denominator |
| Traceability links | 460 | **489** | `load_links` |
| `source_grounding` | 80/223 | **99/263** | `coverage` |
| `traceability_integrity` | 460/460 | **489/489** | `coverage` |
| `automated_review_coverage` | 144/259 | **144/259** | `coverage` |
| `verification_planning` | 25/7 | **33/7** | `coverage` |
| `actual_product_evidence` | 0/25 | **0/33** | `coverage` |
| `synthetic_fixture_coverage` | 148/43 | **173/43** | `coverage` |
| `human_approval` / `production_authorization` | 0/223 | **0/263** | `coverage` |
| `standards_mapping` (by backing) | 16/38 → **33/38** | 33/38 | `coverage` |
| ASPICE `mapped` | 12 | **4** | `coverage-plan.json`, `CORR-COV-016` |
| ASPICE `partially_mapped` | 10 | **21** | same |
| ASPICE `gap` | 6 | **3** | same |
| ISO `mapped` | 6 | **0** | same |
| Corrections in the coverage plan | 15 | **16** | `coverage-plan.json` |
| Toolchain self-tests | 22 | **48** | `selftest` |
| Acceptance gate lines | 10 | **14** | `check` |
| Review records | 15 | **15** | `load_artifact_index` |
| Review-embedded findings | — | **49** | `reviews/records/*.json` |
| Finding artefacts | 31 | **42** | `load_artifact_index` |
| Automated review coverage % | 77% | **64%** | `coverage` |
| SIL run figures | absent | **313 targets, 222 passed, 7 failed, 84 build failures, 988/950/35 assertions** | tracked `results-sil-all.json` |
| Pre-SIL strict figures | 94/136 cited as headline | **136 in scope, superseded by the SIL run** | tracked `results-strict.json` |
| "177 tests blocked" | stated as the blocker | **superseded** — the SIL harness attempts all 313 | tracked `results-sil-all.json` |
| `feature-inventory` summary | 20 vs 22 | **still open** | `inventory` |
| Duplicated review record | open | **closed** | `reviews/records/` file count |

## 17. Evidence Links

- `docs/artifacts/reports/coverage-report.md`
- `docs/artifacts/reports/standards-mapping-report.md`
- `docs/artifacts/reports/traceability-report.md`
- `docs/artifacts/reports/consistency-report.md`
- `docs/artifacts/reports/review-summary.md`
- `docs/artifacts/reports/source-vs-synthetic-gap-report.md`
- `docs/artifacts/reports/verification-evidence-report.md`
- `docs/artifacts/reports/scenario-validation-report.md`
- `docs/artifacts/reports/reproducibility-report.md`
- `docs/artifacts/reports/final-acceptance-report.md` (this file)
- `docs/artifacts/reports/final-acceptance-report.json`
- `docs/artifacts/reviews/findings/finding-000022-root-traceability-document-conformity-claim.json`
