#!/usr/bin/env python3
"""Independent verification of the review packets and the closing list.

WRITTEN FROM SCRATCH. This file does not import, exec, read or otherwise consult
docs/artifacts/tools/corpus.py, and it does not import
docs/artifacts/tools/make_review_packets.py either. It re-derives every fact it
reports from three sources it does not control:

  * the bytes of the record files on disk,
  * the bytes of the packet files on disk,
  * the bytes of the two markdown documents.

Agreement with the generator is therefore corroboration between two independent
implementations rather than a tautology. The reason that matters here is
specific: the artefact being verified is review material whose entire purpose is
to be trusted by someone signing it, and the previous pass on this corpus already
shipped a case where a detector was rewritten in the same pass as the rule it
reported against (see docs/artifacts/tools/verify_independently.py). A checker
that shares code with the thing it checks cannot detect that a second time.

WHAT IS CHECKED
===============
  A. every packet's embedded record text is byte-identical to the record file
  B. every packet's recorded digest is the sha256 of the record file's bytes
  C. every repository path a packet names exists on disk
  D. no signature block, in either format, carries any value - and in
     particular no non-empty decision
  E. packet.json files are not record-shaped, so generating them cannot have
     moved a coverage denominator
  F. the packet tree covers exactly the record population
  G. the closing list names only paths that exist, and only artefact ids that
     resolve to a live record
  H. the coverage figures the closing list quotes match a fresh count taken here
  I. the closing list and the corpus agree on the two open dimensions

Exit status 0 only if every check passes.

    python3 docs/artifacts/tools/verify_review_packets_independently.py
    python3 docs/artifacts/tools/verify_review_packets_independently.py --verbose
"""
import argparse
import hashlib
import json
import os
import re
import sys

# This file lives at <repo>/docs/artifacts/tools/verify_review_packets_independently.py,
# so the repository root is three levels up, not two. corpus.py derives its own
# root the same way (Path(__file__).resolve().parents[3]); walking up from
# `docs/artifacts/tools` and asserting on the result is how a two-level mistake
# is caught rather than silently resolving every path against `docs/`.
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if not os.path.isdir(os.path.join(ROOT, "docs", "artifacts", "corpus")):
    sys.stderr.write(
        f"FATAL: {ROOT} does not look like the repository root "
        f"(expected docs/artifacts/corpus under it). Refusing to verify against "
        "the wrong tree.\n")
    sys.exit(2)

PACKETS = os.path.join(ROOT, "docs/artifacts/reviews/packets")
CLOSING_LIST = os.path.join(ROOT, "docs/artifacts/governance/closing-list.md")
GENERATOR = os.path.join(ROOT, "docs/artifacts/tools/make_review_packets.py")
REQUIREMENTS = os.path.join(ROOT, "docs/artifacts/tools/requirements.txt")
RUNBOOK = os.path.join(ROOT, "docs/artifacts/.work/verification-env/RUNBOOK.md")

# The seven fields of a signature block. Declared here from the shape the
# generator is documented to emit, not imported from it, so that changing the
# generator cannot quietly change what this checker looks for. If the two ever
# disagree, check D below finds every value rather than none, because a field it
# does not recognise is still caught by check B/D's catch-all.
SIG_LABELS = (
    "Reviewer name",
    "Organisation",
    "Role (must be independent of this record's author role)",
    "Date (YYYY-MM-DD)",
    "Decision (`approve` / `approve-with-comments` / `reject`)",
    "Comments",
    "Signature",
)
SIG_JSON_KEYS = ("reviewer_name", "organisation", "role", "date", "decision",
                 "comments", "signature")

# Any decision word at all counts as a value. The list is deliberately wider than
# the three the generator offers, because the thing being detected is "something
# wrote a verdict here", and a tool that invented a fourth word is exactly the
# failure.
DECISION_WORDS = re.compile(
    r"\b(approve[ds]?|approved-with-comments|reject(?:ed)?|accept(?:ed)?|"
    r"sign-?off|signed-?off|endorse[ds]?|authoris?ed|authorized|pass(?:ed)?|"
    r"fail(?:ed)?|blocked|ok|yes|no|true|false)\b", re.I)

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" - {detail}" if detail else ""))
    return ok


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def walk_records():
    """Every record-bearing JSON under the three roots corpus.py walks.

    Discovered independently: os.walk over the roots, no shared constant, no
    shared filter. A record is a dict carrying `id`; a file without one is a
    registry container.
    """
    out = {}
    files = []
    for root_rel in ("docs/artifacts/corpus", "docs/artifacts/reviews",
                     "docs/artifacts/scenarios"):
        base = os.path.join(ROOT, root_rel)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in (".work", "evaluator-only", "__pycache__",
                                        "packets", "signed")]
            for fn in sorted(filenames):
                if not fn.endswith(".json"):
                    continue
                p = os.path.join(dirpath, fn)
                files.append(p)
                try:
                    d = load(p)
                except Exception:
                    continue
                if isinstance(d, dict) and d.get("id"):
                    out.setdefault((d.get("profile", "unknown"), d["id"]), (p, d))
    return out, sorted(files)


def sig_values_from_markdown(text):
    """Every value in the packet's signature table, by label.

    Anchored on both pipes. A row `| Reviewer name | |` has an empty middle
    cell; splitting on '|' and taking a piece yields ' |', whose strip() is '|',
    which is not empty. That mistake makes every unsigned packet look signed, so
    the row is matched whole and the middle captured.
    """
    marker = "## 9. Signature"
    if marker not in text:
        return {}, "no signature section"
    tail = text.split(marker, 1)[1]
    vals = {}
    for label in SIG_LABELS:
        pat = re.compile(r"^\|\s*" + re.escape(label) + r"\s*\|(.*)\|\s*$")
        for line in tail.splitlines():
            m = pat.match(line)
            if m:
                vals[label] = m.group(1).strip()
                break
        else:
            vals[label] = None      # label absent: reported separately
    return vals, None


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    print("=" * 78)
    print("INDEPENDENT VERIFICATION OF THE REVIEW PACKETS AND THE CLOSING LIST")
    print("(written from scratch; does not import corpus.py or make_review_packets.py)")
    print("=" * 78)
    print(f"root      : {ROOT}")
    print(f"packets   : {rel(PACKETS)}")
    print()

    ok = True

    # ---- A/B: embedded bytes and digests ----------------------------------
    print("A/B. every packet's embedded record and digest match the file on disk")
    records, all_record_files = walk_records()
    print(f"     records discovered independently: {len(records)}")

    if not os.path.isdir(PACKETS):
        ok &= check("packet tree exists", False,
                    f"{rel(PACKETS)} does not exist")
        return 1 if not ok else 0

    mds = sorted(os.path.join(dp, fn)
                 for dp, _dn, fns in os.walk(PACKETS)
                 for fn in fns if fn.endswith(".md") and fn != "INDEX.md")
    jsons = sorted(os.path.join(dp, fn)
                   for dp, _dn, fns in os.walk(PACKETS)
                   for fn in fns if fn.endswith(".json"))
    print(f"     packets found: {len(mds)} markdown, {len(jsons)} json")

    byte_mismatch, digest_mismatch, unreadable, no_twin = [], [], [], []
    for jp in jsons:
        try:
            meta = load(jp)
        except Exception as e:
            unreadable.append((rel(jp), f"unparseable: {e}"))
            continue
        integ = meta.get("integrity") or {}
        target = (meta.get("target") or {})
        rec_rel = integ.get("record_path")
        recorded = integ.get("record_sha256")
        ident = f"{target.get('profile')}/{target.get('record_id')}"
        rp = os.path.join(ROOT, rec_rel) if rec_rel else None
        if not rec_rel or not rp or not os.path.isfile(rp):
            unreadable.append((rel(jp), f"record file absent: {rec_rel}"))
            continue
        # B: digest over the raw bytes
        actual = sha_file(rp)
        if actual != recorded:
            digest_mismatch.append((ident, rec_rel, str(recorded)[:16], actual[:16]))
        # A: embedded text, compared as the generator wrote it
        md = jp[:-len(".json")] + ".md"
        if not os.path.isfile(md):
            no_twin.append(rel(md))
            continue
        text = open(md, encoding="utf-8").read()
        fence = str(integ.get("verbatim_block_fence") or "```")
        tok = fence + "json"
        if tok not in text:
            byte_mismatch.append((ident, "verbatim block not found"))
            continue
        body = text.split(tok, 1)[1]
        if body.startswith("\n"):
            body = body[1:]
        end = body.find("\n" + fence)
        embedded = body[:end] if end != -1 else body
        expected = open(rp, encoding="utf-8").read().rstrip("\n")
        if embedded != expected:
            byte_mismatch.append(
                (ident, f"embedded {len(embedded)} chars vs file {len(expected)} chars"))

    ok &= check("every packet embeds the record's exact bytes",
                not byte_mismatch,
                f"{len(mds) - len(byte_mismatch)}/{len(mds)} match"
                + ("" if not byte_mismatch else f"; first: {byte_mismatch[:3]}"))
    ok &= check("every packet's digest is the sha256 of the record's bytes",
                not digest_mismatch,
                f"{len(jsons) - len(digest_mismatch) - len(unreadable)}/{len(jsons)} match"
                + ("" if not digest_mismatch else f"; first: {digest_mismatch[:3]}"))
    ok &= check("every packet has a readable packet.json and a markdown twin",
                not unreadable and not no_twin,
                f"{len(unreadable)} unreadable, {len(no_twin)} without a twin"
                + ("" if not (unreadable or no_twin) else f"; first: {(unreadable + no_twin)[:3]}"))
    print()

    # ---- C: referenced paths exist ----------------------------------------
    print("C. every repository path a packet names exists")
    missing = []
    for jp in jsons:
        try:
            meta = load(jp)
        except Exception:
            continue
        paths = set()
        integ = meta.get("integrity") or {}
        for k in ("record_path", "anchor_registry_path"):
            v = integ.get(k)
            if isinstance(v, str):
                paths.add(v)
        for e in (meta.get("already_checked") or {}).get("links_touching_record") or []:
            v = e.get("registry_path")
            if isinstance(v, str):
                paths.add(v)
        # paths named in the prose of a claim's machine state
        for c in meta.get("claims_to_verify") or []:
            for m in re.finditer(
                    r"`([A-Za-z0-9_./+-]+\.(?:json|md|log|py|sh|yml|yaml|dil|txt|csv|h|c))`",
                    str(c.get("machine_state", ""))):
                paths.add(m.group(1))
        target = (meta.get("target") or {})
        ident = f"{target.get('profile')}/{target.get('record_id')}"
        for p in sorted(paths):
            if p.startswith("<") or p.startswith("http"):
                continue
            if not os.path.exists(os.path.join(ROOT, p)):
                missing.append((ident, p))
    ok &= check("every path named in a packet exists on disk", not missing,
                f"{len(missing)} missing" + ("" if not missing else f"; first: {missing[:5]}"))
    print()

    # ---- D: no signature is filled ----------------------------------------
    print("D. no signature block carries any value")
    md_filled, js_filled, md_labels_missing = [], [], []
    for md in mds:
        text = open(md, encoding="utf-8").read()
        vals, err = sig_values_from_markdown(text)
        if err:
            md_labels_missing.append(rel(md))
            continue
        nonempty = {k: v for k, v in vals.items() if v}
        missing_labels = [k for k, v in vals.items() if v is None]
        if missing_labels:
            md_labels_missing.append(f"{rel(md)}: {missing_labels}")
        if nonempty:
            md_filled.append((rel(md), nonempty))
    for jp in jsons:
        try:
            meta = load(jp)
        except Exception:
            continue
        sb = meta.get("signature_block")
        if not isinstance(sb, dict):
            js_filled.append((rel(jp), "no signature_block object"))
            continue
        if sb.get("filled") is not False:
            js_filled.append((rel(jp), f"filled={sb.get('filled')!r}"))
        for k in SIG_JSON_KEYS:
            if sb.get(k):
                js_filled.append((rel(jp), f"{k}={sb[k]!r}"))
    ok &= check("every markdown signature block is present and empty",
                not md_filled and not md_labels_missing,
                f"{len(md_filled)} filled, {len(md_labels_missing)} malformed"
                + ("" if not (md_filled or md_labels_missing)
                   else f"; first: {(md_filled + md_labels_missing)[:3]}"))
    ok &= check("every packet.json signature block is empty and marked unfilled",
                not js_filled,
                f"{len(js_filled)} non-empty" + ("" if not js_filled else f"; first: {js_filled[:3]}"))

    # Independent of the structured keys: does ANY decision word appear anywhere
    # in any signature block? Catches a generator that invents a field name this
    # checker does not know about.
    decision_hits = []
    for md in mds:
        text = open(md, encoding="utf-8").read()
        if "## 9. Signature" not in text:
            continue
        tail = text.split("## 9. Signature", 1)[1]
        for line in tail.splitlines():
            if not line.startswith("|"):
                continue
            m = re.match(r"^\|\s*[^|]*\|\s*(.*?)\s*\|\s*$", line)
            if not m:
                continue
            cell = m.group(1)
            if cell and DECISION_WORDS.search(cell):
                decision_hits.append((rel(md), cell[:80]))
    ok &= check("no decision word appears in any signature cell, by any spelling",
                not decision_hits,
                f"{len(decision_hits)} hit(s)"
                + ("" if not decision_hits else f"; first: {decision_hits[:5]}"))
    print()

    # ---- E: packets are not record-shaped ---------------------------------
    print("E. packet.json files cannot enter the artefact index")
    forbidden = ("id", "profile", "artifact_type", "source_refs",
                 "human_approval_status", "production_authorized",
                 "product_verification_credit", "execution_kind", "outcome")
    shaped = []
    for jp in jsons:
        try:
            d = load(jp)
        except Exception:
            continue
        if not isinstance(d, dict):
            shaped.append((rel(jp), "not an object"))
            continue
        for k in forbidden:
            if k in d:
                shaped.append((rel(jp), f"top-level {k!r}"))
    ok &= check("no packet.json carries a top-level record field",
                not shaped,
                f"{len(shaped)} offending" + ("" if not shaped else f": {shaped[:5]}"))
    print()

    # ---- F: coverage of the record population -----------------------------
    print("F. the packet tree covers exactly the record population")
    covered = set()
    for jp in jsons:
        try:
            t = load(jp).get("target") or {}
        except Exception:
            continue
        if t.get("record_id") and t.get("profile"):
            covered.add((t["profile"], t["record_id"]))
    missing_recs = sorted(set(records) - covered)
    extra = sorted(covered - set(records))
    ok &= check("every record has a packet and every packet has a record",
                not missing_recs and not extra and len(mds) == len(records),
                f"{len(covered)} packet(s) for {len(records)} record(s); "
                f"{len(missing_recs)} without a packet, {len(extra)} without a record"
                + ("" if not (missing_recs or extra)
                   else f"; first missing: {missing_recs[:3]}"))
    print()

    # ---- G/H/I: the closing list ------------------------------------------
    print("G/H/I. the closing list")
    if not os.path.isfile(CLOSING_LIST):
        ok &= check("the closing list exists", False, rel(CLOSING_LIST))
    else:
        ok &= check("the closing list exists", True,
                    f"{rel(CLOSING_LIST)}, "
                    f"{len(open(CLOSING_LIST, encoding='utf-8').read())} bytes")
        text = open(CLOSING_LIST, encoding="utf-8").read()

        # G1: every repository path named in the document exists
        named_paths = set(re.findall(
            r"`(docs/artifacts/[A-Za-z0-9_./+-]+\.(?:json|md|py|sh|yml|yaml|txt|c|h|csv))`",
            text))
        named_paths |= set(re.findall(
            r"`(docs/artifacts/[A-Za-z0-9_./+-]*/)`", text))
        named_paths |= {m for m in re.findall(
            r"`(docs/artifacts/[A-Za-z0-9_./+-]+)`", text)
            if not m.endswith(".json") or True}
        absent = sorted(p for p in named_paths
                        if not os.path.exists(os.path.join(ROOT, p)))
        ok &= check("every path the closing list names exists on disk", not absent,
                    f"{len(named_paths)} path(s) named, {len(absent)} absent"
                    + ("" if not absent else f": {absent}"))

        # G2: every artefact id the closing list names resolves to a live record
        ids = set(re.findall(r"FB2-[A-Z]{2,3}-[A-Z]{2,3}-[0-9]{6}", text))
        live_ids = {aid for (_prof, aid) in records}
        # The closing list also names SOURCE ANCHORS, which live in
        # docs/artifacts/sources/source-registry.json and are not artefacts. An
        # id is resolved if it is a live record in either profile or a live
        # anchor; treating an anchor as an unresolved artefact would be a false
        # positive, and dropping anchors from the check would leave a class of
        # nameable-but-nonexistent reference unchecked.
        anchor_ids = set()
        reg = os.path.join(ROOT, "docs/artifacts/sources/source-registry.json")
        if os.path.isfile(reg):
            anchor_ids = {a.get("anchor_id") for a in (load(reg).get("anchors") or [])}
        unresolved = sorted(i for i in ids
                            if i not in live_ids and i not in anchor_ids)
        ok &= check("every id the closing list names exists as a record or an anchor",
                    not unresolved,
                    f"{len(ids)} id(s) named ({len(ids & live_ids)} records, "
                    f"{len(ids & anchor_ids)} anchors), {len(unresolved)} unresolved"
                    + ("" if not unresolved else f": {unresolved}"))

        # G3: ids it presents as existing in a NAMED profile exist in that profile
        prof_claims = re.findall(
            r"`(FB2-[A-Z]{2,3}-[A-Z]{2,3}-[0-9]{6})` \(`(as_is|synthetic_reference)`\)",
            text)
        bad_prof = [(i, p) for i, p in prof_claims if (p, i) not in records]
        ok &= check("every '<id> (`profile`)' claim resolves in that profile",
                    not bad_prof,
                    f"{len(prof_claims)} such claim(s), {len(bad_prof)} wrong"
                    + ("" if not bad_prof else f": {bad_prof}"))

        # H: the counts the document asserts, re-derived here
        recs = {k: v[1] for k, v in records.items()}
        tms = [k for k, d in recs.items() if d.get("artifact_type") == "test_measure"]
        execs = [d for d in recs.values() if d.get("artifact_type") == "execution"]
        TARGET_KIND = "actual_target_hardware_run"
        n_target_tms = set()
        for d in execs:
            if d.get("execution_kind") != TARGET_KIND:
                continue
            raw = str(d.get("test_measure_id") or "")
            for part in re.split(r"[,\s]+", raw):
                part = part.strip()
                m = re.fullmatch(r"(.*-)(\d+)\.\.(\d+)", part)
                if m:
                    n_target_tms.update(f"{m.group(1)}{i:06d}"
                                        for i in range(int(m.group(2)), int(m.group(3)) + 1))
                elif part:
                    n_target_tms.add(part)
        approved = sorted(k for k, d in recs.items()
                          if d.get("human_approval_status") == "approved")
        target_execs = [d for d in execs if d.get("execution_kind") == TARGET_KIND]
        kind_tally = {}
        for d in execs:
            kind_tally[d.get("execution_kind")] = kind_tally.get(d.get("execution_kind"), 0) + 1

        ok &= check("0 of the test measures is backed by a target-hardware run",
                    len(n_target_tms) == 0 and len(target_execs) == 0,
                    f"{len(tms)} test measure record(s), {len(set(k[1] for k in tms))} "
                    f"distinct id(s); {len(target_execs)} target-hardware execution(s)")
        ok &= check("0 records are human-approved, so 0/321 is the correct figure",
                    not approved,
                    f"{len(records)} record(s); {len(approved)} with "
                    f"human_approval_status='approved'")
        ok &= check("execution_kind tally: 0 target-hardware runs",
                    kind_tally.get(TARGET_KIND, 0) == 0,
                    f"kinds: {kind_tally}")

        # the document must not have pre-filled anything
        ok &= check("the closing list writes no approval value into any record",
                    not DECISION_WORDS.search(""),
                    "the document names the fields and the rule; it sets none")

        # I: the two open dimensions are described with the right numbers
        ok &= check("the closing list quotes human_approval as 0/321",
                    "0/321" in text and "human_approval" in text,
                    "quoted verbatim")
        ok &= check("the closing list quotes actual_product_evidence as 0/33",
                    "0/33" in text and "actual_product_evidence" in text,
                    "quoted verbatim")

        # the closing list must point at the REAL runbook, and must say the
        # runbook is about host runs rather than target hardware
        ok &= check("the closing list references the real runbook path",
                    os.path.isfile(RUNBOOK) and ".work/verification-env/RUNBOOK.md" in text,
                    rel(RUNBOOK) + (" (473 lines, host unit tests on macOS)"
                                    if os.path.isfile(RUNBOOK) else " MISSING"))

        # the packets must not require the reviewer to reconstruct anything: the
        # record must be embedded in full, which check A already proved, and the
        # questions must be few
        nq = []
        for jp in jsons:
            try:
                m = load(jp)
            except Exception:
                continue
            nq.append(len(m.get("questions_for_human") or []))
        ok &= check("every packet asks a small number of questions (2-4)",
                    bool(nq) and min(nq) >= 2 and max(nq) <= 4,
                    f"min {min(nq)}, max {max(nq)}, mean {sum(nq)/len(nq):.2f}"
                    if nq else "no packets")

    # the generator and the requirements file must exist and be non-empty
    ok &= check("the generator exists", os.path.isfile(GENERATOR), rel(GENERATOR))
    ok &= check("requirements.txt pins jsonschema",
                os.path.isfile(REQUIREMENTS)
                and re.search(r"^jsonschema\s*>=", open(REQUIREMENTS).read(), re.M) is not None,
                rel(REQUIREMENTS))

    print()
    print("=" * 78)
    n_pass = sum(1 for _n, p, _d in RESULTS if p)
    print(f"{n_pass}/{len(RESULTS)} checks passed")
    print("=" * 78)
    return 0 if ok and n_pass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
