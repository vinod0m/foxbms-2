# TRACEABILITY_DOCUMENT.md — pointer

**This path is a pointer, not the document.** It contains no engineering
content, so it cannot go stale and cannot make a claim the corpus does not
support.

## What the document is

The traceability document for the foxBMS 2 **synthetic** lifecycle artifact
corpus under `docs/artifacts/`. It is a derived work product: a census of the
records the corpus holds, of the links between them, of the guard-field
position across the whole corpus, of standards dispositions as the corpus's own
coverage plan records them, of the coverage dimensions recomputed on the run,
and of the negative-scenario suite's measured result.

## Where it is

**Canonical (generated):** [`docs/artifacts/views/traceability/traceability-document.md`](docs/artifacts/views/traceability/traceability-document.md)

A second pointer to the same canonical file, kept so that the path this note
replaces stays meaningful, is at
[`docs/artifacts/reports/TRACEABILITY_DOCUMENT.md`](docs/artifacts/reports/TRACEABILITY_DOCUMENT.md).
There is exactly one document with engineering content; these are the only two
places that point at it.

## It is generated

The canonical file is produced by `python3 docs/artifacts/tools/corpus.py render`
and carries the same provenance header and guard-field contract as every other
generated view: it states that it is derived rather than authored, that it is
regenerable, that no record in it is human-approved, and that it asserts no
standard conformity and no capability level. Two render runs are byte-identical
apart from the `Generated:` stamp.

Edit the canonical JSON records under `docs/artifacts/` and re-render. Do not
edit a generated file, and do not create a second copy of this document at this
path.

## Why this file is a pointer

This file used to be a 600-line hand-authored document that no tool read, no
renderer regenerated, and no check covered. It carried an unsupported ISO 26262
conformity claim, an ASIL capability claim and a fabricated approval sign-off
block. Those defects were corrected by hand, but a hand-maintained control is
not a control: it drifted back once already, and nothing would have detected it.
That is recorded as finding `FB2-REV-FND-000022`, and the drift risk is now
closed by the file being generated rather than by human discipline.

## What this document is not

It is not a conformity, certification or qualification package. It records no
human approval, no tool qualification, no ASPICE capability level, and no ASIL
determination for any real product. Every artifact in the corpus is
`human_approval_status: pending` and `production_authorized: false`, and no
HARA has been performed for any real product.
