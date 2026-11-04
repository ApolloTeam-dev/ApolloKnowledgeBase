---
title: 68080 FPU performance model (measured)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fpu, latency, throughput, scheduling, mac]
related:
  - core/cpu-68080/prm/fpu-unit.md
  - core/best-practices/fpu-schedule-by-completion-slot.md
  - core/best-practices/fpu-when-it-pays.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 4.1"
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03)"
---

## Summary

The FPU issues in order, one instruction per cycle, in pipe 1 only, and has
one result-write port. fmul has latency 5, fadd/fsub 6. The model below
predicted all 25 measured patterns exactly.

## Details

- Issue is in order, 1 FPU instruction per cycle, pipe 1 only. Integer
  instructions pair in pipe 2 for free: 24 fmul + 24 add.l = 26 cycles (M).
- **One FP register write per cycle.** An instruction whose completion cycle
  (issue + latency) is already taken stalls.
- Latencies: fmul 5, fadd/fsub 6, fmove load 1, fmove.x copy 1. `fmove.s`/`.d`
  stores write no FP register and never collide.
- So the mix matters, not only the dependencies. Alternating fmul/fadd costs
  1.5 cycles per instruction.
- Measured patterns (L = load, M = mul, A = add), cycles per instruction:

  | Pattern | Cycles |
  |---|---|
  | MMA | 1.33 |
  | LA | 1.17 |
  | LMA, ALM, MAL | 1.0 |
  | AML, MLA | 1.33 |

- Best multiply-accumulate term order: `fmove.s coef,fpT` / `fmul.s mem,fpT` /
  `fadd fpT,acc` = **3.13 cycles per term**. Other orders cost 3.5–4.5. An
  integer operand (`fmove.l` / `fmul.l`) costs 4.0–5.1.
- The float MAC floor is 3 FPU instructions per term (about 33 M MAC/s at
  99 MHz). The integer MAC (`muls.l` + add/addx) measured 4.27 per term, with
  a floor of 4.0.
- Gunnar's rule (G): **a pipelined unit showing more than 1 cycle per
  instruction means the schedule is wrong.**
- Gunnar's rule of thumb (G): expect about 6 cycles latency for fadd and
  fmul, unroll FPU code to cover it, and use the 32 registers available for
  FPU work (FP0–FP7 and E0–E23). The measured fmul latency is 5.

## Differences from AmigaOS / AROS / 68060

- The 68881/68882 are not pipelined. The 68080 FPU accepts one instruction
  per cycle, but only if enough independent chains are in flight (at least
  5 for fmul, 6 for fadd).
- The single write port is 68080 specific: instructions with different
  latencies can collide even when they are independent.

## Do / Don't

- DO benchmark latency with 1 chain and throughput with at least "latency"
  chains, and report both.
- DO schedule by completion slot, not only by dependency.
- DON'T expect FPU instructions to pair with each other: only integer
  instructions pair with them.
