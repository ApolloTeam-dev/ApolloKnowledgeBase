---
title: FPU exceptions never trap and FPSR exception bytes stay 0
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fpu, exceptions, fpsr, fpcr, divide-by-zero]
related:
  - core/pitfalls/fpu-broken-instructions.md
  - core/pitfalls/fpu-precision-and-rounding.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 4.2"
---

## Symptom

Code that enables FPU exception traps in FPCR (DZ, OPERR, INEX2) never sees
a trap, and code that checks the FPSR exception or accrued bytes never sees
an error.

## Cause

On Core 12841 FPU exceptions never trap, even with the FPCR enable bits set.
In FPSR, only the condition byte (N, Z, I, NAN) is ever set. The exception
byte, the accrued byte and the `fmod`/`frem` quotient byte stay 0. There is
no packed decimal format either.

## Wrong

```asm
    fmove.l #$00000400,fpcr ; enable divide-by-zero trap
    fdiv.x  fp1,fp0         ; fp1 = 0: no trap
    fmove.l fpsr,d0
    btst    #4,d0           ; accrued DZ: always 0
```

## Right

Test the result itself with `fcmp`/`ftst` + `FBcc`:

```asm
    fdiv.x  fp1,fp0
    fbun.w  .nan            ; NAN result (condition byte NAN bit)
    fmove.l fpsr,d0
    btst    #25,d0          ; condition byte I bit: result is infinity
    bne.s   .inf
```

## Detection

Search for writes to FPCR enable bits, FPSR exception or accrued byte tests,
and uses of the `fmod`/`frem` quotient byte.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| DZ, OPERR and INEX2 traps never taken with the FPCR enable bits set | (M) | Core 12841 | FPU test suite |
| Only the FPSR condition byte is ever set | (M) | Core 12841 | Same |
