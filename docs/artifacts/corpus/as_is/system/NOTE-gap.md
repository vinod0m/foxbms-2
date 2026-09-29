# Declared gap: no as_is system-level record

**This directory is intentionally empty of corpus artifact records.**
This file is a factual declaration of *why*, so that the emptiness is visible
rather than silent. It is not an artifact. It has no `id`, it is not a link
endpoint, and it is deliberately **not** a JSON record — see
"Why this is a `.md` and not a `.json` record" below.

- Profile: `as_is`
- Baseline commit investigated: `308028fb`
- Investigation date: 2026-09-29
- Guard posture for this directory: no record here is human-approved
  (`human_approval_status` would be `pending` on any record), none is
  `production_authorized` (`false`), and none carries
  `product_verification_credit` (`false`). No approval of any kind is claimed.

## What was searched for

The `as_is` profile may only record what the pinned source actually
demonstrates, marked `origin: "source_observed"`. The validator hard-fails an
`as_is` artifact claiming `origin: "synthetic"`, so nothing could have been
invented to fill this directory. The following searches were run against the
pinned tree, read-only:

1. `graft ask` over the indexed graph for *"system requirements specification,
   stakeholder needs, operational scenarios for the BMS item"*. Ranked retrieval
   returned only lexical noise on code symbols (`BMS_GetBatterySystemState`,
   `parse_config_to_system`, `validate_requirements_txt_versions` — the last of
   which validates **Python package pins** in `requirements.txt`, not
   engineering requirements). No requirement artifact surfaced.
2. Enumeration of every `.rst` / `.md` file in the pinned `docs/` tree: **237
   files**.
3. Path search across the whole pinned tree for `requirement`: the only hit is
   `requirements.txt` (Python package version pins).
4. Path search across the whole pinned tree for
   `use.case|operational.scenario|stakeholder`: the only hit is
   `docs/introduction/use-case.rst`.
5. Content search across pinned `docs/` for normative requirement language
   (`shall` / `must`): **zero matching files**.
6. Content search across pinned `docs/` for `risk register|project plan|
   measurement plan|capability level`: **zero matching files**.

## What was found

Two pinned documents describe the system in prose, and both are informal
explanatory text rather than requirements:

| Pinned file | Present at `308028fb` | What it actually contains |
|---|---|---|
| `docs/introduction/use-case.rst` | yes | Narrative prose. States that a use case must be defined per application, that the default application considers a **stationary storage**, that on error the **contactors open and disconnect the battery**, that **three power contactors** are used (main plus, main minus, pre-charge) and that there is **no separate charge path**. Carries a drawio figure. |
| `docs/introduction/bms-overview.rst` | yes | Narrative description of the platform: master plus slave boards, ARM Cortex-R5, CAN communication, passive balancing, daisy-chained slaves, contactor control. |

That is genuinely useful source evidence, and it is why no `source_observed`
record is **fabricated** to hide the gap. It is not, however, a system
requirements specification.

## Why no record was created

A corpus `requirement` record would imply more than the source supports, on
three independent counts:

1. **No elicitation, no identification, no baseline, no approval.** The pinned
   documentation contains zero normative `shall` / `must` statements and zero
   requirement identifiers. `use-case.rst` has no id, no verification method,
   no acceptance criteria, no revision history and no approval of any kind.
   Recording it as a requirement would grant it a status the source never gave it.
2. **It is a use case, not a system requirement.** ASPICE PAM 4.1 separates
   SYS.1 (Requirements Elicitation — stakeholder needs, use cases, operational
   scenarios) from SYS.2 (System Requirements Analysis). `use-case.rst` is
   SYS.1-flavoured narrative at best. Promoting it into the `system` domain
   would conflate the two.
3. **The generated view would overstate it.** The `system` view renders every
   `requirement`-typed record whose `engineering_domain` is `system` or
   `stakeholder` under a heading reading *"## System requirements"*. A use case
   placed there would be presented to a reader as a system requirement. Note
   that `engineering_domain` in `schemas/artifact-base.schema.json` has no
   `stakeholder` member, so the `stakeholder` branch of that filter cannot even
   be satisfied without a schema violation. Writing the record would have
   **created a new overclaim in exchange for closing one**, which is the exact
   failure mode this corpus exists to prevent.

## Consequence for the coverage plan

This gap is the evidence behind two corrections recorded in
`docs/artifacts/governance/coverage-plan.json`:

- `CORR-COV-002` — `process_inventory[SYS.2].disposition`: `mapped` → `gap`.
  The prior text asserted *"synthetic_reference SYS requirements created"*.
- `CORR-COV-001` — `process_inventory[SYS.1].disposition`: `mapped` → `gap`.
  The prior text asserted *"synthetic_reference stakeholder needs created;
  as_is back-inferred from features"*.

`CORR-COV-005` applies the same finding to
`iso26262_coverage.part_4_system`, which claimed *"system requirements,
architecture, technical safety concept"*. Only the architecture element is
backed, by the HSI interface authority `FB2-SYS-HSI-000001`.

The `expected_artifacts` and `capability_attributes` lists for SYS.1 and SYS.2
were **retained unchanged**. No expectation was deleted or narrowed to make a
dashboard look better.

## What would legitimately close this gap

Only real work, not a new file:

- An actual elicited and baselined system requirements specification for the
  pinned baseline, with stable ids, verification methods and review state; or
- a change to the corpus policy permitting `derived` reconstruction in the
  `as_is` profile, which the current policy forbids for this purpose.

Neither exists, so the gap stands.

## Why this is a `.md` and not a `.json` record

`docs/artifacts/tools/corpus.py` indexes artifact records by globbing `*.json`
under `corpus/` and `reviews/`. A JSON file placed here would be picked up and
validated as an artifact. A declaration of emptiness is not an artifact, and
forcing it into the artifact model would have required inventing an `id`, an
`artifact_type` outside `ARTIFACT_TYPE_SCHEMAS` (which the validator reports as
a high-severity *"schema … missing"* finding), and a link target. A Markdown
note is therefore the honest representation: visible, inert to the tooling, and
incapable of inflating any coverage count.

## Residual known-stale statement (reported, not fixed)

`docs/artifacts/tools/corpus.py` renders a fixed sentence into
`docs/artifacts/views/system/system.md` asserting that the coverage plan *"is
left unmodified because it is a canonical governance record"*. That sentence
described the corpus's prior state and is now inaccurate, because this task did
modify the coverage plan. The tool may not be modified under the task
constraints, so the stale sentence is reported rather than fixed. The **gap
itself** — the absence of any system-level or stakeholder requirement record —
remains true and is still correctly reported by the view.
