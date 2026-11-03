---
title: 32-bit writes can clear the upper half of a 64-bit register
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, ammx, e-registers, 64-bit, move, moveq, bug]
related:
  - core/cpu-68080/prm/programming-model.md
  - core/cpu-68080/bank-prefix.md
  - core/cpu-68080/core-bugs-by-revision.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 6"
  - "Gunnar (core developer), move.l must keep the upper 32 bits, 2026-10-30"
---

## Symptom

An AMMX operation on a D or E register that was last written with
`move.l #imm` sees zeros in the upper 32 bits, but only on trained passes of
a loop.

## Cause

`move.l` must keep the upper 32 bits of a D or E register untouched (G,
2026-10-30). On Core 12841:

- `move.l Dn,Dn` and `move.l (An),Dn` keep them;
- `move.l #imm` (D or E register) clears them on trained passes (bug,
  regression test "test-upper");
- `moveq`, `ext.l` and `extb.l` behave like `move.l #imm`, and a banked
  `moveq` changes from pass to pass;
- `clr.l` always keeps them.

Whether `moveq`, `ext` and `clr` should follow the `move.l` rule has been
asked of the core developer.

## Wrong

```asm
    load.w  #$1111,e0               ; e0 = $1111111111111111
    move.l  #$22222222,e0           ; upper half may become 0 when trained
    paddw   e0,d1,d2                ; uses all 64 bits
```

## Right

Write all 64 bits with an AMMX instruction (`load`, `peor`, or another AMMX
op) before any 64-bit use, and don't rely on a 32-bit write leaving the upper
half alone.

## Detection

Look for 32-bit writes (`move.l #imm`, `moveq`, `ext.l`, `extb.l`) to
registers that AMMX code later reads as 64 bits. Test over several passes:
the cold pass hides the bug.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `move.l` must keep the upper 32 bits | (G, 2026-10-30) | any | Statement |
| `move.l #imm`, `moveq`, `ext.l`, `extb.l` clear them on trained passes; `clr.l` keeps them | (M) | Core 12841 | Regression test "test-upper" |
