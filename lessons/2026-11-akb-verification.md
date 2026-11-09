---
title: Automated verification of the knowledge base, and the first V4 test runs
type: lesson
owner: WDrijver
status: draft
origin: ai-assisted
basis: [core-developer, measured, source-code]
components: [toolchain, cpu-68080, hardware, general]
applies_to:
  core: "any"
  os: [any]
  board: [v4-unicorn]
tags: [verification, ci, kb-expect, vasm, gcc, hardware-test, serial, ash, acp, ccc]
related:
  - toolchain/compiler-variants.md
  - toolchain/pitfalls/float-settings-mismatch.md
  - toolchain/pitfalls/vasm-68080-encoding-issues.md
  - core/cpu-68080/caches-and-memory.md
  - core/cpu-68080/performance-counters.md
  - core/saga-registers/system.md
  - guides/benchmark-method.md
sources:
  - "ApolloTeam-dev/ApolloKnowledgeBase pull requests #32 to #41 (2026-11-08 to 2026-11-09)"
  - "WDrijver/ApolloCrossDev pull request #24 (README opcode list)"
  - "Test programs tools/v4/tests/ (moviw, add-mem-dbra, fpu-m68881, serial-out), run on a V4 UniCorn, Core 12556, 2026-11-09"
  - "WDrijver: ApolloControl CO prints the core number (2026-11-09)"
---

## Project

Step 3 of the knowledge base plan: automated verification of the
knowledge base itself. Done by Claude (AI) with WDrijver, 2026-11-08 to
2026-11-09, in ApolloKnowledgeBase pull requests #32 to #41.

1. `kb:expect` checks: CI compiles code blocks with ApolloCrossDev and
   checks the emitted assembly or bytes.
2. Fact cross-checks: every SAGA address must be documented, and every
   `asm` block must assemble.
3. Tests on V4 hardware with `tools/v4/v4test.py`: build with ApolloCrossDev,
   copy with `acp`, run with `ash`, collect output, serial log, screenshot or
   video, and power-cycle a hung V4.

## What went well

- The CI checks found real errors in reviewed files at once:
  - `movec $809,Dn` does not assemble in vasm; `movec ccc,Dn` does. Fixed in
    three files.
  - The `$DFF300` Maggie counters were used in the knowledge base but
    missing from the SAGA register documentation.
  - The ApolloCrossDev README listed `moviw.l` and `bcc.s+` as GCC output;
    GCC has no patterns for them, only vasm accepts them.
- `kb:expect` checks catch a stale compiler: a GCC-6.50-Dev built before a
  fix fails the check of that fix.
- The remote test loop from the ApolloOS-Port project worked for the
  knowledge base with few changes. Three open questions from step 1 were
  measured in one afternoon.
- Alternating variants and printing load addresses (from
  [benchmark-method.md](../guides/benchmark-method.md)) turned a confusing
  result into a clear one within two runs.

## What went wrong

- The local GCC-6.50-Dev was older than the fixes the checks test. The
  checks failed locally until it was reinstalled. `find-acd.sh` now reports
  an install older than its script.
- CI failed twice on GitHub 502/504 errors in `check_owners.py`; it retries
  now.
- `ash` hung on the test V4 (ApolloOS R9.5) until ApolloExplorerSrv was
  updated; `acp` worked with the old server.
- A CI run after an ApolloCrossDev update rebuilds the toolchain from
  scratch, which takes more than 30 minutes.
- Three claims in the vasm pitfall did not reproduce with vasm 2.0f. They
  stay open until ApolloCrossDev ships vasm 2.0g.

## What the AI got wrong

- **`SER:` is not the debug serial line.** To test the serial log, the AI
  wrote `Echo >SER:` on the V4 and listened at 9600 to 115200 baud: nothing
  arrived. The cable was fine: the debug output (ApolloLib
  `ApolloDebugPutChar()`) writes the Paula UART registers directly at
  115200. A test that does the same was received at once.
- **Soft-float links without `-lm`.** The AI built a `-m68080` (soft-float)
  variant without `-lm`; the link failed on `__mulsf3`. libnix keeps the
  soft-float routines in `libm`.
- **One run of a benchmark is not a result.** The first `add.l #1,mem` loop
  run gave 2 cycles per iteration in two rounds and 21.6 in the third. Only
  after printing the counter's address did it show that the counter
  shared a cache line with the loop code.
- **vasm and `moviw.l #$8123`.** The AI wrote the PRM's example literally;
  vasm warns "using signed operand as unsigned" and wants `#-32477`.
- **Looking for the core number in registers.** The AI looked for the core
  number in the SAGA registers; `$DFF3EA` is undocumented. `ApolloControl CO`
  prints it.
- **A `kb:expect` check that tests nothing.** The first `-mrtd` check called
  a function in the same file; GCC inlined it, so no call was left to
  test. The called function must be external.
- **Tools that hang.** The first ffmpeg recording from the HDMI capture
  hung: the device rejects the default pixel format (`-pixel_format
  uyvy422` is needed), and without a timeout nothing stopped it. Every
  remote command (ash, acp, ffmpeg) needs a timeout and stdin from
  `/dev/null`.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `add.l #1,mem` + `dbra`: 2 cycles per iteration; `dbra` alone and `addq.l #1,Dn` + `dbra`: 1 | (M) | Core 12556 | `tools/v4/tests/add-mem-dbra`, CCC, 65536 iterations, 8 rotating rounds under `Disable()`, V4 UniCorn |
| Same loop, counter in the same 64-byte line as the loop code: 20–23 cycles per iteration (38 once with `(An)`) | (M) | Core 12556 | Same test, counter at 7 distances from the loop, 2 runs |
| Gunnar expects about 1 iteration per cycle | (G) 2026-11-03 | not stated | [caches-and-memory.md](../core/cpu-68080/caches-and-memory.md) |
| `-m68080 -m68881`: 8 cycles per element of a float dot product; `-m68080` alone: 63 | (M) | Core 12556 | `tools/v4/tests/fpu-m68881`, 3 alternating rounds |
| `moviw.l` runs: register, memory and N/Z flags correct; encoded `$303D 8123` | (M) | Core 12556 | `tools/v4/tests/moviw`, 5 passes |
| CCC (`movec ccc,Dn`) reads in user mode | (M) | Core 12556 | All tests above |
| Direct Paula UART writes at 115200 reach the USB serial adapter; `Echo >SER:` does not | (M) | Core 12556 | `tools/v4/tests/serial-out`; `Echo >SER:` listened for at 5 baud rates |
| Soft-float routines are in libnix `libm`; `-m68080` with or without `-m68881` links the base multilib `.` | (SRC) | any | `m68k-amigaos-nm` over the libraries; `gcc -print-multi-directory` |
| GCC 6.5 emits `cmpiw.l`, `addiw.l`, `dbra.l`, but never `moviw.l` or `bcc.s+` | (M) | any | `kb:expect` checks in [compiler-variants.md](../toolchain/compiler-variants.md) |
| vasm accepts `movec ccc,Dn` (`$4E7A x809`), not `movec $809,Dn` | (M) | any | Fragment assembly in CI (PR #34) |
| `ash` needs a recent ApolloExplorerSrv; `acp` works with an older one | (M) | Core 12556 | ApolloOS R9.5, before and after the server update |
| Power cycle with a Tasmota plug: the V4 answers `ash` 15 s after power-on | (M) | Core 12556 | `v4test.py power-cycle` |

## Candidates for distillation

- **New `core/pitfalls/data-next-to-running-code.md`:** writing data in the
  cache line of running code costs about 10 times as much. First measure it
  on Core 12841, and find the exact distance at which the cost starts.
- **New `guides/testing-on-v4-hardware.md`:** the remote test loop:
  - `ash`/`acp` with timeouts;
  - `ApolloControl CO` for the core number;
  - serial output through the Paula UART, not `SER:`;
  - HDMI capture with ffmpeg;
  - power cycling.
- **Update `toolchain/vasm-assembler.md` or
  `toolchain/pitfalls/vasm-68080-encoding-issues.md`:** immediates above
  `$7FFF` for `moviw.l` and other sign-extended word immediates must be
  written as negative values.
- **Update `toolchain/c-compiler-options.md`:** the multilib that
  `-m68080` links, and `-lm` for soft-float.
- **Update `core/cpu-68080/performance-counters.md`:** widen
  `applies_to.core` once more cores are measured; CCC already works on Core
  12556. Done for the note in PR #41.
- **Update `float-settings-mismatch.md` (done in PR #41):** `-lm` and the
  FPU measurement.
