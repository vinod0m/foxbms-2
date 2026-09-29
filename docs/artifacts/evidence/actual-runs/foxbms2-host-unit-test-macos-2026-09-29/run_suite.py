#!/usr/bin/env python3
"""Run the foxBMS 2 host unit tests one at a time and record real evidence.

Each test is executed in its own Ceedling invocation so that every test gets
an unambiguous pass/fail verdict and its own log file. Nothing is inferred:
the pass/fail counts are parsed out of Ceedling's own OVERALL TEST SUMMARY
block and cross-checked against the process exit code.

Outputs, relative to the verification-env workspace:
    logs/tests/<slug>.log   raw stdout+stderr of the Ceedling invocation
    logs/results.json       machine-readable per-test record

Usage:
    run_suite.py                 # all tests with no HALCoGen dependency
    run_suite.py --all           # every discovered test, including blocked ones
    run_suite.py --only test_x.c  # substring filter
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
LOGS = HERE / "logs"
TEST_LOGS = LOGS / "tests"

SUMMARY_RE = re.compile(
    r"TESTED:\s*(\d+)\s*\n\s*PASSED:\s*(\d+)\s*\n\s*FAILED:\s*(\d+)\s*\n\s*IGNORED:\s*(\d+)",
    re.MULTILINE,
)
CEEDLING_EXC_RE = re.compile(r"🧨 EXCEPTION: (.*)", re.MULTILINE)
FATAL_RE = re.compile(r"fatal error: (.*)", re.MULTILINE)
ERR_RE = re.compile(r"^\s*\d+ \| ", re.MULTILINE)


def slug(test: str) -> str:
    return test.replace("/", "__").removesuffix(".c")


def tool_versions() -> dict[str, str]:
    def run(cmd: list[str]) -> str:
        try:
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=180, check=False
            )
            return (out.stdout + out.stderr).strip()
        except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
            return f"<error: {exc}>"

    env = dict(os.environ)
    env["GEM_HOME"] = str(HERE / ".work-gems")
    env["GEM_PATH"] = env["GEM_HOME"]
    env["PATH"] = f"{HERE}/bin:{env['GEM_HOME']}/bin:{env['PATH']}"
    return {
        "uname": run(["uname", "-a"]),
        "ruby": run(["ruby", "--version"]),
        "gcc": run(["gcc", "--version"]).splitlines()[0] if run(["gcc", "--version"]) else "",
        "clang": (run(["clang", "--version"]).splitlines() or [""])[0],
        "ceedling": run(["ceedling", "version"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--only", default=None)
    parser.add_argument("--out", default="results.json")
    parser.add_argument("--relax", action="store_true")
    parser.add_argument(
        "--log-subdir",
        default=None,
        help="subdirectory of logs/ for the per-test logs; defaults to the\n"
        "run flavour, so a strict run and a relaxed run never share logs",
    )
    args = parser.parse_args()

    closure = json.loads((LOGS / "hcg-closure.json").read_text(encoding="utf-8"))
    rows = closure["tests"]
    if not args.all:
        rows = [r for r in rows if r["hcg_count"] == 0]
    if args.only:
        rows = [r for r in rows if args.only in r["test"]]

    global TEST_LOGS
    if args.log_subdir is None:
        args.log_subdir = "relaxed" if args.relax else "strict"
    TEST_LOGS = LOGS / args.log_subdir
    TEST_LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["GEM_HOME"] = str(HERE / ".work-gems")
    env["GEM_PATH"] = env["GEM_HOME"]
    env["PATH"] = f"{HERE}/bin:{env['GEM_HOME']}/bin:{env['PATH']}"
    if args.relax:
        env["RELAX_CLANG_DIAGNOSTICS"] = "1"

    results = []
    for index, row in enumerate(rows, start=1):
        test = row["test"]
        rel = test.removeprefix("tests/unit/")
        is_bootloader = "/bootloader/" in test
        variant = "bootloader_host_unit_test" if is_bootloader else "app_host_unit_test"
        cwd = HERE / "build" / variant
        if not (cwd / "project.yml").is_file():
            subprocess.run(
                [
                    str(HERE / "provision.sh"),
                    "bootloader" if is_bootloader else "app",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        target = f"test:../../{test}"
        started = time.time()
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        proc = subprocess.run(
            [str(HERE / "run.sh"), target],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )
        output = proc.stdout + proc.stderr
        (TEST_LOGS / f"{slug(test)}.log").write_text(output, encoding="utf-8")
        summary = SUMMARY_RE.search(output)
        exception = CEEDLING_EXC_RE.search(output)
        record = {
            "test": test,
            "ceedling_target": target,
            "working_directory": str(cwd),
            "halcogen_headers_required": row["hcg_headers"],
            "start_time": stamp,
            "duration_s": round(time.time() - started, 2),
            "exit_code": proc.returncode,
            "outcome": None,
            "tested": int(summary.group(1)) if summary else None,
            "passed": int(summary.group(2)) if summary else None,
            "failed": int(summary.group(3)) if summary else None,
            "ignored": int(summary.group(4)) if summary else None,
            "first_error": None,
            "log": f"logs/tests/{slug(test)}.log",
        }
        if summary and proc.returncode == 0 and int(summary.group(3)) == 0:
            record["outcome"] = "pass"
        elif summary:
            record["outcome"] = "fail"
            record["first_error"] = _first_failure(output)
        else:
            record["outcome"] = "build_failure"
            if exception:
                record["first_error"] = exception.group(1)[:500]
            else:
                fatals = FATAL_RE.findall(output)
                record["first_error"] = (
                    f"fatal error: {fatals[0]}" if fatals else output[-500:]
                )
        # Ceedling accumulates objects, mocks and dependency files per test.
        # With 136 tests that is tens of megabytes of transient data that no
        # evidence depends on, so reclaim it as we go.
        for scratch in ("test/out", "test/dependencies", "test/preprocess", "mocks"):
            shutil.rmtree(cwd / scratch, ignore_errors=True)
        results.append(record)
        state = record["outcome"].upper()
        counts = (
            f"tested={record['tested']} pass={record['passed']} fail={record['failed']}"
            if record["tested"] is not None
            else "no test summary (build failure)"
        )
        print(f"[{index:>3}/{len(rows)}] {state:<14} {counts:<40} {test}", flush=True)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": tool_versions(),
        "selection": "all" if args.all else "no_halcogen_dependency",
        "total": len(results),
        "passed_tests": sum(1 for r in results if r["outcome"] == "pass"),
        "failed_tests": sum(1 for r in results if r["outcome"] == "fail"),
        "build_failures": sum(
            1 for r in results if r["outcome"] == "build_failure"
        ),
        "total_assertions_tested": sum(r["tested"] or 0 for r in results),
        "total_assertions_passed": sum(r["passed"] or 0 for r in results),
        "total_assertions_failed": sum(r["failed"] or 0 for r in results),
        "results": results,
    }
    payload["relaxed_clang_diagnostics"] = bool(args.relax)
    (LOGS / args.out).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print()
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}, indent=2))
    return 0


def _first_failure(output: str) -> str | None:
    for line in output.splitlines():
        if ":FAIL:" in line or "Failure" in line and "Unity" in output:
            return line.strip()[:500]
    for line in output.splitlines():
        if "FAIL" in line:
            return line.strip()[:500]
    return None


if __name__ == "__main__":
    sys.exit(main())
