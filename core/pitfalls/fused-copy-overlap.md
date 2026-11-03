---
title: Fused quad moves break overlapping forward copies
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fusing, copy, overlap, memmove]
related:
  - core/best-practices/use-fusable-pairs.md
  - core/cpu-68080/prm/instruction-fusing.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 24) and 2.4"
---

## Symptom

A forward copy whose destination is less than 8 bytes ahead of its source
(for example the `dst = src + 4` "replicate" trick) gives wrong data once the
loop is trained: L0, L0, L1 instead of L0, L0, L0. The first, cold pass is
correct, which makes the bug hard to see.

## Cause

Two fused `move.l (an)+,(am)+` act as one quad move: they read both longs
(8 bytes) before writing (G: by design). On the cold pass the instructions do
not fuse yet, so the result differs between the first and later passes.

## Wrong

```asm
    lea     4(a0),a1        ; destination 4 bytes ahead: replicate the first long
loop:
    move.l  (a0)+,(a1)+
    move.l  (a0)+,(a1)+     ; fuses: reads 8 bytes before writing
    dbra    d0,loop
```

## Right

- Copy backwards, or keep source and destination at least 8 bytes apart.
- To replicate a value, load it into a register once and store it.

```asm
    move.l  (a0),d1
loop:
    move.l  d1,(a1)+
    move.l  d1,(a1)+        ; fuses to a quad store
    dbra    d0,loop
```

## Detection

Look for memmove-style or replicate copies with a forward distance under 8
bytes. Test copies over more than one pass: the cold pass hides the bug.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Fused `move.l (an)+,(am)+` pairs read 8 bytes before writing, by design | (G) | Core 12841 | Statement |
| `dst = src + 4` gives L0,L0,L1 trained, L0,L0,L0 cold | (M) | Core 12841 | Loop test, cold vs trained pass |
