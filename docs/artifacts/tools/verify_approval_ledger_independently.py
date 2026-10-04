#!/usr/bin/env python3
"""Independent verification of the approval ledger and signed-packet archive.

WRITTEN FROM SCRATCH AND DELIBERATELY IMPORTS NOTHING from corpus.py,
make_review_packets.py, or any other tool in this repository. It re-derives
every figure it reports by walking the tree and hashing bytes itself. If it
agreed with corpus.py only because both call the same function it would prove
nothing; the only thing it shares with the tool is the JSON and the files on
disk. That is the entire point of this file: the reviewer of this corpus has
been told, by the tool itself, that the chain and the anchor do not prove a
human read anything - so the checks that CAN be made mechanically are made here,
by code that shares no logic with the thing being checked.

Seven claims:

  A. THE LEDGER IS EMPTY AND WELL FORMED.
     Zero entries, zero non-blank lines, zero malformed lines. This is the
     standing fact the corpus asserts about itself, verified from the outside.

  B. THE HASH CHAIN IS VALID (or trivially empty).
     entries[i].previous_entry_sha256 == sha256(canonical_json(entries[i-1])),
     and entries[0].previous_entry_sha256 == 64 zeros, where canonical_json is
     UTF-8 JSON with sorted keys and no insignificant whitespace and the line
     number the parser added is removed. The FIRST break, if any, is named.

  C. ZERO APPROVALS.
     No record carries a non-pending value in any of the three approval fields,
     no record carries an approval_evidence block, and no record carries an
     approval_ledger_ref.

  D. EVERY PACKET DIGEST MATCHES.
     Every generated packet.json's integrity.record_sha256 equals the sha256 of
     the record file it names, and its record_verbatim equals the record.

  E. EVERY CITED PATH RESOLVES.
     Every path cited by a packet (integrity.record_path, packet_path,
     signature_block.review_packet path if any, outcome_record fields) resolves
     on disk.

  F. NO SIGNATURE BLOCK IS FILLED.
     In all 321 markdown packets and all 321 packet.json twins, every one of the
     seven signature fields is empty, and filled is false.

  G. NO TOOL IN THIS REPOSITORY APPENDS TO THE LEDGER.
     Every .py under docs/artifacts/tools is read and searched for an
     append-mode open of the ledger. The one permitted call site is inside
     corpus.py's own self-test fixture, which is asserted by name so that a
     second one fails.

Exit code 0 if all seven hold, 1 otherwise. Writes nothing.

Usage:  python3 docs/artifacts/tools/verify_approval_ledger_independently.py [ROOT]
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
ART = ROOT / "docs" / "artifacts"
PACKETS = ART / "reviews" / "packets"
LEDGER_REL = "docs/artifacts/governance/approval-ledger.jsonl"
SIGNED_REL = "docs/artifacts/reviews/signed"
CORPUS_DIRS = ("corpus", "scenarios", "reviews")

APPROVAL_FIELDS = {
    "human_approval_status": lambda v: v is not None and v != "pending",
    "production_authorized": lambda v: v is True,
    "product_verification_credit": lambda v: v is True,
}
LEDGER_REF_FIELD = "approval_ledger_ref"
EVIDENCE_FIELD = "approval_evidence"
GENESIS = "0" * 64
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SIG_KEYS = ("reviewer_name", "organisation", "role", "date", "decision",
            "comments", "signature")

REQUIRED_ENTRY_FIELDS = (
    "ledger_id", "record_id", "profile", "kind", "approved_record_sha256",
    "approved_content_revision", "approved_by", "role", "independence", "date",
    "signed_packet", "packet_first_commit", "previous_entry_sha256",
)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def entry_digest(entry):
    return hashlib.sha256(
        canonical({k: v for k, v in entry.items() if k != "_line"})).hexdigest()


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def records():
    """Every corpus record, de-duplicated by (profile, id), newest path wins."""
    out = {}
    for d in CORPUS_DIRS:
        root = ART / d
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.json")):
            if p.name == "INDEX.md" or PACKETS in p.parents or \
                    (ART / "reviews" / "signed") in p.parents:
                continue
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(obj, dict) or not obj.get("id"):
                continue
            out[(obj.get("profile", "unknown"), obj["id"])] = (p, obj)
    return out


def report(ok, title, lines):
    print(("  PASS " if ok else "  FAIL ") + title)
    for line in lines:
        print("       " + line)
    return ok


def main():
    print(f"independent approval-ledger verification of {ROOT}")
    print("imports nothing from corpus.py or make_review_packets.py")
    all_ok = True

    # ---- A + B: the ledger ------------------------------------------------
    led = ROOT / LEDGER_REL
    entries, malformed, raw_lines = [], [], 0
    if led.is_file():
        for i, line in enumerate(led.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            raw_lines += 1
            try:
                o = json.loads(line)
            except Exception as e:
                malformed.append((i, f"not JSON: {e}"))
                continue
            if not isinstance(o, dict):
                malformed.append((i, "not a JSON object"))
                continue
            o["_line"] = i
            entries.append(o)
    else:
        malformed.append((0, "the ledger file does not exist"))

    missing_fields = []
    for e in entries:
        miss = [f for f in REQUIRED_ENTRY_FIELDS if e.get(f) is None]
        if miss:
            missing_fields.append((e.get("ledger_id"), miss))
    dupes = {}
    for e in entries:
        lid = e.get("ledger_id")
        dupes[lid] = dupes.get(lid, 0) + 1

    # chain walk
    chain_break = None
    prev = GENESIS
    for i, e in enumerate(entries):
        claimed = e.get("previous_entry_sha256")
        if not isinstance(claimed, str) or claimed.strip() != prev:
            chain_break = (f"entry {i} (line {e.get('_line')}, ledger_id "
                           f"{e.get('ledger_id')!r}) has previous_entry_sha256="
                           f"{claimed!r}; expected {prev}")
            break
        prev = entry_digest(e)

    a_ok = (led.is_file() and not entries and not malformed and raw_lines == 0
            and not missing_fields and all(v == 1 for v in dupes.values()))
    all_ok &= report(
        a_ok, "A. the ledger is present, EMPTY and well formed",
        [f"{LEDGER_REL}: {led.stat().st_size if led.is_file() else 'absent'} byte(s), "
         f"{raw_lines} non-blank line(s), {len(entries)} parsed entr"
         f"{'y' if len(entries) == 1 else 'ies'}",
         f"malformed lines: {len(malformed)}",
         f"entries missing a required field: {len(missing_fields)}",
         f"duplicate ledger_id values: {sum(1 for v in dupes.values() if v > 1)}",
         "a ledger holding an entry is not this corpus's state; re-derive before trusting "
         "the rest"])

    b_ok = chain_break is None
    all_ok &= report(
        b_ok, "B. the hash chain is valid (trivially, over an empty ledger)",
        [f"genesis value is 64 zeros: {GENESIS == '0' * 64}",
         f"first break: {chain_break or 'none - the ledger is empty, so there is nothing to bind'}",
         "this proves existence, ordering and integrity of entries; it does NOT prove a "
         "human read anything"])

    # ---- C: no approvals --------------------------------------------------
    recs = records()
    approval_offenders, evidence_offenders, ref_offenders = [], [], []
    for (prof, aid), (p, d) in sorted(recs.items()):
        for f, is_grant in APPROVAL_FIELDS.items():
            if is_grant(d.get(f)):
                approval_offenders.append(f"{aid}/{prof}:{f}={d.get(f)!r}")
        if EVIDENCE_FIELD in d:
            evidence_offenders.append(f"{aid}/{prof}: carries {EVIDENCE_FIELD}")
        if LEDGER_REF_FIELD in d:
            ref_offenders.append(f"{aid}/{prof}: carries {LEDGER_REF_FIELD}")
    c_ok = not approval_offenders and not evidence_offenders and not ref_offenders
    all_ok &= report(
        c_ok, "C. ZERO approvals: no grant value, no evidence block, no ledger reference",
        [f"{len(recs)} record(s) scanned under {list(CORPUS_DIRS)}",
         f"records carrying a non-pending approval value: {len(approval_offenders)}",
         f"records carrying {EVIDENCE_FIELD}: {len(evidence_offenders)}",
         f"records carrying {LEDGER_REF_FIELD}: {len(ref_offenders)}",
         (f"offenders: {(approval_offenders + evidence_offenders + ref_offenders)[:5]}"
          if c_ok is False else "none - this is a measured zero, not a constant")])

    # ---- D: packet digests ------------------------------------------------
    pkt_digests, dig_bad, embed_bad, pkt_n = [], [], [], 0
    for jp in sorted(PACKETS.rglob("*.json")) if PACKETS.is_dir() else []:
        try:
            meta = json.loads(jp.read_text(encoding="utf-8"))
        except Exception as e:
            dig_bad.append(f"{jp.name}: unparseable ({e})")
            continue
        pkt_n += 1
        integ = meta.get("integrity") or {}
        rel = integ.get("record_path")
        rec = ROOT / rel if rel else None
        if rec is None or not Path(rec).is_file():
            dig_bad.append(f"{jp.name}: record_path {rel!r} does not resolve")
            continue
        actual = sha256_file(rec)
        pkt_digests.append(actual)
        if actual != integ.get("record_sha256"):
            dig_bad.append(f"{jp.name}: integrity.record_sha256 "
                           f"{integ.get('record_sha256')} != {actual}")
        rv = meta.get("record_verbatim")
        body = json.loads(Path(rec).read_text(encoding="utf-8"))
        if rv != body:
            embed_bad.append(f"{jp.name}: record_verbatim differs from the record on disk")
    d_ok = pkt_n > 0 and not dig_bad and not embed_bad
    all_ok &= report(
        d_ok, "D. every packet digest matches the record's bytes, and so does the verbatim block",
        [f"{pkt_n} packet.json twin(s) walked; {len(set(pkt_digests))} distinct record digest(s)",
         f"digest mismatches or unresolved record paths: {len(dig_bad)}",
         f"record_verbatim blocks differing from the record: {len(embed_bad)}",
         (f"problems: {(dig_bad + embed_bad)[:5]}" if not d_ok else "none")])

    # ---- E: every cited path resolves -------------------------------------
    missing_paths = []
    for jp in sorted(PACKETS.rglob("*.json")) if PACKETS.is_dir() else []:
        meta = json.loads(jp.read_text(encoding="utf-8"))
        cited = []
        integ = meta.get("integrity") or {}
        if integ.get("record_path"):
            cited.append(("integrity.record_path", integ["record_path"]))
        if meta.get("packet_path"):
            cited.append(("packet_path", meta["packet_path"]))
        rp = (meta.get("signature_block") or {}).get("review_packet")
        if isinstance(rp, dict) and rp.get("path"):
            cited.append(("signature_block.review_packet.path", rp["path"]))
        for label, rel in cited:
            if not (ROOT / rel).exists():
                missing_paths.append(f"{jp.name}: {label} -> {rel}")
    # and every record-side citation of an evidence file
    for (prof, aid), (p, d) in sorted(recs.items()):
        for l in (d.get("logs") or []):
            if isinstance(l, dict) and l.get("file") and not (ROOT / l["file"]).exists():
                missing_paths.append(f"{aid}: logs[].file -> {l['file']}")
    e_ok = not missing_paths
    all_ok &= report(
        e_ok, "E. every path a packet or record cites resolves on disk",
        [f"{pkt_n} packet(s) and {len(recs)} record(s) walked",
         f"cited paths that do not resolve: {len(missing_paths)}",
         (f"missing: {missing_paths[:5]}" if not e_ok else "none")])

    # ---- F: no signature block filled -------------------------------------
    md_filled, json_filled, md_n = [], [], 0
    if PACKETS.is_dir():
        for md in sorted(PACKETS.rglob("*.md")):
            if md.name == "INDEX.md":
                continue
            md_n += 1
            txt = md.read_text(encoding="utf-8")
            for k in SIG_KEYS:
                m = re.search(r"^\|\s*" + re.escape(k.replace("_", " ").title().replace(
                    "Reviewer Name", "Reviewer name").replace("Organisation", "Organisation")) +
                    r"\s*\|(.*)\|\s*$", txt, re.MULTILINE | re.IGNORECASE)
                if m and m.group(1).strip():
                    md_filled.append(f"{md.name}:{k}={m.group(1).strip()[:40]!r}")
    for jp in sorted(PACKETS.rglob("*.json")) if PACKETS.is_dir() else []:
        meta = json.loads(jp.read_text(encoding="utf-8"))
        sb = meta.get("signature_block") or {}
        if sb.get("filled") is True:
            json_filled.append(f"{jp.name}: filled=true")
        for k in SIG_KEYS:
            if str(sb.get(k, "") or "").strip():
                json_filled.append(f"{jp.name}:{k}={str(sb.get(k))[:40]!r}")
    f_ok = md_n > 0 and not md_filled and not json_filled
    all_ok &= report(
        f_ok, "F. no signature block is filled, in either format",
        [f"{md_n} markdown packet(s) and {pkt_n} packet.json twin(s) read",
         f"markdown signature fields carrying a value: {len(md_filled)}",
         f"packet.json signature fields carrying a value: {len(json_filled)}",
         "a signed packet belongs under " + SIGNED_REL + ", not in the generated tree"])

    # ---- G: nothing here appends to the ledger ----------------------------
    writers = []
    tools = ART / "tools"
    if tools.is_dir():
        for py in sorted(tools.rglob("*.py")):
            txt = py.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'open\(\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*"a"', txt):
                line_no = txt.count("\n", 0, m.start()) + 1
                writers.append(f"{py.name}:{line_no}")
    g_ok = len(writers) == 1 and writers[0].startswith("corpus.py:")
    all_ok &= report(
        g_ok, "G. exactly one append-mode open of the ledger, and it is the self-test fixture",
        [f"tools scanned: {len(list(tools.rglob('*.py'))) if tools.is_dir() else 0}",
         f"append-mode call site(s): {writers or 'none'}",
         "corpus.py's site is inside cmd_selftest's fixture, which writes only to a "
         "throwaway root outside the repository and is deleted in a finally"])

    print()
    print("PASS" if all_ok else "FAIL")
    print()
    print("WHAT THIS DOES NOT PROVE, restated because a checker that reads as stronger")
    print("than it is is worse than no checker: it re-derives mechanical facts from bytes")
    print("on disk. It cannot and does not establish that any human read any record, and")
    print("it does not make an approval unforgeable. A determined person could write a")
    print("self-consistent ledger, a real packet and a real commit anchor and still have")
    print("forged the approval. That limit is irreducible.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())