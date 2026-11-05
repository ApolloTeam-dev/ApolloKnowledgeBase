---
title: Write fusable instruction pairs back to back
type: best-practice
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fusing, 3-operand, quad-move]
related:
  - core/cpu-68080/prm/instruction-fusing.md
  - core/cpu-68080/superscalar-issue.md
  - core/pitfalls/fused-copy-overlap.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 2.4"
---

## Goal

Speed: two instructions that fuse behave as one. A copy plus an operation
becomes one 3-operand instruction; two long moves become one quad move.

## Technique

Write the pair adjacent, in the order of the PRM's fusing table
([prm/instruction-fusing.md](../cpu-68080/prm/instruction-fusing.md)).
Write the copy and then the operation naturally, without trying to avoid the
copy.

```asm
    move.l  d0,d2           ; copy ...
    add.l   d1,d2           ; ... and operate: fuses to add.l d1,d0,d2

    move.l  (a0)+,(a1)+     ; two long moves ...
    move.l  (a0)+,(a1)+     ; ... fuse to one quad move

    moveq   #0,d3
    move.b  (a2),d3         ; fuses to a zero-extending byte load
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| 16 x (`move.l dn,dm` + `add.l`), split apart | 9.1 cycles | Core 12841 | CCC (M) |
| Same, adjacent | 5.1 cycles | Core 12841 | Same |
| Same with E registers, adjacent | 1 pair per cycle | Core 12841 | Same |
| `fmove.x` + `fmul.x`, independent pairs, split / adjacent | 2.25 / 1.12 cycles per pair | Core 12841 | fpu3 test (M) |

## When not to use

- Fused `move.l (an)+,(am)+` pairs read 8 bytes before writing: never use
  them for a forward copy whose destination is less than 8 bytes ahead of the
  source. See [fused-copy-overlap.md](../pitfalls/fused-copy-overlap.md).
- `subq.l #1,dn` + `bpl` does not fuse; `fsub` does not fuse.
- Fused FPU pairs count as 2 instructions in IEP1/IEP2: measure them with
  CCC.
