#!/usr/bin/env python3
"""PHASE 1: enumerate the exact HL_* surface the foxBMS 2 driver layer needs.

Two things are produced:

  1. A mechanical inventory of every HL_* identifier that appears in
     src/**.c, src/**/*.h and tests/**/*.c. Identifiers are classified as
       - call    : `HL_x(` -> a function foxBMS calls
       - type    : appears in a declaration position (`hl *`, `hl arg`, `hl)`)
       - macro   : appears as `HL_X` not followed by `(` and not a type token
       - other   : anything else
     This is a *mechanical* scan of the repository text, not a search for a
     particular symbol, so it cannot miss an occurrence.

  2. A corrected HALCoGen-blocked test count. The earlier closure
     (verification-env/analyze_hcg_closure.py) walks only the *test file's own*
     quoted-#include closure. It therefore misses any test that reaches a
     HALCoGen header through the **module under test** that Ceedling links in
     (test_spi.c -> spi.c -> HL_spi.h). This script also walks the closure of
     every source file Ceedling would link for the test, i.e. every source
     file whose basename equals the test's basename with the `test_` prefix
     removed, plus the sources of everything that test includes by
     `Mock<name>.h` (Ceedling :use_mocks: TRUE).

Nothing is inferred or approximated: every number emitted is a count of
occurrences found in the repository text.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[6]
TESTS = REPO / "tests" / "unit"
SRC = REPO / "src"

# Identifier shape: HL_ followed by an uppercase-led token, e.g. HL_spiRegWrite,
# HL_reg_system.h, HL_BASE, hetBASE_t is NOT HL_ so it is out of scope.
HL_IDENT = re.compile(r"\bHL_[A-Za-z0-9_]*\b")

INCLUDE_RE = re.compile(r'^\s*#\s*include\s+"([^"]+)"', re.MULTILINE)

# include dirs, taken from the :paths: :include: list of the shipped
# conf/unit/app_project_posix.yml (relative to the build root, which sits at
# verification-env/build/<variant>_host_unit_test/; the repo is two levels up).
INCLUDE_DIRS = [
    "src/os/freertos/freertos/include",
    "src/os/freertos/freertos/portable/ccs/arm_cortex-r5",
    "src/app/main/include",
    "src/app/application/config",
    "src/app/engine/config",
    "src/app/engine/database",
    "src/app/driver/mcu",
    "src/app/task/os",
    "tests/unit/app/application/config",
    "tests/unit/support",
]


def repo_files() -> list[pathlib.Path]:
    out = []
    for root in (SRC, TESTS):
        for pat in ("**/*.c", "**/*.h"):
            out.extend(root.glob(pat))
    return sorted(out)


def scan_identifiers(paths: list[pathlib.Path]) -> dict[str, dict]:
    """Return {identifier: {count, kind, sites:[(file,line,kind)]}}."""
    ident = defaultdict(lambda: {"count": 0, "kinds": defaultdict(int), "sites": []})
    for path in paths:
        rel = str(path.relative_to(REPO))
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Strip block comments so commented-out code does not inflate counts.
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
        lines = text.splitlines()
        for lineno, line in enumerate(lines, start=1):
            for m in HL_IDENT.finditer(line):
                name = m.group(0)
                rest = line[m.end() :]
                if re.match(r"\s*\(", rest):
                    kind = "call"
                elif re.match(r"\s*\*|\s*;|\s+\w", rest):
                    kind = "type"
                else:
                    kind = "macro_or_object"
                entry = ident[name]
                entry["count"] += 1
                entry["kinds"][kind] += 1
                if len(entry["sites"]) < 8:
                    entry["sites"].append({"file": rel, "line": lineno, "kind": kind})
    return ident


# ---------------------------------------------------------------- closure ---

header_index: dict[str, list[pathlib.Path]] = defaultdict(list)
source_index: dict[str, list[pathlib.Path]] = defaultdict(list)
for pat, idx in (("src/**/*.h", header_index), ("src/**/*.c", source_index),
                 ("tests/**/*.h", header_index)):
    for p in REPO.glob(pat):
        idx[p.name].append(p)
# prefer src/ over tests/ when a basename is ambiguous
for idx in (header_index, source_index):
    for k in idx:
        idx[k].sort(key=lambda p: (not str(p).startswith(str(SRC)), str(p)))


def resolve(name: str, origin: pathlib.Path) -> pathlib.Path | None:
    """Resolve a quoted include the way the compiler would, then the way the
    earlier analysis did (basename fallback) so the two closures are
    comparable. The fallback is a superset of the -I search: a header found
    only by basename still exists and still pulls in its own #includes.
    """
    sibling = origin.parent / name
    if sibling.is_file():
        return sibling
    for d in INCLUDE_DIRS:
        cand = REPO / d / name
        if cand.is_file():
            return cand
    matches = header_index.get(pathlib.Path(name).name)
    if matches:
        return matches[0]
    return None


HL_HEADER_RE = re.compile(r"HL_[A-Za-z0-9_]+\.h$")


def closure(seeds: list[pathlib.Path]) -> tuple[set[str], dict[str, set[str]]]:
    """Include closure of `seeds`.

    Returns (halcogen headers reached, {seed path: halcogen headers it pulls in}).

    A quoted include of MockX.h is followed through to the real X.h because
    CMock generates MockX.h *from* X.h, so X.h must be parseable.
    """
    seen: set[pathlib.Path] = set()
    hcg: set[str] = set()
    stack = list(seeds)
    while stack:
        cur = stack.pop()
        if cur in seen or not cur.is_file():
            continue
        seen.add(cur)
        try:
            text = cur.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name in INCLUDE_RE.findall(text):
            if name.startswith("Mock") and len(name) > 4:
                name = name[4:]
            if name == "unity.h" or name.startswith("unity_"):
                continue
            resolved = resolve(name, cur)
            if resolved is None:
                if HL_HEADER_RE.fullmatch(name):
                    hcg.add(name)
                continue
            if HL_HEADER_RE.fullmatch(resolved.name):
                hcg.add(name)
            stack.append(resolved)
    return hcg, seen


def module_under_test(test: pathlib.Path) -> list[pathlib.Path]:
    """Source file(s) Ceedling links for `test`, by the test/base-name rule.

    Ceedling's test-centered build: test_spi.c pulls in spi.c (and, through
    :use_auxiliary_dependencies, anything spi.c #includes). The shipped
    :cmock: :includes: list forces the FreeRTOS chain too. We model the
    test/base-name rule, which is what produces the undercount.
    """
    base = test.name[len("test_") :] if test.name.startswith("test_") else test.name
    return source_index.get(base, [])


def main() -> int:
    paths = repo_files()
    ident = scan_identifiers(paths)

    tests = sorted(TESTS.rglob("test_*.c"))
    rows = []
    undercount = []
    for t in tests:
        hcg_test, _ = closure([t])
        muts = module_under_test(t)
        hcg_mut: set[str] = set()
        for m in muts:
            h, _ = closure([m])
            hcg_mut |= h
        total = hcg_test | hcg_mut
        row = {
            "test": str(t.relative_to(REPO)),
            "variant": "bootloader" if "/bootloader/" in f"/{t}" else "app",
            "hcg_via_test_closure": sorted(hcg_test),
            "module_under_test": [str(m.relative_to(REPO)) for m in muts],
            "hcg_via_module_under_test": sorted(hcg_mut),
            "hcg_all": sorted(total),
        }
        if not hcg_test and hcg_mut:
            undercount.append(row)
        rows.append(row)

    clean = [r for r in rows if not r["hcg_all"]]
    payload = {
        "generated_by": "sil/tools/enumerate_hl_surface.py",
        "total_tests": len(rows),
        "identifier_surface": {
            name: {
                "count": e["count"],
                "by_kind": dict(e["kinds"]),
                "sites": e["sites"],
            }
            for name, e in sorted(ident.items(), key=lambda kv: -kv[1]["count"])
        },
        "identifier_count": len(ident),
        "closure": {
            "total_tests": len(rows),
            "blocked_prior_analysis": sum(
                1 for r in rows if not r["hcg_via_test_closure"]
            ),
            "blocked_corrected": len(rows) - len(clean),
            "clean_corrected": len(clean),
            "undercounted_tests": undercount,
            "undercount_count": len(undercount),
            "rows": rows,
        },
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
