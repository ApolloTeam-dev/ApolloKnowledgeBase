---
title: A branch that alternates every iteration is always mispredicted
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, branches, prediction, misprediction]
related:
  - core/cpu-68080/branches-and-prediction.md
  - core/best-practices/predicated-bcc-over-one-instruction.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 5) and 2.6"
---

## Symptom

A loop with a branch that goes taken, not taken, taken, not taken runs
slower than the same loop with random branch directions: about 7 extra
cycles per iteration.

## Cause

The 68080 branch predictor does not learn a strict alternation: it
mispredicts it every time. A mispredicted Bcc costs about 7 cycles.

Loop benchmarks hide a related problem: a size-dispatch branch is
unpredictable when the sizes in real use are random, but predictable in a
benchmark with a fixed size.

## Wrong

```asm
loop:
    btst    #0,d7           ; flips every iteration
    beq.s   .even
    ; ... odd case, more than one instruction ...
    bra.s   .next
.even:
    ; ... even case ...
.next:
    dbra    d7,loop
```

## Right

- Unroll by 2, so each copy handles one case without a branch.
- Or compute the value without a branch.
- Or, if one case is a single short single-cycle instruction, use a
  predicated `bcc.s` over it (see
  [predicated-bcc-over-one-instruction.md](../best-practices/predicated-bcc-over-one-instruction.md)).

## Detection

Look for branches on a loop counter bit or on toggling state. Benchmark
dispatch code with random sizes, and pull the small cases out first.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Alternating pattern: 10.5 cycles per turn vs 3.0 always taken, 7.0 random | (M) | Core 12841 | `beq` over 2 instructions, 65536 branches, CCC, median of 7 |
| Mispredicted Bcc costs about 7 cycles | (M) | Core 12841 | Same |
