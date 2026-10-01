# Traceability Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> Structural traceability integrity only. Nothing here asserts ISO 26262
> conformity, ASIL capability, ASPICE capability level, certification, human
> approval or tool qualification. All **263** indexed records are
> `human_approval_status: pending` and `production_authorized: false`.
>
> Every number is from a live tool run on 2026-10-01.

## 1. Overview

The corpus implements bidirectional traceability as a set of canonical link
registries. **Eleven** relation types are in use. All **489 links resolve, 0
dangling**.

**Link *resolution* is verified. Link *currency* is not, and the difference
matters.** See §1.1.

## 1.1 A measured traceability weakness: 326 links are stale and none is marked suspect

Every link carries both endpoint revisions. Comparing each link's recorded
endpoint revision against the endpoint artefact's current revision, measured over
all 489 links on 2026-10-01:

| Measure | Value |
|---|---:|
| Links whose **both** endpoint revisions match the endpoint artefacts' current revisions | **163** |
| Links with **at least one** endpoint revision that differs | **326** |
| Links carrying `change_suspect_status: true` | **0** |
| Links carrying `change_suspect_status: false` | **489** |
| Artefacts at a revision other than 1 | **109** |

So the corpus holds **326 links whose recorded endpoint revision no longer
matches the artefact they point at**, and marks **none** of them suspect. The
`change_suspect_status` field is `false` on all 489 links, which means it is a
blanket default rather than a derived value.

This is a real gap, not a rounding artefact, and it is the specific shortfall
behind `SUP.11 Traceability Management` being demoted from `mapped` to
`partially_mapped` on 2026-10-01. The corpus's own supporting-process record
says the same thing in its own words
(`FB2-SUP-CFM-000001`, `limitations`): *"Currency of a link's recorded revisions
is not automated. The process describes the control and does not claim the
tooling enforces it."*

What the corpus **does** verify about links, on every run: both endpoints
resolve (0 dangling of 489), every link carries a rationale, provenance and
review state, ordering is deterministic, and de-duplication by
`(profile, link_id)` is stable. What it does not verify is whether a link's
recorded revision is still the artefact's revision.

## 2. Link Registry Statistics

| Profile | Links | Share |
|---|---|---|
| `synthetic_reference` | 372 | 76% |
| `as_is` | 117 | 24% |
| **Total** | **489** | **100%** |

Links are de-duplicated by `(profile, link_id)`, so the same `link_id` in two
profiles is two intentional links, not one.

### Registry file layout (measured, not assumed)

Four registry files hold 540 link entries in total and de-duplicate to 489:

| Registry file | Entries |
|---|---:|
| `traceability/link-registry/as_is/links-cell-voltage.json` | 117 |
| `traceability/link-registry/synthetic_reference/links-cell-voltage.json` | 195 |
| `corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json` | 51 |
| `corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-concept-lifecycle.json` | 177 |

Two of these were previously described as one redundant pair, and that was wrong
in a way that mattered:

- The 51-link `links-cell-voltage.json` under `corpus/` **is** a strict subset of
  the canonical 195-link registry. It is redundant. It is left in place and
  reported rather than removed unrecorded.
- The 177-link `links-concept-lifecycle.json` is **not** a duplicate. The
  canonical tree holds **no counterpart for it** — those 177 links exist in
  exactly one place in the repository, and removing that file would delete them.
  Describing it as redundant would have invited exactly the wrong action.

540 − 51 = 489, which is the de-duplication arithmetic exactly.

## 3. Link Type Coverage

| Relation type | Total | `synthetic_reference` | `as_is` | Role |
|---|---|---|---|---|
| `reviewed_by` | 229 | 151 | 78 | review record → artifact under review |
| `verifies` | 55 | 46 | 9 | test measure → requirement (test measure is the **source**) |
| `allocated_to` | 46 | 37 | 9 | HW/SW/system requirement → FSR it satisfies |
| `refines` | 41 | 32 | 9 | FSR → safety goal; scenario → parent scenario |
| `result_of` | 33 | 28 | 5 | execution → the measure it resulted from |
| `supports` | 29 | 29 | 0 | analysis / TARA → requirement or goal it supports |
| `changes` | 16 | 16 | 0 | change record → artifact it revises |
| `implements` | 13 | 7 | 6 | design → requirement it implements |
| `validates` | 12 | 12 | 0 | test measure → requirement (validation direction) |
| `depends_on` | 12 | 12 | 0 | artifact → artifact it depends on |
| `mitigates` | 3 | 2 | 1 | safety goal → hazard |
| **Total** | **489** | **372** | **117** | |

`reviewed_by` dominates at 229 of 489 links, because every artefact covered by a
review record receives one. That is a direct consequence of automated review
coverage, which is currently **144/224** distinct IDs — **80** IDs carry no
review link at all.

`supports`, `changes`, `validates` and `depends_on` are entirely
`synthetic_reference`: the TARA, the safety case, the analyses, the three change
records, the validation measures and the concept-lifecycle chain exist only in
that profile, so there is no `as_is` artefact for them to link to. That is
profile isolation working as designed, and it is also why four of the eleven
relation types carry no evidence about the real product at all.

### Link review state

| State | Count | Share |
|---|---|---|
| reviewed | 414 | 85% |
| pending | 75 | 15% |

## 4. The `verifies` / `validates` Direction Convention

**The test measure is the source; the requirement is the target.** A
well-verified requirement therefore appears as a link **target**, never as a
source.

This is not a stylistic choice — it is load-bearing, and getting it backwards
produces a false conclusion. The corpus validator's rule inspects only the
**source** side of a `verifies`/`validates` relation, because it is the missing
verification-link detector used by mutation scenario `SCN-MUT-*`. Under the
corpus's own convention that rule can never be satisfied by a requirement that
*is* verified, so it fires on every verified safety requirement.

This is recorded as finding **`FB2-REV-FND-000001`**, which states the honest
reading for a reviewer:

> Verification links must be examined on **both** sides before concluding that
> a safety requirement is unverified.

The check was deliberately left unchanged. Relaxing it would suppress a genuine
detector the corpus needs for its mutation scenarios. The correct fix is a
joint decision about link-direction convention between the corpus owner and the
schema owner, not something a finding record can settle.

## 5. Worked Trace: Cell Voltage Protection Chain

Reproduce with `python3 docs/artifacts/tools/corpus.py trace <ID>`.

```
FB2-SAF-HAZ-000001  (hazard, as_is + synthetic_reference)
  <-mitigates- FB2-SAF-SGO-000001  (safety goal, FTTI 100 ms, asil ASIL_D)
      <-refines- FB2-SAF-FSR-000001  cell voltage acquisition and validation
      <-refines- FB2-SAF-FSR-000002  SOA voltage limit monitoring with debounce
      <-refines- FB2-SAF-FSR-000003  contactor opening on SOA violation
      <-refines- FB2-SAF-FSR-000004  independent hardware voltage monitor

  FB2-SAF-FSR-000001 <-allocated_to- FB2-HW-TSR-000001, FB2-HW-TSR-000002
  FB2-SAF-FSR-000001 <-allocated_to- FB2-SW-SWR-000001
  FB2-SAF-FSR-000002 <-allocated_to- FB2-SW-SWR-000002
  FB2-SAF-FSR-000003 <-allocated_to- FB2-HW-TSR-000003, FB2-SW-SWR-000003
  FB2-SAF-FSR-000004 <-allocated_to- FB2-HW-TSR-000004

  FB2-SAF-FSR-000001 <-verifies-    FB2-VER-TMS-000003
  FB2-SAF-FSR-000002 <-verifies-    FB2-VER-TMS-000001, -000008, -000011
  FB2-SAF-FSR-000003 <-verifies-    FB2-VER-TMS-000002, -000008, -000011
  FB2-SAF-FSR-000004 <-verifies-    FB2-VER-TMS-000004, -000008, -000011

  FB2-SAF-FSR-000002 <-supports-    FB2-SAF-SEC-000003
  FB2-SAF-FSR-000003 <-supports-    FB2-SAF-TAR-000001
  FB2-SAF-HAZ-000001 <-changes-     FB2-MAN-CHG-000001
  FB2-SYS-HSI-000001 <-changes-     FB2-MAN-CHG-000002
```

Both profiles carry the chain. `FB2-SAF-FSR-000004` additionally has
lateral peers, being the shared refinement target of `FB2-REV-000001`,
`FB2-REV-000009` and `FB2-REV-000010`.

### Where this chain stops

- There is **no functional safety concept or technical safety concept record**
  anywhere above the safety goal.
- The **highest-level unmet link is the system requirements layer**: no system
  requirement record exists in either profile, so the chain cannot be extended
  from FSR to a system requirement. This is `SYS.2`, recorded `gap` under
  `CORR-COV-002`.
- No execution in this chain is target-hardware evidence.

## 6. Cybersecurity Chain

New since the previous revision of this report and fully resolvable:

```
FB2-SAF-TAR-000001  (tara: 8 threats, 9 mitigations, item_and_scope defined)
  -supports-> FB2-SAF-SEC-000001  authenticated/confidential transport
  -supports-> FB2-SAF-SEC-000002  bounded connection admission, resource budget
  -supports-> FB2-SAF-SEC-000003  message integrity and freshness (CAN)
  -supports-> FB2-SAF-SEC-000004  framing, integrity, authorisation (serial)
  -supports-> FB2-SAF-SEC-000005  strong entropy for security parameters
  -supports-> FB2-SAF-SGO-000001, FB2-SAF-FSR-000001, -000002, -000003
  -supports-> FB2-SAF-SCS-000001  (safety case skeleton)
  -supports-> FB2-SAF-SEC-000001 -supports-> FB2-SAF-SGO-000001

  each of SEC-000001..000005 <-reviewed_by- FB2-REV-000003, FB2-REV-000009, FB2-REV-000012
```

The chain runs threat → security requirement → safety goal and **stops**. There
is no communication-specific hazard, safety goal or FSR, and no design, test
measure or execution for any of the five security requirements.

## 7. Change Lifecycle Traceability

Three change records, each with a full lifecycle scenario:

| Change record | Target | Scenario |
|---|---|---|
| `FB2-MAN-CHG-000001` | `FB2-SAF-HAZ-000001` (cell voltage max limit 4200 → 4150 mV) | `FB2-SCN-CHG-000001` |
| `FB2-MAN-CHG-000002` | `FB2-SYS-HSI-000001` (AFE front-end migration LTC6811 → ADI) | `FB2-SCN-CHG-000002` |
| `FB2-MAN-CHG-000003` | SOA debounce counter defect | `FB2-SCN-CHG-000003` |

All 3 change-lifecycle scenarios validate structurally complete
(`scenario-test` gate: 3/3).

## 8. Mutation Scenario Traceability

20 mutation scenarios under `corpus/scenarios/mutations/`, each injecting a
specific defect and asserting that the validator detects it. All 20 pass. Two
mutation artifacts (`FB2-SCN-MUT-000001`, `FB2-SCN-MUT-000002`) record the first
two as corpus records.

Coverage: **20/20 mutations detected by the rule each declares; 3/3 change lifecycles.**

## 9. Traceability Limitations

1. **Link revision currency is not maintained.** 326 of 489 links record a stale
   endpoint revision and **none** is marked `change_suspect_status: true`. See
   §1.1. This is the largest traceability limitation and the reason `SUP.11` is
   `partially_mapped`.
2. **The system-architecture layer is absent.** `SYS.3` is
   `partially_mapped` with no system-architecture record, and `SYS.2` has no
   system modes/states and no system-level interface requirements. No vertical
   chain can be traced *through* an architecture that does not exist, even though
   both safety concepts now exist and the `as_is` profile has no system records
   at all.
3. **`verifies` direction convention** is documented in `FB2-REV-FND-000001` and
   will mislead a reader who inspects only the source side.
4. **75 links are `pending` review state** (15%).
5. **80 distinct artifact IDs are covered by no review record**, so their
   `reviewed_by` links do not exist and automated review coverage is **64%**
   (**144/224**). The unreviewed set includes every `post_development_record`,
   `process_record`, `measurement_plan`, `risk_register`, `project_plan`,
   `stakeholder_need`, `use_case` and `safety_concept` record — which is to say,
   the records the process-coverage claims rest on.
6. **The link-direction convention question is unresolved** and belongs jointly
   to the corpus owner and the schema owner.
7. **A redundant link registry copy** exists under `corpus/` (51 links, a strict
   subset of the canonical 195); it is de-duplicated by the tool and inflates
   nothing. Its 177-link `links-concept-lifecycle.json` sibling is **not**
   redundant and must not be treated as such.
8. **4 of the 11 relation types carry no `as_is` evidence at all** — `supports`,
   `changes`, `validates` and `depends_on` are entirely `synthetic_reference`,
   because the artefacts they would connect exist only in that profile. A
   relation-type census that does not split by profile would hide this.
