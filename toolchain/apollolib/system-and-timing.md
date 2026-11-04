---
title: ApolloLib system and timing routines (VBlank, CPU cycles, takeover)
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain, cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, vblank, timer, ccc, delay, takeover, forbid, disable]
related:
  - toolchain/apollolib/index.md
  - core/cpu-68080/performance-counters.md
  - os/os-takeover.md
  - toolchain/pitfalls/apollolib-known-bugs.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_LibC.c, _LibASM.s), commit ce1fcbf (2026-11-04)"
---

## Summary

ApolloLib waits for VBlank, reads the 68080 cycle counter and waits a
number of milliseconds, counts VBlanks in an interrupt server, and has
three takeover helpers. None of the takeover helpers has a counterpart
that undoes it: a program has to restore the system itself.

## Details

| Function | What it does |
|---|---|
| `ApolloWaitVBL()` | Polls INTREQR bit 5 (VERTB) until set, then clears it in INTREQ |
| `ApolloCPUTick()` | Returns the clock cycle counter CCC (`movec $809,d0`, see [performance-counters.md](../../core/cpu-68080/performance-counters.md)) |
| `ApolloCPUDelay(ms)` | Busy-waits `ms × 92000` cycles on CCC |
| `ApolloTimer()` | Adds a VBlank interrupt server (`AddIntServer`, `INTB_VERTB`) that increments `GlobalTimer` every frame |
| `ApolloTakeOver()` | Opens intuition.library, `CloseWorkBench()`, sets the task priority to 20 |
| `ApolloForbid()` | Calls exec `Forbid()` |
| `ApolloDisable()` | Calls exec `Disable()` |

### Limits

- **`ApolloWaitVBL` clears VERTB** itself. Under a running OS that takes
  the event away from the OS's VBlank handling; use it in takeover code.
- **`ApolloCPUDelay` assumes 92 MHz** (92000 cycles per ms, also
  `APOLLOCYCLES`). The V4 runs at 99.31 MHz (14 × 7.09379 MHz, see
  [core-at-a-glance.md](../../core/cpu-68080/core-at-a-glance.md)), so a
  delay is about 7 % short there.
- **No restore functions:** there is no Permit, Enable, `OpenWorkBench`
  or priority reset, and no `RemIntServer` for `ApolloTimer`. See
  [apollolib-known-bugs.md](../pitfalls/apollolib-known-bugs.md) for what
  that means at exit.

### Restore at exit (your code)

| After | Call before exit |
|---|---|
| `ApolloForbid()` | `Permit()` |
| `ApolloDisable()` | `Enable()` |
| `ApolloTakeOver()` | `SetTaskPri(FindTask(NULL), old)`, `OpenWorkBench()`, `CloseLibrary()` on the intuition.library base it opened (you don't get it back) |
| `ApolloTimer()` | `RemIntServer(INTB_VERTB, …)`: the server node is internal to ApolloLib, so this isn't possible yet |

This is what [os-takeover.md](../../os/os-takeover.md) asks of every
takeover program: restore multitasking and the Workbench screen on exit.

## Differences from AmigaOS / AROS / 68060

- `ApolloCPUTick` reads a 68080 control register; there is no such
  counter on the 68060. Use timer.device or the CIA timers for portable
  timing.
- The takeover helpers wrap single exec and Intuition calls; they don't
  save the display, the interrupt enables or the DMA state.

## Do / Don't

- DO pair `ApolloForbid` with `Permit()` and `ApolloDisable` with
  `Enable()` in your exit code.
- DO reopen the Workbench after `ApolloTakeOver`.
- DO calibrate `ApolloCPUDelay` with the clock multiplier from `$DFF3FC`
  if the delay must be exact.
- DON'T call `ApolloTimer` in a program that exits back to the OS (see the
  known bugs).
