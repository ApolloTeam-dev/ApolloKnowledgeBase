---
title: FPU values above 47 bits change at task switches
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12830-12841"
  os: [any]
tags: [68080, fpu, fmovem, context-switch, precision, double]
related:
  - core/cpu-68080/prm/fpu/fmovem.md
  - core/best-practices/fpu-when-it-pays.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 11) and 4.2"
  - "Gunnar (core developer), new FMOVEM encoding, 2026-10-30"
---

## Symptom

Doubles with 48 to 53 significant bits change at random while a program
runs: rarely, and only when interrupts or task switches happen in between.
Exact integer arithmetic in doubles and the `x + 1.5*2^52` floor trick give
occasional wrong results.

## Cause

Task switches and interrupts save the FP registers with `fmovem.x`, which
stores the Apollo extended format: about 48 mantissa bits. Values that need
more bits lose them when the registers are restored. The PRM documents the
Apollo extended layout ([prm/fpu/fmovem.md](../cpu-68080/prm/fpu/fmovem.md)).

## Wrong

```asm
    ; floor() by adding 1.5 * 2^52: relies on all 53 bits surviving
    fadd.d  #6755399441055744.0,fp0
    fsub.d  #6755399441055744.0,fp0
```

## Right

- Keep exact integer arithmetic in doubles at 47 significant bits or less.
- Don't use the `1.5*2^52` trick; convert with `fmove.l` in RZ mode instead
  (see [fpu-float-to-integer-conversion.md](fpu-float-to-integer-conversion.md)).
- Exchange values through memory with `fmove.d`, which keeps all bits.

Gunnar (G, 2026-10-30): a new `FMOVEM` in the 3-operand encoding will save
and restore all 32 FPU registers in 64 bits, and only that one is to be used
in the future. The PRM says newer cores will use the normal extended format.

## Detection

Run the code under load (other tasks, interrupts) for millions of iterations
and compare with a reference. Check every double that must hold more than 47
significant bits.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Apollo extended format in memory differs from Motorola's | (official) PRM, FMOVEM page | any | Manual |
| About 3150 changed values per 20 M checks in a busy loop; values of 47 bits or less never change | (M) | Core 12830-12841 | Busy-loop check |
| New 64-bit FMOVEM in the 3-operand encoding planned | (G, 2026-10-30) | Future core | Statement |
