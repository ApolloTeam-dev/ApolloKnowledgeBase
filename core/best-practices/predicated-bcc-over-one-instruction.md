---
title: Use bcc.s over one instruction as a conditional instruction
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, branches, predication, conditional]
related:
  - core/cpu-68080/branches-and-prediction.md
  - core/cpu-68080/prm/optimizing.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 5) and 2.6"
---

## Goal

Speed: a conditional operation that is never mispredicted, at the cost of a
correctly predicted branch.

## Technique

Branch with `bcc.s` over exactly one instruction. The 68080 executes the pair
as a conditional instruction when the skipped instruction:

- is at most 8 bytes long;
- is single-cycle;
- does not change an An (so not `(An)+`, `-(An)`, `addq An` or `lea`).

```asm
    cmp.l   d1,d0
    bge.s   .skip
    move.l  d1,d0           ; executed only when d0 < d1
.skip:
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| `beq.s`/`beq.w` over 2 instructions, random pattern | 7.0 cycles per turn | Core 12841 | 65536 branches, CCC, median of 7 (M) |
| `beq.w`/`beq.s` over 2 instructions, alternating | 10.5 | Core 12841 | Same |
| `beq.s` over 1 instruction, any pattern | 3.0 | Core 12841 | Same |
| No branch | 2.0 | Core 12841 | Same |

## When not to use

- When the skipped code is more than one instruction, or changes an An: then
  it is an ordinary branch and can be mispredicted.
- Don't insert other instructions between the `bcc.s` and the skipped
  instruction when you interleave code. An FPU instruction placed there made
  the branch land inside it ("CHK instruction error") (M).
- Don't replace the pattern with Scc + mask: the predicated branch is as fast
  and simpler.
