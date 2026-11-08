---
title: ApolloLib system and timing routines (VBlank, CPU cycles, takeover)
type: reference
owner: WDrijver
status: reviewed
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
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_LibC.c, _LibASM.s), commit 639e195 (2026-11-04)"
---

## Summary

ApolloLib waits for VBlank, reads the 68080 cycle counter and waits a
number of milliseconds, counts VBlanks in an interrupt server, and has
three takeover helpers. From commit 639e195 every one of them has a
counterpart that undoes it; call it before the program exits.

## Details

| Function | What it does |
|---|---|
| `ApolloWaitVBL()` | Polls INTREQR bit 5 (VERTB) until set, then clears it in INTREQ |
| `ApolloCPUTick()` | Returns the clock cycle counter CCC (`movec ccc,d0`, register `$809`, see [performance-counters.md](../../core/cpu-68080/performance-counters.md)) |
| `ApolloCPUDelay(ms)` | Busy-waits `ms × multiplier × 7094` cycles on CCC; the multiplier is the low byte of `$DFF3FC` (14 if 0) |
| `ApolloTimer()` | Adds a VBlank interrupt server (`AddIntServer`, `INTB_VERTB`) that increments `GlobalTimer` every frame |
| `ApolloTimerStop()` | Removes that server (`RemIntServer`) |
| `ApolloTakeOver()` | Opens intuition.library, `CloseWorkBench()`, sets the task priority to 20, and remembers the library base and the old priority |
| `ApolloRelease()` | Restores the old priority, `OpenWorkBench()`, closes intuition.library |
| `ApolloForbid()` / `ApolloPermit()` | Call exec `Forbid()` / `Permit()` |
| `ApolloDisable()` / `ApolloEnable()` | Call exec `Disable()` / `Enable()` |

`ApolloTimerStop`, `ApolloRelease`, `ApolloPermit` and `ApolloEnable`
exist from ApolloLib commit 639e195.

### Limits

- **`ApolloWaitVBL` clears VERTB** itself. Under a running OS that takes
  the event away from the OS's VBlank handling; use it in takeover code.
- **`ApolloCPUDelay`** counts `multiplier × 7.094` MHz cycles per ms, so
  it follows the clock the board reports at `$DFF3FC` (see
  [system.md](../../core/saga-registers/system.md)). Before 639e195 it
  assumed 92 MHz, about 7 % short on a 99.31 MHz V4.
- **`ApolloRelease`** restores the priority that `ApolloTakeOver` saved.
  Call it only after `ApolloTakeOver`; otherwise it sets priority 0.

### Restore at exit

| After | Call before exit |
|---|---|
| `ApolloTimer()` | `ApolloTimerStop()`: the server node lives in the program, so a server left behind runs freed memory |
| `ApolloTakeOver()` | `ApolloRelease()` |
| `ApolloForbid()` | `ApolloPermit()` |
| `ApolloDisable()` | `ApolloEnable()` |

This is what [os-takeover.md](../../os/os-takeover.md) asks of every
takeover program: restore multitasking and the Workbench screen on exit.

## Differences from AmigaOS / AROS / 68060

- `ApolloCPUTick` reads a 68080 control register; there is no such
  counter on the 68060. Use timer.device or the CIA timers for portable
  timing.
- The takeover helpers wrap single exec and Intuition calls; they don't
  save the display, the interrupt enables or the DMA state.

## Do / Don't

- DO call `ApolloTimerStop`, `ApolloRelease`, `ApolloPermit` and
  `ApolloEnable` in your exit code, in the reverse order of their
  counterparts.
- DON'T use `ApolloTimer` with an ApolloLib older than 639e195 in a
  program that exits back to the OS: there is no way to remove the server.
