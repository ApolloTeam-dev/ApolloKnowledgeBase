---
title: TOUCH slows sequential streams, and only one form is valid
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, touch, prefetch, cache, encoding]
related:
  - core/cpu-68080/prm/integer/touch.md
  - core/best-practices/memory-access-patterns.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 5.2 and 12"
---

## Symptom

- A loop with `touch` on a sequential stream takes twice as long.
- A program crashes after a `touch` with a full extension word, or a
  `touch (An)` writes memory.

## Cause

- The CPU already prefetches sequential streams; `touch` only adds work.
- The only valid form is the 2-word `(An,Xn)` brief extension (G). A
  full-extension form is decoded as 2 words, so the next word runs as an
  instruction.
- The PRM's `touch (An)` encoding (`$F61x`) is `move16 (An),abs.l` (M).

## Wrong

```asm
loop:
    touch   64(a0,d1.l)     ; on a sequential stream: 2x slower
    move.l  (a0)+,d2
    ; ...
```

## Right

Use `touch d8(An,Dn)` only for random accesses, about 12–15 cycles before the
data is needed:

```asm
    touch   0(a1,d1.l)      ; random lookup, issued early
    ; ... 12-15 cycles of other work ...
    move.b  0(a1,d1.l),d2
```

## Detection

Search for `touch` in loops that walk memory with `(An)+` or a fixed stride,
and for `touch (An)` or full-extension `touch` forms.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Only mode 6, brief extension, no multiplier | (official) PRM, TOUCH page | any | Manual |
| Only the 2-word `(An,Xn)` brief extension is valid | (G) | Core 12841 | Statement |
| `touch` on a sequential stream doubles the cycles | (M) | Core 12841 | CCC |
| `$F61x` (`touch (An)` in the PRM) is `move16 (An),abs.l` | (M) | Core 12841 | Test program |
| A full-extension form runs the next word as an instruction (crash) | (M) | Core 12841 | Test program |
