# The approval ledger

**This ledger is empty. That is the state of this corpus, and it is a measured
state rather than a placeholder.**

```
docs/artifacts/governance/approval-ledger.jsonl    0 entries
```

Zero lines means zero approvals. It is not a ledger awaiting its first entry by
accident: no code path in this repository appends to it, and none may be added
without a person. `corpus.py selftest` reads the file on every run and fails the
suite if a non-empty entry appears.

The machine-readable contract is
`docs/artifacts/governance/role-and-review-policy.json#/approval_ledger_contract`
(amendment `APPROVAL-LEDGER-A1`), and `corpus.py` reads it from there rather than
restating it. The design decision is recorded at
`docs/artifacts/governance/corpus-policy.json#/review_policy/approval_ledger_amendment`.

---

## Why this file exists

An approval used to be recorded as a `revision_history` entry. That was not a
stylistic choice, it was a contradiction:

- a `revision_history` entry at a new revision **is** a content change, so the
  record's `revision` must move;
- every link that pins that record's revision goes stale when it moves; and
- every review record stores a `sha256` of that record, so all of them are
  invalidated when it moves.

An approval therefore could not be recorded without breaking two controls that
nobody had authorised breaking. The workaround was to record the approval against
the *current* revision — which satisfied the validator and was never ratified as
policy (it sat as open item P3 in `closing-list.md` §1.6).

The fix is to stop treating an approval as a change to the thing it approves. It
is not one. It is an event **about** the record, and events belong somewhere
append-only.

## What an entry carries

One JSON object per line, in approval order, append-only. Each entry carries at
least:

| field | what it is |
| --- | --- |
| `ledger_id` | unique within the ledger |
| `record_id`, `profile` | the pair is the key (`ID-RULE-004-A1`) |
| `kind` | `human_approval` or `production_authorization` |
| `approved_record_sha256` | the **content digest** of the record at the moment of signing |
| `approved_content_revision` | the record's content revision at the moment of signing |
| `approved_by` | a named individual, not a role and not a team |
| `role` | a `role_id` declared in `role-and-review-policy.json#/roles` |
| `independence` | `owner_role`, `satisfied`, `evidence`, `policy_ref` — enforced, not asserted |
| `date` | ISO-8601, grammar- and parse-checked |
| `signed_packet` | `{path, sha256}` for a packet under `docs/artifacts/reviews/signed/` |
| `packet_first_commit` | the git commit that first contained that packet |
| `previous_entry_sha256` | the preceding entry's digest, or 64 zeros |

## Why recording one is now free

The record keeps exactly one thing: `approval_ledger_ref`, naming its ledger
entry. That field is **approval metadata, not content**, and the corpus says so
mechanically rather than by convention:

- **the content digest strips it.** The content digest of a record is the
  `sha256` of its bytes with approval metadata removed. A record carrying no
  `approval_ledger_ref` — which is all 321 of them today — therefore has content
  digest equal to the `sha256` of its file bytes, so every one of the 261 stored
  review digests already verifies against it and nothing already verified moves.
- **it is never a `revision_history` entry,** so it does not bump the revision and
  does not stale a link.
- **the review-digest check compares the content digest,** so recording an
  approval cannot invalidate a review digest.

Two self-tests pin this. *"an approval recorded through the ledger stales no link
and invalidates no review digest"* performs the whole recording on a throwaway
copy of the tree and asserts the link state, the review-digest verified count and
the record's revision are all unmoved. *"the content digest ignores approval
metadata and nothing else"* asserts the strip is exactly one field.

## Why an approval is only admissible from `signed/`

An approval citing `docs/artifacts/reviews/packets/…` **fails validation**, with a
message saying the signed packet must be archived first. That tree is regenerated
by `make_review_packets.py`; the generator refuses to overwrite a packet that
already carries a signature, so evidence parked there survives by luck of
ordering rather than by rule. `docs/artifacts/reviews/signed/` is the only
admissible home, and that is enforced rather than described.

## Staleness is a state, not a silent failure

An entry whose `approved_record_sha256` no longer matches the record's current
content digest is **STALE**. Stale is **not invalid**:

- it does **not** fail validation;
- it is **counted** — `approval_staleness` in the coverage output reports
  `stale / total`;
- it is **reported** in a finding that names the record, the ledger entry and
  **which fields changed** — recoverable because every signed packet embeds the
  approved record verbatim under `record_verbatim`, so the validator diffs the
  approved bytes against the current ones rather than printing two opaque digests.

A stale approval is also **not counted in the `human_approval` numerator**, because
that numerator means "records carrying an approval that describes the bytes now on
disk" and a stale one does not. Nothing is discarded: `human_approval` and
`approval_staleness` together account for every approval in the ledger.

The current value is `0 / 0` — there are no approvals to go stale.

---

## The residual limit, stated plainly

> **The chain proves existence, ordering and integrity. It does not prove a human
> read anything, and it does not make an approval unforgeable.**

Stated on one unwrapped line as well, so it cannot be missed by a reader skimming
a wrapped paragraph and cannot be checked only by eye:

RESIDUAL LIMIT: the hash chain proves existence, ordering and integrity; the git anchor proves when and in what state the packet was committed. Neither proves that a human read anything, and none of this makes an approval unforgeable. That limit is irreducible.

Every control below raises the **cost** of forgery and makes forgery
**detectable after the fact**. None of them prevents it.

| control | what it proves | what it does NOT prove |
| --- | --- | --- |
| hash chain across the ledger | the entries exist, are in the order written, and none has been edited, deleted or reordered — deleting or moving any entry breaks the chain from that point on, and `corpus.py` reports the **first** break | that any of it is true |
| `packet_first_commit` + blob present in it | **when** the signed packet was first committed and **in what state** — the bytes the reviewer signed existed in this repository at a known point in its history | **who read them** |
| `signed/`-only admissibility | the cited packet cannot be regenerated out from under the approval | that its contents are honest |
| six-element evidence contract | that a *specific* person, in a *specific* declared role, asserted a *specific* judgement about *specific* bytes on a *specific* date | that the person exists, was competent, or read anything |

A determined person can write all six elements, archive a packet under
`signed/`, cite a real commit, maintain the chain correctly and produce an entry
that passes every check in this repository. **Nothing here distinguishes that from
an approval a competent independent reviewer genuinely gave.** That limit is
irreducible: any attestation can be forged by someone determined to lie, and the
only honest response is to say so rather than to imply otherwise.

Do not describe the hash chain, the git anchor or the archive rule as making
approval unforgeable. They do not, and this file is the place that has to keep
saying so.

---

## Procedure, in order

1. Read the packet for the record:
   `docs/artifacts/reviews/packets/<profile>/<id>.md`.
2. Fill section 9 **in your own copy**. No tool may do this.
3. Archive the signed packet at
   `docs/artifacts/reviews/signed/<profile>/<id>.json`, keeping the twin as you
   signed it. A corrected packet is a new document with a new signature, never an
   edit to a signed one.
4. `python3 docs/artifacts/tools/make_review_packets.py --transcribe <ID> --profile <profile>`
   — resolves both digests and prints the ledger entry and the record's
   `approval_ledger_ref`. **It writes nothing and fills no decision.**
5. A human appends the printed entry to `approval-ledger.jsonl` as one line, and
   merges the printed `approval_ledger_ref` into the record. **Never record the
   approval in `revision_history`.** That is the defect this ledger exists to
   remove, and doing it still stales links and invalidates review digests.
6. Run `python3 docs/artifacts/tools/corpus.py validate` and read the result.
   Zero approval findings means the approval is properly evidenced.
7. Read `approval_staleness` in the coverage output. If a later content change
   invalidates the approval, that figure moves and the finding names what
   changed. That is the mechanism working, not a regression.

## Rules for this file

- **No tool may write here.** `corpus.py`, `make_review_packets.py` and every
  other script in this repository open it read-only.
- **Never edit, reorder or remove an entry.** The chain makes each of those
  detectable, which is the point; do them anyway only to be caught.
- **A ledger entry is never deleted**, on the same grounds a finding record is
  never deleted: a corpus that deletes the record of an approval it granted
  cannot show that it ever granted one.
- **Never hand-type a digest.** Use `--transcribe`.