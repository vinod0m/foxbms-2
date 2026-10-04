# The closing list

**What is left, who has to do it, and in what order.**

This document covers the two coverage dimensions of this corpus that cannot move
by authoring:

| dimension | current | why it cannot move by authoring |
| --- | --- | --- |
| `human_approval` | **0/321** | needs a named human who reads a record and signs it |
| `actual_product_evidence` | **0/33** | needs the product running on its own TMS570 hardware |

Every figure below was read from the tree on the date at the foot of this
document, not from a plan. Where a figure is a constant rather than a
measurement, it says so, because the difference matters when you go looking for
the number to move.

> **STATUS 2026-10-04 (second pass) - the approval path is now complete, and
> three of the four residual risks `CORR-COV-022` recorded are closed.**
> Amendment `APPROVAL-LEDGER-A1` moved approvals out of `revision_history` into
> an append-only ledger, so recording one no longer stales a link or invalidates
> a review digest (RISK 4); made an invalidated judgement a **counted and
> reported** state rather than a silent one (RISK 3); and made
> `reviews/signed/` the only admissible home for a signed packet, enforced rather
> than advised (RISK 2). RISK 1 - that a person can forge all six elements - is
> **REDUCED, NOT FIXED**, and is stated as such in four places.
> §0.1, §0.1a, §0.2 and §0.2a below are kept and marked, because they record what
> the corpus looked like before each amendment and why the amendment was needed.
> §1.4, §1.6, §1.8 and §3.1 are rewritten to the rule now in force.
>
> The approval still reads 0/321, and the reason is still a measurement rather
> than a ban: **no approval has been recorded, because producing one needs a
> person.** The ledger at
> `docs/artifacts/governance/approval-ledger.jsonl` is **0 bytes**.

---

## 0. Read this before you start

Three things about the corpus's current state will waste a day if you do not know
them. All three are read from the code, not inferred.

### 0.1 SUPERSEDED - `human_approval` used to be a constant, not a measurement

> **As of 2026-10-04 this section no longer describes the code.** The literal is
> gone. See the note at the top of this document and §0.1a.

`docs/artifacts/tools/corpus.py`, in `_coverage_dimensions()`:

```python
dims["human_approval"] = {"numerator": 0, "denominator": total_art,
                          "detail": "all artifacts pending human approval (none performed)"}
```

The numerator is the literal `0`. The coverage report's own basis table
classifies this dimension as **`constant`**, not `measured`, and says so:
*"0 by corpus policy; every record is `pending`. The policy is enforced by the
`human_approval_rejected` rule, not measured by this dimension."*

**Consequence.** When the first hundred records are approved, this dimension
will still read `0/321`. That is not a sign the signatures failed to land. If you
want the figure to move, changing the dimension to a measurement is a separate,
deliberate decision with its own review - see §1.6.

### 0.1a `human_approval` and `production_authorization` are now measured

Both dimensions are computed from the records, by the **same predicate the
validator enforces** - `_approval_evidence_defects`, reached through
`_approval_dimension_counts()`.

A record counts in the numerator only if its approval field carries a grant
value **and** its `approval_evidence` block satisfies all six elements of
`role-and-review-policy.json#/approval_ledger_contract/required_elements`. A
bare `approved` does not count and does not validate. `production_authorization`
uses the same computation with a **strictly higher** bar (§0.2a).

**Element 6 changed on 2026-10-04 and the numerator followed it.** Until
`APPROVAL-LEDGER-A1` it counted an approval whose ledger... whose
`revision_history` recorded it. It now counts an approval that also resolves to
a live entry in the ledger **and whose ledger entry still describes the bytes on
disk**:

| numerator figure | what it means now |
| --- | --- |
| `evidenced` | granted, all six elements satisfied |
| `evidenced_current` (= the numerator) | ...and the ledger entry's `approved_record_sha256` equals the record's current **content** digest |
| `evidenced_stale` | ...and the record's content has changed since. **Not** counted here; counted in `approval_staleness` (§0.2b) |
| `unevidenced` | granted, elements unmet. Rejected by the validator |

The numerator means *records carrying an approval that describes the bytes now on
disk*. A stale approval does not, so it is not counted - and it is not discarded
either, because `human_approval` and `approval_staleness` together account for
every approval in the ledger.

**What this changes for you.** The figure will move, and it will move only when
an approval is *properly evidenced and current*. If it reads 0 after you have
recorded approvals, they are not properly evidenced - read the validate output,
which names which of the six elements is missing - or they have gone stale, which
`approval_staleness` reports separately. If it moves without you signing anything,
that is §3.1 and it is the worst thing that can happen here.

**The figure is still 0/321, and the reason is now the right kind of reason.** It
is 0 because nothing is approved, not because the dimension cannot see an
approval. The self-test *"human_approval and production_authorization are
measured, not literals"* proves both halves: it reads 0 on the live tree AND it
reads 1/321 on a throwaway copy carrying one properly evidenced, current
approval. A literal could not pass that test.

### 0.2 SUPERSEDED - recording the first approval used to turn `check` RED

> **As of 2026-10-04 this section no longer describes the code.** Recording a
> properly evidenced approval now keeps `check` green. See §0.2a. It was already
> incomplete when written, though, because the prohibition it describes could
> not have been lifted into something that WORKED: the six-element contract it was
> replaced with required the approval to be recorded in `revision_history`, which
> made recording one impossible without collateral damage. That is §0.2b and the
> `APPROVAL-LEDGER-A1` amendment.

Three governance rules fire on the approval fields being anything other than the
"nothing happened" value:

| rule | fires when | severity |
| --- | --- | --- |
| `human_approval_rejected` | `human_approval_status == "approved"` | high |
| `production_authorized_rejected` | `production_authorized == true` | critical |
| `verification_credit_rejected` | `product_verification_credit == true` | high |

The acceptance suite gates on this: `[7/8] no production authority, no
verification credit, no human approval`. So the corpus is presently built so that
**no approval of any kind can be recorded without failing validation.**

That is the correct default for a corpus with zero approvals and the wrong
default for a corpus that has just acquired its first one. Changing it is not a
reviewer's decision to make quietly in the same commit as a signature - it is a
corpus-owner decision, taken in the open, with the rule change and its rationale
in `revision_history`. **This is prerequisite P1 in §1.6 and it must be done
before the first signature is recorded, or the person who signs gets blamed for
breaking the build.**

### 0.2a What replaced the prohibition, and what to expect instead

**A ban is the wrong instrument.** A rule that fails on the value alone cannot
distinguish a fabricated approval from a real one, because it never looks at
one. It could only say "no", never "this one is unsigned", which left the corpus
with two reachable states for approval - absent, and forbidden - and no way to
record the legitimate middle.

**The rule now in force** (`human_approval_rejected`, and its two siblings) is
an **evidence requirement**. The grant value is necessary and **not sufficient**.
An approval passes only if the record itself carries all six elements:

| # | element | what the validator checks |
| --- | --- | --- |
| 1 | the grant value | `human_approval_status` is `approved` or `rejected`. A value alone is never enough. |
| 2 | `approved_by` | a named **person**: at least two tokens, not a declared `role_id` or role name, no token a declared `role_id`, no token from the team vocabulary (`team`, `group`, `board`, `committee`, `reviewers`, `automation`, `system`, `tool`, `agent`, ...). |
| 3 | `role` + `independence` | `role` is a declared `role_id`; `independence` carries `owner_role` (must equal **this record's own** `owner_role`), `satisfied: true`, an `evidence` string of ≥24 characters that is not a placeholder, and a `policy_ref` naming the policy. Then independence is **enforced**, not just asserted: the role must differ from `owner_role` **and** from the author of the last content revision. |
| 4 | `date` | ISO-8601, grammar-checked **and** parse-checked. |
| 5 | `review_packet` | `path` resolves to a `packet.json` on disk under **`reviews/signed/` and nowhere else**; `sha256` equals that file's bytes **now**; `record_sha256_at_signing` equals **the packet's own** `integrity.record_sha256`; the packet's `target.record_id` **and** `target.profile` name this record; its `integrity.record_path` is this record's file. A path under `reviews/packets/` is **rejected** with a message telling you to archive the signed packet first (§0.2c). |
| 6 | `approval_ledger_ref` | an object naming the approval's entry in the append-only ledger `docs/artifacts/governance/approval-ledger.jsonl` - `ledger_id` plus `entry_sha256`. The entry must exist, must name this record's `(profile, id)`, must carry this approval's `kind`, and its `approved_record_sha256` must equal the record's current **content** digest. **NOT a `revision_history` entry** - see §0.2b. |

The finding names **which** element is unmet, numbered, so a reviewer can fix it
in one pass instead of guessing. Example from the suite:

```
FB2-HW-TSR-000001: human_approval_status asserts a recorded human approval decision but the
approval is NOT properly evidenced -- 3 requirement(s) unmet. An approval value alone is not an
approval. Each unmet element is listed below; fix them all in one pass against
docs/artifacts/governance/role-and-review-policy.json#/approval_evidence_contract/required_elements:
    [1] element 1 MISSING: human_approval_status asserts a recorded human approval decision but
        the record carries no 'approval_evidence' block. ...
```

**`production_authorization` is strictly harder, not the same bar twice.** It
requires the same six elements **plus**: the approving role must be one this
corpus grants production authority to (`architect` or `safety_manager`, declared
in the policy with its basis), and the record's `artifact_type` must be one human
approval is required for (`safety_case`, `post_development_record`, `change`).
On a hazard record, production authority is a category error, not a weaker
approval.

**What to expect now.** A properly evidenced approval: `check` stays green,
`human_approval` moves by one, and validate reports no approval finding. An
approval missing any element: `check` goes red **and the finding tells you
which element**. That second case is the guard working. If you see red after
signing, read the message before assuming the rule is wrong.

**Two things this amendment deliberately did NOT do**, so they are not
discovered later as surprises:

* It did **not** record an approval. Producing one needs a person; see §3.1.
* It did **not** relax `human_approval_status: "not_required"`. That value is
  not an approval, the contract does not speak to it, and it still fails for
  want of evidence. Relaxing it is a separate decision nobody has taken.
  **UPDATE 2026-10-04: that decision has now been taken**, by `APPROVAL-NOTREQ-A1`,
  and this bullet describes the state *at the time of that amendment* rather than
  the current one. `not_required` is now **LEGITIMATE**, permitted only on a record
  family that genuinely does not require human approval, rejected on each of the
  three families that does, and never counted toward the `human_approval` numerator.
  The bullet above is left standing rather than rewritten because an amendment that
  is edited in place cannot be audited. See §1.6 P3 and §0.2g.
* It did **not** touch the recursive authority-key scan (`production_release`,
  `authorized_for_production` and eight siblings) or the ASIL / conformity /
  certification claim classes. Those are unchanged, and the self-test *"a
  production grant hidden in a nested key is still caught"* proves nesting a
  claim inside the new `approval_evidence` block does not evade them.

### 0.2b An approval is recorded in the LEDGER, not in `revision_history`

This is the whole of `APPROVAL-LEDGER-A1`, and it exists because the six-element
contract, as first written, was **unsatisfiable in practice**.

**Why it was unsatisfiable.** Element 6 used to require a `revision_history`
entry. A `revision_history` entry *is* a statement that the record's content
moved, so recording an approval through one **forces the revision to bump**. And a
bumped revision breaks two controls nobody authorised breaking:

| what breaks | why |
| --- | --- |
| every link pinning that record's revision | a link states `target_revision`; move the revision and the link is stale |
| every review record storing that record's sha256 | `reviewed_ids[].digest` is recomputed against the file on disk; move the bytes and it no longer matches |

So a properly evidenced approval could not be recorded at all without collateral
damage, and the corpus papered over it by recording the approval against the
record's **current** revision. That was an unratified convention, open P3 in §1.6.

**The tell was the tool's own happy-path self-test.** It had to pick a record
that **no review record covers**, purely so the approval would not invalidate a
stored digest. A test that must choose an uncovered record to demonstrate its own
happy path is demonstrating an unsatisfiable requirement, not a working one.

**What replaced it.** An approval is an **event about** a record, not a change
**to** it. So it goes in an append-only ledger, and the record keeps only a
reference:

```
docs/artifacts/governance/approval-ledger.jsonl     one JSON object per line, 0 bytes today
  ledger_id, record_id, profile, kind,
  approved_record_sha256, approved_content_revision,
  approved_by, role, independence, date,
  signed_packet{path, sha256},
  packet_first_commit,             the commit that first held that packet
  previous_entry_sha256            the preceding entry's digest, or 64 zeros

the record gains exactly one thing:
  approval_ledger_ref: {ledger_id, entry_sha256}
```

**The mechanism that makes it free is the CONTENT DIGEST.** A record's content
digest is its bytes projected through a view in which approval evidence is removed
and approval state is reset to the no-claim values every record already carries.
Two consequences, both measured:

- a record nobody approved projects to **its own bytes**, so all **261** stored
  review digests still verify, unchanged, for all **321** records;
- an approved record projects back to **the file it had before the approval**,
  rendered in that file's own detected layout (the records are a mix of 1- and
  2-space indent, so the layout is probed and verified, never assumed).

The review-digest check compares the **content** digest. Therefore recording an
approval **neither bumps the revision, nor stales a link, nor invalidates a review
digest.** The self-test *"an approval recorded through the ledger stales no link
and invalidates no review digest"* proves it on a record a review record **already
covers** - the record the old test had to avoid:

```
FB2-HW-TSR-000001/as_is: revision 2 -> 2;
  stale-link observations 122/1170 -> 122/1170;
  review digests verified 261 -> 261; mismatch findings 0 -> 0;
  approval landed in revision_history = False (must be False);
  content digest unchanged = True
```

**What it costs, stated rather than glossed.** A review digest no longer pins a
record's *approval state*, so flipping `production_authorized` from `false` to
`true` is not caught by `review_digest_mismatch`. It is caught by four controls
that are stronger for that purpose: `production_authorized_rejected` (which now
requires a complete ledger entry), the recursive authority-key scan, the
ASIL/conformity/certification claim classes, and acceptance gate `[7/8]`. The
division is deliberate: a review digest is a statement about **what was reviewed**,
and an approval is not what was reviewed.

### 0.2c `reviews/signed/` is the ONLY admissible home - enforced

Element 5 used to accept a cited packet from **either** `reviews/packets/` or
`reviews/signed/`, while every packet *told* the reviewer to archive under
`signed/`. Guidance implemented as a permissive rule. Now:

- an approval citing `docs/artifacts/reviews/packets/...` **fails validation**;
- the finding names the archive and says **ARCHIVE THE SIGNED PACKET FIRST**,
  because a reviewer told only that their path is wrong goes looking for a
  different wrong path.

Why this is the right rule and not a technicality: `reviews/packets/` is
**rewritten** by `make_review_packets.py` on every regeneration. The generator
refuses to overwrite a packet that already carries a signature, so evidence
parked there survives by ordering luck rather than by rule - and when it is
finally overwritten, the approval fails element 5 for a reason that has nothing to
do with the reviewer's judgement.

Self-test: *"an approval citing a packet in the regenerated `packets/` tree FAILS
and names the archive"*, which builds a complete approval, re-points its
`review_packet.path` at a real `packets/` file and re-points `sha256` at that same
file, so that admissibility is the *only* thing that can fire - and requires the
rejection to name the archive.

### 0.2d `approval_staleness` - staleness is a state, not a silence

When a record's content changes after an approval, the ledger entry's
`approved_record_sha256` no longer matches. That used to be **correct but
invisible**: the approval simply stopped counting, with no finding and no count.
The only symptom was a numerator that stopped moving, which is indistinguishable
from a reviewer who changed their mind.

Now it is a **first-class measured state**:

- **STALE, not invalid.** It does **not** fail validation. A self-test asserts both
  halves - the stale approval produces zero defects *and* one finding - because a
  fix that only made it visible would leave the invisibility latent in the
  validator, and a fix that only made it non-fatal would leave it unmeasured.
- **Counted.** `approval_staleness` reads `stale / total approvals`, printed by
  `coverage` beside the fifteen dimensions and by `check`. It is a counted METRIC
  and not a sixteenth DIMENSION, because "this corpus has fifteen coverage
  dimensions" is a claim the audit trail relies on.
- **Reported with what changed.** The finding names the record, the ledger entry,
  the two digests, the revision delta and **which fields differ** - recoverable
  because every signed packet embeds the approved record verbatim under
  `record_verbatim`, so the validator diffs the approved bytes against the current
  ones instead of printing two opaque digests.
- **Excluded from the numerator, not discarded.** See §0.1a.

Current value: **0/0**. The ledger holds no entry, so there is nothing to go
stale - a measured zero over an empty population, and the detail string says so
rather than claiming a fact nothing looked at.

### 0.2e The hash chain and the git anchor - and the limit that remains

Two controls were added to raise the **cost** of forging an approval and make
forgery **detectable after the fact**.

| control | what it proves | what it does NOT prove |
| --- | --- | --- |
| hash chain: each entry's `previous_entry_sha256` is its predecessor's digest | the entries exist, are in the order written, and none has been edited, deleted or reordered. Deleting, reordering or editing any entry breaks the chain **from that point on**, and `corpus.py` reports the **first** break | that any of it is true |
| `packet_first_commit`, whose commit and blob presence are both confirmed | **when** the signed packet was first committed, and **in what state** - the bytes the reviewer signed existed in this repository at a known point in its history | **who read them** |

Both are exercised. The chain self-test builds a genuine three-entry chain and
then mutates a copy of it three ways - edits one entry's payload, deletes the
middle entry, reorders two entries - and requires each to be detected at the
first break with exactly one finding. The git-anchor self-test builds a **real
git repository** in a tempdir, commits the archived packet, and requires that
citing the commit which contains it anchors, that citing a non-existent commit is
reported, and that citing a real commit which does **not** contain the blob is
reported.

> **THE RESIDUAL LIMIT, AND IT IS NOT FIXED.** The chain proves existence,
> ordering and integrity. The git anchor proves when and in what state the packet
> was committed. **Neither proves that a human read anything, and none of this
> makes an approval unforgeable.** A determined person can write all six elements,
> archive a packet, cite a real commit and maintain the chain correctly, and
> nothing in this repository can distinguish that from an approval a competent
> independent reviewer genuinely gave. **That limit is IRREDUCIBLE** - any
> attestation can be forged by someone determined to lie. What was added is cost
> and detectability, not prevention.

The limit is recorded in four places so it cannot be quietly dropped:
`corpus-policy.json#/review_policy/approval_ledger_amendment`,
`docs/artifacts/governance/approval-ledger.md`, the docstring of
`CorpusTool._check_ledger_git_anchor`, and
`docs/artifacts/tools/verify_approval_ledger_independently.py`. A self-test reads
the code and the documentation and asserts the wording is still there - because an
anchor that reads as stronger than it is would be worse than no anchor.

### 0.2f The second signature, and what it does *not* buy

A single signature means a single forger. Every layer above binds **one**
signature, so every layer above is satisfied by one person acting alone — which
is why §0.2e's residual is stated as *irreducible* rather than *merely
expensive*. That has now been changed on the cost side, and the change is
recorded in full at
`role-and-review-policy.json#/approval_countersignature_contract`
(amendment `APPROVAL-COUNT-A1`) and, as element 7, enforced in
`corpus.py::_countersignature_defects`.

**The rule.** An approval now requires **two** signatures: the approver and an
**independent countersigner**. The countersigner must be a different person; must
hold a `role_id` declared in `role-and-review-policy.json#/roles`; must not be the
record's `owner_role`, must not be the author of **any** content revision at or
below the revision being approved, must not hold the approver's role, and must
not be a role the policy excludes for that record's `owner_role`. Both signatures
carry the **full six-element evidence** and the **same packet digest**, and both
live in **one** ledger entry — so the hash chain binds them together, and
dropping the countersignature breaks the chain from that entry onward.

**The per-`owner_role` part** is declared in the policy
(`countersigner_excluded_roles_by_owner_role`) and read by the code, not inferred
by it. Eight `owner_role` values on disk are not in `roles[]` at all
(`change_manager`, `configuration_manager`, `cybersecurity_engineer`,
`data_quality_engineer`, `integration_engineer`, `quality_engineer`,
`sys_engineer`, `verification_lead`), so for those records the per-`owner_role`
clause has an empty exclusion set. That is recorded as a **declared gap** rather
than closed by inventing role definitions — see open item P2 in §1.6. Clauses 1–4
and the different-person rule still bind in full for every record.

**What this buys, stated exactly.** One forger acting alone is no longer enough.
A forgery now requires **two** people to both be named, both hold roles
independent of the record's `owner_role` and of every content author, both attest
the same packet digest, and both appear in one entry whose chain stays intact.

**What it does not buy, stated as plainly as the above.** **Two colluding
parties are still enough**, and they may collude trivially: one person writes two
names, in two role-shaped forms of a fiction, and every machine check in this
repository passes. The name comparison is token-set based, so `Ada Lovelace` and
`A. Lovelace` are correctly rejected as one person — but a second *invented* name
in a different shape is indistinguishable from a second real person, and **nothing
here can tell those apart**. And **no number of signatures fixes it**: a third
needs three colluding parties, a fourth four, and the residual does not approach
zero with arity.

**THE LIMIT IS THAT ATTESTATION IS NOT PROOF OF COMPREHENSION.** A signature says
a person asserts. It does not say a person understood, and no digest, chain,
anchor, role declaration, exclusion map or second name converts an assertion into
an understanding. This limit is **irreducible**: it is not a gap a later amendment
could close, it is the nature of the instrument.

**`forge_resistance` — the full layer-by-layer accounting.** What each layer
actually establishes, and what each leaves open, is enumerated at
**`docs/artifacts/governance/approval-ledger.md` § `forge_resistance`**. Six
layers, each with an explicit "does not establish", plus a summary of what the
stack as a whole detects, what it prevents (**nothing**), what it costs a forger,
and what it cannot do. Referenced from here so that a reader deciding how much
weight an approval can bear is never more than one link from the accounting.

**No text in this repository describes any layer — including the two independent
signatures — as making an approval unforgeable.** Four self-tests assert the two
headline rejections, and a fifth asserts the rule is not over-strict (a properly
countersigned approval on a record a review record already covers must be
accepted, and must not stale that review digest). A sixth measures, over all 321
records, that at least two independent signing parties remain available for every
one — because a two-party rule that made approval impossible for some record type
would be a functional regression disguised as a control. Worst case measured: **6
eligible countersigner roles** remain after excluding the owner role, every
content author, the approver's role and the policy's per-`owner_role`
exclusions.

### 0.2g `not_required` — decided, and it is not a loophole

Full reasoning at
`role-and-review-policy.json#/human_approval_not_required_decision`; measured
effect at `coverage-plan.json` `CORR-COV-024`; the decision itself in
`corpus-policy.json#/review_policy/human_approval_not_required_amendment`.

**Decided: LEGITIMATE.** `human_approval_status: "not_required"` is permitted, on
exactly one condition — the record's artefact type must be one that genuinely
does **not** require human approval — and it **never counts toward the
`human_approval` numerator**.

Why it was legitimate rather than left rejected:

- The policy already scoped it and the data model did not represent it.
  `review_policy.additional_fields/human_approval_required_for` is a **positive
  list** of three families, so the scoping could be enforced *negatively* (a bare
  `approved` fails) and never recorded *positively*.
- It was already a member of the enum in `schemas/artifact-base.schema.json` and
  of `approval_semantics.human_approval_status_values`. The schema permitted it
  and the validator rejected it, so `pending` was the only value that was both
  schema-valid and validator-valid — an inconsistency in the corpus, not a policy.
- Two genuinely different states were indistinguishable. A record on a family
  with no sign-off gate, and a record waiting for an approval that will never
  come, both read `pending`.

Why it is not a loophole:

- The boundary is the policy's own positive list, **read** rather than restated,
  from the same block that already governs production authority. On each of the
  three required families — `safety_case`, `post_development_record`, `change` —
  the value is **rejected at high severity** by `human_approval_not_required_misdeclared`,
  reached by *both* validation paths so gate `[7/8]` cannot be blind to it.
- Two contradictions are rejected as well: a `not_required` record carrying an
  `approval_evidence.human_approval` block, and one carrying an
  `approval_ledger_ref` resolving to a `human_approval` ledger entry.
- It cannot move a measured number. It is excluded from the grant test, so it never
  enters `granted`, `evidenced` or `evidenced_now`; the denominator is unchanged at
  every record carrying an id; and the count is reported *inside* the dimension —
  in the detail text and as `not_required_records` / `not_required_misdeclared` —
  so relabelling moves a number that is on the record rather than one that is
  quietly absent.
- **It is not a review exemption.** `automated_review_coverage` counts such a
  record exactly like any other, so a `not_required` record that receives no
  review is a visible gap, not an excused one. This is the hazard worth naming:
  `not_required` is easy to misread as "no review needed", and it records the
  absence of a **sign-off gate**, not the absence of review.

**Residual, stated rather than left implicit.** The obvious abuse — relabelling a
pending record to dodge a future approval — is rejected on exactly the records
where an approval could ever be owed. The failure mode that survives is the
opposite and quieter one: **a record that needed a gate and says `pending` forever
is indistinguishable from one that is simply not due yet, and no rule here detects
that.** And the value is unexercised by the live tree: **0 of 321** records carry
it, so the self-tests are the only evidence the rule works, and they are tests of
the rule rather than of any approval.

### 0.3 `actual_product_evidence` cannot reach 33/33

Also in `_coverage_dimensions()`:

```python
tms = [aid for aid in (...) if "-TMS-" in aid]
target_tms = {d.get("test_measure_id") for d in target_execs} & set(tms)
dims["actual_product_evidence"] = {"numerator": len(target_tms),
                                   "denominator": len(tms), ...}
```

`len(tms)` counts **records**, and `set(tms)` counts **distinct ids**. There are
33 test-measure *records* but only **28 distinct ids**, because five identifiers
are carried by both profiles (`FB2-VER-TMS-000001..000005` exist once in `as_is`
and once in `synthetic_reference`; ID-RULE-004-A1 makes that legitimate). So the
denominator is 33 and the numerator can never exceed 28.

**Consequence.** A complete and honest target-hardware campaign lands at
**28/33**, not 33/33. Do not chase the last five points; they are not
reachable. If a 33/33 figure is wanted, the denominator has to be de-duplicated -
which is a change to a measured dimension and needs its own review.

### 0.4 No hardware run has ever been performed, and the corpus says so

`actual_product_evidence` reads 0, and its detail string names the reason
verbatim: *"0 target-hardware executions: `execution_kind` can now express a run
on the product's own hardware, but none has been performed (blocked, not
fabricated)"*. Of the 44 execution records: **15** `actual_host_run`,
**6** `synthetic_fixture`, **23** `none`. Zero `actual_target_hardware_run`.

Every test measure in the corpus - all 33 records - lacks a target-hardware
execution. Of those, 5 are `as_is` (real foxBMS 2 claims) and 28 are
`synthetic_reference` (the hypothetical reference project). Only the 5 `as_is`
ones are about the product. See §2.

---

## 1. `human_approval` - 0 of 321

### 1.1 The count, and why zero is the correct state

**0 of 321 records carry a human approval.** Every one of the 321 records carries
`human_approval_status: "pending"`, `production_authorized: false` and
`product_verification_credit: false`.

Zero is the **correct and only honest** current state. It is not a defect, not a
regression, and not something to be closed by writing the value. An approval is a
statement that a competent, independent person read a record and concluded it is
correct. Nobody has read 321 records. The corpus is therefore right to report
zero, and any figure above zero that appeared without 321 signatures would be a
fabrication.

### 1.2 Who is required

Named individuals, one per domain competence, each holding the competence the
record's domain demands. Roles and their independence requirements are taken
verbatim from `docs/artifacts/governance/role-and-review-policy.json`. The
`independence` column is that file's own text.

| # | role (`role_id`) | records where this role is `owner_role` | domains | independence (per the policy file) |
| --- | --- | --- | --- | --- |
| R1 | Functional Safety Engineer (`safety_engineer`) | 34 | safety (33), management (1) | Separate from HW/SW authors |
| R2 | System Engineer (`system_engineer`) | 23 | system (22), management (1) | Separate from HW/SW authors |
| R3 | Hardware Engineer (`hw_engineer`) | 10 | hardware | Separate from SW author |
| R4 | Software Engineer (`sw_engineer`) | 82 | software (80), supporting (1), production (1) | Separate from HW author |
| R5 | Verification Engineer (`verification_engineer`) | 82 | verification (81), integration (1) | Separate from implementation authors |
| R6 | Cybersecurity Engineer (`cybersecurity_engineer`) | 17 | verification (11), safety (6) | not named in the policy file - **assign explicitly, see §1.5** |
| R7 | Quality / Process Engineer (`quality_engineer`) | 41 | verification (23), supporting (7), management (4), safety (4), operation, production, system | not named - **assign explicitly** |
| R8 | Project Manager (`project_manager`) | 12 | management (6), supporting (3), decommissioning, release, service | Management role; not technical author |
| R9 | Traceability / Data Engineer (`traceability_engineer`) | 7 | management (3), safety (3), supporting (1) | Separate from content authors |
| R10 | Data Quality Engineer (`data_quality_engineer`) | 4 | management (2), verification (2) | not named - **assign explicitly** |
| R11 | Safety Manager (`safety_manager`) | 1 | management | Independent from technical authors per ISO 26262 |
| R12 | Verification Lead (`verification_lead`) | 2 | verification | not named - **assign explicitly** |
| R13 | Change Manager (`change_manager`) | 3 | management | not named - **assign explicitly** |
| R14 | Configuration Manager (`configuration_manager`) | 1 | management | not named - **assign explicitly** |
| R15 | Integration Engineer (`integration_engineer`) | 1 | verification | not named - **assign explicitly** |
| R16 | System Engineer (`sys_engineer`) | 1 | system | see R2; this spelling appears once, confirm the same person |
| R17 | Domain Reviewer (`reviewer_domain`) | 0 authored; signs as the second reader on every batch | all | Separate from artifact authors |
| R18 | Adversarial Reviewer (`reviewer_adversarial`) | 0 authored; signs the `review` and `finding` batches | all | Maximum independence; separate session/context |
| R19 | System Architect (`architect`) | 0 authored; owns §0.2, §1.6 and §4 decisions | all | Does not author implementation artefacts |

**R6-R16 are not in the role policy file.** The corpus declares eleven roles and
the records use sixteen `owner_role` values. That gap is real and it is not this
document's job to close by invention: **the corpus owner must either add these
roles to `role-and-review-policy.json` or map each to an existing role, and that
mapping must be recorded before their records are signed.** A signature under a
role that the policy does not define is not traceable to a competence
requirement, which is the whole point of requiring one.

`docs/artifacts/governance/role-and-review-policy.json` also declares that human
approval is *required for* `safety_case`, `production_release` and
`change_approval`. Read as a floor, not a ceiling: it does not say the other 318
records are optional.

### 1.3 What they receive

One packet per record, already generated, at:

```
docs/artifacts/reviews/packets/<profile>/<record-id>.md     the reviewable document
docs/artifacts/reviews/packets/<profile>/<record-id>.json   machine-readable twin
docs/artifacts/reviews/packets/INDEX.md                     index, 321 rows
```

Each packet contains, in this order: identity (including that `(profile, id)` is
the primary key); the sha256 of the record's exact current bytes; **the full
record embedded verbatim**; the claims that could be false, derived from the
record's own fields; what is already machine-checked and by which detector, with
**machine-verified / peer-reviewed-and-disputed / unexamined** stated as three
distinct states; the record's own limitations and honesty fields verbatim; the
**2 to 4 questions only a human can answer**; what a signature changes; and an
**empty** signature block.

The reviewer needs no other file open. That is the point: the failure mode this
is built against is a reviewer who cannot tell what has already been checked and
therefore either redoes the machine work or approves something nobody flagged.

Regenerate the packets before each batch:

```bash
python3 docs/artifacts/tools/make_review_packets.py
python3 docs/artifacts/tools/make_review_packets.py --verify
```

Filter to a slice: `--only-type finding`, `--only FB2-SAF-FSR-000001`, or
`--only as_is:FB2-SAF-FSR-000001` when an id exists in both profiles.

### 1.4 What they return

Per record: one **signed packet archived under `signed/`**, one **line appended to
the ledger**, and one small edit to the record. Nothing else.

1. **The signed packet, archived.** Fill section 9 **in your own copy** - no tool
   may do it - and copy the signed packet twin to
   `docs/artifacts/reviews/signed/<profile>/<id>.json`, byte-for-byte as you
   signed it. Keep the `.md` too if you annotated it; the machine-readable twin
   is what the validator checks. **This is the only admissible home.** A citation
   into `docs/artifacts/reviews/packets/` is rejected, because that tree is
   rewritten on every regeneration (§0.2c). A corrected packet is a new document
   with a new signature, never an edit to a signed one.

2. **One line appended to the ledger.** `--transcribe <ID>` prints the entry with
   every machine-readable field resolved. You fill in the human fields - your
   name, role, date - and a human appends the line. The ledger is **append-only**:
   entries are never reordered and never removed, and each entry names its
   predecessor's digest, so a deletion or an edit breaks the chain from that point
   on and the validator says where.

3. **The decision, transcribed into the record by a human:**
   - `human_approval_status`: `approved` or `rejected` (the schema's value set is
     `pending | approved | rejected | not_required`, per
     `role-and-review-policy.json` `approval_semantics`);
   - the full `approval_evidence.human_approval` block of §0.2a: `approved_by`
     as a **person**, `organisation`, `role` as a declared `role_id`, `date` in
     ISO-8601, `independence{owner_role, satisfied, evidence, policy_ref}`, and
     `review_packet{path, sha256, record_sha256_at_signing}` - **both** digests,
     so the record is traceable to the exact packet bytes and the exact record
     bytes that were read. `make_review_packets.py --transcribe <ID>` prints them
     already resolved; it writes nothing;
   - **`approval_ledger_ref: {ledger_id, entry_sha256}`**, naming the line you
     just appended. **Nothing in `revision_history`.** That is the whole point of
     §0.2b and it is the one instruction in this document that is a hard rule
     rather than a convention;
   - `automated_review_status` **left alone**. It describes machine checks
     (`schema_valid`, `links_valid`, `provenance_consistent`,
     `consistency_checks`) and is not a statement about human judgement;
   - `production_authorized` and `product_verification_credit` **left `false`**.
     No signature on a corpus record authorises production or confers
     verification credit. Changing those requires a production-authority role
     (`architect` or `safety_manager`), a record family human approval is required
     for (§0.2a) and **its own ledger entry** - one reference per kind, because a
     human approval and a production grant are different claims.

4. **The comments**, which are the most valuable output. A `reject` with a
   reason is worth more than an `approve`.

**Run `--transcribe` twice, not once.** The digest an approval must cite is the
digest of the **archived signed copy**, and that copy has your signature in it, so
it is a different file from the generated packet and its digest cannot be known
before you have signed it. The first run therefore tells you the digest is *not
resolved* and to archive first; the second run, after the copy exists, resolves it
from the file on disk. A self-test asserts both halves, that both printed digests
are the real ones, that the output contains no decision, and that the packet tree
is byte-identical afterwards.

### 1.5 Independence - what "independent" has to mean here

The corpus has been reviewed so far by automated agent sessions, and says so in
every `reviewer_identity` block: *"This is an automated review: it is NOT
organizational independence, NOT human confirmation, and NOT a qualified-checker
result. No human reviewer, independent party, or separate agent session
participated."* That disclosure is accurate and must not be quietly dropped when
human signatures arrive.

Minimum for a signature to mean anything:

1. **The signer did not author the record.** `owner_role` is on the record; a
   signer in the same role as the record's `owner_role` for its own work is not
   independent. Every packet states the record's `owner_role` in section 1 for
   exactly this comparison.
2. **The signer did not write the machine results.** The packets' section 5 is
   machine-derived. Signing that section is signing a tool's output.
3. **For `safety_case`, `production_release` and `change_approval`** - the three
   the policy names - the policy requires a `safety_manager` for the safety case
   (R11) and independence per ISO 26262.
4. **For the `review` and `finding` batches**, R18 `reviewer_adversarial`, whose
   declared independence is *"Maximum independence; separate session/context"*.
   Those 53 records are themselves statements about the corpus's correctness;
   approving them needs someone who did not produce them.
5. **A second reader for every batch (R17).** The batch is signed by the domain
   owner **and** countersigned by a `reviewer_domain`. 140 of the 321 records are
   covered by no other record in the corpus (see §1.7), and for those a single
   signature is the only reading that will ever exist.
6. **Record who did not sign.** A batch with 40 signatures and 60 omissions must
   say which 60 and why, or the batch is indistinguishable from a batch where the
   other 60 were refused.

### 1.6 What must be decided before the first signature lands

> **Every item that can be decided by amendment has now been decided.** P1 and the
> first two P2 items were decided on 2026-10-04 by `APPROVAL-RULE-A1`; the P3
> revision-convention item and the P2 archive item were decided the same day by
> `APPROVAL-LEDGER-A1`; the `not_required` P3 was decided on 2026-10-04 by
> `APPROVAL-NOTREQ-A1`. They are kept, marked DONE, because they record what was
> decided and why. **One P2 remains OPEN**, and one limit is permanently open by
> nature.

| id | decision | status | why it blocks |
| --- | --- | --- | --- |
| **P1** | Amend `human_approval_rejected` so a **recorded, attributed** human approval is not a validation failure. | **DONE 2026-10-04** (`APPROVAL-RULE-A1`) | Without it the first signature turned `check` RED (§0.2). Done as an evidence requirement over six elements, read from the policy file rather than hardcoded (§0.2a). |
| **P1** | Decide whether `human_approval` stays a constant `0` (§0.1) or becomes a measurement. | **DONE 2026-10-04** - measured, by the validator's own predicate (§0.1a). `production_authorization` likewise, with a strictly higher bar. | Either answer is defensible; leaving it undecided meant nobody could tell whether a landed signature worked. |
| **P2** | Ratify that recording an approval against the record's **current** revision, without bumping it, is the correct convention. | **RESOLVED DIFFERENTLY 2026-10-04** (`APPROVAL-LEDGER-A1`, §0.2b) | The convention was a workaround for an unsatisfiable requirement, so ratifying it would have ratified the workaround. Instead the approval moved out of `revision_history` into an append-only ledger and the record keeps only a reference; recording one now costs nothing anywhere else, so there is no convention left to ratify. Proven by self-test, not asserted. |
| **P2** | Confirm `docs/artifacts/reviews/signed/` as the canonical archive location. | **DECIDED 2026-10-04** (`APPROVAL-LEDGER-A1`, §0.2c) | The open half - whether it is the *only* permitted home - is now decided: yes, and it is **enforced**. A `packets/` citation fails with a message naming the archive. Self-tested. |
| **P2** | Add the **eight** undeclared `owner_role` values to `role-and-review-policy.json`, or map them to declared roles (§1.2). | **OPEN — now the highest-value open item, with a second consequence** | A signature under an undefined role is not traceable to a competence requirement. The approver's `role` must be a **declared** `role_id`, so a record whose `owner_role` is undeclared can still be approved (independence is judged against the owner role, not against the approver's), but the *reviewer's* role must exist in the policy. **Measured correction: this row previously said "seven". The measured figure is EIGHT** — `change_manager`, `configuration_manager`, `cybersecurity_engineer`, `data_quality_engineer`, `integration_engineer`, `quality_engineer`, `sys_engineer`, `verification_lead`. The eighth was not re-asserted against the tree by the pass that recorded it, so the count stood. Since `APPROVAL-COUNT-A1` the same eight also have **no entry** in the countersigner's per-`owner_role` exclusion map, so a countersignature on a record they own is checked **strictly less** than on a record owned by a declared role. That is declared in the policy's `unmapped_owner_role_policy` rather than closed by inventing role definitions. |
| **P2** | Amend `production_authorized_rejected` and `verification_credit_rejected` - or record explicitly that they stay as they are. | **DONE 2026-10-04** (`APPROVAL-RULE-A1`) - both amended to the same evidence requirement. `production_authorization` additionally requires the approving role to hold production authority and the record's family to be one human approval is required for, and since `APPROVAL-LEDGER-A1` its own ledger entry. `verification_credit` takes the same six elements. | A corpus owner should say so rather than leave it ambiguous. |
| **P3** | Decide whether `human_approval_status: "not_required"` should remain rejected. | **DECIDED 2026-10-04** (`APPROVAL-NOTREQ-A1`) - it is **LEGITIMATE**, permitted only where the record's family genuinely does not require approval, and never counted toward the `human_approval` numerator. | It sat open through two amendments, which is a governance question carried without being answered rather than a conservative one. **The decision, on the merits:** `review_policy.additional_fields/human_approval_required_for` is a **positive list** of three families, so the scoping the policy declares could be enforced negatively and never recorded positively — the corpus could reject a bare `approved` but had no way to record that a family has no gate. Meanwhile `not_required` was **already** in the schema enum and **already** listed in `approval_semantics.human_approval_status_values`, so the schema permitted it and the validator rejected it, and `pending` was the only value that was both schema-valid and validator-valid. Two genuinely different states were indistinguishable: a record with no gate, and a record waiting for an approval that will never come. **It is not a bypass:** the value is permitted only on the *complement* of the very list that says where approval is required, and on those three families it is **REJECTED** at high severity by `human_approval_not_required_misdeclared`, reached by both validation paths so gate `[7/8]` cannot be blind to it. Two contradictions are rejected too — a `not_required` record carrying an `approval_evidence.human_approval` block, and one carrying a `approval_ledger_ref` resolving to a `human_approval` entry. **It cannot move a measured number:** it is excluded from the grant test, the denominator is unchanged, and the count is reported inside the `human_approval` dimension as `not_required_records` / `not_required_misdeclared` so relabelling is visible rather than silent. **It is NOT a review exemption:** `automated_review_coverage` counts such a record like any other. Measured: **0 of 321** records carry it, and 0 carry it on a required family. Full reasoning at `role-and-review-policy.json#/human_approval_not_required_decision`; measured effect at `coverage-plan.json` `CORR-COV-024`. |
| **P3** | Ratify the approval-recording convention. | **CLOSED, NOT BY RATIFICATION** | See the P3 row above; superseded by the ledger amendment. |
| **RISK 1** | Make an approval unforgeable. | **NOT POSSIBLE. RAISED COST, CHANGED SHAPE; NOT CLAIMED AS FIXED.** | One forger acting alone is no longer enough since `APPROVAL-COUNT-A1`: a forgery now needs two named people in mutually independent roles, over the same packet digest, in one chain-bound entry. **Two colluding parties are still enough**, trivially, and no number of signatures fixes it. The limit is **irreducible**: attestation is not proof of comprehension. Accounted for layer by layer at `approval-ledger.md#forge_resistance` (§0.2f). Do not describe any of it as making approval unforgeable. |

**The one thing left to do, and it is not engineering.** Every item above is
either decided or explicitly open. What remains is a person reading a record and
deciding whether they can put their name on it. That is §1.7's batches, and the
corpus holds **no** approval because doing it needs a person.

### 1.7 Recommended order

Derived from the corpus, not from intuition: engineering-link degree (excluding
`reviewed_by` links, which inflate review records and are not engineering
dependencies) crossed with review coverage. **52 records are both depended upon
by other records and covered by no review.** They come first.

**Batch 0 - the vocabulary and the safety argument other records depend on.**
Sign before anything that cites them. Approving a derived requirement before its
allocation vocabulary is settled is approving a conclusion whose premises are
unreviewed.

| record | type | `owner_role` | engineering links | signer |
| --- | --- | --- | --- | --- |
| `FB2-SAF-VOC-000001` (`synthetic_reference`) | `controlled_vocabulary` | safety_engineer | 4 | R1 |
| `FB2-SAF-TSC-000001` (`synthetic_reference`) | `safety_concept` | safety_engineer | 15 | R1 |
| `FB2-SAF-TAR-000001` (`synthetic_reference`) | `tara` | safety_engineer | 10 | R1 |
| `FB2-SAF-SGO-000001` (`synthetic_reference`) | `safety_goal` | safety_engineer | 19 - the most-depended-on non-review record | R1 |
| `FB2-SAF-HAZ-000001` (both profiles) | `hazard` | safety_engineer | root of the §13 chain | R1 |
| `FB2-SAF-FSR-000001..000003` (`as_is`), `-000004` (`synthetic_reference`) | `requirement` | safety_engineer | 10, 10, 8, 6 | R1 + R17 |
| `FB2-SAF-ITE-000001` (`synthetic_reference`) | `item_definition` | safety_engineer | 17 | R1 |
| `FB2-SAF-SCS-000001` (`synthetic_reference`) | `safety_case` | safety_manager | terminal stage of the §13 chain | **R11** - the policy requires it |

**Batch 1 - the requirements and designs other records depend on AND that no
review covers.** This is the batch the ordering rule was built for: 12 software
requirements, 3 hardware requirements, 2 software designs and the integration
plan, every one of them uncovered.

| record | type | `owner_role` | engineering links |
| --- | --- | --- | --- |
| `FB2-SW-SWR-000001`, `-000002`, `-000003` (`synthetic_reference`) | `requirement` | sw_engineer | 12, 10, 10 |
| `FB2-SYS-SYR-000007`, `-000008` (`synthetic_reference`) | `requirement` | system_engineer | 9, 11 |
| `FB2-SW-SIR-000006` (`synthetic_reference`) | `requirement` | sw_engineer | 8 |
| `FB2-HW-TSR-000001..000003` (`as_is`), `-000004` (`synthetic_reference`) | `requirement` | hw_engineer | 7, 6, 5 |
| `FB2-SW-DSN-000002` (`synthetic_reference`) | `design` | sw_engineer | 7 |
| `FB2-VER-SIP-000001` (`synthetic_reference`) | `integration_plan` | integration_engineer | 5 |
| `FB2-SW-DSN-000001` (`as_is`) | `design` | sw_engineer | 8 |

**Batch 2 - the verification backbone.** The unit-test specifications and the
qualification plan are depended on by 7-8 records each and are uncovered.

| record | type | `owner_role` | engineering links |
| --- | --- | --- | --- |
| `FB2-VER-UTS-000001` (`synthetic_reference`), `FB2-VER-UTS-000002` (`as_is`) | `unit_test_specification` | verification_engineer | 7, 7 |
| `FB2-VER-SQP-000001` | `qualification_test_plan` | verification_lead | 8 |
| `FB2-VER-TMS-000001`, `-000003` | `test_measure` | verification_engineer | 5, 5 |
| `FB2-VER-VSR-000001` | `verification_summary` | verification_lead | 4 |
| `FB2-MAN-VDR-000001` | `verification_deficiency_register` | project_manager | 4 |

**Batch 3 - the records with unverifiable provenance.** 24 records cite at least
one of the 13 source anchors that name no file in this repository (4 Altium
design files in the separate `foxBMS2_hw` repository, 5 fetched URLs, and test
anchors recorded under `location.file_or_executable` rather than
`location.path`). Every one of those 24 records carries a machine-unverifiable
claim, and 5 of them are `test_measure` records - so this batch overlaps Batch 2
and should be signed **with** it, not after it. Types affected: 6 `requirement`,
5 `test_measure`, 4 `review`, 2 `hazard`, and one each of `execution`, `design`,
`safety_concept`, `safety_analysis`, `item_definition`,
`hardware_detailed_design_gap`, `post_development_record`. This batch needs R3
and R1 in the room, because the question on each packet is *"does this claim
still hold, on evidence outside the corpus?"*

**Batch 4 - the `review` records (18) and the `finding` records (42, of which 35
are uncovered).** These are statements *about the corpus's own correctness*, so
they need R18 `reviewer_adversarial` and cannot be signed by whoever produced the
automation they describe. Sign them after Batches 0-3, because a review record
should be judged against the records it reviewed, and those must be settled
first. Each finding packet asks the disposition question directly: is `resolved`
right, given that `resolved` asserts the condition **no longer holds**?

**Batch 5 - the remainder.** The remaining `deviation` records (26, all `as_is`,
all observations of real source), the `scenario` fixtures (18), the
`implementation` records (14), and the management and supporting records.

**Order rules, stated so they can be checked:**

1. **Dependencies before dependents.** Batch 0 before Batch 1 before Batch 2. The
   chain is: vocabulary and safety concept -> goals and hazards -> FSRs ->
   system/HW/SW requirements -> designs -> implementations -> test measures ->
   executions.
2. **Unreviewed before reviewed.** Within any band, the records covered by no
   other review record come first. Approving an unreviewed record is close to
   meaningless, and approving a reviewed one on top of an unreviewed dependency
   is worse.
3. **Verification before evidence.** The `test_measure` and `execution` records
   must be settled before any §2 hardware run, because the run is judged against
   the measure's acceptance criteria. A run performed against criteria that are
   later revised is not evidence for the revised criteria.
4. **Findings last.** A finding record asserts something is wrong; it cannot be
   judged until the records it is about are settled.

### 1.8 What happens to the corpus when each batch lands

Per batch, in order:

1. Fill section 9 of each packet **in your own copy**. **A human does this. No
   tool does this**, and no tool in this repository has a code path that can.
2. Archive each signed packet to `docs/artifacts/reviews/signed/<profile>/<id>.json`,
   byte-for-byte as signed. Cite the archived copy in `review_packet.path` - it is
   the only path that resolves.
3. Run `--transcribe <ID>` for each record, fill the human fields, and **append one
   line per record to `docs/artifacts/governance/approval-ledger.jsonl`**. Chain
   the `previous_entry_sha256` fields: entry N names entry N-1's digest, and the
   first names 64 zeros.
4. Merge into each record: `human_approval_status`, the
   `approval_evidence.human_approval` block, and `approval_ledger_ref`. **Nothing
   in `revision_history`.**
5. Record the batch: which records, which signatures, which rejections and why,
   and which records in the batch were not signed and why. A batch record that
   lists only approvals is a misleading batch record.
6. Re-run and read every number:
   ```bash
   python3 docs/artifacts/tools/corpus.py validate
   python3 docs/artifacts/tools/corpus.py check
   python3 docs/artifacts/tools/corpus.py selftest
   python3 docs/artifacts/tools/make_review_packets.py --verify
   python3 docs/artifacts/tools/verify_approval_ledger_independently.py
   ```
7. **Expect `check` to stay GREEN, and `human_approval` to move by the number of
   approvals you recorded** that are evidenced *and current*. If `check` is red,
   read the finding: it names which of the six elements is unmet. A red result on
   an approval you believe is complete is a defect in the approval or in the rule -
   do not paper over it by removing the approval.
8. **Expect the revision numbers and the link counts NOT to move.** That is the
   whole claim of `APPROVAL-LEDGER-A1`, and if a batch changes a revision or makes
   a link stale, something recorded the approval the wrong way.
9. Expect `approval_staleness` to read `0/N` for a batch of current approvals. If
   it reads `M/N`, `M` human judgements no longer describe the bytes on disk. Read
   the finding: it names the record, the ledger entry and **which fields
   changed**. Re-review those fields and append **new** entries - never edit or
   delete the old ones.
10. Regenerate the packets. Records that changed get new digests; the generator
    refuses to overwrite the signed packets you archived elsewhere, and the
    freshly generated packets for those records carry the *new* digest. A signature
    against the old digest provably does not cover the new bytes - which is the
    point of the digest, and which now shows up as **staleness in the ledger** and
    a named field diff, rather than as a bare validator failure.
11. `automated_review_coverage` is expected to stay at `172/282` and
    `production_authorization` at `0/321`. Neither measures human approval. If
    either moves, something wrote a value nobody signed.

---

## 2. `actual_product_evidence` - 0 of 33

### 2.1 The count

**0 of 33 test measures are backed by a run on the product's own hardware.**

The dimension counts *distinct test-measure ids* backed by an execution whose
`execution_kind` is `actual_target_hardware_run`. There are none. Of the 44
execution records: 15 `actual_host_run`, 6 `synthetic_fixture`, 23 `none`
(blocked), 0 target.

The 33 records break down as:

| group | test measures | what a real target run could honestly do for them |
| --- | --- | --- |
| `as_is` - real foxBMS 2 claims | **5** (`FB2-VER-TMS-000001..000005`) | these are the only ones a TMS570 run is evidence for |
| `synthetic_reference` - the hypothetical reference project | **28** | a real run would produce evidence about the **real product**, which these measures are not about. Moving this dimension by running hardware would be exactly the synthetic/real blur the profile split exists to prevent. |

**So the honest ceiling for hardware work is the 5 `as_is` measures**, and the
dimension would then read 5/33. Getting past 5 requires either deciding that the
synthetic profile's measures are legitimately verified on real hardware - a
substantive decision with a real argument on both sides - or accepting that 5/33
is what a complete campaign looks like.

The 5 `as_is` measures, with their existing execution history:

| measure | title | existing executions (all `actual_host_run` unless noted) |
| --- | --- | --- |
| `FB2-VER-TMS-000001` | SOA Voltage Limit Detection | 000001 pass; 000006, 000007, 000015 fail |
| `FB2-VER-TMS-000002` | Contactor State Machine and Fault Response | 000002 pass; 000006, 000007, 000015 fail |
| `FB2-VER-TMS-000003` | AFE Cell Voltage Plausibility Checks | 000003, 000012 pass; 000006-000011, 000013-000015 fail |
| `FB2-VER-TMS-000004` | LTC6813-1 AFE Driver Communication and Measurement | **000004 `none` / blocked**; 000006, 000007, 000015, 000016 fail |
| `FB2-VER-TMS-000005` | Contactor Driver Configuration and Control | 000005 pass; 000006, 000007, 000015 fail |

`FB2-VER-TMS-000004` is the one with no host run at all: execution `000004` is
`execution_kind: none`, `outcome: blocked`, and the corpus records it as blocked
rather than dressed up.

### 2.2 The hardware required

**TMS570LC4357, on the released foxBMS 2 BMS-Master hardware, board revision
1.2.3.**

The corpus already names this in several places - the blocked execution records
carry `environment.hardware` of
`"Target TMS570LC4357 + HIL bench (blocked - unpublished upstream)"`, and the
`hardware_variant_applicability` and `hardware_configuration_baseline` records
carry the board revision. Two constraints follow and both are real:

1. **The schematic is not in this repository.** Source anchors
   `FB2-SRC-HW-000001` and `FB2-SRC-HW-000002` name Altium `.SchDoc` files in the
   **separate `foxBMS2_hw` repository**, and the anchor registry records their
   `content_hash` as the literal string `"unresolved"` with
   `hash_status: external_design_file_unverifiable_from_this_repository`. The
   registry's own note says the files are *"present neither in the working tree of
   foxbms-2 nor in any commit of it"*. **Whoever runs the hardware must record
   which `foxBMS2_hw` commit the board corresponds to.** Without that, the run
   cannot be tied to a design and the record repeats the same unverifiable
   provenance this corpus has already criticised elsewhere.
2. **The test harness does not exist.** The blocked execution records name
   `tests/hil` as an *"unpublished upstream placeholder"*. Nothing in this
   repository can drive the target. **Writing that harness is software work
   against `tests/`, which is outside the scope of this document and outside the
   scope of whoever signs the execution record.**

### 2.3 The procedure - the existing runbook, audited

**The runbook that exists is `docs/artifacts/.work/verification-env/RUNBOOK.md`.**
It is 473 lines, headed *"foxBMS 2 host unit tests on macOS - runbook"*, and its
status line reads *"Status: working. The suite was made runnable natively on macOS
arm64 and executed for real."*

**Audit finding, and it is the important part of this section: that runbook
describes HOST runs, not target-hardware runs.** Its own §8 says so in its own
words:

> `actual_product_evidence` did not move, and should not have
>
> The numerator is a hard-coded `0` and the dimension is scoped to
> **target-hardware** executions. This run is a **host** run, not a target
> execution, so it does not satisfy that dimension and the metric stays `0/16`.
> `corpus.py` was deliberately **not** edited to make the number move; doing so
> would relabel host runs as target evidence, which is exactly the blurring the
> corpus rules forbid.

**Consequence: there is no target-hardware procedure in this corpus, and this
document does not invent one.** What exists is a *host-environment* runbook whose
reusable parts are named below, plus an environment that is already provisioned
and disposable. What does not exist, and cannot be written without the hardware,
is marked in §2.5.

**What the runbook gives you, and its real path:**

| step | real path | reusable for a target run? |
| --- | --- | --- |
| provision the host toolchain | `docs/artifacts/.work/verification-env/provision.sh` | partially - it provisions Ceedling/CMock/Unity for a host build, not a cross-compile and flash toolchain |
| run the suite, every test in its own invocation | `docs/artifacts/.work/verification-env/run_suite.py` | the *shape* is right - one invocation per test so every verdict is individually attributable and every raw log is retained - but the harness behind it is host-only |
| the shell recipe | `docs/artifacts/.work/verification-env/run.sh` | host-only |
| classify empty tests | `docs/artifacts/.work/verification-env/sil/tools/find_vacuous_tests.py` | **yes, unchanged.** It reads `test_*.c` statically, runs nothing, and is exactly the instrument that produced `FB2-REV-FND-000042`. Its output convention is the model for a target run's output convention. |
| the evidence layout to copy | `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/` | **yes.** 647 evidence files already live under `docs/artifacts/evidence/`; the convention is one directory per run, named for the run, with `results-*.json` plus a `logs-<variant>/` tree, and separate log trees per variant so **a record can never cite the other run's log**. |
| regenerate the corpus records from the run | `docs/artifacts/.work/verification-env/make_corpus_records.py` | the mechanism, yes. **It is hard-wired to the host runs** and would emit `actual_host_run`. It must not be reused unmodified for a target run, or it will label silicon evidence as host evidence - which is §3's third forgery. |
| what the runbook itself says is still broken | `docs/artifacts/.work/verification-env/RUNBOOK.md` §6 | directly relevant: 177 of 313 `test_*.c` files are blocked on proprietary TI code generation and are **not** stubbed. A target run inherits that: HALCoGen output is required before anything can be built for the TMS570 at all. |
| the honest account of the ceiling | `docs/artifacts/.work/verification-env/RUNBOOK.md` §7 and §8 | yes, and it is why the corpus is trusted on this point at all |

**Two more facts from the runbook that bear directly on a target run:**

- The host harness *"mocks the HAL and verifies driver logic against upstream's
  own assertions, so it establishes nothing about register maps, timing,
  clocking, interrupts, DMA transfer, bus or electrical behaviour, or device
  identity."* That is the exact gap a TMS570 run closes - and it means a target
  run's evidence is not a superset of the host evidence, it is evidence about
  something the host run cannot reach at all.
- The 5 strict host failures are *"not artifacts of the macOS adaptation"* and
  *"reproduce under any compiler"* - they are real product defects. A target run
  will meet them too. **A target run that reports them as failures is a
  successful campaign.** Do not treat a red target run as a failed campaign; see
  §3.2.

### 2.4 Who must be present

| who | why |
| --- | --- |
| **R5 Verification Engineer** (`verification_engineer`) - runs the test, captures the logs, writes the execution record | owns `execution_kind`, `outcome`, evidence handling. Sole author of the execution record. |
| **R3 Hardware Engineer** (`hw_engineer`) - confirms the board, the `foxBMS2_hw` commit, and the variant | the schematic is not in this repository (§2.2). Without this the run is tied to nothing. |
| **R17 Domain Reviewer** - signs the execution record | independence from the author, per §1.5. |
| **R19 System Architect** - decides the 5-vs-33 question in §2.1 before the run starts | it changes what the run is *for*, and a run performed before the question is settled may have to be redone. |
| optional: **R1 Functional Safety Engineer** - if the run touches the SOA limit or the safety chain | measures 000001-000003 are exactly those. |

**A campaign that is one engineer alone is not admissible** for this corpus: the
execution record needs a signer who is not its author, and the hardware identity
needs someone who can speak to the `foxBMS2_hw` commit.

### 2.5 What evidence must be captured, and what cannot be prepared without the hardware

**Can be prepared now, without the hardware:**

- [x] the environment - `docs/artifacts/.work/verification-env/` is provisioned
      and explicitly disposable;
- [x] the evidence directory convention -
      `docs/artifacts/evidence/actual-runs/foxbms2-<what>-<date>/`;
- [x] the one-invocation-per-test rule and the separate log tree per variant, so
      a record cannot cite another run's log;
- [x] the vacuity census instrument -
      `docs/artifacts/.work/verification-env/sil/tools/find_vacuous_tests.py`;
- [x] the draft execution record skeleton, with every field the schema and the
      rules require, **and every evidence field left empty**;
- [x] the §2.1 decision on whether synthetic measures are in scope;
- [x] the §1.6 P1 rule amendment (`APPROVAL-RULE-A1`, 2026-10-04), so the
      resulting record can be recorded without breaking the suite - and, since
      the same day, without breaking any other control either.

**CANNOT be prepared without the hardware. Nothing in this list may be filled in
by anyone but the person who runs the hardware:**

- [ ] **The firmware image.** Its sha256. Nothing in this repository can produce
      it.
- [ ] **The hardware identity.** Board revision, the `foxBMS2_hw` commit the
      board corresponds to, and the probe/debugger used. The schematic is
      external, so this is the only link between the run and a design.
- [ ] **The measured timestamps.** `timestamps.start` and `timestamps.end` from
      the run. A duration nobody measured is a fabricated duration.
- [ ] **`input_hashes`** - what went into the target. Real digests of the real
      firmware image and configuration.
- [ ] **`output_hashes`** - what came out. Real digests of the captured logs.
- [ ] **`logs[]`** - the captured output files themselves, on disk, at the paths
      the record names. `_validate_evidence_files` checks existence *and* hash for
      every entry; a citation to a file that is not there is a high-severity
      `evidence_file_missing`.
- [ ] **`evidence_refs`** - the pointers to the archived evidence.
- [ ] **`outcome` and `aggregate_outcome`** - the real verdicts, including the
      failures the host run already predicts.
- [ ] **`environment.hardware`** - the real string. See §2.6: it is
      pattern-checked.

**The five conditions `execution_kind_classifier` enforces on any record claiming
`actual_target_hardware_run`.** All five are read from
`docs/artifacts/tools/corpus.py`; a record missing any one is a high-severity
finding, and a missing hash sets the function-level verdict to False:

1. `logs[]` is non-empty **and every `logs[].file` exists on disk**.
2. `input_hashes` is non-empty.
3. `output_hashes` is non-empty.
4. `evidence_refs` is non-empty.
5. `environment.hardware` is non-empty and does **not** name a non-target
   platform.

Plus, from `_validate_evidence_files`: every `logs[].hash` must be a real digest
that matches the file's bytes. A `"sha256:placeholder"` there is a medium
`evidence_file_hash_mismatch` and fails the gate.

Plus, from the same rule: `origin` must be `source_observed`. A record with
`origin: derived` or `origin: synthetic` claiming a hardware run raises a medium
finding naming it a *"fabricated evidence classification"*.

**And `environment.hardware` is word-boundary checked against this list:**

```
x86_64  x86-64  amd64  arm64  aarch64  apple silicon  macos  darwin  linux
win32   windows  posix   host    workstation  laptop  ci   virtual  container
docker  qemu    emulated  simulator  simulation  fixture  none  unknown  tbd  n/a
```

A legitimate string is `TMS570LC4357 BMS-Master 1.2.3` - or whatever the real
board is called. Two traps: the word **`none`** is on the list, so a string like
`"TMS570LC4357, none of the host peripherals"` fails; and the match is
word-boundary, so `simulator` inside a longer word does not fire but `simulation`
as a standalone word does. When in doubt, write the board's real name and nothing
else.

### 2.6 How to record the result

Under the existing schema, with no schema change:

1. **New record** under `docs/artifacts/corpus/as_is/verification/`, with the next
   free `FB2-VER-EXE-NNNNNN` in **profile `as_is`**. `(profile, id)` is the
   primary key; check for a collision in the other profile before using an id.
2. `artifact_type: "execution"`, `execution_kind: "actual_target_hardware_run"`,
   `origin: "source_observed"`.
3. `test_measure_id` = the `as_is` measure, e.g. `FB2-VER-TMS-000001`. Not a
   range, not a synthetic measure.
4. `profile: "as_is"`, `scenario_id: "SCN-BASELINE"`, `baseline_id: "BAS-REF-001"`.
5. `human_approval_status: "pending"`,
   `production_authorized: false`,
   `product_verification_credit: false`. **A hardware run grants neither.**
6. `environment`: `hardware` per §2.5, plus `software`, `tools`,
   `configuration`, `tool_versions` - and `tool_versions` must be the real
   versions, because the corpus's own host records were caught out by exactly this
   (see `FB2-REV-FND-000041`).
7. `timestamps` measured, not typed.
8. `input_hashes` / `output_hashes` / `logs[]` / `evidence_refs` per §2.5.
9. `limitations` - and this record will have real ones. Say what the run did
   **not** establish: register coverage, timing, clocking, interrupt behaviour,
   DMA, bus and electrical behaviour, device identity, whatever the harness still
   mocks. A target run closes the mock gap; it does not close every gap.
10. `revision` incremented with a `revision_history` entry naming who ran it, on
    what board, on what date, with the `foxBMS2_hw` commit.
11. Then `python3 docs/artifacts/tools/corpus.py validate` and `check`, and read
    the numbers. `actual_product_evidence` should move by exactly the number of
    distinct measures newly backed. If it moves by more, a `test_measure_id` is
    wrong.

**Superseding the blocked records.** The `execution_kind: none` / `outcome:
blocked` records (including `FB2-VER-EXE-000004` (`as_is`) and the 22 synthetic ones,
`FB2-VER-EXE-000007..000028`) are **not deleted and not edited into passes.**
Append a revision, or raise a new record, and cross-reference. A finding record is
never deleted in this corpus - its existence is part of the audit trail, and a
corpus that deletes the record of a gap it later filled cannot show it ever had
one.

---

## 3. What must NOT be done

The value of this corpus is that two columns are trustworthy. Each of the ways
below would make them worthless, and each has a check in the tree that catches
it. This section is as important as the two procedures above.

### 3.1 Writing an approval field by a tool or an agent

**The forgery.** `human_approval_status: "approved"` written by a script, by a
CI job, by an agent asked to "close the approval gap", or by a human who did not
read the record. Also: `production_authorized: true` or
`product_verification_credit: true` written on a record because it is finished.

**Why it is the worst thing that could happen here.** `human_approval` is 0/321
*because* nobody has approved anything. That zero is the corpus's one claim to
being honest about its own incompleteness. A single fabricated approval makes the
other 320 zeroes meaningless - not because they were wrong, but because a reader
can no longer tell them apart from the fake.

**The check that catches it.**

| check | where | what it does |
| --- | --- | --- |
| `human_approval_rejected` | `corpus.py` `_approval_evidence_defects`, severity **high** | fails validation on any record whose `human_approval_status` is a grant value, **unless** the record carries all six evidence elements of §0.2a. Reports each unmet element by number. |
| `production_authorized_rejected` | same, severity **critical** | the same six elements on `production_authorized: true`, **plus** an approving role that holds production authority and a record family human approval is required for |
| `verification_credit_rejected` | same, severity **high** | the same six elements on `product_verification_credit: true` |
| the digest chain | same, element 5 | a cited `review_packet.sha256` must equal the packet file's bytes **now**, and `record_sha256_at_signing` must equal **that packet's own** `integrity.record_sha256`. Not "a packet exists for this record" - the binding to one record state is what is checked. |
| the same check via the other path | `_validate_governance_semantics` | the identical predicate, because gate `[7/8]` runs that and never `_validate_artifact`. Reported once per (rule, artefact), so the violation count is not inflated. |
| acceptance gate | `corpus.py check` `[7/8] no production authority, no verification credit, no human approval` | counts violations across all **8** governance rules, and separately asserts the rule set is non-empty and covers the four named claim classes, so the filter cannot be emptied |
| packet-level | `make_review_packets.py --verify`, and `corpus.py check` `[7c/8]` | a non-empty signature block in a generated packet is reported by name |
| self-test | `corpus.py selftest` | *"every signature block in every generated packet is empty, in both formats"* - reads all 321 markdown packets **and** all 321 `packet.json` twins and asserts every one of the seven fields is empty |
| self-test | `corpus.py selftest` | *"the generator refuses to overwrite a packet that already carries a signature"* - injects a signature, regenerates, asserts it survived |
| independence | `corpus.py selftest` | *"the packet generator's signature fields match the ones check looks for"* - so the checker cannot be blinded by editing the generator's field labels |
| self-test | `corpus.py selftest` | *"no record in the corpus carries an approval of any kind"* - scans all 321 records for a non-pending value in any of the three fields, and for any record carrying an `approval_evidence` block at all. This is the standing fact that the corpus holds none. |
| self-test | `corpus.py selftest` | *"a bare approved with no evidence FAILS validate"*, *"an approved missing the signed-packet digest FAILS"*, *"an approved citing a packet digest that does not resolve FAILS"*, *"the packet digest is verified against the packet's own recorded digest"*, *"an approved recorded by the record's own author FAILS"*, *"an approved_by that is a role, a role name or a team FAILS"* - six rejection cases, each built by removing exactly one thing from an otherwise complete approval. Together they are the proof that the amendment did not weaken the ban it replaced. |
| self-test | `corpus.py selftest` | *"a fully evidenced approval PASSES validate, and the approval dimension moves"* - the required counterweight: builds a complete approval against a **throwaway copy of the tree outside the repository**, writes it there, asserts `cmd_validate` over the whole copy still passes with zero errors and the same 5 findings as the same tree without it, asserts `human_approval` reads 1/321 there, then deletes the copy. A ban with extra steps also rejects everything; only this distinguishes the two. |
| self-test | `corpus.py selftest` | *"the approval happy path persists nothing into the corpus"* - re-reads the real tree after the accepting case has run and asserts no record carries a grant value, no record carries an `approval_evidence` block, and no temporary tree was left under the repository root. |
| self-test | `corpus.py selftest` | *"production authority is strictly harder to satisfy than an approval"* and *"production authority is reachable on a production-release family"* - the first asserts the same record and the same complete approval is ACCEPTED as an approval and REFUSED as production authority on two independent grounds; the second asserts the strict bar is satisfiable, so it is a bar and not a second ban. |
| self-test | `corpus.py selftest` | *"a production grant hidden in a nested key is still caught"* - a production-authority key and a conformity claim nested inside the new `approval_evidence` object are still caught by the unchanged recursive scan. The new field is not a shadow. |
| self-test | `corpus.py selftest` | *"one approval violation produces one finding across both detector paths"* - `cmd_validate` runs two methods that both check these fields; the count must stay 1. |
| self-test | `corpus.py selftest` | *"no packet states the superseded prohibition"* and *"every packet states the current approval rule and the six required fields"* - all 642 packet files are read, so the instruction a reviewer holds cannot drift back to "your signature turns check red" and cannot be merely deleted. |
| self-test | `corpus.py selftest` | *"--transcribe resolves both digests correctly and writes nothing"* - runs the command a reviewer runs TWICE, because the procedure is two steps: the first must say the digest is not resolved and to archive first, the second must print the real digest of the archived file. Asserts both printed digests are real, that the output contains no decision, that it prints `approval_ledger_ref` and forbids a `revision_history` entry, that it states the forgeability limit, that the packet tree is byte-identical afterwards, and that the ledger is still 0 bytes. |
| `approval_ledger_ref` resolution | `corpus.py` element 6, inside `_approval_evidence_defects` | the named ledger entry must exist, must name this record's `(profile, id)`, must carry this approval's `kind`, and its `entry_sha256` must equal the digest of that entry as it stands. A forged `ledger_id` or a wrong `entry_sha256` is rejected by name. Self-tested. |
| chain walk | `corpus.py` `_validate_approval_ledger`, **high** | walks every entry, reports the **first** break of `previous_entry_sha256` with its index, line and `ledger_id`. Also reports a malformed line, a duplicate `ledger_id`, a missing required field, and a non-sha256 digest field. |
| git anchor | `corpus.py` `_check_ledger_git_anchor`, **high** | the cited `packet_first_commit` must exist (`git cat-file -e`) **and** the packet blob must be present in it. Proves WHEN and IN WHAT STATE; proves nothing about WHO. A tree with no `.git` reports it unverified rather than failing every clean checkout. |
| the signed archive rule | `corpus.py` `_resolve_approval_packet`, element 5 | a cited packet is admissible **only** from `docs/artifacts/reviews/signed/`. A `reviews/packets/` citation is rejected with a message naming the archive and saying to archive the signed packet first. Self-tested with the digest re-pointed at the same `packets/` file, so admissibility is the only thing that can fire. |
| staleness, made visible | `corpus.py` `_report_stale_approvals`, **medium, never gating** | an approval whose ledger entry no longer matches the record's current content digest is STALE, not invalid. Reported with the record, the ledger entry, both digests, the revision delta and **the fields that differ** - recoverable because every signed packet embeds the approved record verbatim. |
| staleness, counted | `coverage` and `check`, plus `corpus.py selftest` | `approval_staleness` reads `stale / total approvals` on every run and is asserted to move from 0 to 1 when a tempdir approval's content is edited afterwards. |
| the ledger is empty | `corpus.py selftest` | *"the approval ledger is empty and nothing in this repository appends to it"* - asserts the real ledger has zero non-blank lines, zero parsed entries and zero malformed lines, and that EXACTLY ONE append-mode open of it exists across `docs/artifacts/tools` - corpus.py's own self-test fixture - so a second one fails. |
| from-scratch checker | `docs/artifacts/tools/verify_approval_ledger_independently.py` | imports nothing from `corpus.py`; re-derives the chain, the approvals count, the packet digests, the cited paths, the empty signature blocks and the single-append-site fact from bytes on disk, and states its own limits. |
| self-test | `corpus.py selftest` | *"governance gate [7/8] sees a ledger fabrication, not only the artifact path"* - proves element 6 is reached through `_validate_governance_semantics`, which is the only path gate [7/8] runs. Without this the gate would go blind to exactly the claim class it exists to catch. |
| self-test | `corpus.py selftest` | *"the approval ledger hash chain is walked and a mutated chain is detected"* - a genuine three-entry chain, then three mutations of a copy: edit one entry's payload, delete the middle entry, reorder two entries. Each must be detected at the first break with exactly one finding, and the chain must validate again once restored. |
| self-test | `corpus.py selftest` | *"a ledger entry must anchor its packet to a commit that contains it, and the limit is stated"* - builds a **real git repository** in a tempdir so the anchor check is live rather than vacuous; then cites the commit that holds the packet (anchors), a non-existent commit (rejected), and a real commit that does not hold the blob (rejected). Also reads the code and `approval-ledger.md` and asserts the forgeability limit is still stated in both. |

**Two forgeries this section must also name, because the ledger invites them.**

**Recording the approval in `revision_history` "just this once".** It is the one
instruction in this document that is a hard rule rather than a convention, and it
is tempting precisely because it used to be the documented procedure. What it does
is real damage and does it silently: it bumps the record's revision, which makes
every link pinning that revision stale, which invalidates the `sha256` that every
review record stores for it. The corpus ends up with a signed approval and a
corpus that no longer validates, and the two failures have nothing obviously to do
with each other. The self-test *"an approval recorded through the ledger stales no
link and invalidates no review digest"* asserts `approval landed in
revision_history = False`, on a record that a review record already covers, so the
right way round is demonstrated on the record where the wrong way round actually
bites.

**Editing an existing ledger entry instead of appending a new one.** The ledger is
append-only, and that is enforced the only way an append-only structure can be:
each entry binds its predecessor by digest, so editing entry 3 changes its digest
and invalidates entry 4's `previous_entry_sha256`, to the end. The validator
reports the **first** break and names it. The same applies to deleting or
reordering. All three are exercised by a self-test against a copied chain. If you
need to record a changed judgement - because the content changed, or because you
were wrong the first time - **append a new entry**. Never repair the old one. (The
stale one then shows up in `approval_staleness`, which is correct: it is a real
human judgement that has been overtaken, and hiding it would defeat the point of
counting it.)

**The residual risk, stated honestly.** The first amendment (2026-10-04) DID
weaken one thing, and it should be named rather than defended away: before it,
*any* approval value failed, so the mechanical guard against fabrication was total.
Now a fully evidenced approval passes, and what guards fabrication is the evidence
requirement rather than the ban. Six things had to be true for that to be a trade
rather than a hole - a named person, a declared role, enforced independence from
both the owner role and the content author, a date, a digest chain resolved
against an archived packet on disk and checked against that packet's own recorded
record digest, and a live append-only ledger entry - and each one is a separate
way to fabricate less easily than the value alone.

Four residual risks remain, and none of them is closed by either amendment:

1. **A person can still forge all six.** This is IRREDUCIBLE, and the second
   amendment does not change it - it makes forgery more expensive and more
   detectable, which is not the same thing as preventing it. The hash chain proves
   the entries exist, are in order and were not edited; the git anchor proves when
   and in what state the packet was committed. **Neither proves a human read
   anything.** A determined person can write all six elements, archive a packet,
   cite a real commit and maintain the chain correctly, and nothing in this
   repository can tell that from a real approval. See §0.2e.
2. **`human_approval_status: "not_required"` is still rejected**, which means a
   record that legitimately needs no approval has no way to say so, and the next
   person to hit that will be tempted to work around it. Open P3 in §1.6.
   **RESOLVED 2026-10-04 by `APPROVAL-NOTREQ-A1`** — `not_required` is now
   legitimate and permitted on any family outside the policy's positive list, so
   a record that legitimately needs no approval can say so. The residual that
   survives the resolution is narrower and worth stating: **a record that needed a
   gate and says `pending` forever is indistinguishable from one that is simply
   not due yet, and no rule in this corpus detects that.** The opposite mistake —
   a record that needed a gate and claims `not_required` — *is* detected, by
   `human_approval_not_required_misdeclared`.
3. **The eight undeclared `owner_role` values** (§1.2) mean the reviewer's role
   must still be added to the policy or mapped before their signature is
   traceable. Open P2 in §1.6. **Since `APPROVAL-COUNT-A1` the same eight also have
   no entry in the countersigner's per-`owner_role` exclusion map**, so a
   countersignature on a record they own is checked strictly less than on a record
   owned by a declared role. Declared in the policy's `unmapped_owner_role_policy`;
   not closed by inventing role definitions.
4. **A review digest no longer pins a record's approval state**, because approval
   metadata is excluded from the content digest. Flipping `production_authorized`
   is therefore not caught by `review_digest_mismatch` - it is caught by four other
   controls (§0.2b). Stated here because a control that silently stopped covering
   something is the defect this corpus exists to prevent.

What neither amendment weakened, checked rather than asserted: the recursive
authority-key scan, the ASIL/conformity/certification claim classes, the
provenance gate, and the packet-generator rule that no code path writes a
signature. Element 5 is **tighter** than before, not looser: one of its two
admissible roots was removed.

### 3.2 An execution record with fabricated timestamps or hashes

**The forgery.** A `execution_kind: actual_target_hardware_run` record whose
`timestamps`, `input_hashes`, `output_hashes` or `logs[].hash` were typed from
memory, copied from a host run, generated to satisfy the shape, or produced by
hashing a file nobody produced. Also the softer version: **the run really
happened, but the record overstates what it established.**

**The checks that catch it.**

| check | where | what it does |
| --- | --- | --- |
| `execution_kind_classifier` | `corpus.py` `_validate_semantic_rules` | on `actual_target_hardware_run`: requires non-empty `logs` with every file existing on disk, non-empty `input_hashes`, non-empty `output_hashes`, non-empty `evidence_refs`, a non-empty `environment.hardware` that names no host platform, and `origin` of `source_observed`. Missing hashes set the verdict to False |
| `evidence_file_hash_mismatch` | `_validate_evidence_files`, **high** | every `logs[].hash` is recomputed against the file's bytes |
| `evidence_file_missing` | same, **high** | every `logs[].file` and `evidence_files[]` path must exist |
| `evidence_file_hash_mismatch` for a placeholder | same, **medium**, and **fails the gate** | `"sha256:placeholder"` is counted and reported as unverified, never skipped |
| `execution_kind_classifier` on the other kinds | same | an `actual_host_run` with no `evidence_refs` is a **high** finding; a `synthetic_fixture` without evidence is a **medium** |
| `evidence_reference_validator` | same | every `evidence_refs` entry must resolve to an artefact id or a file that exists |
| provenance gate | `check` `[7b/8]`, prints a full tally | reports log entries verified / mismatched / unverified / missing, and evidence_files entries missing, every run |

**The residual risk.** Every one of these checks verifies *internal consistency*:
that a hash matches a file that exists. **None of them can tell you the file was
produced by the run the record describes.** That is why §2.5 lists the
un-preparable items as un-preparable: the human being present in §2.4 is the
actual control, and the machine checks are the ones that stop an *accident*.

### 3.3 Counting a host or simulation run as target hardware

**The forgery.** The most available one, because 15 real host runs already exist
with real logs and real hashes, and relabelling them costs nothing. Also: running
on a simulator, on a QEMU target, in a container, or on a CI runner and calling it
target hardware.

**Why it is the specific forgery this corpus is most exposed to.** The host run
was real work with real evidence - 647 evidence files, 16 recorded hashes
re-verified against disk. It is *tempting* precisely because it is good. The
corpus's own runbook refused it in writing:

> `corpus.py` was deliberately **not** edited to make the number move; doing so
> would relabel host runs as target evidence, which is exactly the blurring the
> corpus rules forbid.

**The checks that catch it.**

| check | where | what it does |
| --- | --- | --- |
| the `execution_kind` enum | `TARGET_EXECUTION_KIND` / `HOST_EXECUTION_KINDS` / `NON_EXECUTION_KINDS` / `DECLARED_EXECUTION_KINDS` | `actual_target_hardware_run` is the **only** kind that counts. The dimension reads the enum, not prose |
| `environment.hardware` word-boundary check | `_names_non_target_hardware` | rejects `arm64`, `darwin`, `macos`, `x86_64`, `host`, `ci`, `container`, `docker`, `qemu`, `emulated`, `simulator`, `simulation`, `fixture`, `virtual`, `workstation`, `laptop`, `posix`, `windows`, `win32`, `linux`, `none`, `unknown`, `tbd`, `n/a` - **high** finding on a target claim |
| `execution_kind_classifier` bars | same | the `actual_target_hardware_run` branch demands the higher evidence bar, because it is the only kind a reader may take as a result on the MCU the product ships on |
| `origin` cross-check | same | `origin` must be `source_observed`; `derived` or `synthetic` on a target claim is a **medium** *"fabricated evidence classification"* |
| self-test | `corpus.py selftest` | *"actual_product_evidence counts a genuine target run and ignores host runs"* - asserts the enum contains the target member, that a host run does **not** move the dimension, and that a target run does. Two further self-tests cover the record shape: *"target-hardware execution with real evidence validates"*, and *"target-hardware execution without evidence is reported"* |
| the `execution_kind` tally | `check` `[3/8]` detail | prints `N host/simulation (real product code, not target hardware)`, `N synthetic_fixture/none`, `N undeclared` on every run - so the buckets are visible, not just the numerator |

**The residual risk, and it is the honest limit of this whole section.** Every
check reads the record. A person who owns a TMS570 board, writes
`environment.hardware: "TMS570LC4357"`, generates the hashes from files they
produced on a Mac and archives them under `docs/artifacts/evidence/actual-runs/`,
and sets `origin: source_observed` will pass **every check in this repository**.
Nothing here can detect it. What makes it detectable is §2.4: an independent
signer who was present, and an archived signed packet naming the `foxBMS2_hw`
commit. **The corpus can enforce the shape of honesty. It cannot supply the
witness. That is the entire reason the two remaining dimensions are worth doing
by hand.**

### 3.4 Related, and worth naming because they are cheap

| forgery | the check that catches it |
| --- | --- |
| approving an unreviewed record and calling it reviewed | `automated_review_coverage` reports `reviewed_by_only` and `records_only` separately, and the `[3/8]` gate asserts the link registry and the review records **agree**. It is a union numerator, so the ratio alone cannot see a deletion - which is why the agreement field exists and is gated |
| editing a record's digest so a review appears current | `review_digest_mismatch`, **high**, in `_validate_review_digests` - every `reviewed_ids[].digest` recomputed against the artefact's bytes now, profile-scoped |
| leaving a `"sha256:placeholder"` digest unnoted | `review_digest_placeholder` - the literal is **permitted** only with a per-entry note, and both the noted and unnoted counts are printed every run |
| inflating `standards_mapping` | measured, not counted: a numerator entry must name >= 1 artefact id that resolves in the index or the source registry. `[3/8]` gates the numerator > 0 and reports the unbacked tally |
| calling a vacuous test a pass | `FB2-REV-FND-000042`: 53 of 245 green files assert nothing. Re-derive with `docs/artifacts/.work/verification-env/sil/tools/find_vacuous_tests.py` |
| letting a rule block stop running | `semantic_consistency_checks` is counted by a recorder each rule block calls on entry, not declared. `[3/8]` gates `rules_executed == rules_declared`, and a self-test asserts every declared rule has an emission site in the source |
| letting the provenance detector be rewritten alongside the rule it reports against | this happened, which is why `docs/artifacts/tools/verify_independently.py` exists: written from scratch, importing nothing from `corpus.py`, re-deriving every fact from the JSON, git blobs and sha256 |

---

## 4. Prerequisites

Two things this corpus needs are declared nowhere in the repository, and **a
restart that prompted this work silently removed both.**

### P-a: `jsonschema` in the system `python3`

`corpus.py` exits **2** if `jsonschema` cannot be imported. It has always done
so — failing closed is correct, and nothing below changes that — but the text it
printed used to be one line:

```
ERROR: jsonschema library required (pip install jsonschema)
```

**That message told an operator nothing actionable.** It named a package and a
command, and `pip install jsonschema` is *not* a command that succeeds on a
macOS-managed Python. It did not name the requirement file, did not name the
interpreter that wanted the package, did not say why a `--user` install might
refuse, and offered no route that works.

`make_review_packets.py` degrades differently: it reports schema checks as
*"validator unavailable"* in section 5.1 of every packet and carries on.

**Why this matters more than a missing package.** Neither tool is installed by
anything: there is no `pyproject.toml`, no CI step, no packaging manifest. The
corpus tooling is a set of scripts run directly against the system interpreter.
On a machine without `jsonschema`, `corpus.py check` **does not run at all** —
and a reader who has not read the source concludes the corpus is unverified
rather than un-runnable. Those are very different situations and the difference
is invisible from outside.

**This recurred three times, and pinning is why it could.** The dependency went
missing on three separate occasions and the failure mode was *different each
time*:

| # | What happened | Why the previous fix did not help |
|---|---|---|
| 1 | `corpus.py` exited **0** having validated nothing | There was no failure to read. A reader saw success. |
| 2 | `pip3 install --user jsonschema` refused: `error: externally-managed-environment` | The bare command in the old message names neither `--user` nor `--break-system-packages`. |
| 3 | `pip3 install --user --break-system-packages jsonschema` worked — but the failure message on the *next* machine still read `ERROR: jsonschema library required (pip install jsonschema)` | The message was fixed per-environment rather than per-cause. |

**`jsonschema>=4.18` being pinned does not install it.** A version range in
`requirements.txt` is a *statement in a file*; whether an interpreter holds the
distribution is a *fact on that interpreter's disk*. Nothing reconciles the two.
A pin that has been in the repository for months satisfies the reader while the
suite is un-runnable, and it will do so again on the next fresh checkout or the
next restart. This is stated here rather than left implicit because it is the
actual cause of the recurrence, and a cause that is not written down gets
re-diagnosed from scratch every time.

**Three fixes, in the order to try them.**

The pinned requirements are declared in `docs/artifacts/tools/requirements.txt`:

```
jsonschema>=4.18
referencing>=0.30
```

`referencing` is pinned as well as `jsonschema` because the corpus schemas use
relative `$ref` (`./artifact-base.schema.json`), which `jsonschema` resolves only
through a `referencing.Registry`. Both tools import it explicitly and both fall
back to a **registry-less validator** without it - which silently drops
cross-file `$ref` resolution and would under-report schema violations without
saying so.

**(1) Preferred — `bootstrap.sh`, which touches nothing in this repository.**

```bash
docs/artifacts/tools/bootstrap.sh
```

It creates a virtualenv **outside** the tree (default
`~/.cache/foxbms-corpus-venv`, override with `FOXBMS_CORPUS_VENV`), installs the
pinned requirements into it, verifies by *import* rather than by reading pip's
output, and prints the command to run the suite with it. Inside a virtualenv
there is no PEP 668 marker to override and no system `site-packages` to shadow,
so a plain `pip install -r` is both sufficient and safe.

It **creates nothing inside the repository** — no `.venv`, no marker file, no
`__pycache__` — and it **refuses to run** if `FOXBMS_CORPUS_VENV` resolves inside
the tree. That check is made on the *resolved* path, not on the string typed,
because the two disagree in exactly the cases that matter: `venv`, `./venv` and
`${PWD}/venv` are one directory, and a symlink can name a directory outside the
tree while pointing into it.

**(2) Install into this interpreter.**

```bash
python3 -m pip install -r docs/artifacts/tools/requirements.txt
```

Use `python3 -m pip`, never bare `pip3` or `pip`: a bare `pip` may belong to a
different interpreter than the one running the corpus, and installing into the
wrong `site-packages` is a failure that *looks* like success — the import still
fails here after pip reports no error.

**(3) On a macOS- or Debian-managed Python (PEP 668).**

The command above refuses with `error: externally-managed-environment`. That
refusal is the OS protecting a system interpreter, and it is correct. Either use
`bootstrap.sh`, or pass the flag whose name is a warning:

```bash
python3 -m pip install --user --break-system-packages -r docs/artifacts/tools/requirements.txt
```

**Confirm before believing anything else about this corpus's status.**

```bash
python3 -c "import jsonschema, referencing; print(jsonschema.__version__)"
python3 docs/artifacts/tools/corpus.py check
```

`corpus.py` now prints this preflight itself, naming the missing distribution,
the interpreter actually running, the requirement file, both install commands and
the virtualenv route, and still exits 2. It is still a hard failure: failing
closed is correct, and a corpus that cannot validate must not report that it
validated.

Resolved in the environment the 321 packets were generated in: `jsonschema`
4.25.1, `referencing` 0.35.1, CPython 3.9.6.

### P-b: `git-lfs` on `PATH`, for the clean-checkout proof

`.gitattributes` tracks `*.zip` with `filter=lfs`, and the repository contains
`docs/artifacts/spnc030g.zip` at **190,122,216 bytes**. Without `git-lfs`, a
`git archive` produces a pointer file where the archive should be, and the clean
checkout no longer matches the working tree the acceptance suite was verified
against.

`git-lfs` is installed at `/opt/homebrew/bin/git-lfs` and is **not on `PATH` by
default** for a non-login shell. The clean-checkout proof therefore needs:

```bash
export PATH="$PATH:/opt/homebrew/bin"
git archive HEAD | tar -x -C /tmp/cl && cd /tmp/cl \
  && python3 docs/artifacts/tools/corpus.py check
```

**`PATH` is APPENDED, never prepended.** Prepending `/opt/homebrew/bin` puts
Homebrew's `python3` ahead of `/usr/bin/python3`. That is a different interpreter
with a different `site-packages`, so `jsonschema` - installed user-scoped for
`/usr/bin/python3` - is not importable, and `corpus.py check` exits 2 with
`ERROR: jsonschema library required`. The failure looks like a missing dependency
and is actually a wrong interpreter. Append.

### P-c: the packets themselves are not in `HEAD` yet

The clean-checkout proof above runs against `HEAD`, which predates
`docs/artifacts/reviews/packets/`. It passes, and it passes **because** the packet
report degrades correctly: `corpus.py check` `[7c/8]` prints

```
no packet tree at reviews/packets: 0 packet(s). Nothing to verify. This is the
expected state on a checkout that predates the packets
```

and does not gate. That degradation is deliberate and is itself tested - the
packet report catches every exception and reports it rather than raising, so a
missing tree can never be the reason a suite is red. **Once the packets are
committed, the clean checkout will report 321 and verify 321.**

### P-d: `git archive` is not a substitute for the working tree

A second, independent proof is needed, because `git archive HEAD` cannot see
uncommitted work. After the packets and both documents are committed, re-run the
suite from a fresh copy of the working tree as well as from `git archive HEAD`.
Both must agree on all fifteen coverage dimensions.

---

## 5. The two commands, and what a correct result looks like

```bash
# 1. packets are current
python3 docs/artifacts/tools/make_review_packets.py
python3 docs/artifacts/tools/make_review_packets.py --verify
#    expect: 321 packet(s); digest matches 321/321; stale 0; signed 0; verify OK

# 2. the corpus is unchanged by having produced them
python3 docs/artifacts/tools/corpus.py coverage
#    expect: human_approval 0/321   actual_product_evidence 0/33
#            standards_mapping 38/38  source_grounding 131/321
#            automated_review_coverage 172/282  traceability_integrity 585/585

# 3. the suite passes
python3 docs/artifacts/tools/corpus.py check     # Acceptance suite: PASSED
python3 docs/artifacts/tools/corpus.py selftest  # 130/130

# 3b. an independent checker, sharing no code with the tool it checks
python3 docs/artifacts/tools/verify_approval_ledger_independently.py   # PASS

# 4. it passes from a clean checkout of HEAD, too
export PATH="$PATH:/opt/homebrew/bin"
git archive HEAD | tar -x -C /tmp/cl && cd /tmp/cl \
  && python3 docs/artifacts/tools/corpus.py check
```

```bash
# 5. the ledger is empty and nothing has been signed
python3 docs/artifacts/tools/verify_approval_ledger_independently.py
#    expect: A PASS (0 entries), B PASS (chain valid over an empty ledger),
#            C PASS (0 non-pending approvals, 0 evidence blocks, 0 ledger refs),
#            D PASS (321/321 packet digests), E PASS (every cited path resolves),
#            F PASS (0 filled signature blocks), G PASS (exactly one append site)
wc -c docs/artifacts/governance/approval-ledger.jsonl   # 0
```

**If `human_approval` is anything other than `0/321`, or `actual_product_evidence`
anything other than `0/33`, before any human has signed anything and before any
hardware has run, then something wrote a value it had no right to write.** Find it
before anything else.

**Equally: if the ledger is not 0 bytes, or `approval_staleness` is not `0/0`,
something wrote an approval without a person.** The first is a forgery or a
leftover; the second is a real judgement that no longer describes the bytes on
disk. Neither may be fixed by editing or deleting the entry - append a new one, or
find the person who signed.

---

*Figures in this document were read from `docs/artifacts/corpus/`,
`docs/artifacts/sources/source-registry.json`,
`docs/artifacts/traceability/link-registry/`, `docs/artifacts/reviews/records/`,
`docs/artifacts/reviews/findings/`,
`docs/artifacts/governance/role-and-review-policy.json` (both
`#/approval_evidence_contract` and the effective `#/approval_ledger_contract`),
`docs/artifacts/governance/corpus-policy.json`,
`docs/artifacts/governance/approval-ledger.jsonl` (0 bytes) and
`docs/artifacts/governance/approval-ledger.md`,
`docs/artifacts/governance/finding-disposition-vocabulary.md`,
`docs/artifacts/tools/corpus.py`,
`docs/artifacts/tools/make_review_packets.py` and
`docs/artifacts/tools/verify_approval_ledger_independently.py`. Every claim about
a rule names the rule; every claim about a count was counted from the tree, not
copied from a report.

The `approval_staleness` figure is a COUNTED METRIC reported beside the fifteen
coverage dimensions, not a sixteenth dimension, because "this corpus has fifteen
coverage dimensions" is a claim the audit trail relies on and inflating the count
to advertise a new measurement would make it false. It is reported on every
`coverage` run and on every `check` run, so it is as visible as a dimension would
be.*
