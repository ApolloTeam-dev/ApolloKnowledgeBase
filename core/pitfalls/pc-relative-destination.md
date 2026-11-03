---
title: PC-relative destinations are miscomputed after a full-extension source
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080, toolchain]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, pc-relative, addressing, memory-corruption, vasm]
related:
  - core/cpu-68080/prm/integer-unit.md
  - core/cpu-68080/isa-notes-measured.md
  - toolchain/vasm-assembler.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 22), 7.2 and 9.4"
---

## Symptom

Silent memory corruption: a write meant for a variable lands somewhere else.
It happens only in instructions that combine a full-extension-format source
with a PC-relative destination.

## Cause

The 68080 allows PC-relative addressing for destinations (the 68000–68060
only for sources). The PC used is the address of the destination's extension
word, and it is computed wrongly when the source uses the full extension
format, for example `(table.l,d0.w)` or memory indirect.

vasm with `-m68080` makes such destinations by itself: it rewrites an
absolute destination `move.x <src>,label` into `label(pc)` by default (also
for addq/subq, bchg/bclr/bset, eor, fmove and AMMX stores). The
toolchain side is described in [toolchain/vasm-assembler.md](../../toolchain/vasm-assembler.md).

## Wrong

```asm
    move.b  (table.l,d0.w),result(pc)   ; destination miscomputed
    ; or, written with an absolute destination, rewritten by vasm -m68080:
    move.b  (table.l,d0.w),result
```

## Right

Address the destination through a register:

```asm
    lea     result(pc),a1
    move.b  (table.l,d0.w),(a1)
```

Or assemble the file with vasm `-no-opt` (this disables all vasm
optimizations).

## Detection

Scan the assembler listing for MOVE (and the other instructions above) with
destination mode 7/2 (`d16(pc)`) and a full-format source.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| PC-relative destination is not calculated correctly with some extended source formats | (official) PRM, integer unit page | any | Manual |
| Miscomputed after a full-extension source; silent corruption | (M) | Core 12841 | Test program |
| vasm `-m68080` creates `(d16,PC)` destinations by default; `-nodpc` and `opt` don't stop it, `-no-opt` does | (M) | any | vasm 2.0f/2.0g listings |
