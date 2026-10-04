#!/usr/bin/env bash
#
# bootstrap.sh - create an interpreter that can actually run this corpus.
#
# WHY THIS SCRIPT EXISTS
# ----------------------
# `docs/artifacts/tools/corpus.py` refuses to run without `jsonschema`, and it
# refuses to run on purpose: a corpus that cannot validate its records must not
# report that it validated them. The consequence is that a machine without the
# dependency has no corpus at all, rather than a degraded one.
#
# The dependency has gone missing three times, and each time the fix differed,
# which is why this script exists rather than a one-line note:
#
#   * once it failed SILENTLY, with `corpus.py` exiting 0 having validated
#     nothing - the worst outcome, because a reader saw success;
#   * once `pip3 install --user jsonschema` refused with
#     `error: externally-managed-environment`, a correct diagnosis with a remedy
#     that does not work on that interpreter;
#   * and the message printed on failure named `pip install jsonschema`, which
#     is not a command that succeeds on a macOS-managed Python and does not
#     mention the requirement file at all.
#
# WHAT IT DOES
# ------------
# 1. Creates a virtualenv OUTSIDE the repository - by default
#    ~/.cache/foxbms-corpus-venv, overridable with FOXBMS_CORPUS_VENV.
# 2. Instsalls docs/artifacts/tools/requirements.txt into it, pinned.
# 3. Prints the exact command to run the suite with that interpreter.
#
# WHAT IT DELIBERATELY DOES NOT DO
# --------------------------------
# * It creates NOTHING inside the repository. Not a `.venv`, not a
#   `.venv/`, not `venv/`, not a `__pycache__`, not a marker file. A virtualenv
#   inside a git working tree is an untracked directory that every `git status`,
#   every archive and every `.gitignore` review has to notice, and this corpus
#   already has a `.gitignore` that has to be correct. Keeping the interpreter
#   outside the tree removes that whole class of problem instead of managing it.
# * It does not modify the system interpreter. Nothing here runs
#   `pip install` against a system or user site-packages, so it cannot be the
#   thing that breaks a working machine.
# * It does not run the suite. Preparing the interpreter and running the corpus
#   are separate acts; this script does the first and tells you the second.
#
# WHY A VIRTUALENV AND NOT `pip install --user`
# ---------------------------------------------
# `--user --break-system-packages` works, and the preflight message in corpus.py
# prints it, because an operator who wants to install into their own user site
# should be able to. But it mutates a shared interpreter that other projects also
# import, and `--break-system-packages` is a flag whose name is a warning. A
# virtualenv containing exactly the two distributions this corpus declares is
# the reproducible option: it cannot be broken by an upgrade elsewhere, and
# removing it is `rm -rf` on one directory in a cache.
#
# USAGE
# -----
#   docs/artifacts/tools/bootstrap.sh                     # default location
#   FOXBMS_CORPUS_VENV=/tmp/myvenv docs/.../bootstrap.sh  # elsewhere
#
# Both print the run command. The default location is reused if it already
# exists and its interpreter still works, so re-running is cheap and safe.

set -euo pipefail

# --- locate the repository from this script, not from $PWD -----------------
# Deriving it from the script's own location means the script works from any
# working directory, which matters because the most common failure is an
# operator running it from somewhere else and getting a different answer.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd -P)"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"

VENV_DIR="${FOXBMS_CORPUS_VENV:-${HOME}/.cache/foxbms-corpus-venv}"

if [ -n "${FOXBMS_CORPUS_VENV:-}" ]; then
    VENV_ORIGIN="FOXBMS_CORPUS_VENV"
else
    VENV_ORIGIN='default (~/.cache/foxbms-corpus-venv)'
fi

say()  { printf '%s\n' "$*"; }
rule() { printf '%s\n' "------------------------------------------------------------------"; }
die()  { printf 'bootstrap.sh: %s\n' "$*" >&2; exit 1; }

# --- refuse a venv inside the repository -----------------------------------
#
# Checked before anything is created, and checked on the RESOLVED path rather
# than on the string the operator typed, because the two disagree in exactly the
# cases that matter: `venv`, `./venv` and `${PWD}/venv` are the same directory,
# and a symlink can point at a directory inside the tree while naming one
# outside it. A string comparison catches none of those.
#
# `realpath -m` resolves symlinks in the existing prefix of the path and
# normalises the rest without requiring the leaf to exist, so a not-yet-created
# venv can still be classified correctly. macOS ships no `realpath -m`, so the
# fallback resolves the deepest existing ancestor and re-appends the remainder.
resolve_path() {
    local p="$1" out=""
    if realpath -m -- "$p" 2>/dev/null; then
        return 0
    fi
    local probe="$p"
    while [ ! -e "$probe" ] && [ "$probe" != "/" ]; do
        probe="$(dirname -- "$probe")"
    done
    local base
    base="$(cd -- "$probe" && pwd -P)"
    out="${p#"${probe}"}"
    printf '%s\n' "${base}${out}"
}

RESOLVED_REPO="$(resolve_path "${REPO_ROOT}")"
RESOLVED_VENV="$(resolve_path "${VENV_DIR}")"

case "${RESOLVED_VENV}" in
    "${RESOLVED_REPO}")
        die "FOXBMS_CORPUS_VENV resolves to the repository root itself (${RESOLVED_VENV}).
       Refusing to run: this script must create nothing inside the repository.
       Choose a path outside the tree, e.g.
         FOXBMS_CORPUS_VENV=\"\$HOME/.cache/foxbms-corpus-venv\" ${BASH_SOURCE[0]}"
        ;;
    "${RESOLVED_REPO}/"*)
        die "FOXBMS_CORPUS_VENV resolves INSIDE the repository:
         requested : ${VENV_DIR}
         resolved  : ${RESOLVED_VENV}
         repo root : ${RESOLVED_REPO}
       Refusing to run. A virtualenv inside the tree is an untracked directory
       that git status, git archive and every .gitignore review has to notice,
       and this corpus has no mechanism to exclude one.
       Choose a path outside the tree, e.g.
         FOXBMS_CORPUS_VENV=\"\$HOME/.cache/foxbms-corpus-venv\" ${BASH_SOURCE[0]}"
        ;;
esac

# The reverse direction is not an error and needs no check: a venv outside the
# tree may not exist yet, which is the normal case.

# --- interpreter choice -----------------------------------------------------
#
# `--user` installs land in whatever interpreter the operator invoked. The
# preflight message in corpus.py has to say "this interpreter", so this script
# has to name one and print the commands for that one specifically.
PYTHON="${PYTHON:-python3}"
if ! command -v "${PYTHON}" >/dev/null 2>&1; then
    die "'${PYTHON}' is not on PATH. Set PYTHON to the interpreter you want the
       corpus to run under, e.g. PYTHON=/usr/bin/python3 ${BASH_SOURCE[0]}"
fi
command -v "${PYTHON}" >/dev/null 2>&1 || die "cannot execute ${PYTHON}"
PYTHON_BIN="$(command -v "${PYTHON}")"
PY_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(sys.version.split()[0])')"

# --- preflight the inputs before creating anything --------------------------
[ -f "${REQUIREMENTS}" ] || die "requirements file not found: ${REQUIREMENTS}"
REPO_REL_REQUIREMENTS="${REQUIREMENTS#"${REPO_ROOT}/"}"

say ""
rule
say "foxBMS 2 corpus - interpreter bootstrap"
rule
say ""
say "  repository root : ${REPO_ROOT}"
say "  requirements    : ${REPO_REL_REQUIREMENTS}"
say "  base interpreter: ${PYTHON_BIN} (Python ${PY_VERSION})"
say "  virtualenv      : ${RESOLVED_VENV}"
say "  origin          : ${VENV_ORIGIN}"
say ""
rule
say ""

# --- create the virtualenv ---------------------------------------------------
#
# `python3 -m venv` rather than the `virtualenv` tool: venv ships with the
# interpreter, so there is nothing extra to install first, and the resulting
# environment is the one that interpreter documents. `--clear` only when the
# directory already exists and has no usable interpreter, so a re-run over a
# good environment is a no-op rather than a rebuild.
if [ -x "${RESOLVED_VENV}/bin/python" ]; then
    say "virtualenv already present and its interpreter exists; reusing it."
    say "(delete ${RESOLVED_VENV} to force a clean rebuild)"
else
    if [ -e "${RESOLVED_VENV}" ]; then
        say "virtualenv directory exists but has no usable interpreter; recreating."
        rm -rf -- "${RESOLVED_VENV}"
    fi
    # Create the parent directory too: the default is ~/.cache/<name> and
    # ~/.cache does not exist on every machine.
    mkdir -p -- "$(dirname -- "${RESOLVED_VENV}")"
    say "creating virtualenv at ${RESOLVED_VENV}"
    "${PYTHON_BIN}" -m venv "${RESOLVED_VENV}" \
        || die "'${PYTHON_BIN} -m venv' failed. On some distributions the venv
       module is a separate package (Debian/Ubuntu: python3-venv)."
fi

VENV_PY="${RESOLVED_VENV}/bin/python"

# --- install the pinned requirements ----------------------------------------
#
# This is the step that was missing three times. Inside a virtualenv there is no
# PEP 668 marker to override and no system site-packages to shadow, so a plain
# `pip install -r` is both sufficient and safe. `--require-hashes` is
# deliberately NOT used: requirements.txt pins ranges, not per-file hashes, and
# adding hash checking here would mean rewriting that file's pinning contract.
say ""
say "installing pinned requirements into the virtualenv"
say "  ${VENV_PY} -m pip install -r ${REPO_REL_REQUIREMENTS}"
"${VENV_PY}" -m pip install --disable-pip-version-check \
    -r "${REQUIREMENTS}" \
    || die "pip install failed inside the virtualenv. This is a network or index
       problem, not a repository problem: the virtualenv at
       ${RESOLVED_VENV} is intact and re-running this script will reuse it."

# --- confirm the dependency is genuinely importable BY THIS INTERPRETER ------
#
# Checked by importing, not by reading pip's output. pip reporting success and
# the import failing is precisely the third failure mode this script exists to
# close, so the confirmation has to be the same operation the corpus will
# perform.
say ""
say "verifying the dependency imports under the virtualenv interpreter"
if ! "${VENV_PY}" -c 'import jsonschema, referencing; print("  jsonschema   ", jsonschema.__version__); print("  referencing  ", referencing.__version__ if hasattr(referencing, "__version__") else "importable")' 2>/dev/null; then
    die "the install reported success but 'import jsonschema, referencing' still
       fails under ${VENV_PY}. That combination means the interpreter running the
       corpus is not this one - check which python3 is on PATH."
fi

# --- report, and print the commands ----------------------------------------
say ""
rule
say "READY"
rule
say ""
say "Run the corpus suite with this interpreter:"
say ""
say "  ${VENV_PY} ${REPO_REL_REQUIREMENTS%/requirements.txt}/corpus.py check"
say "  ${VENV_PY} ${REPO_REL_REQUIREMENTS%/requirements.txt}/corpus.py validate"
say "  ${VENV_PY} ${REPO_REL_REQUIREMENTS%/requirements.txt}/corpus.py selftest"
say "  ${VENV_PY} ${REPO_REL_REQUIREMENTS%/requirements.txt}/corpus.py coverage"
say ""
say "Or export the interpreter once and use the documented commands unchanged:"
say ""
say "  export PATH=\"${RESOLVED_VENV}/bin:\$PATH\""
say "  python3 docs/artifacts/tools/corpus.py check"
say ""
say "If you are running the clean-checkout proof, APPEND to PATH rather than"
say "prepending, because prepending shadows /usr/bin/python3 with a different"
say "interpreter and a different site-packages:"
say ""
say "  export PATH=\"\$PATH:/opt/homebrew/bin\""
say ""
say "This script created nothing inside the repository. The virtualenv is at"
say "  ${RESOLVED_VENV}"
say "and can be removed with 'rm -rf ${RESOLVED_VENV}'."
say ""