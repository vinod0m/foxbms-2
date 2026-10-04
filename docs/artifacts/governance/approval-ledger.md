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

An approval requires **two** signatures — an approver and an independent
countersigner — under amendment `APPROVAL-COUNT-A1`, recorded at
`role-and-review-policy.json#/approval_countersignature_contract`. What that buys,
and what it does not, is accounted for layer by layer in
**[`forge_resistance`](#forge_resistance--what-each-layer-actually-buys)** below.

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
| `countersignature` | **the second, independent signature** — the countersigner's own full six-element evidence over the **same** packet digest (`APPROVAL-COUNT-A1`) |

Both signatures live in **one** entry, not two. That is deliberate and it is the
whole mechanism: two entries would let a forger drop the countersignature and
leave the chain valid, which is precisely the property the second signature
exists to remove.

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

## `forge_resistance` — what each layer actually buys

**This section is an accounting, not a defence.** It enumerates, one layer at a
time, the specific thing each control establishes and — at least as long — the
specific thing it leaves open. The purpose is that a reader deciding how much
weight an approval can bear should be able to do it from this table alone,
without having to work out for themselves whether "hash-chained" and
"independently countersigned" mean what the words sound like.

Layers are listed in the order an approval passes through them.

### Layer 1 — the six-element evidence contract

**Establishes.** That a *specific* person, holding a *specific* declared
`role_id`, asserted a *specific* judgement about *specific* bytes on a *specific*
date, and cited a packet that exists on disk whose **own recorded** digest equals
the digest they attested. Six separate, independently sufficient obstacles: a
script that writes `approved` fails at element 1; one that pastes a plausible
block fails at element 5 unless a real packet exists whose own
`integrity.record_sha256` is the digest attested; one with a real packet still
fails at element 3 unless the approver is independent of both the record's
`owner_role` and the author of the content being approved.

**Does not establish.** That the person exists, was competent, or read anything.
Independence is *enforced* as a relation between a name, a declared role, a
record's `owner_role` and a `revision_history` author — it is not verified
against any personnel record, because this repository holds no personnel record
and cannot be the authority on who works here.

### Layer 2 — the six-element contract, on the **countersignature** as well

**Establishes.** That a *second, different* person, in a *different* declared
role, which is neither the record's `owner_role` nor any role that authored
content in that record at the revision being approved nor the approver's own
role nor a role the policy excludes for that `owner_role`, attested **the same
packet digest** over **the same revision**. Seven clauses, each checked
separately so a rejection names which one failed.

The same-digest clause is what makes it a *countersignature* rather than a second
review that happened to be filed nearby. Two signatures over different digests are
two separate judgements about two different states of the world, and pairing them
in one entry would imply a concurrence that does not exist.

**Does not establish.** That the second name is a second person. The check is
token-set based on normalised names, so `Ada Lovelace`, `A. Lovelace` and
`lovelace, ada` are correctly recognised as one person and rejected — but a
person who writes a *second invented name in a different shape* satisfies the
check exactly as a genuine second party would. **Nothing in this repository can
tell those two cases apart.** That is not a defect in the check; it is a defect in
the idea that a name is a person, and it is not fixable by any amount of hashing.

### Layer 3 — the hash chain across the ledger

**Establishes.** That the entries exist, are in the order written, and that none
has been edited, deleted or reordered *relative to the others*. Deleting the
middle entry, swapping two entries, or changing one entry's payload breaks the
chain from that point on, and `corpus.py` reports the **first** break by entry
index and `ledger_id` rather than forty break messages.

Because both signatures live in **one** entry, the chain binds them *together*.
Removing the countersignature from an entry changes that entry's digest, which
invalidates every later entry's `previous_entry_sha256`. A forger therefore cannot
drop the second signature and keep the chain intact — they must recompute the
whole tail, which is possible, and which is why this is a cost and not a control.

**Does not establish.** That any of it is true. The chain is a commitment device,
not a truth oracle: it certifies the integrity of a sequence of assertions, not
the correctness of any of them. A chain of one hundred forgeries is a perfectly
valid chain.

### Layer 4 — `packet_first_commit` and the git anchor

**Establishes.** **When** the signed packet was first committed and **in what
state** — that the exact bytes the reviewer signed existed in this repository's
history at a known commit, and that the blob is still present in it. This is the
one layer that anchors an approval to something outside this file: the hash chain
lives only in the ledger, and the packet digest is recomputed from the working
tree, so without the anchor both could be edited in the same commit that records
the judgement.

**Does not establish.** **Who read them.** A git commit records an author field
and a timestamp; it does not record comprehension, and a commit author field is
itself as forgeable as anything else here.

### Layer 5 — `signed/`-only admissibility

**Establishes.** That the cited packet cannot be regenerated out from under the
approval. `docs/artifacts/reviews/packets/` is rewritten on every packet
regeneration; an approval citing it would fail element 5 after the next
regeneration for a reason that had nothing to do with the reviewer's judgement.
Making `signed/` the only admissible home means the evidence cannot be destroyed
by a routine tooling run.

**Does not establish.** That its contents are honest. It is an ordinary directory
with no cryptographic control over it; `git`'s immutability of committed blobs is
the only thing protecting it, and an uncommitted signed packet is protected by
nothing at all.

### Layer 6 — content digests and `approval_staleness`

**Establishes.** That an approval is *about specific bytes*. If the record's
content digest moves after the judgement, the entry goes **stale**: reported in a
finding that names the record, the ledger entry and the fields that changed, and
counted in the `approval_staleness` metric so the invalidation is visible on
every run instead of surfacing months later. The ledger is walked whether or not
any record references it, so a stale approval with a deleted reference is still
reported.

**Does not establish.** That the content is correct. And note what it does *not*
do: `STALE IS NOT INVALID`. A stale approval does not fail `validate` and cannot
turn the suite red, because an editing mistake must not look like a fabrication.

### What all six layers add up to

| | |
| --- | --- |
| **Detects** | tampering with the record after the fact — an edited entry, a deleted entry, a reordered ledger, a signed packet regenerated away, a judgement invalidated by a later content change. |
| **Prevents** | nothing. |
| **Costs a forger** | one to name one person, one to invent a second name in a different shape, one to hold roles satisfying five independence clauses on both sides, one to produce two real packets or one archived packet attested twice, one to cite a real commit containing it, one to recompute the chain tail after every edit. |
| **Cannot** | tell a second real person from a second invented name; prove any signatory read anything; detect a forgery that is internally consistent from the first entry. |

### The residual, restated

**ONE FORGER IS NO LONGER ENOUGH.** Under the single-signature contract a
determined person acting alone could satisfy every clause, because every clause
bound one signature and one signature was all that was ever asked for. Under
`APPROVAL-COUNT-A1` a forgery requires **two** people to both be named, both hold
roles independent of the record's `owner_role` and of every content author, both
attest the same packet digest, and both appear in one ledger entry whose chain
stays intact. That is a real increase in cost and a real change in the kind of
act required.

**TWO COLLUDING PARTIES ARE STILL ENOUGH.** They may collude trivially: one
person writes both names, in two role-shaped forms of a fiction, and every
machine check in this repository passes. The second signature raises the number
of co-conspirators required. It does not change their existence.

**AND NO NUMBER OF SIGNATURES FIXES IT.** A third signature would require three
colluding parties, a fourth four, and the residual does not approach zero with
arity — because the binding is not *how many* people signed but *whether any of
them read anything*. Adding signatures past two buys coordination cost, not
assurance, and at some arity it buys less than the coordination it costs.

**THE LIMIT IS THAT ATTESTATION IS NOT PROOF OF COMPREHENSION.** A signature says
a person asserts. It does not say a person understood, and no digest, chain,
anchor, role declaration, exclusion map or second name converts an assertion into
an understanding. **This limit is irreducible.** It is not a gap in the current
design that a later amendment could close; it is the nature of the instrument.

Do not describe any layer above — including the two independent signatures — as
making approval unforgeable. None of them does.

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
6. **The entry must carry a `countersignature`.** Obtain it from a second,
   independent person before the entry is appended, not afterwards: appending and
   then editing in a countersignature breaks the chain at that entry and every
   entry after it, so the two signatures have to be in the line from the start.
   The countersigner must be a different person, in a role satisfying every
   independence clause for this record's `owner_role`, and must attest the **same**
   packet digest over the **same** revision. See
   `role-and-review-policy.json#/approval_countersignature_contract`.
7. Run `python3 docs/artifacts/tools/corpus.py validate` and read the result.
   Zero approval findings means the approval is properly evidenced.
8. Read `approval_staleness` and the `two-party signature` line in the coverage
   and `check` output. If a later content change invalidates the approval, the
   staleness figure moves and the finding names what changed. That is the
   mechanism working, not a regression.

## Rules for this file

- **No tool may write here.** `corpus.py`, `make_review_packets.py` and every
  other script in this repository open it read-only.
- **Never edit, reorder or remove an entry.** The chain makes each of those
  detectable, which is the point; do them anyway only to be caught.
- **A ledger entry is never deleted**, on the same grounds a finding record is
  never deleted: a corpus that deletes the record of an approval it granted
  cannot show that it ever granted one.
- **Never hand-type a digest.** Use `--transcribe`.