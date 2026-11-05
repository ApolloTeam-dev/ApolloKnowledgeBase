---
title: FPU instructions that give wrong results on Core 12841
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "Core 12001-12841"
  os: [any]
tags: [68080, fpu, fscc, ftrapcc, flognp1, fmovem, fmove, fdbcc, bugs]
related:
  - core/cpu-68080/core-bugs-by-revision.md
  - core/pitfalls/fpu-precision-and-rounding.md
  - core/cpu-68080/prm/fpu/fdbcc-l.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 4.2 (bugs first reported by Morten on Core 12001, rechecked on Core 12841)"
---

## Symptom

Some FPU instructions run without an exception but do the wrong thing: an
extension word runs as an instruction, a trap ignores the flags, a function
returns a different function, or memory operands are read partly.

## Cause

Core bugs or unsupported forms, still present on Core 12841 unless noted:

| Instruction | What happens |
|---|---|
| `FScc` to `d16(An)` or `d8(An,Xn)` | The byte is stored, then the extension word runs as an instruction. `fst 95(a0)` leaves `$005F`, which runs as `ori.b #x,(a7)+` and hangs |
| `FTRAPcc` | Ignores the FPU flags: conditions 0, 3, 4, 7, 8, A, C and F always trap (vector 7), the others never do |
| `flognp1` | Returns ln(x), not ln(1+x): `flognp1 0.5` = −0.693 |
| `fmovem.x` with a dynamic list (`fmovem.x Dn,<ea>` / `<ea>,Dn`) | Not supported (G), as on the 68060. No exception: the store writes wrong values, the load leaves the registers unchanged |
| `fmove.x` load of a 12-byte Motorola value | Ignores the low long of the mantissa: about 32 bits (1+2^−40 loads as 1.0) |
| `fmove.x` store to memory | Writes only the first 8 bytes; the third long is left untouched |
| `FDBcc` (Core 12830 and 12840 only) | Never decremented and always branched. Fixed in Core 12841 |

## Wrong

```asm
    fseq    95(a0)          ; extension word runs as an instruction
    ftrapeq                 ; trap decision ignores the compare
    fmovem.x d0,-(sp)       ; dynamic list: wrong values
    fmove.x fp0,(a1)        ; stores 8 of 12 bytes
```

## Right

- `FScc` to `Dn`, `(An)`, `(An)+` or `-(An)`, which work.
- `FBcc` instead of `FTRAPcc` (FBcc is correct).
- `fadd #1` + `flogn` instead of `flognp1` (mind the precision).
- A static register list in `fmovem`.
- `fmove.d` to exchange values with memory.
- Avoid `FDBcc` on cores before 12841.

## Detection

Search the source and the disassembly for FScc with displacement modes,
FTRAPcc, flognp1, dynamic fmovem lists and `fmove.x` memory operands.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Dynamic fmovem lists are not supported, as on the 68060 | (G) | any | Statement |
| FScc, FTRAPcc, fmove.x behaviour as in the table | (M) | Core 12001, rechecked Core 12841 | FPU test suite |
| `flognp1` returns ln(x) | (M) | Core 12841 | Found while rechecking |
| FDBcc fixed: word and long counters, all conditions | (M) | Core 12841 | FPU test suite |
