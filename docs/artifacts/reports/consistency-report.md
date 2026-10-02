# Consistency Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> Semantic consistency results only. Nothing here asserts ISO 26262 conformity,
> ASIL capability, ASPICE capability level, certification, human approval or
> tool qualification.
>
> Guard fields, corpus-wide: every one of the **263** indexed records carries
> `human_approval_status: pending` and `production_authorized: false`. **No human
> has approved anything in this corpus.**
>
> Every number is from a live run of `corpus.py validate` and `corpus.py
> selftest` on 2026-10-01.

## 1. Headline Result

| Measure | Value | Which population |
|---|---|---|
| Schema-validated artifact files | **286** | `validate`: 263 corpus records + 23 scenario records |
| Unique `(profile, id)` records in the index | **263** | `load_artifact_index` |
| Distinct artifact IDs across both profiles | **224** | `automated_review_coverage` denominator |
| Validator findings raised this run | **4** | provenance observations; **none is an error** |
| **`finding` artifacts recording standing conditions** | **42** | `artifact_type: finding` |
| **Errors** | **0** | — |
| Check categories executed per run | 10 / 10 | declared count of categories |
| Toolchain self-tests | **48 PASS, 0 FAIL** | — |
| Mutation scenarios | 20 / 20 detected | executed, each by the rule it declares |
| Change lifecycles | 3 / 3 structurally complete | 19/19 content checks each |
| Acceptance suite | **PASSED** (8 stages, 14 gate lines, 0 FAIL) | — |

**4 findings, 0 errors** is the honest validator state: the validators raise 4
observations and none of them is an integrity error. All four are provenance
observations — three anchors whose Altium design files live in the external
`foxBMS2_hw` repository and cannot be hashed from here, and four anchors whose
symbol is prose rather than a plain identifier, so their occurrence is not
machine-verifiable. The acceptance gate reads `[PASS] validate`.

That figure was **21** before the remediation pass in §6, and **9** at
`CORR-COV-015`. It fell because one rule that read the wrong endpoint of the
`verifies` link was producing false gaps (`FB2-REV-FND-000029`), and because the
provenance workstream repaired the anchor set. **No finding was removed by
relaxing a check**, and the `verifies`-direction rule is still in place and still
fires.

The **42** figure is a different thing and is not a discrepancy. It counts the
first-class `finding` records under `reviews/findings/`, which transcribe and
disposition standing conditions so they are legible rather than buried in
validator output. The counts do not correspond one to one and never did: a single
record can transcribe several conditions, one record can be a pure rule artefact
that no longer produces validator output, and one record (`FB2-REV-FND-000022`)
records a defect outside the corpus write boundary that the validator cannot see
(§4.4). By severity: **32 `medium`, 9 `high`, 1 `low`, 0 `critical`.**

## 2. The 10 Check Categories

`corpus.py` executes 10 check categories on every run. The
`semantic_consistency_checks` coverage dimension reports 10/10.

| # | Category | What it enforces | Result |
|---|---|---|---|
| 1 | JSON parseability | every corpus/review/scenario file parses | pass |
| 2 | Schema validation | every record validates against its type schema | pass, 26 schemas, 286 files |
| 3 | Link validity | no dangling link; no invalid relation type | pass, **547 links, 0 dangling** |
| 4 | Source-reference resolution | every `source_refs` entry resolves to a registry anchor | pass |
| 5 | Provenance / guard fields | no `production_authorized: true`, no approved artifact | pass, 0 violations this run |
| 6 | Semantic rules | `execution_kind`/`outcome` enums, FTTI budget arithmetic | pass |
| 7 | Profile isolation | no cross-profile contamination of derived records | pass |
| 8 | Duplicate detection | no duplicate ID within a profile | pass, but see §3 |
| 9 | Export consistency | two exports produce identical content hashes | pass |
| 10 | Source registry pinning | the source registry is pinned to baseline commit `308028fb` | pass |

## 3. Findings, and What Each One Actually Says

The 30 `finding` artifacts under `reviews/findings/` fall into **four families
plus one recorded report**, and the remediation pass in §6 added a fifth family
of its own (`FB2-REV-FND-000030`, declared-forward references). Conflating them
would be a mistake, because two families are genuine gaps and one was a rule
artefact that has since been corrected at source.

Note that the corpus validator itself raises **9** findings; the 30
`finding` artifacts are the transcribed, dispositioned records of standing
conditions, and include one (`FB2-REV-FND-000022`) that records a defect
outside the corpus write boundary rather than a validator output.

### Family A — `verifies`-direction mismatch (7 of 12, `FB2-REV-FND-000001`…`000007`) — **RULE CORRECTED**

**Verbatim rule text:** `safety requirement has no verifies/validates link`

**The literal statement was accurate and the rule was wrong.** The rule inspected
only the **source** side of a `verifies`/`validates` relation. The corpus's
convention, and the direction master prompt §13 declares, is that the **test
measure is the source and the requirement is the target**, so a correctly
verified requirement appears as a link *target*, never as a source.
`FB2-SAF-FSR-000001` in profile `as_is` is the target of at least one
`TMS → FSR` verifies link, but is the source of none — which is what the rule
tested, so the rule could never clear the finding it raised.

Measured link census on the registry: `verifies` links run TMS→FSR (15),
TMS→SWR (10), TMS→TSR (7); `validates` links run TMS→SCO (1), TMS→SGO (1).

**The rule is not wrong to exist** — it is the missing-verification-link detector
that the mutation scenarios depend on. But its firing on a well-verified
requirement is a direction mismatch between the rule and the registry
convention, not a traceability defect.

**Resolution: RESOLVED by fixing the rule's endpoint, not by relaxing it.**
`corpus.py` now reads the link's **target**, which is the direction §13 declares.
The rule still fires for a safety requirement with no verification at all, and it
is now *harder* to satisfy by accident than before, because a requirement that
appears as the **source** of a `verifies` link is a malformed link and no longer
counts as verification of that requirement. Three self-tests were added to
`cmd_selftest` to hold both directions open: a correctly directed link is not
flagged, a requirement with no link is flagged, and a link with the requirement as
source is flagged. See `FB2-REV-FND-000029` and §6.

Every other rule that reads a link endpoint was audited for the same inversion and
none was found. The `refines` and `mitigates` rules already read the declared
direction. The `reviewed_by` rule reads the target, which **is** consistent with
how the corpus stores those links (review as source, artefact as target) — but
that storage is the reverse of the direction §13 declares for the relation. That
is a link-convention gap in the **data**, not a rule defect: it produces no false
finding today because the rule is consistent with the storage, and correcting it
would mean rewriting 229 links. It is reported here, not fixed.

**Honest reading for a reviewer, after the correction:** a safety requirement that
still raises this finding genuinely has no `verifies` or `validates` link pointing
at it in either direction. Before the correction the opposite was true — a reader
who trusted the finding literally went looking for missing test evidence that was
in fact present, and a reader who dismissed it as a rule artefact dismissed it for
Family B too, where dismissal would have been **wrong**.

### Family B — security requirements genuinely unverified (5, `FB2-REV-FND-000008`…`000012`)

**Same verbatim rule text, but a real and open gap.** `FB2-SAF-SEC-000001` …
`FB2-SAF-SEC-000005` — authenticated transport, bounded connection admission,
CAN message integrity and freshness, serial-link framing and authorisation,
strong entropy and component governance — carried the entire cybersecurity
requirement set with **no verification link in either direction**. Each now has a
correctly directed `verifies` link to a measure with a declared oracle basis
(`FB2-VER-TMS-000016`…`000020`). What they still do not have is **verification
evidence**: every paired execution record carries `execution_kind: none` and
`outcome: blocked`, and a plan is not an outcome. These five findings are
therefore still open, on the point that no test has been run.

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

### Corrected under explicit owner authorisation

**`FB2-REV-FND-000022`** (severity `high`, category `consistency`, disposition
`accepted`) recorded that `TRACEABILITY_DOCUMENT.md` at the **repository root**
stated ISO 26262 and IEC 61508 compliance evidence and an ASIL-D/ASIL-B
capability, and additionally carried a fabricated human-approval sign-off block.
No corpus record was authored against IEC 61508 and it is absent
from the standards lock. The file lies outside the absolute `docs/artifacts/` write
boundary, so the repository owner **explicitly authorised amending it** and it was
corrected on 2026-09-29 (finding revision 3). See §4.4.

## 4. Structure Defects Found and Reported, Not Hidden

### 4.1 Duplicated review record — **closed**

`FB2-REV-000001` previously existed in two files with identical content
(`corpus/as_is/reviews/records/review-vertical-slice.json` and
`reviews/records/review-vertical-slice.json`), and the index absorbed the second
silently because de-duplication happens upstream of the duplicate-detection rule.
**That duplicate has been removed.** `docs/artifacts/reviews/records/` now holds
**15 files for 15 review records**, and measured over the corpus **every
`(profile, id)` pair is unique** — the index collapses nothing.

The validator gap that let it pass silently is unchanged: duplicate detection
runs inside the validator while index de-duplication runs upstream of it, so a
future duplicate would again be absorbed without a finding. That is worth fixing
in the tool and is outside this workstream's boundary.

### 4.2 Redundant link registry copy

`corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json`
holds 51 links that are a strict subset of the **195** in the canonical
`traceability/link-registry/synthetic_reference/links-cell-voltage.json`. The
tool de-duplicates on `(profile, link_id)`, so no count is inflated. Reported,
not deleted.

**Its sibling is not redundant.** `…/links-concept-lifecycle.json` holds 177
links and the canonical tree has **no counterpart for it** — those links exist in
exactly one place in the repository. Describing it as a duplicate would have
invited deleting 177 real links.

### 4.3 Link revision currency — **open, and larger than any defect above**

Measured over all 547 links: **326 record an endpoint revision that differs from
the endpoint artefact's current revision, and all 489 carry
`change_suspect_status: false`.** The `change_suspect_status` field is therefore
a blanket default, not a derived value, and 109 artefacts have moved past
revision 1 without any link being marked suspect.

This is recorded as `SUP.11 Traceability Management = partially_mapped` and as
`FB2-REV-FND-000029`'s subject area. It is not a validator finding because no
rule checks it — the tool verifies that a link *resolves*, never that its
recorded revision is *current*.

### 4.3 Stale feature-inventory summary

`sources/feature-inventory.json` carries `summary.total_features: 20` while the
file holds **22** feature records. `corpus.py inventory` reports 22, so the tool
is correct and the summary field is stale. This is the origin of the
previously-reported "All features (20)" coverage target, which has been
corrected under `CORR-COV-013`.

### 4.4 Conformity claim in the hand-authored root document — corrected

`TRACEABILITY_DOCUMENT.md` at the repository root **stated** ISO 26262 and IEC 61508
compliance evidence and an ASIL-D/ASIL-B capability, and additionally carried a
`Status: APPROVED` document-control block naming a safety engineer as reviewer and
a safety manager as approver. No approval of that kind ever existed, and no corpus
record was authored against IEC 61508. The file is outside the absolute
`docs/artifacts/` write boundary, so the **repository owner explicitly authorised
amending it**; it was corrected on 2026-09-29 and the finding is recorded at
**`FB2-REV-FND-000022`** (severity `high`, category `consistency`, disposition
`accepted`), now at revision 4.

What was changed: the compliance sentence, the IEC 61508 clause rows and the
fabricated sign-off block were removed; a non-conformity READ FIRST header was
added; every ASIL value was relabelled hypothetical at the point of use including
the artifact-type definition table; the standards table was retitled a reference
index with a preamble corrected so it no longer implies the IEC rows are corpus
references; and the false "automatically generated" provenance claim was replaced
with the truth that the file is hand-authored and drift-prone.

**Finding revision 4, 2026-09-29: the durable fix is implemented and the drift
risk is closed by construction.** The document is now generated —
`corpus.py render` emits
`docs/artifacts/views/traceability/traceability-document.md` from the canonical
records through the same view preamble as the other generated views, with every
figure computed at render time — and both hand-authored copies (the repository-root
file and `docs/artifacts/reports/TRACEABILITY_DOCUMENT.md`) were reduced to
short, content-free pointers to that single canonical document. A hand-maintained
control was never a control; there is now nothing to hand-maintain.

The same pass repaired a second instance of the same defect class:
`negative_scenario_validation` counted scenario **files** rather than executing
them, so it read 20/20 while the mutation gate was broken. It now runs the suite
and reports passes (§5).

### 4.5 Fifteen governance overclaims corrected

`governance/coverage-plan.json` carried 15 status claims that verification
against disk contradicted. All 15 are now corrected with a recorded reason and
evidence. A **sixteenth** correction, `CORR-COV-016`, was recorded on 2026-10-01:
the first fifteen read each disposition and asked whether the corpus
contradicted it, which cannot detect a disposition naming a process that **no
artefact references at all** — the case for `SWE.3`, which sat at `mapped` with
zero referencing artefacts. `CORR-COV-016` derives every process's backing set
from each artefact's own `standards_mappings[].reference` and asks whether those
records carry the engineering the process defines. It demoted 23 of the 28
applicable ASPICE processes and 8 of the 10 applicable ISO parts and raised
nothing. Two landed on a *different* status than the originally reported
reality suggested, because verification found evidence on both sides; both record
the divergence explicitly. Every `expected_artifacts` and
`capability_attributes` list was retained unchanged, and no artifact was
fabricated to make a status true.

## 5. Integrity Dimensions

| Dimension | Ratio | % | Reading |
|---|---|---|---|
| scope_accounting | 1/1 | 100% | complete, **presence** check |
| artifact_population | 13/13 | 100% | complete |
| standards_mapping | **33/38** | 87% | ASPICE 25/28 + ISO 8/10 have a disposition naming a resolving artefact. **Not a favourability score** — the ASPICE disposition tally is 4 `mapped` / 21 `partially_mapped` / 3 `gap` and no ISO part is `mapped` |
| source_grounding | **99/263** | 38% | 164 records carry no `source_refs`; mostly synthetic, which is expected |
| traceability_integrity | **489/489** | 100% | 0 dangling, from a link validation re-run for this figure. Resolution yes; **currency no** — see §4.3 |
| semantic_consistency_checks | 10/10 | 100% | 4 findings, 0 errors — **declared** count, not a measurement |
| automated_review_coverage | **144/259** | 64% | **80** distinct IDs uncovered |
| verification_planning | **33/7** | 471% | over-covered; a ratio, not a score |
| actual_product_evidence | **0/33** | 0% | blocked by policy; no target-hardware member in the enum |
| synthetic_fixture_coverage | **173/43** | 402% | over-covered |
| negative_scenario_validation | 20/20 | 100% | **measured**: 20 scenarios executed, 20 detected by their own declared rule; plus 3/3 change lifecycles executed |
| export_reproducibility | 1/1 | 100% | manifest present (**presence**); hash stability is measured by gate [6/8] |
| human_approval | **0/263** | 0% | pending; none performed |
| production_authorization | **0/263** | 0% | false; by policy |

## 6. Remediation Pass — 7 Record Defects and 1 Rule Defect

A separate controlled pass corrected seven defects in existing records and one
defect in the validator itself. Every corrected record had its `revision`
incremented and a `revision_history` entry appended; no history was rewritten.
Every dependent record was regenerated. This section exists so that a reader
comparing an older copy of this report against this one can account for the
difference.

| Finding | Subject | What was corrected | Disposition |
|---|---|---|---|
| `FB2-REV-FND-000023` | `FB2-SAF-SEC-000005` | `safety_goal_ref` `FB2-SAF-SCO-000001` → `FB2-SAF-SCS-000001`; a second instance of the same typo in `FB2-SAF-TAR-000001` THR-008 → `FB2-SAF-SGO-000001` | `accepted`, `reviewed` |
| `FB2-REV-FND-000024` | `FB2-SAF-FSR-000003` | three figures for one chain separated by the point each measures: 40 ms to feedback-open, 35 ms to mechanically-open, 30 ms mechanical | `accepted`, `reviewed` |
| `FB2-REV-FND-000025` | `FB2-SAF-SGO-000001` | `margin_ms` 20 → 15, so 85 + 15 = 100 = the FTTI | `accepted`, `reviewed` |
| `FB2-REV-FND-000026` | `FB2-SAF-FSR-000004` | stale 115 ms removed from two records and from `FB2-ASM-008` in both registries; justification restated on the parameter registry | `accepted`, `reviewed` |
| `FB2-REV-FND-000027` | `FB2-HW-TSR-000004` | Part 4 and Part 5 records separated; coverage criterion resolved to 100 % of the monitored cell set | `accepted`, `reviewed` |
| `FB2-REV-FND-000028` | `FB2-SAF-SEC-000003` | unsatisfiable zero-false-rejection criterion replaced by a rate bound, a required population and a minimum integrity width | `accepted`, `reviewed` |
| `FB2-REV-FND-000029` | validator rule | `verifies` rule reads the link **target**; 3 self-tests added | `accepted`, `reviewed` |

`accepted` is the corpus's closed disposition: `finding.schema.json` has no
`closed` or `resolved` member, and the finding was valid, so the acceptance
stands and the closure is recorded in `resolution`, `revision_history` and
`lifecycle_status: reviewed`. `reviewed` means a review pass read the corrected
records — **not** approved. `human_approval_status` is `pending` on every record
named above, `production_authorized` is `false`, and `product_verification_credit`
is `false`.

**Validator findings: 21 → 9 → 4.** All 12 removed at the remediation pass were
the false gaps of Family A. The further fall from 9 to 4 came from the
provenance workstream repairing the anchor set: three anchors whose Altium design
files live in the external `foxBMS2_hw` repository now report the limitation
instead of a mismatch, and the 2 ASIL-justification findings are dispositioned
against the records themselves. **What remains, and is real:** 3 anchors with
`hash_status: external_design_file_unverifiable_from_this_repository` and
`symbol_unverifiable_prose` on 4 anchors whose claim is about a whole module, a
markdown README, `requirements.txt` or a licence header. None is an integrity
error, which is why `errors=0`.

**What the pass deliberately did not do.** It did not relax, delete or relabel
any check. It did not change the FTTI rule, even though that rule reads
`ftti_ms` and the safety goal names the field `fault_tolerant_time_interval_ms`
— the safety goal's budget now closes whether or not the rule fires, and
`check_references.py` performs the arithmetic the rule cannot. It did not
change the `reviewed_by` link-storage convention, which differs from §13's
declared direction but produces no false finding. It did not author
`FB2-SW-DSN-000004` or `FB2-PIM-IMP-000003` to close the forward references,
because inventing design or improvement content is fabrication; those are
recorded as `FB2-REV-FND-000030`. It did not decide the 50 ms vs 100 ms
weld-detection disagreement between `FB2-SAF-FSR-000003` and
`FB2-HW-TSR-000004`, because no record settles it.

**New tool:** `docs/artifacts/tools/check_references.py` resolves every
id-shaped string in every corpus and scenario record against the artifact index
and the source, assumption, link and parameter registries, and checks the FTTI
arithmetic of every timing allocation and every published `arithmetic_check`
block. It exists because a free-string id inside a payload field is outside
every validator rule's reach, which is how `FB2-SAF-SCO-000001` survived.

## 7. What Consistency Does Not Mean Here

A clean validator run establishes that the corpus is **internally** consistent:
schemas hold, links resolve, guards are correct, and mutations are detected. It
establishes nothing about whether the engineering content is right, whether the
records describe the real product, or whether any standard is satisfied. The
corpus is synthetic, no artifact is human-approved, none is
production-authorized, and no target-hardware verification evidence exists.
