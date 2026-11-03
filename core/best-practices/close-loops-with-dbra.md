---
title: Close loops with dbra, and dbra.l for 32-bit counters
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
  - core/cpu-68080/prm/integer/dbcc-l.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 4), 2.4 and 5.3"
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03), coding rules 4, 6 and 7"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
---

## Goal

Speed: loop overhead of 1 cycle instead of 3. "Loops can often be free, or
very low cost" (G).

## Technique

`dbra` is the best loop instruction (G). Use `dbra` for a 16-bit counter and
the 080 encoding `dbra.l` for a 32-bit counter (see
[prm/integer/dbcc-l.md](../cpu-68080/prm/integer/dbcc-l.md)). A
`bne.w` is not an accelerated branch.

A good general-purpose loop (G):

```asm
    bra.s   .start
.loop:
    ; ... body ...
.start:
    dbra.l  d0,.loop
```

Keep the loop counter in a data register and pointers in address registers.
Then the EA unit updates the pointer and the ALU runs the loop, independently
of each other (G):

```asm
.loop:
    clr.l   (a0)+           ; EA unit updates the pointer
    dbra.l  d0,.loop        ; ALU does the loop
```

When the loop needs an index, keep it in an address register and step it
with an EA instruction, so it does not hit the
[ALU-to-EA bubble](../pitfalls/alu-to-ea-bubble.md):

```asm
.loop:
    move.l  (a0,a1.l),d1    ; index in a1: no bubble
    addq.l  #4,a1           ; EA unit
    add.l   d1,d2
    dbra.l  d0,.loop
```

Gunnar does not recommend closing loops with `subq.l #1,Dn` + `bne` (G,
2026-11-03). One reason is the loop size limit: a short branch reaches at
most 256 bytes back (`bcc.s+`), while `dbra` has a 16-bit displacement.

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Loop closed with a `bne.w` that does not fuse | 3 cycles overhead | Core 12841 | CCC counter (M) |
| Loop closed with `dbra` or `subq.l` + `bne.s` | 1 cycle overhead | Core 12841 | Same |
| `subq.l` + `bne` | Not recommended, partly for the loop size limit | any | Statement (G, 2026-11-03) |

`subq.l #1,dn` + `bne.s/.s+/.w` fuses; `subq` + `bpl` does not (M). Gunnar:
"DBRA is fast and nearly free" (G).

## When not to use

- Very short loops (1–4 turns) are expensive whatever the closing branch: one
  turn cost about 12 cycles, each extra turn 3 (M). Special-case them.
