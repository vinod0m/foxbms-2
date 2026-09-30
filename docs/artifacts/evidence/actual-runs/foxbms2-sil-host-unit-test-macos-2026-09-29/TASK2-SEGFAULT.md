# TASK 2 — the `test_dp83869.c` segfault: root cause

## Getting a stack trace at all

`lldb` is genuinely broken on this host, confirmed independently of the prior
investigation:

```
$ lldb --version      # works
lldb-1700.0.9.502
$ lldb --batch -o run -o "bt all" ./test_dp83869.out
(lldb) target create "./test_dp83869.out"
PLEASE submit a bug report to and include the crash report from
~/Library/Logs/DiagnosticReports/.
LLDB diagnostics will be written to /var/folders/.../diagnostics-9a7066
```

It fails identically on a trivial `hello.c` compiled in `/tmp`, so it is not
related to this test, this binary, or its size. `~/Library/Logs/DiagnosticReports/`
does not exist and the emitted `diagnostics.log` is zero bytes, so the crash
report is unreadable. `gdb` is not installed. The predecessor's
`bin/gdb`→LLDB shim has a Python 3 syntax error at line 64.

AddressSanitizer was re-tried and does hang, exactly as reported. It hangs at
the **link** step, and it does so because the shipped `:tools: :test_linker:`
appends `-flto`; LTO plus ASAN deadlocks this toolchain. Removing `-flto` alone
was not sufficient within the time available.

## The approach that worked

A constructor-installed signal handler, injected into the debug build only, via
`sil/tools/sil_crash_trace.h`:

* `SIGSEGV`/`SIGBUS` handler installed with `SA_SIGINFO` in a
  `__attribute__((constructor))`,
* prints `si_addr` and a `backtrace()` via `backtrace_symbols_fd`,
* then re-raises with the default handler so the exit status is unchanged.

It needs neither `lldb` nor ASAN. It is enabled by `SIL_DEBUG=1`, which also
strips `-flto` and adds `-g -O0 -fno-omit-frame-pointer`. It prints; it never
alters a verdict, and a non-debug run is byte-identical to a baseline run.

A secondary problem had to be fixed first: `run.sh` was **not idempotent**. It
re-inserted its `-include`, `-I` and `-D` lines on every invocation, so after
several runs `project.yml` carried nine copies of the SIL include path and
three of the define. That is now fixed and verified over repeated runs. It is
worth recording because it is exactly the kind of harness drift that produces
confusing, irreproducible results.

## The result

Running the test through a pty (`script -q /dev/null ./test_dp83869.out`),
13 of 15 cases pass, 2 fail with the class-A message, and the 15th crashes:

```
test_dp83869.c:871:testPHY_SwReset:PASS (0 ms)

=== SIL CRASH: signal 11 at fault address 0xfff7bc38 ===
0   test_dp83869.out  FoXBMS_SilCrashHandler + 204
1   libsystem_platform.dylib  _sigtramp + 56
2   test_dp83869.out  UnityAssertEqualIntArray + 260
3   test_dp83869.out  IO_PinReset + 524
4   test_dp83869.out  PHY_ResetHardware + 40
5   test_dp83869.out  testPHY_HardwareReset + 88
6   test_dp83869.out  run_test + 168
7   test_dp83869.out  main + 1004
```

The Ceedling log had blamed `testPHY_OperationModeGet` at line 897. **That was
wrong.** Ceedling attributes a crash to whichever test was in flight when the
process died, and because the runner aborts, every case after the faulting one
is reported as crashed. The real faulting case is
`testPHY_HardwareReset`, `test_dp83869.c:885`, which starts at line 885 and
whose first statement of substance is line 889.

## Root cause

`test_dp83869.c:889`:

```c
IO_PinReset_Expect(&((gioPORT_t *)0xFFF7BC34u)->DOUT, 1u);
```

`0xFFF7BC34` is the real TMS570 `gioPORTA` base address — it is recorded in the
repository's own committed HALCoGen input, `conf/hcg/app.dil:1707`:

```
DRIVER.GIO.VAR.GIO_BASE_PORTA.VALUE=0xFFF7BC34
```

so the constant is not invented; it is the correct device value, and on target
the test is right.

`&((gioPORT_t *)0xFFF7BC34u)->DOUT` evaluates to `0xFFF7BC38`
(`0xFFF7BC34 + offsetof(DOUT)`, `DOUT` being the second `uint32_t`). That
address is **never dereferenced by the test**: it is only taken and handed to
CMock.

CMock's `:when_ptr: :compare_data` then compares it **by content**, because
`IO_PinReset`'s parameter is a typed pointer:

```c
void IO_PinReset(volatile uint32_t* pRegisterAddress, uint32_t pin)
...
UNITY_TEST_ASSERT_EQUAL_HEX32_ARRAY(cmock_call_instance->Expected_pRegisterAddress,
                                   CMOCK_DEVOLATILE_PTR(pRegisterAddress), 1, ...)
```

and CMock dereferences **both** operands. The expected operand is
`0xFFF7BC38`, a device address that does not exist on the host. Dereferencing it
is the `SIGSEGV`, and `si_addr` is exactly `0xfff7bc38`, confirming it.

The production code passes a completely different, perfectly valid object:

```c
/* phy_cfg.h:65 */  #define PHY_IO_HW_RESET_REG_DOUT (gioPORTA->DOUT)
/* dp83869.c:542 */ IO_PinReset(&PHY_IO_HW_RESET_REG_DOUT, PHY_HW_RESET_PIN);
```

which in the SIL model is `&sil_gio.PORT[0].DOUT`, a real host address.

## Classification: **SIL harness / test-harness defect, not a product defect**

* **Not product code.** `dp83869.c:542` and `544` do the right thing: they pass
  the address of the reset register to the driver API. Nothing in
  `src/app/driver/phy/` is wrong, and nothing here says anything about the
  device.
* **Not the SIL model.** `sil/iface/HL_gio.h` maps `gioPORTA` to
  `&sil_gio.PORT[0]` of a real host object. That mapping is the whole point of
  the harness and it works: the code under test dereferences a valid pointer.
* **It is the test, meeting a host on which a device address is not mapped.**
  The test asserts against a *target* peripheral address. On the target that
  address is mapped and the comparison reads two real registers. On the host it
  is unmapped and the same comparison faults.

The prior report's statement that "the crash is not caused by the test's
hard-coded peripheral address ... that address is only *taken*, never
dereferenced" is **incorrect**, and the backtrace is what disproves it: CMock
dereferences it on the test's behalf. That is precisely the kind of claim that
needed a stack trace rather than reasoning, and it is now settled.

## Can it be fixed?

Not test-side, and not without inventing a register map. The three options were
each considered and rejected:

1. **Give the SIL model a `gioPORTA` at `0xFFF7BC34`.** This is the only fix
   that would make the assertion meaningful, and it is forbidden and dishonest:
   it fabricates a target base address into the harness, which
   `sil/REPORT.md` §3.3 and the harness rules explicitly refuse, and it would
   create the appearance of having verified register placement when nothing of
   the kind is verified.
2. **Change the test to expect `gioPORTA->DOUT`.** That would make the test
   pass, but it would *delete the assertion that matters*: the test exists to
   check that the PHY driver resets the correct physical pin, and the device
   address is the only thing that says which pin. It would silently turn a real
   check into a tautology. This is a product-owner decision about what the test
   is for, not a harness fix.
3. **Suppress the comparison.** Would weaken the assertion.

## Verdict

**`test_dp83869.c` cannot be brought up on a host SIL harness without either
inventing a target register map or weakening the assertion.** The test now
builds, runs, and its 13 genuinely-passing cases and 2 class-A failures are
visible individually instead of the whole file being reported as 15/15 failed
after an abort — that is a real improvement in the evidence, and it is all the
improvement that is honest here.

Recorded as an open finding, not closed.
