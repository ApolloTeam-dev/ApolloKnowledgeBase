---
title: vasm -m68080 turns absolute destinations into PC-relative ones
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, official, source-code]
components: [toolchain, cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [vasm, pc-relative, optimization, memory-corruption, 68080]
related:
  - core/pitfalls/pc-relative-destination.md
  - toolchain/vasm-assembler.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 22) and 9.4"
  - "ApolloCrossDev Compilers/_archives/vasm/vasm.tar.tar: vasm 2.0f"
---

## Symptom

Silent memory corruption in assembly code that writes to a label: the write
lands at the wrong address. The source looks correct, because the label is
written as an absolute address.

## Cause

- With `-m68080`, vasm optimizes an absolute destination `move.x <src>,label`
  into a PC-relative destination `label(pc)` by default. It does the same
  for addq/subq, bchg/bclr/bset, eor, fmove and AMMX stores.
- The 68080 computes a PC-relative destination wrongly when the source uses
  the full extension format (for example `(table.l,d0.w)` or memory
  indirect). See [core/pitfalls/pc-relative-destination.md](../../core/pitfalls/pc-relative-destination.md).
- This optimization is on by default; `-opt-speed` is not what causes it.
  `-nodpc` and `opt` directives do not turn it off; only `-no-opt` does.
- ApolloCrossDev ships vasm 2.0f (SRC), which has this behaviour (M). The
  vasm author has been informed; a fix will come in a future ApolloCrossDev
  update.

## Wrong

```asm
    move.b  (table.l,d0.w),result   ; vasm -m68080 emits result(pc): miscomputed
```

## Right

Address the destination through a register in code that combines a
full-format source with a label destination:

```asm
    lea     result,a1
    move.b  (table.l,d0.w),(a1)
```

Or assemble that file with `-no-opt`. That turns off **all** vasm
optimizations (also `moveq` for `move.l #imm` and branch-size choices), so
optimize those by hand.

## Detection

Assemble with a listing (`-L file.lst`) and look for MOVE and the other
instructions above with destination mode 7/2 (`d16(pc)`) and a full-format
source operand.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| PC-relative destination is not calculated correctly with some extended source formats | (official) PRM, integer unit page | any | Manual |
| vasm `-m68080` makes `(d16,PC)` destinations by default; only `-no-opt` stops it | (M) | any | vasm 2.0f/2.0g listings |
| The fix belongs in vasm `cpu.c`: `APOLLO_PCDEST` misses operand types DN/MA/MI/BS/CT | (SRC) | any | vasm source |
| ApolloCrossDev ships vasm 2.0f | (SRC) | any | `vasm.c`: `_VER "vasm 2.0f"` |
