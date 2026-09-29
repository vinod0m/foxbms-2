#!/usr/bin/env python3
"""Derive the exact arity of every TI HAL call, from BOTH ends.

The authoritative source for a CMock-generated mock is the *test*, because the
test's `X_Expect(...)` / `X_ExpectAndReturn(...)` macro is expanded by the
generated mock, so a wrong arity is a compile error. The driver call site is the
second opinion. This script reports both, plus every declaration the repository
already makes, so a disagreement is visible rather than silently resolved.

Output: logs/hal-signatures.json
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[6]

# The set of callees that are NOT declared anywhere in the repository. Derived
# mechanically: parse every declaration/definition site, then every call site,
# and keep the calls whose callee has no declaration. (This is the list the
# report quotes.)
# A declaration line, not a call: there must be whitespace before the callee
# name (so `foo (` is a call but `int foo(` / `x *foo(` is a declaration), no
# assignment before the `(`, and the statement must end in `;` or `{`.
DECL_FUNC = re.compile(
    r"^[ \t]*(?:extern[ \t]+|static[ \t]+|inline[ \t]+)*"
    r"(?:const[ \t]+)?[A-Za-z_][A-Za-z0-9_]*[ \t\*]*"
    r"\b([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(",
    re.MULTILINE,
)


def looks_like_declaration(line: str, name: str) -> bool:
    i = line.find(name)
    if i < 0:
        return False
    before = line[:i]
    if "=" in before or "(" in before or "," in before:
        return False
    stripped = before.rstrip()
    if not stripped:
        return False
    if not (stripped[-1].isalnum() or stripped[-1] in "*_>"):
        return False
    rest = line[line.find("(", i) :] if line.find("(", i) >= 0 else ""
    return rest.rstrip().endswith((";", "{", ")"))
DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
TYPEDEF = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*;", re.MULTILINE)
CALL = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\(")

C_KEYWORDS = {
    "if", "for", "while", "switch", "return", "sizeof", "defined", "do", "else",
    "case", "va_start", "va_end", "vsnprintf", "exit", "main", "assert",
    "FAS_ASSERT", "UNITY_TEST_ASSERT", "TEST_ASSERT", "TEST_FAIL_MESSAGE",
    "printf", "fprintf", "snprintf", "sprintf", "puts", "putchar",
}


def split_args(s: str) -> list[str]:
    args, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        args.append(cur.strip())
    return args


def balanced_call(text: str, open_paren: int) -> tuple[str, int] | None:
    depth = 0
    for i in range(open_paren, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1 : i], i
    return None


def main() -> int:
    files = sorted(
        [p for p in REPO.glob("src/**/*") if p.suffix in (".c", ".h")]
        + [p for p in REPO.glob("tests/**/*") if p.suffix in (".c", ".h")]
    )
    declared: set[str] = set()
    for p in files:
        t = p.read_text(encoding="utf-8", errors="replace")
        for m in DEFINE.finditer(t):
            declared.add(m.group(1))
        for m in TYPEDEF.finditer(t):
            declared.add(m.group(1))
        for line in t.splitlines():
            for m in DECL_FUNC.finditer(line):
                if looks_like_declaration(line, m.group(1)):
                    declared.add(m.group(1))

    driver_calls: dict[str, list[dict]] = defaultdict(list)
    expect_calls: dict[str, list[dict]] = defaultdict(list)

    for p in files:
        t = p.read_text(encoding="utf-8", errors="replace")
        t = re.sub(r"/\*.*?\*/", " ", t, flags=re.DOTALL)
        rel = str(p.relative_to(REPO))
        for m in CALL.finditer(t):
            name = m.group(1)
            if name in C_KEYWORDS or name in declared:
                continue
            got = balanced_call(t, m.end() - 1)
            if got is None:
                continue
            args, _ = got
            lineno = t[: m.start()].count("\n") + 1
            rec = {
                "file": rel,
                "line": lineno,
                "nargs": len(split_args(args)),
                "args": [" ".join(a.split())[:60] for a in split_args(args)],
            }
            if "_Expect" in name or "_ExpectAndReturn" in name or "_Ignore" in name:
                base = re.sub(r"_(ExpectAndReturn|Expect|IgnoreAndReturn|Ignore|ReturnThruPtr_.*|AddCallback|Stub|CallCount|Verify|StubWithCallback)$", "", name)
                expect_calls[base].append(rec)
            else:
                driver_calls[name].append(rec)

    merged: dict[str, dict] = {}
    for name in sorted(set(driver_calls) | set(expect_calls)):
        d = driver_calls.get(name, [])
        e = expect_calls.get(name, [])
        merged[name] = {
            "driver_call_sites": len(d),
            "driver_arities": sorted({r["nargs"] for r in d}),
            "test_expect_arities": sorted({r["nargs"] for r in e}),
            "test_expect_sites": len(e),
            "example_driver_call": d[0] if d else None,
            "example_expect_call": e[0] if e else None,
        }

    out = {
        "distinct_ti_hal_functions": len(merged),
        "functions": merged,
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
