#!/usr/bin/env python3
"""Independent re-derivation of the evidence behind the hardware and interface authoring pass.

Deliberately does NOT import corpus.py. It re-reads the repository through git and
re-derives every claim itself, so that agreement between this script and the corpus
tool is two independent measurements rather than one measurement reported twice.

Commit: 308028fb13d046ba29b98886895c2e17937b1437

Checks, in order:
  1. every path a new record cites exists in that commit
  2. every line number a new record cites is inside the file it is cited against
  3. every symbol a new record attributes to a path occurs in that path
  4. every board version, release archive name and release URL in the hardware
     configuration baseline is byte-identical to hardware/README.md at that commit
  5. the figures the baseline and the applicability record state about hardware/README.md
     and docs/hardware/ are re-derived from those trees
  6. the declaration each interface element transcribes is token-identical to the
     source lines it cites

Exit status is 0 only when every check passes and no mismatch is found.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

COMMIT = "308028fb13d046ba29b98886895c2e17937b1437"
def _find_root(start):
    """Walk up until a .git entry is found. Guessing a fixed number of levels is how this
    script's first run silently resolved its paths against docs/ instead of the repository
    root and therefore matched docs/hardware/ when it meant hardware/."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("repository root not found above " + start)
        d = parent


ROOT = _find_root(os.path.dirname(__file__))
CORPUS = os.path.join(ROOT, "docs/artifacts/corpus/synthetic_reference")

NEW_RECORDS = [
    "hardware/hardware-configuration-baseline.json",
    "hardware/hardware-verification-plan.json",
    "hardware/hardware-detailed-design-gap.json",
    "system/hardware-variant-applicability.json",
    "software/ifs-afe-acquisition.json",
    "software/ifs-soa-monitoring.json",
    "software/ifs-contactor-actuation.json",
    "software/ifs-can-transport.json",
    "software/ifs-database-engine.json",
    "software/ifs-diag-diagnostics.json",
    "software/ifs-os-abstraction.json",
    "software/ifs-serial-bus-drivers.json",
    "software/sir-acquisition-monitoring-interfaces.json",
    "software/sir-actuation-interfaces.json",
    "software/sir-communication-data-interfaces.json",
    "software/sir-platform-service-interfaces.json",
]

_cache = {}
mismatches = []
checks = 0


def blob(path):
    """PRODUCT source at the pinned commit.

    Only product source is read this way. The corpus itself - its registries, its
    governance files and the records under test - was authored against that commit and
    therefore lives in later commits, so a corpus file is read from the working tree by
    wt() below. Reading a corpus file out of the pinned commit returns nothing, which is
    why the two are separated rather than merged.
    """
    if path not in _cache:
        r = subprocess.run(["git", "-C", ROOT, "show", f"{COMMIT}:{path}"],
                           capture_output=True)
        _cache[path] = r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
    return _cache[path]


def wt(path):
    """A corpus file, read from the working tree."""
    key = "WT:" + path
    if key not in _cache:
        try:
            _cache[key] = open(os.path.join(ROOT, path), encoding="utf-8").read()
        except OSError:
            _cache[key] = None
    return _cache[key]


def lines(path):
    b = blob(path)
    return None if b is None else b.splitlines()


def tree(sub):
    r = subprocess.run(["git", "-C", ROOT, "ls-tree", "-r", "--name-only", COMMIT, "--", sub],
                       capture_output=True)
    return r.stdout.decode().splitlines()


def fail(kind, detail):
    mismatches.append((kind, detail))


def walk_strings(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            walk_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_strings(v, out)


def walk_dicts(node, out):
    if isinstance(node, dict):
        out.append(node)
        for v in node.values():
            walk_dicts(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_dicts(v, out)


PATH_RE = re.compile(r"\b((?:src|hardware|docs/hardware|conf|tools)/[A-Za-z0-9_./+-]+?\.(?:c|h|rst|csv|md|txt|drawio|json))\b")
LINEREF_RE = re.compile(r"\bL(\d+)(?:\s*-\s*L?(\d+))?")
IDENT_RE = re.compile(r"\b([A-Z][A-Z0-9_]{4,})\b")


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def check_record(rel, rec):
    global checks
    dicts, strs = [], []
    walk_dicts(rec, dicts)
    walk_strings(rec, strs)

    # 1-3: structured path/line/symbol fields
    for d in dicts:
        for pk, lk in (("declaration_path", "declaration_line"),
                       ("implementation_path", "implementation_line"),
                       ("path", "line")):
            p, ln = d.get(pk), d.get(lk)
            if isinstance(p, str) and isinstance(ln, int):
                checks += 1
                src = lines(p)
                if src is None:
                    fail("path-missing", f"{rel}: {pk}={p} does not exist at {COMMIT}")
                    continue
                if not (1 <= ln <= len(src)):
                    fail("line-out-of-bounds",
                         f"{rel}: {p}:{ln} outside a file of {len(src)} lines")
        p, sym = d.get("declaration_path"), d.get("symbol")
        ln = d.get("declaration_line")
        if isinstance(p, str) and isinstance(sym, str) and isinstance(ln, int):
            checks += 1
            src = lines(p)
            if src is None:
                continue
            window = "\n".join(src[max(0, ln - 1):ln + 8])
            if not re.search(r"\b" + re.escape(sym) + r"\b", window):
                fail("symbol-absent",
                     f"{rel}: symbol {sym} does not occur at or after {p}:{ln}")

    # 1-2: paths and line references embedded in prose
    for s in strs:
        # A corpus path is not a product path and is not expected in the pinned commit.
        # Strip anything under corpus/ or docs/artifacts/ before matching, so that a record
        # naming its own corpus siblings is not reported as citing a missing product file.
        product_text = re.sub(r"(?:corpus/synthetic_reference|docs/artifacts)/[A-Za-z0-9_./-]+",
                              " ", s)
        for m in PATH_RE.finditer(product_text):
            p = m.group(1)
            checks += 1
            src = lines(p)
            if src is None:
                fail("path-missing", f"{rel}: prose cites {p}, absent at {COMMIT}")
                continue
            tail = product_text[m.end():m.end() + 40]
            for lm in LINEREF_RE.finditer(tail):
                a = int(lm.group(1))
                b = int(lm.group(2)) if lm.group(2) else a
                checks += 1
                if not (1 <= a <= b <= len(src)):
                    fail("line-out-of-bounds",
                         f"{rel}: prose cites {p} L{a}{'-L' + str(b) if lm.group(2) else ''} "
                         f"against a file of {len(src)} lines")
        # Identifiers asserted in a string that also cites one or more product paths. The
        # claim in such a sentence is distributed across the paths it names - a single
        # evidence string often cites a wrapper and a task configuration together - so the
        # identifier is required to occur in at least one of them, not in the first one.
        cited = [m.group(1) for m in PATH_RE.finditer(product_text)]
        cited = [p for p in cited if lines(p) is not None]
        if cited:
            union = "\n".join("\n".join(lines(p)) for p in cited)
            for im in IDENT_RE.finditer(s):
                tok = im.group(1)
                # An L-prefixed run of digits is a line reference, not an identifier.
                if re.fullmatch(r"L[0-9]+", tok):
                    continue
                if tok in ("FALSE", "TRUE", "NULL", "UINT8", "UINT16", "UINT32", "STD_NOT_OK",
                           "STD_OK", "FAILED", "UNRESOLVED", "TODO", "PRM", "COD", "SRC",
                           "IFS", "SIR", "TSR", "SYR", "FSR", "DSN", "IMP", "HWE", "SWE",
                           "SYS", "MAN", "VER", "SAF", "ASM", "SCN", "BAS", "VAR", "FB2"):
                    continue
                checks += 1
                if not re.search(r"\b" + re.escape(tok) + r"\b", union):
                    fail("symbol-absent",
                         f"{rel}: {tok} is asserted alongside {cited} but occurs in none of them")

    # 6: transcribed declarations are token-identical to the source
    for d in dicts:
        if "declaration" in d and "declaration_path" in d and "declaration_line" in d:
            p, ln, decl = d["declaration_path"], d["declaration_line"], d["declaration"]
            src = lines(p)
            if src is None or not isinstance(ln, int):
                continue
            checks += 1
            span = norm(decl).count(";") and 1 or 1
            # reconstruct the source span: the declaration text itself gives the token count
            ntok = len(re.findall(r"[A-Za-z_0-9]+", decl))
            joined = ""
            for k in range(ln - 1, min(len(src), ln + 8)):
                joined += src[k] + " "
                got = re.sub(r"\s+", "", re.sub(r"\s*\{\s*$", "", joined))
                want = re.sub(r"\s+", "", decl)
                if got == want:
                    break
                if got.startswith(want) and got[len(want):].strip("") == "":
                    break
            else:
                fail("declaration-mismatch",
                     f"{rel}: {p}:{ln} does not carry the declaration {decl!r} "
                     f"(source: {norm(joined)!r})")
            _ = span, ntok


def check_hardware_baseline(rec):
    global checks
    readme = blob("hardware/README.md")
    if readme is None:
        fail("path-missing", "hardware/README.md absent at the pinned commit")
        return
    rows = []
    for l in readme.splitlines():
        if l.startswith("|") and "Version" not in l and "---" not in l:
            c = [x.strip() for x in l.strip("|").split("|")]
            m = re.search(r"\((https://[^)]+)\)", c[2])
            rows.append((c[0], c[1], m.group(1).rsplit("/", 1)[1], m.group(1)))
    inv = {b["item_label"]: b for b in rec["board_inventory"]}

    checks += 1
    if rec["inventory_counts"]["release_rows"] != len(rows):
        fail("count", f"release_rows {rec['inventory_counts']['release_rows']} != {len(rows)} in the README")
    checks += 1
    if rec["inventory_counts"]["distinct_board_designations"] != len({r[0] for r in rows}):
        fail("count", "distinct_board_designations disagrees with the README Item strings")

    checks += 1
    if sorted(inv) != sorted({r[0] for r in rows}):
        fail("inventory", f"baseline items {sorted(inv)} != README items {sorted({r[0] for r in rows})}")

    for item, v, art, url in rows:
        b = inv.get(item)
        if b is None:
            continue
        got = [(x["version"], x["release_artifact"], x["release_url"]) for x in b["released_versions"]]
        want = [(x[1], x[2], x[3]) for x in rows if x[0] == item]
        checks += 1
        if got != want:
            fail("version", f"{item}: baseline says {got}, README says {want}")
        # the version string must appear verbatim in the README
        for x in b["released_versions"]:
            checks += 1
            if x["version"] not in readme:
                fail("version", f"{item}: version {x['version']} does not appear in hardware/README.md")

    # 5: figures about docs/hardware/
    files = tree("docs/hardware")
    di = rec["documentation_inventory"]
    for key, pred in (("tracked_files", lambda p: True),
                      ("csv_pinout_and_rating_tables", lambda p: p.endswith(".csv")),
                      ("drawio_block_diagrams", lambda p: p.endswith(".drawio"))):
        checks += 1
        actual = len([p for p in files if pred(p)])
        if di[key] != actual:
            fail("count", f"documentation_inventory.{key} says {di[key]}, tree has {actual}")
    checks += 1
    if di["altium_source_files_present"]:
        fail("availability", "the baseline claims an Altium source file is present in docs/hardware/")
    for ext in di["design_file_extensions_sought"] if isinstance(di, dict) and "design_file_extensions_sought" in di else []:
        pass



def check_altium_absence():
    global checks
    checks += 1
    t = tree("hardware")
    if t != ["hardware/README.md"]:
        fail("availability", f"hardware/ tree at the pinned commit is {t}, not [hardware/README.md]")
    for ext in ("*.SchDoc", "*.PcbDoc", "*.PrjPcb"):
        r = subprocess.run(["git", "-C", ROOT, "log", "--all", "--name-only",
                            "--diff-filter=A", "--", ext], capture_output=True)
        checks += 1
        if r.stdout.strip():
            fail("availability", f"{ext} appears in some commit, contradicting the recorded absence")
    checks += 1
    bad = [p for p in tree("docs/hardware") if p.endswith((".SchDoc", ".PcbDoc", ".PrjPcb"))]
    if bad:
        fail("availability", f"Altium files present under docs/hardware: {bad}")


def check_applicability(rec):
    """Re-derive the variant-registry designations and the released-item mapping."""
    global checks
    vm = json.loads(wt("docs/artifacts/sources/variant-matrix.json"))
    found = set()
    non_board = set()
    for v in vm["variants"]:
        for k in ("master_board", "slave_board", "interface"):
            val = v.get(k)
            if not val:
                continue
            hit = re.findall(r"HW-[A-Z0-9-]+", str(val))
            if hit:
                found.update(hit)
            else:
                non_board.add(str(val))
    r = rec["reconciliation"]
    checks += 1
    if sorted(found) != sorted(r["board_designations_in_the_variant_registry"]):
        fail("designation", f"registry names {sorted(found)}, record says "
                            f"{sorted(r['board_designations_in_the_variant_registry'])}")
    checks += 1
    if sorted(non_board) != sorted(r["registry_field_values_that_are_not_board_designations"]):
        fail("designation", "non-designation registry values disagree")
    unmatched = [x["designation"] for x in r["designations_with_no_released_version"]]
    checks += 1
    if sorted(unmatched) != sorted(set(found) - set(r["designations_with_a_released_version"])):
        fail("designation", f"unmatched designations {unmatched} disagree with the set difference")
    checks += 1
    if r["designation_count_with_a_released_version"] + r["designation_count_with_no_released_version"] != len(found):
        fail("count", "designation counts do not sum to the number of designations the registry names")
    for x in r["designations_with_no_released_version"]:
        checks += 1
        if x["designation"] not in found:
            fail("designation", f"{x['designation']} is not named by the registry")
        checks += 1
        v = [y for y in vm["variants"] if y["id"] == x["named_by_variant"]]
        if not v or v[0].get("notes") != x["variant_note"]:
            fail("quote", f"variant note for {x['named_by_variant']} does not match the registry")


def main():
    print(f"independent verification against {COMMIT}")
    print(f"records under test: {len(NEW_RECORDS)}")
    recs = {}
    for rel in NEW_RECORDS:
        p = os.path.join(CORPUS, rel)
        if not os.path.exists(p):
            fail("record-missing", rel)
            continue
        recs[rel] = json.load(open(p))
        check_record(rel, recs[rel])
    if "hardware/hardware-configuration-baseline.json" in recs:
        check_hardware_baseline(recs["hardware/hardware-configuration-baseline.json"])
    check_altium_absence()
    if "system/hardware-variant-applicability.json" in recs:
        check_applicability(recs["system/hardware-variant-applicability.json"])

    print(f"assertions evaluated: {checks}")
    if mismatches:
        print(f"MISMATCHES: {len(mismatches)}")
        seen = set()
        for kind, detail in mismatches:
            if kind in seen:
                continue
            seen.add(kind)
            print(f"  [{kind}] {detail}")
        print("  --- every mismatch, not one per kind ---")
        for kind, detail in mismatches:
            print(f"  [{kind}] {detail}")
        print("RESULT: FAIL")
        return 1
    print("MISMATCHES: 0")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
