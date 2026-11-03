---
title: Interleave two independent dependency chains
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, superscalar, scheduling, crc, sha256]
related:
  - core/cpu-68080/superscalar-issue.md
  - core/cpu-68080/pipeline-15-stages.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 6) and 11"
---

## Goal

Speed: keep both pipes busy. A group of instructions only issues when all its
input registers are ready, so a single dependency chain leaves the second
pipe idle.

## Technique

Split the work into two independent chains (two blocks, two halves of a
buffer, two lanes of a hash) and interleave their instructions, so that each
instruction pairs with one from the other chain.

```asm
; Two independent accumulators instead of one chain
loop:
    move.l  (a0)+,d1        ; chain A
    move.l  (a1)+,d2        ; chain B
    add.l   d1,d3           ; chain A
    add.l   d2,d4           ; chain B
    dbra    d0,loop
    add.l   d4,d3           ; combine at the end
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| CRC, one chain | 178 cycles | Core 12841 | CCC counter, trained loop (M) |
| CRC, two interleaved chains | 89 cycles | Core 12841 | Same |
| SHA-256, one chain | 660 cycles | Core 12841 | Same |
| SHA-256, two interleaved chains | 464 cycles | Core 12841 | Same |

This was the biggest single win in the guide's projects.

## When not to use

- When the loop is already issue-bound (every slot filled), software
  pipelining or interleaving gains nothing: it did not help BlitTemplate,
  Huffman or Rice decoding (M).
- When the second chain needs extra registers that force spills to memory.
