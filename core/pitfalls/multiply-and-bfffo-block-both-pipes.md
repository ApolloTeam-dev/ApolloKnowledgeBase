---
title: Multiply, bfffo and FP-to-integer block both pipes
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, muls, mulu, bfffo, fmove, timing, pairing]
related:
  - core/cpu-68080/measured-instruction-costs.md
  - core/cpu-68080/prm/instruction-timing.md
  - core/best-practices/fpu-when-it-pays.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rules 7 and 10) and 3"
---

## Symptom

Multiply-heavy loops run slower than the PRM's timing predicts, and adding
independent integer work next to a multiply makes the loop longer instead of
filling a free slot.

## Cause

On Core 12841 these instructions issue in about 3 cycles each and block both
pipes, so nothing pairs with them:

- `muls.l`/`mulu.l` (32 and 64-bit), `muls.w`, `mulu.w`: 3.04–3.13 cycles,
  result usable about 3 cycles later;
- `bfffo`: 3 cycles, latency 6 when it feeds the next offset;
- `fmove.l`/`fmove.w` FP to integer: 3.08 cycles.

The PRM gives MUL = 2 or 3 cycles.

## Wrong

```asm
loop:
    muls.l  (a0)+,d1        ; 3 cycles, blocks both pipes
    addq.l  #1,d5           ; does not pair: +1 cycle
    add.l   d1,d2           ; uses the product right away
    dbra    d0,loop
```

## Right

- Count each of these as about 3 cycles that nothing pairs with; put
  independent work before or after the run of multiplies, not between.
- Use the product at least 3 cycles later.
- Consider the FPU for long multiply-accumulate chains (see
  [fpu-when-it-pays.md](../best-practices/fpu-when-it-pays.md)).
- Keep FP-to-integer conversions out of inner loops.

## Detection

Measure with CCC on a trained loop. A loop body around a `muls` that costs
the sum of its instructions instead of the longest chain points here.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| MUL = 2 or 3 cycles | (official) PRM timing page | any | Manual |
| `muls.l` 3.04–3.13 cycles with 1 or 7 chains; mul + independent op = 4.0–4.08 | (M) | Core 12841 | CCC/IEP, trained loops, best of 5 |
| `bfffo` 3 cycles, blocks both pipes | (M) | Core 12841 | Same |
| `fmove.l`/`.w` FP to integer 3.08 cycles, blocks both pipes | (M) | Core 12841 | Same |
| mul + add/addx rounding chain: 5–6 cycles per product | (M) | Core 12841 | Same |
