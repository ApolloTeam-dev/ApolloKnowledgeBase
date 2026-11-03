---
title: Close loops with dbra or subq + bne.s
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, loops, dbra, branches, fusing]
related:
  - core/cpu-68080/branches-and-prediction.md
  - core/best-practices/code-size-and-placement.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 4), 2.4 and 5.3"
---

## Goal

Speed: loop overhead of 1 cycle instead of 3.

## Technique

Close loops with `dbra`, or with `subq.l #1,Dn` followed directly by
`bne.s`, which fuse into one dbra-like instruction. A `bne.w` is not an
accelerated branch.

```asm
loop:
    ; ... body ...
    dbra    d0,loop         ; 16-bit counter

; or, for a 32-bit counter:
loop2:
    ; ... body ...
    subq.l  #1,d1
    bne.s   loop2           ; fuses with the subq
```

A counter that drives addressing can live in An, so it does not hit the
ALU-to-EA bubble:

```asm
loop3:
    ; ... body ...
    subq.l  #1,a6           ; EA unit, no flags
    move.l  a6,d0           ; sets N/Z, no write back
    bne.s   loop3
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Loop closed with a `bne.w` that does not fuse | 3 cycles overhead | Core 12841 | CCC counter (M) |
| Loop closed with `dbra` or `subq.l` + `bne.s` | 1 cycle overhead | Core 12841 | Same |

`subq.l #1,dn` + `bne.s/.s+/.w` fuses; `subq` + `bpl` does not (M). Gunnar:
"DBRA is fast and nearly free" (G).

## When not to use

- Very short loops (1–4 turns) are expensive whatever the closing branch: one
  turn cost about 12 cycles, each extra turn 3 (M). Special-case them.
