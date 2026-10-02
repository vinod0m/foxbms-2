#!/usr/bin/env python3
"""SIL diagnostics-collecting compiler wrapper.

WHY THIS EXISTS
---------------
Ceedling compiles a test's translation units in an order that is NOT stable
across runs, and it aborts the build at the FIRST failing translation unit.
The set of compiler diagnostics that therefore reaches the log is a function
of that unstable order, not of the sources. Measured on test_os_freertos.c:
22/24 clean runs surface the Mockqueue.c errors, 2/24 surface the test-file
error instead. Any classifier that reads the surfaced set -- and every
classifier that reads `first_error` in particular -- is therefore
nondeterministic, and any before/after comparison built on it is unreliable.

This wrapper removes the variability at the source instead of filtering it
downstream. Installed as the project's `:test_compiler:`, it:

  1. runs the real compiler with the EXACT argv it was given,
  2. appends one structured JSON record per invocation to
     $SIL_DIAG_DIR/<slug>.jsonl  (source, rc, every diagnostic),
  3. when SIL_DIAG_COLLECT=1 and the compile FAILED, returns 0 anyway so that
     Ceedling carries on and compiles every remaining translation unit.

The consequence is that the recorded diagnostic set is the union over ALL
translation units of the test, so it no longer depends on the order in which
they were compiled. run_sil_suite.py reads the .jsonl, and if any translation
unit failed it reports a build_failure classified from the complete set.

It also does NOT let a build failure become a vacuous pass. When
SIL_DIAG_COLLECT=1 and a compile failed, no object file is written, so the
link step fails too and Ceedling produces no OVERALL TEST SUMMARY. The runner
treats a missing summary as a build failure, never as a pass.

TRANSPARENCY
------------
With SIL_DIAG_COLLECT unset (the default, and how `./run.sh` behaves when a
human is driving), this wrapper is a pure pass-through: same argv, same
stdout, same stderr, same exit code.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

DIAG = re.compile(
    r"^(?P<file>[^\n:]+\.(?:c|h|m)):"
    r"(?P<line>\d+):(?P<col>\d+): "
    r"(?P<sev>fatal error|error|warning|note): (?P<msg>.*)$",
    re.M,
)
FLAG = re.compile(r"\[((?:-W[a-z0-9-]+)(?:\s*,\s*-W[a-z0-9-]+)*)\]")


def _flags(msg: str) -> str:
    m = FLAG.search(msg)
    if not m:
        return ""
    return ",".join(
        g for g in (x.strip() for x in m.group(1).split(",")) if g != "-Werror"
    )

REAL_CC = os.environ.get("SIL_REAL_CC") or shutil.which("gcc") or "gcc"


def main() -> int:
    argv = sys.argv[1:]

    src = None
    obj = None
    for i, a in enumerate(argv):
        if a == "-o" and i + 1 < len(argv):
            obj = argv[i + 1]
        elif a.endswith(".c"):
            src = a

    collect = os.environ.get("SIL_DIAG_COLLECT") == "1"
    diag_dir = os.environ.get("SIL_DIAG_DIR")
    slug = os.environ.get("SIL_DIAG_SLUG", "run")

    proc = subprocess.run(
        [REAL_CC, *argv],
        capture_output=True,
        text=True,
        check=False,
    )
    out = proc.stdout + proc.stderr
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    if collect and diag_dir:
        os.makedirs(diag_dir, exist_ok=True)
        record = {
            "src": src,
            "obj": obj,
            "rc": proc.returncode,
            "argv": argv,
            # Kept so the record is self-describing: a compiler-level failure
            # ("cannot open dependency file", "no such file or directory")
            # carries no file:line:col and would otherwise be an empty
            # diagnostics list with no explanation.
            "output_tail": out[-1200:],
            "diagnostics": [
                {
                    "file": m.group("file"),
                    "line": int(m.group("line")),
                    "col": int(m.group("col")),
                    "sev": m.group("sev"),
                    "msg": m.group("msg").rstrip(),
                    "flag": _flags(m.group("msg")),
                }
                for m in DIAG.finditer(out)
            ],
        }
        with open(os.path.join(diag_dir, f"{slug}.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    if collect and proc.returncode != 0 and obj:
        # Do not leave a stale object behind: a missing object makes the link
        # fail, which keeps the "no test summary => build failure" invariant.
        try:
            os.remove(obj)
        except OSError:
            pass

    return 0 if (collect and proc.returncode != 0) else proc.returncode


if __name__ == "__main__":
    sys.exit(main())
