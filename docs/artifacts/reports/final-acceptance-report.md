# Final Acceptance Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`, v1.11.0)
**Repository:** `/Users/vinod/Downloads/SoftwareDevLabs/foxbms-2`
**Machine-readable sibling:** `final-acceptance-report.json`

> **Status of this report.** Every number below was produced by a live run of
> `docs/artifacts/tools/corpus.py` on 2026-09-29. None is transcribed from an
> earlier report. The commands are listed in the *Provenance of every number*
> section so each figure can be re-derived.
>
> **This is not a conformity statement.** The corpus holds a **structural
> mapping** to ISO 26262 clause references and to ASPICE process references. It
> asserts **no ISO 26262 conformity**, no ASIL capability, no certification, no
> tool qualification and no ASPICE capability level. Every one of the 222
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
| 1/8 | validate | PASS (246 artifacts, 0 findings, 0 errors) |
| 2/8 | inventory | PASS (612/612 source files) |
| 3/8 | negative_scenario_validation = 20/20 mutations | PASS (20/20 scenarios **present**) — see §2.1 |
| 3/8 | change lifecycles = 3/3 | PASS (3/3 present) |
| 4/8 | hazard present (trace reachability) | PASS |
| 5/8 | scenario-test | PASS (23/23 scenario lines; 20/20 mutations **detected on their own declared detector**) |
| 6/8 | export | PASS |
| 6/8 | deterministic export hashes | PASS |
| 7/8 | no production_authorized/approved artifacts | PASS (0 violations this run) |
| 8/8 | final status recorded | PASS (`synthetic_ready_with_limitations`) |

10 gate lines PASS, 0 FAIL. 23/23 scenario lines pass (20 mutation scenarios
plus 3 change lifecycles).

`python3 docs/artifacts/tools/corpus.py selftest` → **22 PASS, 0 FAIL**
(14 pre-existing + 8 added to test the gate's own soundness; see §2.2).

### 2.1 What the 20/20 in gate 3/8 means, and what it does not

Gate `[3/8]` counts how many mutation scenarios **exist** (`numerator =
len(mutations on disk)`). It is a coverage-of-scenarios figure and it is
unaffected by whether those scenarios detect anything. It would have read
`20/20` at the moment the mutation gate was discovered to be self-certifying,
and it still reads `20/20`. It is not a detection claim and must not be read
as one. The detection claim lives entirely in gate `[5/8]`.

This distinction was not stated in earlier revisions of this report, which
presented `20/20` from dimension 11 as though it were a detection result. It
is not. The coverage dimension's computation is unchanged.

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

| # | Dimension | Ratio | % | Status | Note |
|---|---|---|---|---|---|
| 1 | scope_accounting | 1/1 | 100% | complete | source/feature/variant inventories present |
| 2 | artifact_population | 13/13 | 100% | complete | 13 families populated |
| 3 | standards_mapping | 44/44 | 100% | complete | ASPICE 32/32, ISO parts 12/12 |
| 4 | source_grounding | 80/223 | 36% | **partial** | 102 source anchors available; 143 records carry no `source_refs` |
| 5 | traceability_integrity | 460/460 | 100% | complete | 0 dangling links |
| 6 | semantic_consistency_checks | 10/10 | 100% | complete | 10 check categories per run |
| 7 | automated_review_coverage | 144/187 | 77% | **partial** | 15 review records; `reviewed_by` links consistent with `reviewed_ids` |
| 8 | verification_planning | 25/7 | 357% | over-covered | 25 test measures for 7 FSRs; a ratio, not a score |
| 9 | actual_product_evidence | 0/25 | 0% | **blocked by policy** | 0 target-hardware executions; see §7 |
| 10 | synthetic_fixture_coverage | 148/43 | 344% | over-covered | 148 `synthetic_reference` records against a target of 43 |
| 11 | negative_scenario_validation | 20/20 | 100% | scenarios **present**; detection is gate 5/8, see §2.1 | plus 3/3 change lifecycles |
| 12 | final_status | `synthetic_ready_with_limitations` | — | — | recorded status |
| 13 | export_reproducibility | 1/1 | 100% | complete | export manifest present |
| 14 | human_approval | 0/223 | 0% | **pending by policy** | every record pending; none performed |
| 15 | production_authorization | 0/223 | 0% | **false by policy** | every record `production_authorized=false` |

### Note on the three different denominators

The corpus contains three legitimately different population counts, and a
reader comparing them will otherwise think one is wrong:

- **223** — artifact *files* carrying an `id` under `corpus/` and `reviews/`.
  Used as the denominator for `source_grounding`, `human_approval` and
  `production_authorization`.
- **222** — unique `(profile, id)` records in the tool's artifact index. One
  less than 223 because the record `FB2-REV-000001` exists in two files
  (`corpus/as_is/reviews/records/review-vertical-slice.json` and
  `reviews/records/review-vertical-slice.json`); the index de-duplicates on
  `(profile, id)` and keeps the first. The duplicate is reported in §8.
- **187** — unique artifact *IDs* across both profiles. Lower than 222 because
  most requirement, design and verification IDs deliberately exist in both
  `as_is` and `synthetic_reference`; profile isolation is a design decision, not
  duplication. Used as the denominator for `automated_review_coverage`.

A fourth number, **246**, is printed by `validate`: that is schema-validated
files, being 223 corpus/review files plus 23 scenario files.

## 4. Record Census

**222 unique `(profile, id)` records** in the tool's artifact index. Every count
below is computed from the tool's own index by a live run of
`corpus.py load_artifact_index`, not from a directory listing.

### By artifact type

| Type | Count | | Type | Count |
|---|---|---|---|---|
| execution | 36 | | stakeholder_need | 5 |
| requirement | 34 | | use_case | 4 |
| finding | 31 | | safety_analysis | 4 |
| deviation | 26 | | change | 3 |
| test_measure | 25 | | hazard | 2 |
| review | 15 | | safety_goal | 2 |
| design | 8 | | safety_concept | 2 |
| post_development_record | 6 | | process_improvement | 2 |
| process_record | 6 | | project_plan | 1 |
| scenario | 5 | | risk_register | 1 |
| | | | item_definition | 1 |
| | | | safety_case | 1 |
| | | | tara | 1 |
| | | | measurement_plan | 1 |
| **Total** | **222** | | | |

### By engineering domain

| Domain | Count | | Domain | Count |
|---|---|---|---|---|
| verification | 87 | | management | 11 |
| software | 40 | | hardware | 7 |
| safety | 38 | | production | 2 |
| system | 21 | | decommissioning | 1 |
| supporting | 12 | | operation | 1 |
| | | | release | 1 |
| | | | service | 1 |
| **Total** | **222** | | | |

### By profile

| Profile | Count |
|---|---|
| `synthetic_reference` | 148 |
| `as_is` | 74 |
| **Total** | **222** |

### By lifecycle status

| Lifecycle | Count |
|---|---|
| draft | 96 |
| reviewed | 63 |
| baselined | 63 |
| **Total** | **222** |

### By origin

| Origin | Count |
|---|---|
| synthetic | 126 |
| source_observed | 60 |
| derived | 36 |
| **Total** | **222** |

### Guard fields — corpus-wide

Every one of the 222 records carries `human_approval_status: pending`,
`production_authorized: false` and `product_verification_credit: false`. The
validator raises a finding on any record that does not, and `validate` reports
0 findings.

## 5. Traceability

**460 links**, **0 dangling**. De-duplicated by `(profile, link_id)` across all
registries.

| Relation type | Count | | Relation type | Count |
|---|---|---|---|---|
| reviewed_by | 229 | | depends_on | 12 |
| verifies | 47 | | implements | 6 |
| refines | 41 | | mitigates | 3 |
| allocated_to | 40 | | | |
| supports | 29 | | | |
| result_of | 25 | | | |
| changes | 16 | | | |
| validates | 12 | | | |
| **Total** | **460** | | | |

By profile: `as_is` 111, `synthetic_reference` 349.
By review state: reviewed 408, pending 52.

## 6. Governance State

`governance/coverage-plan.json` holds 32 process entries: **28 applicable**,
**4 explicitly `not_applicable`** (MLE.1–MLE.4, each with a rationale and a
`reference_decision`).

### Disposition status across the 28 applicable processes

| Disposition | Count |
|---|---|
| `mapped` | 12 |
| `partially_mapped` | 10 |
| `gap` | 6 |
| `not_applicable` | 0 |

Plus the 4 explicitly non-applicable MLE entries, giving 32 in total.

### Corrections recorded in the coverage plan

**15 corrections** (`CORR-COV-001` … `CORR-COV-015`), all dated 2026-09-29.

Every correction kept its original `expected_artifacts` and
`capability_attributes`. No expectation was deleted or narrowed, and no
artifact was fabricated to make a status true. Two of the ten corrections made
in the most recent pass (`CORR-COV-008` on MAN.6 and `CORR-COV-011` on ISO Part
6) landed on a *different* status than the originally reported reality
suggested, because verification against disk found evidence on both sides of the
claim; both record the divergence explicitly rather than resolving it in the
convenient direction.

Two residual internal disagreements are recorded rather than hidden, because the
entries concerned were outside the scope of that correction pass:

1. `SUP.1`, `SUP.8`, `SUP.9` and `SUP.10` still read `mapped` in
   `process_inventory`, while the generated `supporting-processes` view reports
   that no *process-definition* record exists for those families. These are
   different claims — review, change and configuration evidence does exist —
   and both readings are now stated in the plan.
2. `sources/feature-inventory.json` carries `summary.total_features: 20` while
   the file contains 22 feature records, and `corpus.py inventory` reports 22.
   The summary field is stale; the tool counts the records.

### Standards lock

| Standard | Edition |
|---|---|
| `ISO_26262_2018` | 2018 |
| `ASPICE_PAM_41` | 4.1 |

Locked by `safety`. **No corpus record was authored against IEC 61508.** No corpus record was authored against IEC 61508. It is absent from `governance/standards-lock.json`, which locks exactly two standards: `ISO_26262_2018` (2018) and `ASPICE_PAM_41` (4.1). No requirement, `standards_mapping`, analysis, test measure or work product in `corpus/`, `governance/`, `schemas/`, `sources/`, `traceability/` or `scenarios/` references it. The standard is **not** alien to the product: the pinned source lists it as a candidate (`docs/general/safety/safety.rst:60`) and cites IEC 61508-3:2010 in `docs/references.bib`. The defect is that the corpus performed no IEC 61508 work, so it cannot supply compliance evidence for it. See §9.

## 7. Verification Evidence

### 7.1 Real macOS host test run

A genuine test-suite run was performed on the build host on 2026-09-29. Source:
`docs/artifacts/.work/verification-env/logs/results-strict.json`.

| Measure | Value |
|---|---|
| Host | Darwin arm64, Darwin Kernel 27.0.0 |
| Toolchain | ruby 4.0.7 (2026-09-15) +PRISM [arm64-darwin27] |
| Run timestamp | 2026-09-29T10:30:52+0200 |
| Selection | `no_halcogen_dependency` |
| Tests in scope | 136 |
| **Passed** | **94** |
| **Failed** | **5** |
| Build failures | 37 |
| Assertions tested | 332 |
| Assertions passed | 323 |
| Assertions failed | 8 |

**macOS is not an upstream-supported foxBMS platform.** This is a host run, not
target-hardware evidence, and it is not credited as such. See
`verification-evidence-report.md` for the full account, including the root cause
of the five failures and why they are a real product defect rather than a
harness artefact.

### 7.2 What is blocked

Of 313 repository tests, 136 were in scope. **177 are blocked** on proprietary
Texas Instruments HALCoGen output and reach **34 distinct `HL_*.h` headers**
(`docs/artifacts/.work/verification-env/logs/hcg-closure.json`). Reconstructing
34 proprietary TI register maps from memory would fabricate the very thing those
tests exist to verify, so it was not done. The blocker is characterised precisely
instead.

### 7.3 Execution record classes

`actual_product_evidence` is **0/16**, and the tool's own detail string states
why: `execution_kind` has no target-hardware member, so none can be claimed. Of
25 execution records, 13 are host/simulation (real product code, not target
hardware) and 12 are `synthetic_fixture` or `none`. Nothing is undeclared.

## 8. Reviews and Findings

**12 review records** in the index (13 files; one duplicate, see §3).

| Profile | critical | high | medium | low | Total (incl. `info`) |
|---|---|---|---|---|---|
| as_is | 0 | 1 | 9 | 3 | 17 |
| synthetic_reference | 0 | 3 | 8 | 2 | 19 |

36 review-embedded findings in total. The rendered view's table has no `info`
column, so the visible columns do not sum to the Total; the 10 unaccounted
findings are `info`. The table is generated and is left as generated.

**22 `finding` artifacts** exist as first-class records under
`docs/artifacts/reviews/findings/`, all at severity `medium` in the corpus
validator's own taxonomy, carrying `validator_finding_verbatim` text.

**3 change records** (`FB2-MAN-CHG-000001..000003`), each with a full change
lifecycle, and **3 change-lifecycle scenarios** all validating structurally
complete.

### Reported defect: duplicated review record

`FB2-REV-000001` exists in two files with identical content:

- `docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json`
- `docs/artifacts/reviews/records/review-vertical-slice.json`

The tool's index de-duplicates on `(profile, id)` and keeps the first, so no
count is inflated in the coverage dimensions. It is reported here rather than
silently deleted, because removing a file is a corpus owner's decision and doing
so unrecorded would be the same class of error this report exists to prevent.
The validator does not currently raise a finding for it.

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
out-of-boundary write. It was corrected on 2026-09-29 and is recorded as finding
**`FB2-REV-FND-000022`** at revision 3,
`docs/artifacts/reviews/findings/finding-000022-root-traceability-document-conformity-claim.json`,
with severity `high`, category `consistency`, disposition `accepted`.

**Residual risk, not closed by that disposition:** the file is still hand-authored and
outside the toolchain's reach, so nothing in CI will detect a regression. The
authorisation did not extend to relocating or regenerating the file.

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
| Analyses | `FB2-SAF-ANL-000001` (FMEA), `-000002` (FTA), `-000003` (dependent failure), `-000004` (FFI) | |
| Test measures | `FB2-VER-TMS-000001`…`-000004` | `verifies` → FSRs |
| Reviews | `FB2-REV-000001`, `-000009`, `-000010` (challenge), `-000011`, `-000012` (meta) | `reviewed_by` |

Change lifecycle is live: `FB2-MAN-CHG-000001` (`changes` → hazard and safety
goal) is the cell-voltage maximum-limit reduction, and
`FB2-MAN-CHG-000002` (`changes` → `FB2-SYS-HSI-000001`) is the AFE front-end
migration.

**Gap that remains:** the chain terminates at the design and test-measure
layers. `FB2-VER-TMS-000001` and `-000003` have execution records, but no
execution in this chain is target-hardware evidence, and there is no functional
safety concept record above the safety goal.

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

**Gap that remains:** still no target-hardware execution in this chain.

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
goal or FSR, and no design, test measure or execution for the security
requirements. The chain runs threat → security requirement → safety goal, and
stops. It is a real and substantial partial chain, not a complete one.

### 10.6 Walkthrough summary

| # | Walkthrough | State | Blocking gap |
|---|---|---|---|
| 1 | Cell voltage protection | complete chain | no FSC/TSC; no target-hardware execution |
| 2 | Temperature measurement | parameters only | no chain at all |
| 3 | Current measurement | parameters only | no chain at all |
| 4 | Precharge and contactor control | complete chain | no target-hardware execution |
| 5 | Communication and watchdog | partial: TARA + 5 security requirements | no hazard/SG/FSR for comms; no design or verification |

## 11. Source Inventory

`corpus.py inventory` → `Inventory: 612/612 source files, 24 modules, 22
features, 23 variants`

The inventory is complete: all 612 discovered source files are accounted for.

## 12. Export and Reproducibility

- Export: **222 nodes, 460 edges** to `docs/artifacts/exports/`
- `exports/manifest.json` present; content hashes identical across two
  consecutive exports (gate `[6/8] deterministic export hashes` PASS)
- `render_spec_documents.py --check` → `INTEGRITY CHECK PASSED`, 10/10 documents
  converted, `DETERMINISM: byte-identical across runs`

## 13. Known Limitations

1. **No target-hardware evidence.** 0 of 16 required target-hardware executions
   exist. The macOS host run in §7.1 is real product code on a development host
   and is not credited as target hardware.
2. **177 tests blocked** on proprietary TI HALCoGen output across 34 distinct
   headers.
3. **5 genuine test failures**, root-caused to untyped `void *` parameters in
   `src/app/engine/database/database.h:209` interacting with the shipped CMock
   configuration. This is a real defect in the product's test setup and is
   compiler- and platform-independent, so the same five tests are expected to
   fail under GNU gcc on Linux. **No result was adjusted to make a test pass.**
4. **Automated review coverage 67%** (82/123 unique IDs). 41 unique IDs are not
   covered by any review record.
5. **Six applicable processes hold no record of any kind**: `SYS.1`, `SYS.2`,
   `MAN.3`, `MAN.5`, `MAN.6`, `PIM.3`. See §6.
6. **No functional safety concept or technical safety concept record** exists in
   either profile, so ISO 26262 Part 3 is only partially mapped and the ASIL
   values on `FB2-SAF-SGO-000001` and `FB2-SAF-FSR-000004` have no
   concept-phase derivation in the corpus.
7. **No system or stakeholder requirement record** exists, so `SYS.1` and
   `SYS.2` are gaps and the corresponding coverage target is unmet.
8. **HWE.2 and HWE.3 are format-limited.** Altium and other CAD binaries are not
   readable by the corpus tooling; only real hardware analysis closes them.
9. **Duplicated review record** `FB2-REV-000001` in two files (§8).
10. **`feature-inventory.json` `summary.total_features` is stale** at 20 against
    22 actual records (§6).
11. **A conformity claim exists outside the write boundary** (§9).
12. **Human approval pending** for all 222 records. No human has approved any
    artifact, and none is production-authorized.

## 14. Final Determination

**`synthetic_ready_with_limitations`**

### What supports the status

- All 8 acceptance gates pass; 23/23 scenario lines pass; 22/22 selftests pass.
- 13/13 artifact families populated.
- 44/44 standards-mapping items carry an explicit disposition.
- 460/460 links resolve; 0 dangling.
- 10/10 semantic consistency check categories execute; 0 errors.
- 20/20 mutation scenarios are detected **by the rule each one declares**, after
  the gate was repaired to assert against that rule. Before finding
  FB2-REV-FND-000032 the gate accepted any finding of the expected severity on
  the scenario's affected artifact, and 8 of the 20 were passing on standing
  defects; four declared a detector that did not exist, was unreachable, or
  could not fire on the record the scenario targets. See §2.1-§2.3.

### What prevents `synthetic_ready`

- Automated review coverage is 67%, not complete.
- Human approval is 0% and is out of the corpus's control.
- Target-hardware product evidence is 0/16, and the tool states the
  `execution_kind` enum has no target-hardware member, so none can be claimed
  without fabricating one.
- Six applicable processes hold no record; the ISO Part 3 concept chain is
  incomplete.
- Two of the five cross-domain walkthroughs are still parameters-only.

### What this status does and does not mean

It **can** describe: a synthetic corpus whose structure, traceability and
negative-scenario behaviour are demonstrably sound, with real host-run test
evidence, with blocked and failed results recorded rather than hidden, and with
its own governance overclaims corrected and recorded.

It **cannot** mean, and is not evidence of: ISO 26262 conformity, ASIL
capability, IEC 61508 conformity, an ASPICE capability level, human approval,
tool qualification, certification, or target-hardware verification.

## 15. Provenance of Every Number

| Figure | Source command |
|---|---|
| 246 validated artifacts, 0 findings, 0 errors | `corpus.py validate` |
| 222 records, 460 links, all censuses | `corpus.py load_artifact_index` / `load_links` via the tool's own loaders |
| 15 coverage dimensions and all ratios | `corpus.py coverage` |
| 8 gates, 23 scenario lines, 20/20 mutations detected on their own declared detector | `corpus.py check` |
| 22/22 selftests, including 8 that break the mutation gate on purpose | `corpus.py selftest` |
| every `safety_goal_ref` and payload-field cross-reference resolves; every FTTI allocation closes | `docs/artifacts/tools/check_references.py` |
| 612/612, 24 modules, 22 features, 23 variants | `corpus.py inventory` |
| 32/28/4 processes, 15 corrections | `governance/coverage-plan.json` |
| 94/136, 5 failed, 37 build failures, 332/323/8 assertions | `.work/verification-env/logs/results-strict.json` |
| 313 / 136 / 177 / 34 headers | `.work/verification-env/logs/hcg-closure.json` |
| 222 nodes, 460 edges | `exports/manifest.json` |
| spec-document integrity and determinism | `render_spec_documents.py --check` |
| conformity claim and fabricated approval sign-off in the hand-authored root document | `TRACEABILITY_DOCUMENT.md` at repository root, corrected under explicit owner authorisation; finding `FB2-REV-FND-000022` rev 3 |

## 16. Evidence Links

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
