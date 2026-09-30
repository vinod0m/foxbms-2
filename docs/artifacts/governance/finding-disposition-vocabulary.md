# Finding disposition vocabulary

**Status:** normative for `disposition` on every record under
`docs/artifacts/reviews/findings/`.
**Applies to:** `docs/artifacts/schemas/finding.schema.json`, whose enum is the
machine-readable form of what this file defines.
**Rationale for its existence:** the enum originally had no `resolved` member, and
`accepted` was carrying at least three different jobs across the 38 finding
records. A corpus that cannot tell a closed finding from an open one by machine is
a corpus whose finding count cannot be read, and that is the same failure as
hiding an open defect — it makes the whole set untrustworthy in the other
direction.

---

## The six members

Each member answers one question: *what is the relationship between the condition
this record asserts and the corpus as it stands?*

| member | the asserted condition | the record is a… |
|---|---|---|
| `resolved` | **no longer holds** | closed record. The fix is named, with the record, field or commit and the evidence. |
| `accepted` | **still holds** | upheld, acknowledged, **not** fixed. Real defect, owner and work identified. |
| `rejected` | **never held** | not upheld. The reason the asserted condition is wrong is given. |
| `deferred` | **still holds** | upheld and deliberately not addressed now. The trigger that brings it back is named. |
| `partial` | **still holds in part** | some of it closed, remainder enumerated item by item. |
| `in_progress` | **still holds** | remediation under way, and the work is named. |

### The three distinctions that matter most

- **`resolved` vs `accepted`.** Both can mean "yes, this was real". They differ in
  whether the condition is still there. `resolved` is a closed defect; `accepted`
  is a live one that someone has agreed to carry. Conflating them inflates the
  open count (a reader assumes unresolved work remains) or, worse, deflates it (a
  reader assumes nothing is open).
- **`accepted` vs `deferred`.** Both are "still holds". `accepted` says the
  condition is the corpus's standing position and the work is somebody's ongoing
  obligation. `deferred` says the condition is out of scope *for now* and names
  the event that makes it due again. A deferred finding with no named trigger is
  indistinguishable from an abandoned one, so the trigger is mandatory.
- **`partial` vs `resolved`.** `partial` is not a softer `resolved`. It asserts
  that a specific enumerated remainder is still open. A `partial` record whose
  remainder is empty is a `resolved` record that was not updated, and that is the
  defect finding `FB2-REV-FND-000038` and `FB2-REV-FND-000031` were, in different
  forms.

---

## Which member each class of record gets

| class | disposition |
|---|---|
| the condition no longer holds and the record says so, with the fix named | `resolved` |
| the condition no longer holds and the record still asserts it does | `resolved`, **and** the record's `resolution` is rewritten — see below |
| the condition no longer holds because a later, better-rooted fix addressed it | `resolved`, with the successor named in `resolution` |
| the condition still holds, it is a real defect, work is identified and left to an owner | `accepted` |
| the condition still holds and cannot be fixed in this corpus at all | `deferred`, with the precise unblock condition named |
| the condition still holds and remediation is under way | `in_progress` |

---

## What a `resolved` record must contain

`resolved` is a claim about the world, so it carries the same burden of evidence
as any other claim in this corpus:

1. **The condition that was detected**, stated in the terms the record used.
2. **What fixed it**, cited by record id and field, or by commit, or by the
   validator rule that was corrected. A `resolved` record that says "fixed"
   without naming the fix is not `resolved`; it is `accepted` with better prose.
3. **The evidence** that it no longer holds, re-derived from the corpus now and
   not inherited from the moment of repair.
4. **The residual**, if any. A record may be `resolved` and still name an open
   remainder, in which case the remainder is a separate finding with its own id —
   never a sentence at the end of a `resolved` record. Two records in this corpus
   are in exactly that position and both are cited in the migration note below.
5. `revision` incremented and `revision_history` appended. **A finding record is
   never deleted.** Its existence is part of the audit trail: a corpus that
   deletes the record of a defect it fixed cannot show that it ever had one, and a
   corpus that leaves the record unamended cannot show that it fixed it.

---

## Migration applied to this corpus

All 38 finding records were re-tested against the corpus as it stood, by
`docs/artifacts/tests/audit_findings.py`, and migrated. The result:

| audit class | count | meaning | dispositions applied |
|---|---|---|---|
| `STALE` | 22 | condition no longer holds, record still asserted it did | `resolved`, with `resolution` rewritten to name the fix |
| `CLOSED` | 9 | condition no longer holds and the record already said so | `accepted` → **`resolved`**; prose already correct, only the vocabulary member was wrong |
| `SUPERSEDED` | 2 | condition closed by a later, better-rooted fix | `partial` → **`resolved`**, with the successor named |
| `OPEN` | 5 | condition still holds | kept, with the member chosen per the distinctions above |

The nine `CLOSED` records are the clearest case for the schema change. Each of
them had already been repaired correctly at source and each said so in its own
`resolution` — but each was filed as `accepted`, which under the old enum was the
only member available for a closed finding. A reader scanning dispositions saw
nine records marked with the same word as five live defects. The distinction was
real and the data model could not express it. Adding `resolved` makes it
machine-readable instead of prose-only.

---

## What this vocabulary does not mean

None of these members asserts, and no combination of them asserts:

- human approval of anything, including the finding itself. `human_approval_status`
  is `pending` on every record in this corpus and this document does not change it.
- tool qualification, for any tool, for any purpose.
- ISO 26262 conformity, certification, type approval, or evidence of any of them.
- an ASPICE capability level.
- product verification credit. `product_verification_credit` is `false` and
  `production_authorized` is `false` on every record.

`resolved` means one thing and one thing only: **the condition this record
asserted no longer holds in this corpus, and the record names what changed.**
