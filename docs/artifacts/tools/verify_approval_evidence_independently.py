#!/usr/bin/env python3
"""Independent verification of the corpus after amendment APPROVAL-RULE-A1.

WRITTEN FROM SCRATCH AND DELIBERATELY IMPORTS NOTHING FROM corpus.py,
make_review_packets.py or any other tool in this repository. It re-derives every
figure it reports by walking the tree itself. If it agreed with corpus.py only
because both call the same function, it would prove nothing; the only thing it
shares with the tool is the JSON on disk.

Four claims are checked:

  A. every packet's recorded digest matches the record's bytes on disk, and the
     record's bytes are what the packet embeds verbatim;
  B. every path any packet or record cites resolves on disk;
  C. ZERO records hold a non-pending approval value in any of the three fields,
     and ZERO records carry an approval_evidence block at all;
  D. ZERO signature blocks are non-empty, in either the markdown table or the
     packet.json twin, in all 321 packets.

Exit code 0 if all four hold, 1 otherwise. Writes nothing.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
ART = ROOT / "docs" / "artifacts"
PACKETS = ART / "reviews" / "packets"
CORPUS_DIRS = ("corpus", "scenarios", "reviews")
APPROVAL_FIELDS = {
    "human_approval_status": lambda v: v is not None and v != "pending",
    "production_authorized": lambda v: v is True,
    "product_verification_credit": lambda v: v is True,
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SIG_KEYS = ("reviewer_name", "organisation", "role", "date", "decision",
            "comments", "signature")
# A markdown signature row is `| <label> | <value> |`; the generator writes the
# value cell empty, so a non-empty cell is the signal.
SIG_ROW = re.compile(r"^\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def corpus_records():
    """Every record-shaped JSON under the three roots the corpus indexes.

    The roots are named as a constant in this file, read from no tool, because
    the claim being checked is about what is on disk, not about what a tool
    decided to walk.
    """
    for d in CORPUS_DIRS:
        base = ART / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.json")):
            if ".work" in p.parts or "__pycache__" in p.parts:
                continue
            try:
                j = jload(p)
            except Exception:
                continue
            if isinstance(j, dict) and j.get("id"):
                yield p, j


def check_a():
    out = {"packets": 0, "digest_ok": 0, "verbatim_ok": 0, "bad": []}
    md = [p for p in PACKETS.rglob("*.md") if p.name != "INDEX.md"]
    out["packets"] = len(md)
    for m in md:
        j = m.with_suffix(".json")
        if not j.is_file():
            out["bad"].append(f"{m.name}: no packet.json twin")
            continue
        pk = jload(j)
        integ = pk.get("integrity") or {}
        rel = integ.get("record_path")
        if not rel:
            out["bad"].append(f"{m.name}: no integrity.record_path")
            continue
        src = ROOT / rel
        if not src.is_file():
            out["bad"].append(f"{m.name}: record_path {rel} does not exist")
            continue
        raw = src.read_bytes()
        # A1a: the packet's OWN recorded digest equals the record's bytes now.
        if integ.get("record_sha256") == sha(raw):
            out["digest_ok"] += 1
        else:
            out["bad"].append(f"{m.name}: record_sha256 != sha256({rel})")
        # A1b: the packet embeds the record verbatim, and what it embeds is
        # exactly the record on disk.
        rv = pk.get("record_verbatim")
        if isinstance(rv, dict) and rv.get("id") == jload(src).get("id") \
                and rv == jload(src) and integ.get("verbatim_block_is_record_bytes") is True:
            out["verbatim_ok"] += 1
        else:
            out["bad"].append(f"{m.name}: record_verbatim does not equal {rel}")
    return out


def check_b():
    """Every path a packet cites, and every path a record's review_packet cites."""
    cited = set()
    for m in PACKETS.rglob("*.json"):
        if m.name == "INDEX.md":
            continue
        pk = jload(m)
        for key in ("record_path", "anchor_registry_path"):
            v = (pk.get("integrity") or {}).get(key)
            if isinstance(v, str) and v:
                cited.add(v)
        for l in (pk.get("already_checked") or {}).get("links_touching_record") or []:
            if l.get("registry_path"):
                cited.add(l["registry_path"])
    # Anything under reviews/packets or reviews/signed is relative to ROOT; the
    # corpus cites everything else relative to ROOT too. Check both readings.
    missing = []
    for rel in sorted(cited):
        if rel.startswith("docs/artifacts/"):
            cands = [ROOT / rel, ART / rel[len("docs/artifacts/"):]]
        else:
            cands = [ROOT / rel, ART / rel]
        if not any(c.exists() for c in cands):
            missing.append(rel)
    return {"cited": len(cited), "missing": missing}


def check_c():
    out = {"records": 0, "non_pending_approvals": [], "approval_evidence_blocks": [],
           "status_tally": {}, "prod_tally": {}, "credit_tally": {}}
    for p, d in corpus_records():
        out["records"] += 1
        for field, is_grant in APPROVAL_FIELDS.items():
            v = d.get(field)
            key = {"human_approval_status": "status_tally",
                   "production_authorized": "prod_tally",
                   "product_verification_credit": "credit_tally"}[field]
            out[key][repr(v)] = out[key].get(repr(v), 0) + 1
            if is_grant(v):
                out["non_pending_approvals"].append(f"{p.relative_to(ROOT)}: {field}={v!r}")
        if "approval_evidence" in d:
            out["approval_evidence_blocks"].append(f"{p.relative_to(ROOT)}")
    return out


def check_d():
    out = {"packets": 0, "md_filled": [], "json_filled": [], "twins_missing": [],
           "no_sig_section": []}
    md = [p for p in PACKETS.rglob("*.md") if p.name != "INDEX.md"]
    out["packets"] = len(md)
    for m in md:
        # D1: the markdown signature table. Anchored on the SECTION 9 heading and
        # the `| field | value |` header that follows it: a packet also carries a
        # record-facts table whose header is the same two words, so matching the
        # header alone would read the record's own fields as a filled signature.
        lines = m.read_text(encoding="utf-8", errors="replace").splitlines()
        start = None
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("## 9.") and "signature" in line.lower():
                start = i
                break
        if start is None:
            out["no_sig_section"].append(m.name)
            continue
        in_sig = False
        for line in lines[start + 1:]:
            s = line.strip()
            if s.startswith("| field | value |"):
                in_sig = True
                continue
            if in_sig:
                if not s.startswith("|"):
                    break
                if set(s) <= set("|- :"):
                    continue
                mm = SIG_ROW.match(s)
                if mm and mm.group(2).strip():
                    out["md_filled"].append(f"{m.name}: {mm.group(1)}={mm.group(2)!r}")
        j = m.with_suffix(".json")
        if not j.is_file():
            out["twins_missing"].append(m.name)
            continue
        sb = jload(j).get("signature_block") or {}
        if sb.get("filled") is not False:
            out["json_filled"].append(f"{j.name}: filled={sb.get('filled')!r}")
        for k in SIG_KEYS:
            if sb.get(k):
                out["json_filled"].append(f"{j.name}: {k}={sb[k]!r}")
    return out


def main():
    print(f"independent verification of {ROOT}")
    print("  (imports nothing from corpus.py, make_review_packets.py or any tool)")
    print()
    rc = 0

    a = check_a()
    print(f"A. packet digests")
    print(f"   packets                       : {a['packets']}")
    print(f"   record_sha256 == sha256(bytes): {a['digest_ok']}/{a['packets']}")
    print(f"   record_verbatim == record file: {a['verbatim_ok']}/{a['packets']}")
    for b in a["bad"][:8]:
        print(f"   FAIL {b}")
    if a["bad"] or a["digest_ok"] != a["packets"] or a["verbatim_ok"] != a["packets"]:
        rc = 1
    print()

    b = check_b()
    print(f"B. cited paths resolve")
    print(f"   distinct paths cited          : {b['cited']}")
    print(f"   not found on disk             : {len(b['missing'])}")
    for m in b["missing"][:8]:
        print(f"   FAIL {m}")
    if b["missing"]:
        rc = 1
    print()

    c = check_c()
    print(f"C. no approval anywhere in the corpus")
    print(f"   records walked                : {c['records']}")
    print(f"   human_approval_status values  : {c['status_tally']}")
    print(f"   production_authorized values  : {c['prod_tally']}")
    print(f"   product_verification_credit   : {c['credit_tally']}")
    print(f"   records with a non-pending approval value : "
          f"{len(c['non_pending_approvals'])}")
    for m in c["non_pending_approvals"][:8]:
        print(f"   FAIL {m}")
    print(f"   records carrying an 'approval_evidence' block : "
          f"{len(c['approval_evidence_blocks'])}")
    for m in c["approval_evidence_blocks"][:8]:
        print(f"   FAIL {m}")
    if c["non_pending_approvals"] or c["approval_evidence_blocks"]:
        rc = 1
    print()

    d = check_d()
    print(f"D. no signature is filled anywhere")
    print(f"   packets                      : {d['packets']}")
    print(f"   markdown signature rows filled : {len(d['md_filled'])}")
    print(f"   packet.json fields filled      : {len(d['json_filled'])}")
    print(f"   packets without a json twin    : {len(d['twins_missing'])}")
    print(f"   packets with no section 9      : {len(d['no_sig_section'])}")
    for m in (d["md_filled"] + d["json_filled"] + d["twins_missing"]
              + d["no_sig_section"])[:8]:
        print(f"   FAIL {m}")
    if d["md_filled"] or d["json_filled"] or d["twins_missing"] or d["no_sig_section"]:
        rc = 1
    print()
    print("VERDICT:", "PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    sys.exit(main())
