# Consistency Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> Semantic consistency results only. Nothing here asserts ISO 26262 conformity,
> ASIL capability, ASPICE capability level, certification, human approval or
> tool qualification.
>
> Guard fields, corpus-wide: every one of the 153 indexed records carries
> `human_approval_status: pending` and `production_authorized: false`. **No human
> has approved anything in this corpus.**
>
> Every number is from a live run of `corpus.py validate` and `corpus.py
> selftest` on 2026-09-29.

## 1. Headline Result

| Measure | Value |
|---|---|
| Schema-validated artifact files | 177 |
| Unique `(profile, id)` records in the index | 153 |
| Validator findings raised this run | **21** |
| **`finding` artifacts recording standing conditions** | **22** |
| **Errors** | **0** |
| Check categories executed per run | 10 / 10 |
| Toolchain self-tests | **11 PASS, 0 FAIL** |
| Mutation scenarios | 20 / 20 detected |
| Change lifecycles | 3 / 3 structurally complete |
| Acceptance suite | **PASSED** (8 stages, 10 gate lines, 0 FAIL) |

**21 findings, 0 errors** is the honest validator state: the validators raise 21
observations and none of them is an integrity error. The acceptance gate reads
`[PASS] validate`.

The **22** figure is a different thing and is not a discrepancy. It counts the
first-class `finding` records under `reviews/findings/`, which transcribe and
disposition standing conditions so they are legible rather than buried in
validator output. 21 of them correspond to validator findings; the 22nd,
`FB2-REV-FND-000022`, records a defect outside the corpus write boundary that
the validator cannot see (§4.4).

## 2. The 10 Check Categories

`corpus.py` executes 10 check categories on every run. The
`semantic_consistency_checks` coverage dimension reports 10/10.

| # | Category | What it enforces | Result |
|---|---|---|---|
| 1 | JSON parseability | every corpus/review/scenario file parses | pass |
| 2 | Schema validation | every record validates against its type schema | pass, 177 files |
| 3 | Link validity | no dangling link; no invalid relation type | pass, 283 links, 0 dangling |
| 4 | Source-reference resolution | every `source_refs` entry resolves to a registry anchor | pass |
| 5 | Provenance / guard fields | no `production_authorized: true`, no approved artifact | pass, 0 violations this run |
| 6 | Semantic rules | `execution_kind`/`outcome` enums, FTTI budget arithmetic | pass |
| 7 | Profile isolation | no cross-profile contamination of derived records | pass |
| 8 | Duplicate detection | no duplicate ID within a profile | pass, but see §3 |
| 9 | Export consistency | two exports produce identical content hashes | pass |
| 10 | Source registry pinning | the source registry is pinned to baseline commit `308028fb` | pass |

## 3. Findings, and What Each One Actually Says

The 22 `finding` artifacts under `reviews/findings/` fall into **four families
plus one recorded report**. Conflating them would be a mistake, because two
families are genuine gaps and one is partly a rule artefact.

Note that the corpus validator itself raises **21** findings; the 22
`finding` artifacts are the transcribed, dispositioned records of standing
conditions, and include one (`FB2-REV-FND-000022`) that records a defect
outside the corpus write boundary rather than a validator output.

### Family A — `verifies`-direction mismatch (7 of 12, `FB2-REV-FND-000001`…`000007`)

**Verbatim rule text:** `safety requirement has no verifies/validates link`

**The literal statement is only partly accurate.** The rule inspects only the
**source** side of a `verifies`/`validates` relation. The corpus's convention is
that the **test measure is the source and the requirement is the target**, so a
correctly verified requirement appears as a link *target*, never as a source.
`FB2-SAF-FSR-000001` in profile `as_is` is the target of at least one
`TMS → FSR` verifies link, but is the source of none, which is what the rule
tests.

Measured link census on the registry: `verifies` links run TMS→FSR (15),
TMS→SWR (10), TMS→TSR (7); `validates` links run TMS→SCO (1), TMS→SGO (1).

**The rule is not wrong to exist** — it is the missing-verification-link detector
that the mutation scenarios depend on. But its firing on a well-verified
requirement is a direction mismatch between the rule and the registry
convention, not a traceability defect.

**Resolution: NOT RESOLVED, and deliberately unchanged.** Relaxing the rule
would suppress a genuine detector the corpus needs. The fix is a joint decision
about link-direction convention between the corpus owner and the schema owner.

**Honest reading for a reviewer:** verification links must be examined on **both
sides** before concluding that a safety requirement is unverified. A reader who
trusts the finding literally will go looking for missing test evidence that is
in fact present. A reader who dismisses the finding as a rule artefact will
dismiss it for Family B too — where the conclusion would be **correct**.

### Family B — security requirements genuinely unverified (5, `FB2-REV-FND-000008`…`000012`)

**Same verbatim rule text, but a real and open gap.** `FB2-SAF-SEC-000001` …
`FB2-SAF-SEC-000005` — authenticated transport, bounded connection admission,
CAN message integrity and freshness, serial-link framing and authorisation,
strong entropy and component governance — carry the entire cybersecurity
requirement set and have **no verification link in either direction**.

**Root cause:** the five security requirements were authored as a derived set
from the TARA (`derived_from FB2-SAF-TAR-000001`) and each states its own
`verification_approach`, but **no verification planning pass was ever run against
the security requirement set**. Verification planning in the corpus
concentrates on the cell-voltage safety chain (FSR/TMS/EXE); the security set was
outside that plan's scope when the plan was written.

**Resolution: NOT RESOLVED.** Closing it requires authoring security
verification measures and executions, and the underlying control does not yet
exist in the real source to be verified against. No check was weakened and no
verification was fabricated.

### Family C — no machine-readable fault reaction (7, `FB2-REV-FND-000013`…`000019`)

**Verbatim rule texts:** `safety requirement FB2-SAF-FSR-00000N has no
fault_reaction defined`, one per FSR per profile. Confirmed by direct inspection:
the `fault_reaction` key is absent from the whole document of each affected FSR,
so the rule's condition is exactly met.

**Why it matters beyond tidiness:** the corpus holds **no machine-readable record
of what the system must do on detection of any of its safety faults** — no
reaction time, no reaction target, no degraded-mode statement per requirement.
The information exists only as prose, so no checker can consume it.

**Root cause is tooling ahead of specification, not an authoring lapse.** The
requirement schema never made `fault_reaction` required, so the records are
schema-valid and no author was ever asked to populate it. The field was added to
the tooling as mutation detector `MUT-008` without a matching authoring
requirement, so the detector fires on the baseline by construction.

**Resolution: NOT RESOLVED.** Resolving it means adding a required
`fault_reaction` field to the requirement schema and populating it across all
seven FSR instances from the existing prose. That is a schema change plus
authoring work, both outside the scope of a finding record. The check was **not**
weakened and no record was relabelled to silence it.

### Family D — ASIL assignment with no justification (2, `FB2-REV-FND-000020`, `000021`)

**Verbatim rule text:** `safety goal FB2-SAF-SGO-000001 ASIL ASIL_D lacks
justification`. Confirmed by direct inspection: the safety goal carries
`asil: "ASIL_D"` and the key `asil_justification` is absent from the document.
The same absence holds in both profiles, which is why the validator reports it
twice.

**This is the load-bearing finding for the ASIL question, and it is a genuine
gap.** An ASIL classification determines the required rigor of everything
derived from it, so an underived `ASIL_D` means the corpus cannot demonstrate
that it applied the correct rigor anywhere in the chain, even where it did apply
it.

**There is no tooling defect and no authoring rule was violated** — the argument
is simply missing. The `MUT-009` detector exists to catch unsupported ASIL
downgrades and it fires correctly: the corpus does carry an ASIL assignment for
which no supporting argument exists.

**Resolution: NOT RESOLVED, and it cannot honestly be resolved in this
revision.** Writing the justification requires an engineering determination —
hazard exposure, system-level integrity, and the aggregate ASIL of the
cell-voltage chain — which this corpus has no basis to assert on its own.
Inventing one would be worse than the gap. No ASIL was changed and no
justification was fabricated.

This finding is also the corpus's own internal acknowledgement of the point
made in `FB2-REV-FND-000022` §5: the ASIL values in this corpus are field
entries without derivation, and they must not be read as an ASIL capability.

### Recorded report outside the validator's scope

**`FB2-REV-FND-000022`** (severity `high`, category `consistency`, disposition
`in_progress`) records that `TRACEABILITY_DOCUMENT.md` at the **repository root**
states ISO 26262 and IEC 61508 compliance evidence and an ASIL-D/ASIL-B
capability. No corpus record was authored against IEC 61508 and it is absent
from the standards lock. The file lies outside the absolute `docs/artifacts/` write
boundary and was **not modified**; it is reported instead. See §4.4.

## 4. Structure Defects Found and Reported, Not Hidden

### 4.1 Duplicated review record

`FB2-REV-000001` exists in two files with identical content:

- `docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json`
- `docs/artifacts/reviews/records/review-vertical-slice.json`

**Effect:** the artifact index de-duplicates on `(profile, id)` and keeps the
first, so no count is inflated. `validate` counts files, so it reports 154
artifact files against 153 indexed records — the difference is exactly this
duplicate.

**Why the validator does not flag it:** duplicate detection is a rule inside the
validator that raises a finding, and the index de-duplication happens upstream of
it, so the duplicate is absorbed silently. This is a real gap in the validator,
not a non-issue.

**Action taken: reported, not deleted.** Removing a file is a corpus owner's
decision, and doing it unrecorded would be the same class of error this report
exists to prevent. It is recorded in the final acceptance report §8 and in
`final-acceptance-report.json` under `reported_defects`.

### 4.2 Redundant link registry copy

`corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json`
holds 51 links that are a strict subset of the 172 in the canonical
`traceability/link-registry/synthetic_reference/links-cell-voltage.json`. The
tool de-duplicates on `(profile, link_id)`, so no count is inflated. Reported,
not deleted.

### 4.3 Stale feature-inventory summary

`sources/feature-inventory.json` carries `summary.total_features: 20` while the
file holds **22** feature records. `corpus.py inventory` reports 22, so the tool
is correct and the summary field is stale. This is the origin of the
previously-reported "All features (20)" coverage target, which has been
corrected under `CORR-COV-013`.

### 4.4 Conformity claim outside the write boundary

`TRACEABILITY_DOCUMENT.md` at the repository root states ISO 26262 and IEC 61508
compliance evidence and an ASIL-D/ASIL-B capability. No corpus record was
authored against IEC 61508. The file is **not** modified — it is outside the absolute
`docs/artifacts/` write boundary — and is recorded as finding
**`FB2-REV-FND-000022`** (severity `high`, category `consistency`, disposition
`in_progress`).

### 4.5 Fifteen governance overclaims corrected

`governance/coverage-plan.json` carried 15 status claims that verification
against disk contradicted. All 15 are now corrected with a recorded reason and
evidence. Two landed on a *different* status than the originally reported
reality suggested, because verification found evidence on both sides; both record
the divergence explicitly. Every `expected_artifacts` and
`capability_attributes` list was retained unchanged, and no artifact was
fabricated to make a status true.

## 5. Integrity Dimensions

| Dimension | Ratio | % | Reading |
|---|---|---|---|
| scope_accounting | 1/1 | 100% | complete |
| artifact_population | 13/13 | 100% | complete |
| standards_mapping | 44/44 | 100% | every locked item has a disposition — but 6 processes and 2 ISO parts are `gap` |
| source_grounding | 76/154 | 49% | 78 records carry no `source_refs`; mostly synthetic, which is expected |
| traceability_integrity | 283/283 | 100% | 0 dangling |
| semantic_consistency_checks | 10/10 | 100% | 21 findings, 0 errors |
| automated_review_coverage | 82/123 | 67% | 41 unique IDs uncovered |
| verification_planning | 16/7 | 229% | over-covered; a ratio, not a score |
| actual_product_evidence | 0/16 | 0% | blocked by policy; no target-hardware member in the enum |
| synthetic_fixture_coverage | 82/43 | 191% | over-covered |
| negative_scenario_validation | 20/20 | 100% | plus 3/3 change lifecycles |
| export_reproducibility | 1/1 | 100% | manifest present, hashes stable |
| human_approval | 0/154 | 0% | pending; none performed |
| production_authorization | 0/154 | 0% | false; by policy |

## 6. What Consistency Does Not Mean Here

A clean validator run establishes that the corpus is **internally** consistent:
schemas hold, links resolve, guards are correct, and mutations are detected. It
establishes nothing about whether the engineering content is right, whether the
records describe the real product, or whether any standard is satisfied. The
corpus is synthetic, no artifact is human-approved, none is
production-authorized, and no target-hardware verification evidence exists.
