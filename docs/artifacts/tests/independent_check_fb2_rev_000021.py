#!/usr/bin/env python3
"""Independent checker for FB2-REV-000021. Imports NOTHING from corpus.py.

Purpose: the review under test claims to have verified 13 records. This program
re-derives, by its own means, every anchor that claim rests on:

  A. the 13 reviewed_ids entries resolve to a real file in the profile named;
  B. each recorded digest is the sha256 of that file's bytes, computed here;
  C. the review's own file is well-formed JSON and its reviewed_ids set equals
     the set of reviewed_by link targets that name this review (the corpus
     compares these corpus-wide; this compares them for this review);
  D. every SOURCE CITATION the review says verifies, re-derived here directly
     from the pinned git object, with no help from the tool;
  E. the lifecycle_status claim in FB2-REV-FND-000174, re-measured here;
  F. the withdrawn claims in the review are re-checked so that the withdrawal
     is itself verified rather than asserted.

Exit 0 = checker agrees with the corpus. Exit 1 = disagreement, listed.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
PIN = "308028fb13d046ba29b98886895c2e17937b1437"
REVIEW = ROOT / "docs/artifacts/reviews/records/review-test-measure-synthetic.json"
LINKS = ROOT / ("docs/artifacts/traceability/link-registry/"
                "synthetic_reference/links-verification-planning.json")

disagreements = []
checks = 0


def check(ok, label, detail=""):
    global checks
    checks += 1
    if not ok:
        disagreements.append(f"{label}: {detail}")


def sha256_file(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def blob(path):
    r = subprocess.run(["git", "show", f"{PIN}:{path}"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return None
    return r.stdout.splitlines()


review = json.loads(REVIEW.read_text())
check(review.get("id") == "FB2-REV-000021", "review id", review.get("id"))
check(review.get("profile") == "synthetic_reference", "review profile")
check(review.get("human_approval_status") == "pending", "human_approval_status is pending",
      str(review.get("human_approval_status")))
check(review.get("production_authorized") is False, "production_authorized is false")
check(review.get("product_verification_credit") is False, "product_verification_credit is false")
check(review.get("conforms_to", None) in (None, [], 0), "conforms_to stays at zero",
      str(review.get("conforms_to")))

# --- A and B: every reviewed_ids entry, digest re-derived here -----------------
index = {}
for p in sorted((ROOT / "docs/artifacts").glob("**/*.json")):
    if "evaluator-only" in p.parts or ".work" in p.parts:
        continue
    try:
        d = json.loads(p.read_text())
    except Exception:
        continue
    if isinstance(d, dict) and isinstance(d.get("id"), str):
        index[(d.get("profile", "unknown"), d["id"])] = (p, d)

claimed = {}
for e in review["reviewed_ids"]:
    aid = e["artifact_id"]
    claimed[aid] = e
    key = ("synthetic_reference", aid)
    check(key in index, f"{aid} resolves to a record in this profile", "absent from index")
    if key not in index:
        continue
    p, d = index[key]
    check(d.get("artifact_type") == "test_measure", f"{aid} is a test_measure", str(d.get("artifact_type")))
    check(d.get("revision") == e.get("revision"), f"{aid} revision matches",
          f"record {d.get('revision')} vs review {e.get('revision')}")
    # No record carries approval metadata, so the content digest is the file digest.
    # That is an ASSUMPTION this checker tests rather than trusts.
    has_approval_meta = "approval_ledger_ref" in d
    check(not has_approval_meta,
          f"{aid} carries no approval metadata, so file digest == content digest",
          "record carries approval_ledger_ref; raw-byte hashing would not suffice")
    actual = sha256_file(p)
    check(actual == e["digest"],
          f"{aid} digest re-derives from the bytes on disk",
          f"review {e['digest'][:16]}... vs independent {actual[:16]}...")

# --- C: per-review reviewed_ids vs this review's own reviewed_by links ---------
link_targets = set()
for p in sorted((ROOT / "docs/artifacts/traceability/link-registry").glob("*/*.json")):
    d = json.loads(p.read_text())
    for l in d.get("links", []):
        if (l.get("relation_type") == "reviewed_by"
                and l.get("source_id") == "FB2-REV-000021"):
            check(l.get("profile") == "synthetic_reference", "link profile", str(l.get("profile")))
            link_targets.add(l["target_id"])
check(link_targets == set(claimed),
      "this review's reviewed_ids equals the targets its own reviewed_by links name",
      f"only in reviewed_ids {sorted(set(claimed) - link_targets)}; "
      f"only in links {sorted(link_targets - set(claimed))}")

# --- D: the source citations the review says verify, re-derived here -----------
LTC = "src/app/driver/afe/ltc/6813-1/ltc_6813-1.c"
DBC = "src/app/engine/database/database.c"
SOA = "src/app/application/soa/soa.c"
DIAG = "src/app/engine/config/diag_cfg.c"
CFG = "src/app/driver/afe/ltc/6813-1/config/ltc_6813-1_cfg.h"
BMSC = "src/app/application/bms/bms.c"

for path, (lo, hi) in ((LTC, (3838, 3878)), (DBC, (164, 196)), (SOA, (271, 279))):
    b = blob(path)
    check(b is not None, f"{path} readable at the pin")
    if b:
        check(len(b) >= hi, f"{path} is long enough for {lo}-{hi}", f"{len(b)} lines")
        seg = b[lo - 1:hi]
        check(seg and seg[0].strip() != "", f"{path}:{lo} is not blank")

ltc = blob(LTC)
check("LTC_CheckPec" in ltc[3837], "LTC_CheckPec defined at ltc_6813-1.c:3838", ltc[3837].strip()[:60])
check("LTC_CheckPec" in ltc[3837] and ltc[3877].strip() == "}", "LTC_CheckPec closes at 3878", ltc[3877].strip())
seg = "\n".join(ltc[3837:3878])
check("invalidCellVoltage" not in seg,
      "FB2-REV-FND-000175: LTC_CheckPec 3838-3878 contains no invalidCellVoltage",
      "the finding's central claim FAILED")
check(seg.count("PEC_valid") >= 3, "LTC_CheckPec writes errorTable->PEC_valid", str(seg.count("PEC_valid")))
check("invalidCellVoltage" in ltc[640], "line 641 sets invalidCellVoltage", ltc[640].strip()[:70])
# which function owns line 641: nearest preceding definition
def owner_function(lines, target):
    """Name of the function whose definition line precedes `target` most closely.

    A definition line starts at column 0 with extern/static/void, contains '(',
    and does not end in ';' (a declaration or a call).
    """
    for i in range(target - 1, -1, -1):
        s = lines[i]
        if s[:1].isalpha() and "(" in s and not s.rstrip().endswith(";"):
            if re.search(r"(extern|static)?\s*[\w \*]+\s+(\w+)\s*\(", s):
                return i, (re.search(r"(\w+)\s*\([^)]*$", s).group(1)
                           if re.search(r"(\w+)\s*\([^)]*$", s) else s.split("(")[0].split()[-1])
    return None, None


owner_idx, owner_name = owner_function(ltc, 641)
check(owner_name == "LTC_SaveVoltages",
      "FB2-REV-FND-000175: line 641 is inside LTC_SaveVoltages, not LTC_CheckPec",
      f"owner was {owner_name} at line {owner_idx}")
# the real propagation site the review names
check("PEC_valid" in ltc[3113] and "invalidCellVoltage" in ltc[3127] and ltc[3128].strip() == "true;",
      "FB2-REV-FND-000175: real PEC->invalid propagation is at 3114-3130",
      f"3114:{ltc[3113].strip()[:50]} / 3128:{ltc[3127].strip()[:50]} / 3129:{ltc[3128].strip()!r}")
# F: the withdrawn claim - is the record's assertion actually true?
cfg = blob(CFG)
check(any("LTC_DISCARD_PEC (false)" in l for l in cfg),
      "withdrawn claim re-checked: LTC_DISCARD_PEC is (false), so the invalid branch is the one taken")
dbc = blob(DBC)
check("DATA_CopyData" in dbc[163] and dbc[195].strip() == "}",
      "TMS-000021 cites DATA_CopyData 164-196, the definition and its closing brace",
      f"164:{dbc[163].strip()[:50]} 196:{dbc[195].strip()}")
check("previousTimestamp" in dbc[180] and "OS_GetTickCount" in dbc[181],
      "DATA_CopyData copies previousTimestamp and stamps timestamp from OS_GetTickCount at 181-182")
check("DATA_CopyData" in dbc[122] and dbc[126].rstrip().endswith(");"),
      "withdrawn claim re-checked: line 123 is the forward DECLARATION, so there is no duplicate definition",
      f"123:{dbc[122].strip()[:60]} 127:{dbc[126].strip()[:60]}")
soa = blob(SOA)
check("SOA_CheckTemperatures" in soa[147], "SOA_CheckTemperatures defined at soa.c:148", soa[147].strip()[:60])
check("BMS_GetCurrentFlowDirection" in soa[159] and "BMS_DISCHARGING" in soa[159],
      "TMS-000026: line 160 tests current-flow direction == discharging", soa[159].strip()[:70])
check("BMS_CHARGING" in soa[185] or "Charge" in soa[186],
      "TMS-000026: the charge tier set is the alternate branch at 186", soa[185].strip()[:60])
check("invalidStringCurrent" in soa[276],
      "TMS-000028: soa.c:277 gates the whole comparison on invalidStringCurrent", soa[276].strip()[:70])
diag = blob(DIAG)
msl = [l for l in diag if "DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MSL" in l]
rsl = [l for l in diag if "DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_RSL" in l]
mol = [l for l in diag if "DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MOL" in l]
check(msl and "DIAG_FATAL_ERROR" in msl[0] and "DIAG_DELAY_200ms" in msl[0],
      "TMS-000023: max-safety over-voltage entry is FATAL with a delay", msl[0].strip()[:90] if msl else "")
check(rsl and "DIAG_WARNING" in rsl[0] and "DIAG_DELAY_DISCARD" in rsl[0],
      "TMS-000023: recommended-safety entry is WARNING with the delay discarded")
check(mol and "DIAG_INFO" in mol[0] and "DIAG_DELAY_DISCARD" in mol[0],
      "TMS-000023: operating-limit entry is INFO with the delay discarded")
bmsc = blob(BMSC)
check(any("BMS_CheckStateRequest" in l for l in bmsc),
      "TMS-000026: BMS_CheckStateRequest exists at the pin (refused-init mechanism)")

# --- E: the FB2-REV-FND-000174 claim, re-measured here ------------------------
cov = set()
for p in sorted((ROOT / "docs/artifacts/reviews/records").glob("*.json")):
    d = json.loads(p.read_text())
    if d.get("id") == "FB2-REV-000021":
        continue
    for e in d.get("reviewed_ids", []) or []:
        if e.get("artifact_id"):
            cov.add((d.get("profile"), e["artifact_id"]))
for p in sorted((ROOT / "docs/artifacts/traceability/link-registry").glob("*/*.json")):
    d = json.loads(p.read_text())
    for l in d.get("links", []):
        if l.get("source_id") == "FB2-REV-000021":
            continue  # this review's own links did not exist when the figure was taken
        if l.get("relation_type") == "reviewed_by" and l.get("target_id"):
            cov.add((l.get("profile"), l["target_id"]))

silent, noted, covered = 0, 0, 0
# The finding's figure is a PRE-REVIEW measurement, so reproduce that state: drop
# the 13 targets this review newly covers, and drop this review's own record
# (a review record cannot cover itself). Both exclusions are stated here rather
# than assumed, and the post-review figure is reported alongside.
SELF = ("synthetic_reference", "FB2-REV-000021")
mine = {("synthetic_reference", a) for a in claimed}
# cov_pre is the coverage as it stood BEFORE this review existed: no reviewed_ids
# from this review, none of this review's reviewed_by links. cov_post adds the 13
# targets this review covers. This review's OWN record is in neither, because a
# review record cannot cover itself - which is the whole reason the review carries
# a lifecycle_status_note.
cov_post = cov | mine


def survey(covered_set, include_self=False):
    s = n = 0
    for k, (p, d) in index.items():
        if d.get("lifecycle_status") != "reviewed" or k in covered_set:
            continue
        if k == SELF and not include_self:
            continue
        if "lifecycle_status_note" in d:
            n += 1
        else:
            s += 1
    return s, n


pre_silent, pre_noted = survey(cov)
post_silent, post_noted = survey(cov_post)
raw_silent, raw_noted = survey(cov_post, include_self=True)
check(pre_silent == 19, "FB2-REV-FND-000174: 19 records assert 'reviewed' with no covering review and no note",
      f"independent count is {pre_silent}")
check(pre_noted == 3, "FB2-REV-FND-000174: 3 of them carry a lifecycle_status_note",
      f"independent count is {pre_noted}")
check(pre_silent + pre_noted == 22, "FB2-REV-FND-000174: 22 records total assert 'reviewed' with no covering review",
      f"independent count is {pre_silent + pre_noted}")
check((post_silent, post_noted) == (14, 3),
      "after this review, 14 silent + 3 noted = 17 among the other records",
      f"independent post-review count is {post_silent} silent + {post_noted} noted")
check((raw_silent, raw_noted) == (14, 4) and raw_silent + raw_noted == 18,
      "counting this review's own record, the raw population is 14 silent + 4 noted = 18",
      f"independent raw count is {raw_silent} silent + {raw_noted} noted = {raw_silent + raw_noted}")
check(pre_silent - post_silent == 5,
      "the five records the finding names are exactly the ones this review covers",
      f"{pre_silent} -> {post_silent} is a drop of {post_silent - pre_silent}, expected 5")
check(index[SELF][1].get("lifecycle_status_note"),
      "this review's own record carries a lifecycle_status_note, so it is in the mitigated class",
      "a review cannot cover itself, so it is one of the 4 noted instances")

# the five records the finding names must be among the uncovered-at-that-time set
five = ["FB2-VER-TMS-00000%d" % i for i in range(1, 6)]
for aid in five:
    _, d = index[("synthetic_reference", aid)]
    check(d.get("lifecycle_status") == "reviewed", f"{aid} asserts lifecycle_status reviewed")
    check("lifecycle_status_note" not in d, f"{aid} carries no lifecycle_status_note")
    check(len(d.get("limitations", [])) == 0, f"{aid} carries an empty limitations array")
    check(d.get("automated_review_status", {}).get("last_run") == d.get("created_at"),
          f"{aid}: automated_review_status.last_run equals its own created_at",
          f"{d.get('automated_review_status', {}).get('last_run')} vs {d.get('created_at')}")
# and the eight siblings must be the opposite
for i in range(21, 29):
    aid = "FB2-VER-TMS-%06d" % i
    _, d = index[("synthetic_reference", aid)]
    check(d.get("lifecycle_status") == "draft", f"{aid} declares draft", d.get("lifecycle_status"))
    check("lifecycle_status_note" in d, f"{aid} carries a lifecycle_status_note")
    check(len(d.get("limitations", [])) == 4, f"{aid} carries 4 limitations",
          str(len(d.get("limitations", []))))

# --- F: the oracle-gap claim, re-measured here --------------------------------
for aid, missing in (("FB2-VER-TMS-000003", "Flagged implausible"),
                     ("FB2-VER-TMS-000001", "No fault triggered")):
    _, d = index[("synthetic_reference", aid)]
    steptexts = " ".join(s.get("expected", "") for s in d.get("steps", []))
    outtexts = " ".join(f"{e.get('signal')}={e.get('expected_value')}" for e in d.get("expected_outcomes", []))
    check(missing in steptexts, f"{aid}: the step expectation exists in prose", missing)
    check(missing.split()[0].lower() not in outtexts.lower(),
          f"FB2-REV-FND-000176: {aid} encodes no outcome expressing '{missing}'", outtexts[:90])
for aid in ("FB2-VER-TMS-000002", "FB2-VER-TMS-000004"):
    _, d = index[("synthetic_reference", aid)]
    eo = d.get("expected_outcomes", [])
    bad = [e for e in eo if str(e.get("expected_value", "")).startswith("<")
           and e.get("tolerance") == "exact"]
    check(len(bad) == 1, f"FB2-REV-FND-000177: {aid} pairs an inequality with tolerance 'exact'",
          f"{len(bad)} such entries")
_, d2 = index[("synthetic_reference", "FB2-VER-TMS-000005")]
check(len(d2.get("referenced_designs", [])) == 0,
      "the review's claim that FB2-VER-TMS-000005 has an empty referenced_designs array")

# --- report ------------------------------------------------------------------
print(f"independent checks run: {checks}")
print(f"disagreements with the corpus: {len(disagreements)}")
for d in disagreements:
    print("  DISAGREE:", d)
sys.exit(1 if disagreements else 0)
