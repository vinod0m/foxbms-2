# Traceability Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> Structural traceability integrity only. Nothing here asserts ISO 26262
> conformity, ASIL capability, ASPICE capability level, certification, human
> approval or tool qualification. All 153 indexed records are
> `human_approval_status: pending` and `production_authorized: false`.
>
> Every number is from a live tool run on 2026-09-29.

## 1. Overview

The corpus implements bidirectional traceability as a set of canonical link
registries. Ten relation types are in use. All **283 links resolve, 0 dangling**.

## 2. Link Registry Statistics

| Profile | Links | Share |
|---|---|---|
| `synthetic_reference` | 172 | 61% |
| `as_is` | 111 | 39% |
| **Total** | **283** | **100%** |

Links are de-duplicated by `(profile, link_id)`, so the same `link_id` in two
profiles is two intentional links, not one.

### Redundant registry copy (reported, not deleted)

`corpus/synthetic_reference/traceability/link-registry/synthetic_reference/links-cell-voltage.json`
holds 51 links that are a **strict subset** of the 172 in the canonical
`traceability/link-registry/synthetic_reference/links-cell-voltage.json`. The
tool de-duplicates on `(profile, link_id)`, so no count is inflated anywhere.
The redundant copy is left in place and reported rather than removed
unrecorded.

## 3. Link Type Coverage

| Relation type | Total | `synthetic_reference` | `as_is` | Role |
|---|---|---|---|---|
| `reviewed_by` | 167 | 89 | 78 | review record → artifact under review |
| `verifies` | 32 | 23 | 9 | test measure → requirement (test measure is the **source**) |
| `result_of` | 16 | 11 | 5 | execution → the measure it resulted from |
| `supports` | 16 | 16 | 0 | analysis / TARA → requirement or goal it supports |
| `changes` | 16 | 16 | 0 | change record → artifact it revises |
| `refines` | 13 | 4 | 9 | FSR → safety goal; scenario → parent scenario |
| `allocated_to` | 13 | 7 | 6 | HW/SW requirement → FSR it satisfies |
| `implements` | 6 | 3 | 3 | design → requirement it implements |
| `mitigates` | 2 | 1 | 1 | safety goal → hazard |
| `validates` | 2 | 2 | 0 | test measure → requirement (validation direction) |
| **Total** | **283** | **172** | **111** | |

`reviewed_by` dominates at 167 of 283 links, because every artifact covered by a
review record receives one. That is a direct consequence of automated review
coverage, which is currently 82/123 unique IDs.

`supports` and `changes` are entirely `synthetic_reference`: the TARA, the safety
case, the analyses and the three change records exist only in that profile, so
there is no `as_is` artifact for them to link to. `validates` is entirely
`synthetic_reference` for the same reason — the only two validating links are
both from `FB2-VER-TMS-000009`, to `FB2-SAF-SGO-000001` and to the project scope
record `FB2-MAN-SCO-000001`, and that test measure is synthetic.

### Link review state

| State | Count | Share |
|---|---|---|
| reviewed | 231 | 82% |
| pending | 52 | 18% |

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

Coverage: **20/20 mutations; 3/3 change lifecycles.**

## 9. Traceability Limitations

1. **System requirements layer absent.** `SYS.1` and `SYS.2` are `gap`. No
   vertical chain can reach above the functional safety requirement level.
2. **`verifies` direction convention** is documented in `FB2-REV-FND-000001` and
   will mislead a reader who inspects only the source side.
3. **52 links are `pending` review state** (18%).
4. **41 unique artifact IDs are covered by no review record**, so their
   `reviewed_by` links do not exist and automated review coverage is 67%
   (82/123).
5. **The link-direction convention question is unresolved** and belongs jointly
   to the corpus owner and the schema owner.
6. **A redundant link registry copy** exists under `corpus/`; it is
   de-duplicated by the tool and inflates nothing.
