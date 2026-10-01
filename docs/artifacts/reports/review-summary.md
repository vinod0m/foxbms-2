# Review Summary Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> **These are automated AI-assisted reviews. They are not human reviews, and
> none of them constitutes approval.** No human has reviewed or approved any
> artifact in this corpus. Every one of the **263** indexed records is
> `human_approval_status: pending` and `production_authorized: false`. Nothing
> here asserts ISO 26262 conformity, ASIL capability, ASPICE capability level or
> certification.
>
> Every number is from a live tool run on 2026-10-01.

## 1. Review Coverage

| Measure | Value |
|---|---|
| Review records (unique, in the artifact index) | **15** |
| Review record *files* on disk | **15** — no duplicate |
| `reviewed_ids` entries summed across records | **229** |
| Unique artifact IDs covered by a review (the union) | **144** |
| Unique artifact IDs in the corpus | **224** |
| **Automated review coverage** | **144/224 = 64%** |
| Unique IDs **not** covered by any review | **80** |
| `reviewed_by` link count | **229** |
| Link/record agreement | consistent — `reviewed_by` links and `reviewed_ids` lists agree exactly |

The denominator is 224 rather than 263 because it counts distinct artifact
**IDs** across both profiles, and **39** IDs exist in both `as_is` and
`synthetic_reference` by design (profile isolation, not duplication). The tool
reports the agreement between the two independent sources of the same fact
rather than silently reconciling them — and here they agree exactly, with 229
`reviewed_by` links matching 229 `reviewed_ids` entries.

## 2. The 15 Review Records

| ID | Profile | Type | Domain | Lifecycle | IDs reviewed | Findings |
|---|---|---|---|---|---|---|
| `FB2-REV-000001` | as_is | domain | safety | **reviewed** | 17 | 5 |
| `FB2-REV-000002` | as_is | domain | software | draft | 26 | 2 |
| `FB2-REV-000003` | synthetic_reference | domain | safety | draft | 6 | 2 |
| `FB2-REV-000004` | synthetic_reference | domain | management | draft | 3 | 2 |
| `FB2-REV-000005` | synthetic_reference | domain | safety | draft | 7 | 4 |
| `FB2-REV-000006` | as_is | domain | verification | draft | 3 | 2 |
| `FB2-REV-000007` | synthetic_reference | domain | verification | draft | 12 | 3 |
| `FB2-REV-000008` | synthetic_reference | domain | system | draft | 8 | 2 |
| `FB2-REV-000009` | synthetic_reference | **challenge** | safety | draft | 20 | 4 |
| `FB2-REV-000010` | as_is | **challenge** | safety | draft | 16 | 3 |
| `FB2-REV-000011` | as_is | **meta** | supporting | draft | 16 | 5 |
| `FB2-REV-000012` | synthetic_reference | **meta** | supporting | draft | 33 | 2 |
| `FB2-REV-000013` | synthetic_reference | **cross_domain** | safety | draft | 32 | 5 |
| `FB2-REV-000014` | synthetic_reference | **cross_domain** | supporting | draft | 17 | 4 |
| `FB2-REV-000015` | synthetic_reference | domain | verification | draft | 13 | 4 |

The `reviewed_ids` counts sum to **229**, which is greater than **144** because
an artefact reviewed by several records is counted once per record. The coverage
figure of 144 is the **union**, so nothing is double-counted.

### Review record types

- **domain** (10 records) — scoped review of a coherent body of work.
- **cross_domain** (2 records) — review across the discipline boundary; added
  2026-09-29 with the concept, system, supporting and security records.
- **challenge** (2 records) — separated adversarial pass over the
  safety-critical chain, deliberately performed against a different profile from
  the original reviewer so it is not a self-review.
- **meta** (2 records) — audit of prior review records' claims against the
  artifacts those reviews covered.

The presence of challenge and meta review types is a real strengthening since
the corpus was first accepted: `FB2-REV-000010` challenges the `as_is`
cell-voltage chain and `FB2-REV-000009` challenges the `synthetic_reference`
chain; `FB2-REV-000011` audits `FB2-REV-000001`'s claims and `FB2-REV-000012`
audits the synthetic review set.

## 3. Findings Raised by Reviews

**49** findings are embedded across the **15** review records.

| Profile | critical | high | medium | low | `info` | Total |
|---|---|---|---|---|---|---|
| `as_is` | **0** | 1 | 9 | 3 | 4 | 17 |
| `synthetic_reference` | **0** | 7 | 15 | 4 | 6 | 32 |
| **All** | **0** | **8** | **24** | **7** | **10** | **49** |

**No critical finding exists in either profile.** Separately, **42 `finding`
artefacts** exist as first-class records under
`docs/artifacts/reviews/findings/` (32 `medium`, 9 `high`, 1 `low`). Those are
the validator's own findings promoted to records; the 49 above are findings
embedded in review records. The two sets are different things and are not added
together.

**Presentation caveat, stated so the table is not misread:** the generated
`views/supporting-processes/supporting-processes.md` table shows only the
critical/high/medium/low columns while its `Total` column sums **all**
severities. The visible columns therefore do not sum to the Total; the 10
unaccounted findings are `info`. That table is generated and is left as
generated.

### The 8 high-severity findings

| Originating record | Type | Profile | Subject |
|---|---|---|---|
| `FB2-REV-000005` | domain | `synthetic_reference` | The safety case's central timing argument `ARG-003` is arithmetically wrong and omits late-fault cases |
| `FB2-REV-000007` | domain | `synthetic_reference` | The `pass` outcome recorded against the synthetic fixture executions is not supported by a real execution |
| `FB2-REV-000009` | **challenge** | `synthetic_reference` | Challenge-pass confirmation of a circular-argument risk in the safety chain |
| `FB2-REV-000010` | **challenge** | `as_is` | The prior review `FB2-REV-000001` recorded a digest that does not match the reviewed content |
| `FB2-REV-000013` | **cross_domain** | `synthetic_reference` | The new concept and system records contradict the pre-existing hazard, safety goal and requirement records |
| `FB2-REV-000014` | **cross_domain** | `synthetic_reference` | The supporting-process records overstate what their own acceptance criteria are met by |
| `FB2-REV-000015` | domain | `synthetic_reference` | The SIL host run's own results — 53 vacuous tests, build-failure misattribution, classifier non-determinism |

**The profile split is 1 in `as_is`, 7 in `synthetic_reference`.** That asymmetry
is itself worth stating plainly: the adversarial layer is finding more defects in
the synthetic profile than in the real one, which is the expected result when a
reviewer examines its own reasoning rather than the pinned upstream source, and
is the opposite of what a reader might assume from the word "challenge".

## 4. The Original Review Record

### `FB2-REV-000001` — Cell Voltage Protection Vertical Slice

- **Type:** domain review, profile `as_is`
- **Lifecycle:** `reviewed` — the **only** review record in the corpus at
  `reviewed`; the other **14** are `draft`
- **Scope:** 17 artifacts — hazard, safety goal, 4 FSRs, 3 HW TSRs, 3 SW SWRs,
  3 SW designs, test measures and an execution
- **Findings:** 5
- **Limitations:** AI-assisted review; not independent human review; timing
  analysis not performed on target hardware

This record is the only one that has progressed past `draft`. That is worth
stating plainly rather than presenting the review programme as uniformly
complete: **14 of 15 review records are still `draft`**, and a draft review is
not a finished review.

## 5. Reported Defects in the Review Programme

### 5.1 The earlier duplicated review record — closed

`FB2-REV-000001` previously existed in two files with identical content
(`corpus/as_is/reviews/records/review-vertical-slice.json` and
`reviews/records/review-vertical-slice.json`). **That duplicate has been
removed**: `docs/artifacts/reviews/records/` now holds **15** files for **15**
review records, and the artifact index's file-to-key collapse is 4 corpus files
rather than 5. Removing it unrecorded would have been the same class of error
this report exists to prevent, so the removal is recorded here.

### 5.2 Coverage is 64%, and 80 IDs are unreviewed

The **80** uncovered distinct artifact IDs are the largest single gap in the
review programme. Any claim that the corpus has been reviewed must carry this
number. The uncovered set includes every `post_development_record`,
`process_record`, `measurement_plan`, `risk_register`, `project_plan`,
`stakeholder_need`, `use_case` and `safety_concept` record that no review
record names — the material that `CORR-COV-016` found to be the only backing for
21 `partially_mapped` ASPICE processes and 8 `partially_mapped` ISO parts.
**That is not a coincidence:** the records the review programme has not looked at
are the records the process-coverage claims rest on.

### 5.3 Fourteen of fifteen review records are `draft`

Review *activity* has occurred across the corpus. Review *completion* has not.

## 6. What These Reviews Do and Do Not Establish

| Established | Not established |
|---|---|
| 15 review records exist, spanning domain, cross_domain, challenge and meta types | That any review is complete — **14 of 15** are `draft` |
| **144 of 224** distinct artifact IDs are covered | That the **80** uncovered IDs have been looked at |
| **8** high-severity findings, 0 critical | That no defect exists — coverage is **64%** |
| The challenge, cross_domain and meta passes found defects the original domain review did not | That the challenge passes were independent of the original reviewer in any organisational sense; they are AI sessions, not separated humans |
| Findings are recorded as first-class artefacts, not just prose | Human review, human approval, or any conformity conclusion |

**Review independence is limited and stated as such.** These are automated
AI-assisted reviews produced within the same session family. They provide
adversarial *pass separation* — a challenge review of a chain the original
reviewer covered — but they are not independent human reviewers, and the corpus
makes no independence or qualification claim.
