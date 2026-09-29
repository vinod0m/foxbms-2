#!/usr/bin/env bash
#
# Run the foxBMS 2 host unit tests in the isolated macOS workspace.
#
# Usage:
#   ./run.sh                      # default task set
#   ./run.sh test:database.c      # a single test
#   ./run.sh test:all             # every discovered test
#   VARIANT=bootloader ./run.sh   # the bootloader variant
#
# Environment deviations from the shipped configuration, all of them additive
# and reversible, are applied here rather than in the live tree:
#
#   1. GEM_HOME is pointed at ./.work-gems so no gem is installed into the
#      user or system Ruby.
#   2. bin/gdb is on PATH. conf/unit/app_project_posix.yml sets
#      ":use_backtrace: :gdb" and Ceedling aborts configuration validation
#      unless an executable named gdb exists. GNU gdb does not ship with
#      macOS; bin/gdb forwards the backtrace request to LLDB. It only runs
#      when a test binary crashes and never affects a pass/fail verdict.
#   3. :use_test_preprocessor: :all is downgraded to :none. With :all,
#      Ceedling 1.1.9 aborts on this test tree with
#        "Failed to read './test/preprocess/files/<test>/directives_only/raw/
#         ftask.h' for comment stripping ... No such file or directory"
#      during the preprocessor's directive-only pass. With :none Ceedling uses
#      its documented source-scan fallback and resolves the same headers.
#      This is a Ceedling-side workaround, not a change to the tests.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANT="${VARIANT:-app}"

case "${VARIANT}" in
  app)        UNIT_DIR="app_host_unit_test" ;;
  bootloader) UNIT_DIR="bootloader_host_unit_test" ;;
  *) echo "VARIANT must be app or bootloader" >&2; exit 2 ;;
esac

export GEM_HOME="${HERE}/.work-gems"
export GEM_PATH="${GEM_HOME}"
export PATH="${HERE}/bin:${GEM_HOME}/bin:${PATH}"

BUILD="${HERE}/build/${UNIT_DIR}"
if [[ ! -f "${BUILD}/project.yml" ]]; then
  "${HERE}/provision.sh" "${VARIANT}"
fi

# Ceedling rewrites, applied to the isolated copy of project.yml only. The
# original conf/unit/<variant>_project_posix.yml is never modified.
#
# The rewrite is idempotent: the inserted block is delimited by marker lines,
# any previous block is removed first, and the desired block is then inserted.
# That keeps repeated invocations in a single session consistent even when
# RELAX_CLANG_DIAGNOSTICS changes between runs.
python3 - "${BUILD}/project.yml" <<'PY'
import os
import pathlib
import sys

BEGIN = "        # >>> host-build adaptation block (verification-env) >>>\n"
END = "        # <<< host-build adaptation block (verification-env) <<<\n"

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Strip any previously inserted block so this is idempotent.
if BEGIN in text and END in text:
    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    text = head + tail

# 1. The shipped config asks the Ceedling preprocessor to run on every test
#    (:use_test_preprocessor: :all). With Ceedling 1.1.9 that aborts on this
#    tree during the directive-only pass:
#      "Failed to read './test/preprocess/files/<test>/directives_only/raw/
#       ftask.h' for comment stripping ... No such file or directory"
#    :none selects Ceedling's own documented source-scan fallback, which
#    resolves the same headers. No test source or test semantics change.
text = text.replace(
    "  :use_test_preprocessor: :all\n",
    "  :use_test_preprocessor: :none\n",
)

needle = "        - -include\n        - test_ignore_list.h\n"
if needle not in text:
    sys.exit("could not locate the -include test_ignore_list.h flag block")

extra = [
    # 2. Force-include the host portability shim. It neutralises the three TI
    #    section-placement attributes in
    #    src/os/freertos/freertos/include/mpu_wrappers.h, which Apple clang
    #    rejects for Mach-O. The build root is already -I"." so the bare
    #    filename resolves.
    "        - -include\n",
    "        - foxbms_host_port_shim.h\n",
    # 3. clang/gcc diagnostic parity. The shipped flags are
    #    -std=c11 -Wextra -Wall -pedantic -Werror, which upstream drives with
    #    GNU gcc on Linux. Apple clang enables a few diagnostics by default
    #    that gcc does not under that same set, so unchanged source can fail
    #    only because the host compiler changed. Each flag below suppresses a
    #    diagnostic only; none can mask an error, a wrong value or a type error.
    "        - -Wno-strict-prototypes\n",
    "        - -Wno-deprecated-non-prototype\n",
]
# 4. OPTIONAL, off by default. Set RELAX_CLANG_DIAGNOSTICS=1 to additionally
#    silence three diagnostics that Apple clang enables but GNU gcc does not,
#    so that tests blocked purely by the compiler change can still be
#    exercised. Each one can indicate a genuine source issue, so the strict
#    run (default) is the primary result and the relaxed run is reported
#    separately. Note the clang spelling "-Wno-enum-conversion"; the gcc
#    spelling "-Wno-enum-conv" is rejected by clang under -Werror as an
#    unknown warning option.
if os.environ.get("RELAX_CLANG_DIAGNOSTICS") == "1":
    extra += [
        "        - -Wno-enum-conversion\n",
        "        - -Wno-array-bounds\n",
        "        - -Wno-parentheses-equality\n",
    ]
text = text.replace(needle, needle + BEGIN + "".join(extra) + END + "\n", 1)
path.write_text(text, encoding="utf-8")
PY

cd "${BUILD}"
if [[ $# -eq 0 ]]; then
  exec ceedling test:all
fi
exec ceedling "$@"
