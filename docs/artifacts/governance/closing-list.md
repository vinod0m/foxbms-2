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

---

## 0. Read this before you start

Four things about the corpus's current state will waste a day if you do not know
them. All four are read from the code, not inferred.

### 0.1 `human_approval` is a constant, not a measurement

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

### 0.2 Recording the first approval will turn `check` RED

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

Per record, one signed packet, and one line of transcription into the record:

1. **The signed packet.** Keep it. Do not leave it in
   `docs/artifacts/reviews/packets/`: regeneration overwrites that tree, and the
   generator **refuses** to overwrite a packet that already carries a signature
   rather than destroy it. Archive signed packets in
   `docs/artifacts/reviews/signed/<profile>/`, which exists and carries a README
   stating the rules; no generator writes there, by design.
2. **The decision, transcribed into the record by a human:**
   - `human_approval_status`: `approved` or `rejected` (the schema's value set is
     `pending | approved | rejected | not_required`, per
     `role-and-review-policy.json` `approval_semantics`);
   - a `revision_history` entry naming the reviewer, their role, the date, and
     **the packet digest they signed** - the sha256 in section 2 of the packet -
     so the record is traceable to the exact bytes that were read;
   - `automated_review_status` **left alone**. It describes machine checks
     (`schema_valid`, `links_valid`, `provenance_consistent`,
     `consistency_checks`) and is not a statement about human judgement;
   - `production_authorized` and `product_verification_credit` **left `false`**.
     No signature on a corpus record authorises production or confers
     verification credit. Changing those is §0.2's business, not a reviewer's.
3. **The comments**, which are the most valuable output. A `reject` with a
   reason is worth more than an `approve`.

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

These are **P1** items. They are not review work; they are the changes that make
review work recordable. Each needs R19 (System Architect) as owner.

| id | decision | why it blocks |
| --- | --- | --- |
| **P1** | Amend `human_approval_rejected` so a **recorded, attributed** human approval is not a validation failure. Proposed shape: the rule fires unless the record carries a human decision block - reviewer name, role, organisation, date, decision, and the packet digest - that resolves to an archived signed packet. | Without this the first signature turns `check` RED (§0.2), and the signer is blamed for it. |
| **P1** | Decide whether `human_approval` stays a constant `0` (§0.1) or becomes a measurement. If measured: `numerator` = records with a human decision, `denominator` = 321, and the coverage report's basis table changes from `constant` to `measured`. | Either answer is defensible. Leaving it undecided means nobody knows whether a landed signature worked. |
| **P2** | Add the seven undeclared `owner_role` values to `role-and-review-policy.json`, or map them to declared roles (§1.2). | A signature under an undefined role is not traceable to a competence requirement. |
| **P2** | Confirm `docs/artifacts/reviews/signed/` as the canonical archive location. **The directory now exists** with a README stating the rules, and no generator writes there; what is outstanding is the corpus owner's ratification of the location. | Otherwise a signed packet has no canonical home and a regeneration is one `rm -rf` away from destroying it. |
| **P2** | Amend `production_authorized_rejected` and `verification_credit_rejected` - or record explicitly that they stay as they are. | They are not in scope for approval work, and a corpus owner should say so rather than leave it ambiguous. |

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

1. Archive the signed packets **outside** `docs/artifacts/reviews/packets/`.
2. Transcribe each decision into its record: `human_approval_status` plus a
   `revision_history` entry naming the reviewer, role, date and signed packet
   digest. **A human does this. No tool does this.**
3. Record the batch: which records, which signatures, which rejections and why,
   and which records in the batch were not signed and why. A batch record that
   lists only approvals is a misleading batch record.
4. Re-run and read every number:
   ```bash
   python3 docs/artifacts/tools/corpus.py validate
   python3 docs/artifacts/tools/corpus.py check
   python3 docs/artifacts/tools/corpus.py selftest
   python3 docs/artifacts/tools/make_review_packets.py --verify
   ```
5. **Expect `check` to be RED on the first batch** unless P1 (§1.6) is done
   first. `human_approval_rejected` will fire on every approved record, in
   `[7/8] no production authority, no verification credit, no human approval`. If
   that is what you see, the signatures worked and the rule needs amending. If
   you see it *after* amending the rule, the amendment is wrong.
6. Expect `human_approval` to still read `0/321` unless P1's second half is done
   (§0.1).
7. Regenerate the packets. Records that changed get new digests; the generator
   refuses to overwrite the signed packets you archived elsewhere, and the
   freshly generated packets for those records carry the *new* digest. A signature
   against the old digest provably does not cover the new bytes - which is the
   point of the digest.
8. `automated_review_coverage` is expected to stay at `172/282` and
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
- [x] the §1.6 P1 rule amendment, so the resulting record can be recorded without
      breaking the suite.

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
| `human_approval_rejected` | `corpus.py` `_validate_artifact`, severity **high** | fails validation on any record whose `human_approval_status == "approved"` |
| `production_authorized_rejected` | same, severity **critical** | fails on `production_authorized == true` |
| `verification_credit_rejected` | same, severity **high** | fails on `product_verification_credit == true` |
| acceptance gate | `corpus.py check` `[7/8] no production authority, no verification credit, no human approval` | counts violations across all **8** governance rules, and separately asserts the rule set is non-empty and covers the four named claim classes, so the filter cannot be emptied |
| packet-level | `make_review_packets.py --verify`, and `corpus.py check` `[7c/8]` | a non-empty signature block in a generated packet is reported by name |
| self-test | `corpus.py selftest` | *"every signature block in every generated packet is empty, in both formats"* - reads all 321 markdown packets **and** all 321 `packet.json` twins and asserts every one of the seven fields is empty |
| self-test | `corpus.py selftest` | *"the generator refuses to overwrite a packet that already carries a signature"* - injects a signature, regenerates, asserts it survived |
| independence | `corpus.py selftest` | *"the packet generator's signature fields match the ones check looks for"* - so the checker cannot be blinded by editing the generator's field labels |

**The residual risk, stated honestly.** The P1 amendment in §1.6 will make
`human_approval_rejected` stop firing on a *legitimately* attributed approval. The
moment it does, the mechanical guard against fabrication is weakened, and what
replaces it is the attribution requirement: reviewer name, role, organisation,
date and signed-packet digest, resolving to an archived packet. **Design P1 so
that a record with a non-attributed approval still fails.** If P1 is implemented
as "allow `approved`", it has removed the guard and installed nothing.

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

`corpus.py` exits **2** with a single line if `jsonschema` cannot be imported:

```
ERROR: jsonschema library required (pip install jsonschema)
```

`make_review_packets.py` degrades differently and worse: it reports schema checks
as *"validator unavailable"* in section 5.1 of every packet and carries on.

**Why this matters more than a missing package.** Neither tool is installed by
anything: there is no `requirements.txt`, no `pyproject.toml`, no CI step. The
corpus tooling is a set of scripts run directly against the system interpreter.
On a machine without `jsonschema`, `corpus.py check` **does not run at all** -
and a reader who has not read the source concludes the corpus is unverified
rather than un-runnable. Those are very different situations and the difference
is invisible from outside.

Now declared, in `docs/artifacts/tools/requirements.txt`:

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

```bash
python3 -m pip install --user -r docs/artifacts/tools/requirements.txt
python3 -c "import jsonschema, referencing; print(jsonschema.__version__)"
python3 docs/artifacts/tools/corpus.py check
```

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
python3 docs/artifacts/tools/corpus.py selftest  # 101/101

# 4. it passes from a clean checkout of HEAD, too
export PATH="$PATH:/opt/homebrew/bin"
git archive HEAD | tar -x -C /tmp/cl && cd /tmp/cl \
  && python3 docs/artifacts/tools/corpus.py check
```

**If `human_approval` is anything other than `0/321`, or `actual_product_evidence`
anything other than `0/33`, before any human has signed anything and before any
hardware has run, then something wrote a value it had no right to write.** Find it
before anything else.

---

*Figures in this document were read from `docs/artifacts/corpus/`,
`docs/artifacts/sources/source-registry.json`,
`docs/artifacts/traceability/link-registry/`, `docs/artifacts/reviews/records/`,
`docs/artifacts/reviews/findings/`,
`docs/artifacts/governance/role-and-review-policy.json`,
`docs/artifacts/governance/finding-disposition-vocabulary.md` and
`docs/artifacts/tools/corpus.py` at commit `cecececf`, with the packet tooling
uncommitted in the working tree. Every claim about a rule names the rule; every
claim about a count was counted from the tree, not copied from a report.*
