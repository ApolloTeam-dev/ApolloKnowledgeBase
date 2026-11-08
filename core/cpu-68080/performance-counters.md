---
title: 68080 performance counters
type: reference
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12830-12841"
  os: [any]
tags: [68080, counters, ccc, iep, movec, benchmark]
related:
  - core/cpu-68080/prm/integer/movec.md
  - core/cpu-68080/prm/optimizing.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 7.3 and 8.1"
---

## Summary

The clock cycle counter (CCC, `$809`) and the per-pipe instruction counters
(IEP1–IEP3) are readable with `movec` in user mode. They are the most
reliable way to time code. The other event counters read 0 on release cores.

## Details

### Counters

| Rc | Name | Use |
|---|---|---|
| `$809` | CCC | Clock cycles |
| `$80A` | IEP1 | Instructions issued in pipe 1 |
| `$80B` | IEP2 | Instructions issued in pipe 2 |
| `$00C` | IEP3 | Instructions issued in pipe 3 (0 on cores with 2 pipes) |
| `$808` | PCR | id `$0440`. Bit 0 = second pipe, bit 1 = FPU off. The core ignores PCR's ESS bit (M) |

- The debug and event counters (BPC/BPW, DCH/DCM `$80E/$80F`,
  STR/STC/STB/MWR) read 0 on release cores (M).
- On Core 12830–12841 the counters are readable with `movec` in user mode.

### Reading the cycle counter

```asm
    movec   ccc,a6         ; CCC ($809) before
    ; ... code to time ...
    movec   ccc,d7
    sub.l   a6,d7          ; cycles, stable to less than 1 %
```

vasm accepts the counter only by name: `movec ccc,d7` assembles to
`$4E7A 7809`, while `movec $809,d7` is an error ("illegal operand types").
ApolloLib writes the instruction as `dc.w $4E7A,$x809` (SRC).

- Measure under exec `Disable()`.
- For whole-program timing, sum CCC deltas around each call in 64 bits: 32
  bits wrap after about 43 s at 99 MHz.
- CCC was more reliable than EClock for benchmarks (M).
- From GCC inline assembler, use GNU syntax: `.short 0x4e7a,0x0809`
  (`movec ccc,d0`), not `dc.w`.

### Counting pipes

Run 6 independent `addq`/`subq` + `dbf`, 32001 turns (n instructions):

- IEP2 < n/16: 1 pipe.
- IEP3 ≥ n/16 and IEP1 + IEP2 < 7/8 n: 3 pipes.
- Otherwise: 2 pipes.

## Differences from AmigaOS / AROS / 68060

- These counters are 68080 specific. `movec` reads of them work in user
  mode, unlike classic control registers.
- The PRM lists event counters (BPC, BPW, DCH, DCM, STR, STC, STB, MWR) that
  read 0 on release cores.

## Do / Don't

- DO time code with CCC, on trained loops, under `Disable()`.
- DON'T measure in supervisor mode with interrupts off: a fault there gurus.
- DON'T write a register the loop uses while under `Disable()`: this hung the
  V4 once.
- DO probe an unknown core safely: install a temporary illegal-instruction
  trap first. Reading 0 means no counters.
