#!/usr/bin/env python3
"""Generate the HALCoGen stand-in headers needed to compile the host tests.

HALCoGen is proprietary Texas Instruments code generation software. It is not
available on this host and cannot be redistributed. This script writes the
smallest set of headers that lets the host unit-test build compile, and it is
deliberately conservative: it provides *only* declarations that the repository
actually references, so that anything genuinely missing fails loudly at compile
time rather than being silently papered over.

Two headers are produced, both into the isolated Ceedling build root.

1. include/config_cpu_clock_hz.h
   Byte-for-byte what cli/cmd_embedded_ut/embedded_ut_impl.py:_cleanup_hcg_sources
   writes. HALCOGEN_CPU_CLOCK_HZ is read out of the repository's own committed
   conf/hcg/<variant>.dil (DRIVER.OS.VAR.OS_CPUCLOCKHZ.VALUE), not guessed.
   See tools/waf-tools/f_hcg.py:150-157: this header is the *only* thing the
   host build needs from HALCoGen.

2. HL_spi.h
   tests/unit/support/struct_helper.h includes "HL_spi.h" and uses exactly one
   type from it, spi_config_reg_t. A SHADOW COPY of the TI header is written to
   the build root, which is already on the include path as -I".". A shadow
   copy (rather than an -I shim directory) is required because
   struct_helper.h lives outside any directory that could be prepended
   usefully, and because -I precedence for a header that exists in an earlier
   -I directory is not guaranteed to favour ours.

   !! FIDELITY WARNING !!
   spi_config_reg_t is RECONSTRUCTED from the public TMS570 SPI peripheral
   register map (offsets 0x00 GCR1 .. 0x60 TBPRD) and the field names the
   repository actually uses. It is NOT the TI original. Consequences:
     * Only the register-shadow layout is modelled. TI's HL_spi.h also
       declares driver functions, enums and macros (spiBASE_t, spi1GetConfig-
       Value, SPIDATAFMT_t, ...). Those are NOT provided here.
     * A host test that needs any of them will fail to compile. That is
       intended: it is reported as an infrastructure gap, not hidden.
     * The register *addresses* are irrelevant on a host because the struct is
       never memory-mapped in a host test; it is used as a plain value buffer.
       What the tests exercise is the field-name-level comparison logic in
       tests/unit/support/struct_helper.c.
   The member list below was derived mechanically from the repository:
       grep -rho '\\.CONFIG_[A-Za-z0-9_]*' src/ tests/ | sort -u
   plus the same for configRegisterBuffer.*.
"""

import pathlib
import re
import sys

CPU_CLOCK_TEMPLATE = """\
#ifndef CONFIG_CPU_CLOCK_HZ_H
#define CONFIG_CPU_CLOCK_HZ_H
#define HALCOGEN_CPU_CLOCK_HZ ({clock_hz})
#endif /* CONFIG_CPU_CLOCK_HZ_H */
"""

HL_SPI_TEMPLATE = """\
/* RECONSTRUCTED stand-in for the TI HALCoGen-generated HL_spi.h.
 *
 * NOT the Texas Instruments original. See the generating script
 * (make_halcogen_stubs.py) and the runbook for the full rationale.
 *
 * Provides only the type tests/unit/support/struct_helper.h needs:
 * spi_config_reg_t, a flat shadow of the TMS570 SPI *configuration* register
 * block. Member names carry the CONFIG_ prefix that TI uses for that block.
 * The member set below is exactly the set the repository references:
 *
 *   grep -rho '\\.CONFIG_[A-Za-z0-9_]*' src/ tests/ | sort -u
 *
 * No function, enum or macro from TI's HL_spi.h is provided, and no register
 * offset is claimed to be authoritative. On a host the struct is never
 * memory-mapped; it is used as a plain value buffer, so only the field names
 * and their integer width are load-bearing for the tests.
 */
#ifndef FOXBMS_HOST_STUB__HL_SPI_H_
#define FOXBMS_HOST_STUB__HL_SPI_H_

#include <stdint.h>

typedef volatile struct {
    uint32_t CONFIG_GCR1;  /* Global Control Register 1                      */
    uint32_t CONFIG_INT0;  /* Interrupt Register 0                           */
    uint32_t CONFIG_LVL;   /* TX/RX FIFO Level Register                      */
    uint32_t CONFIG_PC0;   /* Pin Select Control 0                           */
    uint32_t CONFIG_PC1;   /* Pin Select Control 1                           */
    uint32_t CONFIG_PC2;   /* Pin Select Control 2                           */
    uint32_t CONFIG_PC3;   /* Pin Select Control 3                           */
    uint32_t CONFIG_PC4;   /* Pin Select Control 4                           */
    uint32_t CONFIG_PC5;   /* Pin Select Control 5                           */
    uint32_t CONFIG_PC6;   /* Pin Select Control 6                           */
    uint32_t CONFIG_PC7;   /* Pin Select Control 7                           */
    uint32_t CONFIG_PC8;   /* Pin Select Control 8                           */
    uint32_t CONFIG_TBPRD; /* Transfer Baud Rate Divider                     */
    uint32_t CONFIG_FMT0;  /* Data Format Register 0                         */
    uint32_t CONFIG_FMT1;  /* Data Format Register 1                         */
    uint32_t CONFIG_FMT2;  /* Data Format Register 2                         */
    uint32_t CONFIG_FMT3;  /* Data Format Register 3                         */
    uint32_t CONFIG_DELAY; /* Delay Register                                 */
} spi_config_reg_t;

#endif /* FOXBMS_HOST_STUB__HL_SPI_H_ */
"""

PORT_SHIM_TEMPLATE = """\
/* Host-build portability shim for the foxBMS 2 Ceedling unit test build.
 *
 * WHY THIS EXISTS
 * ---------------
 * src/os/freertos/freertos/include/mpu_wrappers.h defines three macros that
 * place FreeRTOS API functions into TI target-specific sections:
 *
 *     #define PRIVILEGED_FUNCTION  __attribute__( ( section( ".kernelTEXT" ) ) )
 *     #define PRIVILEGED_DATA      __attribute__( ( section( ".kernelBSS" ) ) )
 *     #define FREERTOS_SYSTEM_CALL __attribute__( ( section( ".syscallTEXT" ) ) )
 *
 * These are TI ARM Cortex-R5 (TMS570) image-layout directives. Apple's clang
 * targets Mach-O, whose `section` attribute requires a "SEGMENT,SECTION"
 * pair, and rejects a bare ".kernelTEXT" outright:
 *
 *     error: argument to 'section' attribute is not valid for this target:
 *     mach-o section specifier requires a segment and section separated by a comma
 *
 * GNU/Linux targets ELF, where GCC accepts the bare dotted name. This is
 * therefore a macOS-only build failure. These three definitions are the ONLY
 * occurrences of a TI section attribute anywhere under src/os/freertos and
 * src/app:
 *
 *     grep -rho 'section( *"\\.[A-Za-z_]*"' src/os/freertos/ src/app/ | sort -u
 *     -> section( ".kernelBSS"    section( ".kernelTEXT"    section( ".syscallTEXT"
 *
 * WHY IT IS PRE-DEFINE BASED
 * --------------------------
 * mpu_wrappers.h is included by task.h and list.h, which live in the *same*
 * directory. For a quoted #include the compiler searches the including file's
 * own directory first, so an -I shadow directory cannot intercept those.
 *
 * Pre-defining the header's include guard is the reliable lever: when the real
 * mpu_wrappers.h is reached, MPU_WRAPPERS_H is already defined and the entire
 * file body, including the three attribute macros, is skipped. The three
 * macros are then defined here as empty.
 *
 * The function-declaration body of mpu_wrappers.h is skipped as well. It is
 * reached only through the MPU/access-control API wrappers, which the host
 * tests mock via CMock (Mockmpu_wrappers.h). foxBMS's own shipped Ceedling
 * configuration already declares
 *
 *     :cmock: :strippables: [ "(.FREERTOS_SYSTEM_CALL)", "(.PRIVILEGED_FUNCTION)", ... ]
 *
 * so upstream already treats these attributes as noise to be removed before
 * the mocked code is even parsed.
 *
 * IMPACT ON TEST SEMANTICS
 * ------------------------
 * None. The attributes only control where a function lands in the *target*
 * image. They change no observable behaviour, no foxBMS logic and no Unity
 * assertion. Validated by compiling the full FreeRTOS include chain
 * (FreeRTOS.h, task.h, list.h, queue.h, semphr.h, event_groups.h,
 * stream_buffer.h) with -std=c11 -Wextra -Wall -pedantic -Werror.
 */
#ifndef FOXBMS_HOST_PORTABILITY_SHIM_H_
#define FOXBMS_HOST_PORTABILITY_SHIM_H_

/* Suppress the TI section-placement attributes. See the note above. */
#ifndef MPU_WRAPPERS_H
#define MPU_WRAPPERS_H
#endif
#undef PRIVILEGED_FUNCTION
#define PRIVILEGED_FUNCTION
#undef PRIVILEGED_DATA
#define PRIVILEGED_DATA
#undef FREERTOS_SYSTEM_CALL
#define FREERTOS_SYSTEM_CALL

#endif /* FOXBMS_HOST_PORTABILITY_SHIM_H_ */
"""


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit("usage: make_halcogen_stubs.py <dil-file> <build-root>")
    dil = pathlib.Path(sys.argv[1])
    build_root = pathlib.Path(sys.argv[2])

    match = re.search(
        r"^DRIVER\.OS\.VAR\.OS_CPUCLOCKHZ\.VALUE=(\S+)\s*$",
        dil.read_text(encoding="utf-8", errors="replace"),
        re.MULTILINE,
    )
    if not match:
        sys.exit(f"ERROR: no OS_CPUCLOCKHZ entry in {dil}")
    clock_hz = match.group(1)

    include = build_root / "include"
    include.mkdir(parents=True, exist_ok=True)
    clock_header = include / "config_cpu_clock_hz.h"
    clock_header.write_text(
        CPU_CLOCK_TEMPLATE.format(clock_hz=clock_hz), encoding="utf-8"
    )

    spi_header = build_root / "HL_spi.h"
    spi_header.write_text(HL_SPI_TEMPLATE, encoding="utf-8")

    shim_header = build_root / "foxbms_host_port_shim.h"
    shim_header.write_text(PORT_SHIM_TEMPLATE, encoding="utf-8")

    print(f"HALCOGEN_CPU_CLOCK_HZ = {clock_hz}  (from {dil})")
    print(f"wrote {clock_header}")
    print(f"wrote {spi_header}   (RECONSTRUCTED, not the TI original)")
    print(f"wrote {shim_header}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
