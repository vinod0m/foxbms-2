# Signed review packets land here

**This directory is for completed, signed review packets. It is not generated,
and nothing in it may be written by a tool.**

Every packet under `docs/artifacts/reviews/packets/` carries an empty signature
block, because a signature is a human act and this corpus will not let a process
imitate one. The generator has no code path that writes a decision, an approval
field, a signature or an execution verdict; `corpus.py selftest` reads all 321
generated packets in both formats on every run and fails if any of the seven
signature fields carries a value.

## Where a signed packet goes

1. Take the packet from `docs/artifacts/reviews/packets/<profile>/<id>.md`.
2. Answer its section 7 in your own copy.
3. Fill section 9 in your own copy.
4. Put the signed copy here, under the same `<profile>/` subdirectory, with the
   same filename. Keep it byte-for-byte as you signed it: the sha256 in its
   section 2 is the digest of the *record*, and the packet is the evidence that
   those are the bytes you read.

## Why not sign in place

`docs/artifacts/tools/make_review_packets.py` **refuses to overwrite a packet that
already carries a signature** and says where to move it, rather than destroying
it. That guard is tested - `corpus.py selftest` runs the generator, injects a
signature into a generated packet, runs the generator again, and asserts the
signature survived.

The guard exists because regeneration is routine. A corpus that regenerates its
review material weekly and stores signatures beside the generated material will
lose every approval it has ever collected, silently, within one cycle. This
directory is the separation that makes the guard unnecessary in the common path.

## What gets recorded in the record itself

A signed packet is evidence, not the record. The decision is transcribed into the
record as a human act:

- `human_approval_status`: `approved`, `rejected`, or `not_required`;
- a `revision_history` entry naming the reviewer, their role, the date, and the
  **packet digest they signed** - the sha256 in section 2 of the packet - so the
  record is traceable to the exact bytes that were read;
- `automated_review_status` unchanged: it describes machine checks, not human
  judgement;
- `production_authorized` and `product_verification_credit` unchanged at `false`.
  No signature on a corpus record authorises production or confers verification
  credit.

Recording the first approval currently fails validation, by design: the
`human_approval_rejected` rule fires on any record whose `human_approval_status`
is `approved`, and the acceptance suite gates on it. That amendment is
prerequisite P1 in `docs/artifacts/governance/closing-list.md` §1.6 and must be
made deliberately, by the corpus owner, **before** the first signature is
recorded - otherwise the person who signs is blamed for turning the build red.

## Rules for this directory

- **No generator may write here.** `make_review_packets.py` does not, by design.
- **No packet here may be edited after signing.** A corrected packet is a new
  document with a new signature, not an edit to a signed one.
- **A signed packet is never deleted.** A corpus that deletes the record of an
  approval it granted cannot show that it ever granted one - the same rule this
  corpus applies to finding records, which are never deleted either.
