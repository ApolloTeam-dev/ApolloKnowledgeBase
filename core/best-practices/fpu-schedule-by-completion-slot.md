---
title: Schedule FPU code by completion slot
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fpu, scheduling, mac, latency]
related:
  - core/cpu-68080/fpu-performance-model.md
  - core/best-practices/fpu-when-it-pays.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rules 8-9) and 4.1"
---

## Goal

Speed: one FPU instruction per cycle. The FPU is pipelined, but it has one
result-write port and needs enough independent chains in flight.

## Technique

- Keep at least 5 independent chains for fmul and 6 for fadd (their
  latencies).
- Schedule by completion slot (issue cycle + latency): two instructions that
  would finish in the same cycle collide, and the second stalls.
  Alternating fmul/fadd costs 1.5 cycles per instruction.
- Mix in loads and stores: `fmove.s`/`.d` stores write no FP register and
  never collide; patterns LMA, ALM and MAL run at 1.0 cycle per instruction.
- For a multiply-accumulate, use this term order:

```asm
    fmove.s (a0)+,fp1       ; coefficient
    fmul.s  (a1)+,fp1       ; times sample
    fadd.x  fp1,fp0         ; accumulate
```

- Let integer work run alongside: integer instructions pair with FPU
  instructions in pipe 2 for free.

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| MAC term, best order (above) | 3.13 cycles per term | Core 12841 | CCC, 25 patterns fitted (M) |
| MAC term, other orders | 3.5–4.5 | Core 12841 | Same |
| MAC term with an integer operand (`fmove.l`/`fmul.l`) | 4.0–5.1 | Core 12841 | Same |
| Integer MAC (`muls.l` + add/addx) | 4.27 (floor 4.0) | Core 12841 | Same |
| 24 fmul + 24 add.l | 26 cycles | Core 12841 | Same |

Gunnar's rule (G): a pipelined unit that shows more than 1 cycle per
instruction has a wrong schedule.

## When not to use

- A greedy list scheduler on the FPU model did worse than a hand-designed
  modulo rhythm (2222 vs 1644 cycles, M). Use the model to check a schedule,
  not only to search for one.
- With only 8 FP registers and 2-address code, wide schedules spill: a
  32-point DCT on the FPU lost to integer code.
