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
record as a human act. The machine-readable contract is
`docs/artifacts/governance/role-and-review-policy.json#/approval_evidence_contract`
and the validator implements it exactly; section 8 of every packet restates it
for the reviewer.

- `human_approval_status`: `approved` or `rejected` (both are recorded human
  decisions and both need a person behind them);
- an `approval_evidence.human_approval` block carrying all six required
  elements:
  1. the grant value;
  2. `approved_by` - a named **person**, not a role and not a team;
  3. `role` - a `role_id` declared in `role-and-review-policy.json` - plus
     `independence{owner_role, satisfied, evidence, policy_ref}`, where
     `owner_role` must equal **this record's own** `owner_role`. Independence is
     then enforced rather than asserted: the approving role must differ from
     `owner_role` **and** from the author of the last content revision;
  4. `date` in ISO-8601;
  5. `review_packet{path, sha256, record_sha256_at_signing}` - `path` may cite a
     packet here or in `reviews/packets/`, `sha256` must equal that file's bytes
     as they stand now, and `record_sha256_at_signing` must equal **that
     packet's own** `integrity.record_sha256`;
  6. a `revision_history` entry naming the reviewer, their role, the date, and
     **the packet digest they signed**, so the record is traceable to the exact
     bytes that were read;
- `automated_review_status` unchanged: it describes machine checks, not human
  judgement;
- `production_authorized` and `product_verification_credit` unchanged at `false`.
  No signature on a corpus record authorises production or confers verification
  credit. Granting production authority additionally requires an approving role
  that holds it (`architect` or `safety_manager`) and a record family human
  approval is required for (`safety_case`, `post_development_record`, `change`).

`python3 docs/artifacts/tools/make_review_packets.py --transcribe <ID>` prints
the exact block with both digests already resolved, writing nothing and filling
no decision. Use it rather than typing 64 hex characters.

**Recording the first approval no longer fails validation.** As of 2026-10-04,
amendment `APPROVAL-RULE-A1` replaced the blanket prohibition with the evidence
requirement above, so a properly evidenced approval is accepted and the
acceptance suite stays green. What the amendment did **not** do is produce one:
every record in this corpus is still `pending`, and writing an approval value
needs a person. If a finding arrives naming an unmet element, fix that element -
do not remove the approval.

## Rules for this directory

- **No generator may write here.** `make_review_packets.py` does not, by design.
- **No packet here may be edited after signing.** A corrected packet is a new
  document with a new signature, not an edit to a signed one.
- **A signed packet is never deleted.** A corpus that deletes the record of an
  approval it granted cannot show that it ever granted one - the same rule this
  corpus applies to finding records, which are never deleted either.
