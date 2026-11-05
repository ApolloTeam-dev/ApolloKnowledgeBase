---
title: 68080 FPU precision and rounding differ from the 6888x
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fpu, precision, rounding, fdiv, fsqrt, transcendental]
related:
  - core/cpu-68080/prm/fpu-unit.md
  - core/pitfalls/fpu-float-to-integer-conversion.md
  - core/pitfalls/fpu-broken-instructions.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 4.2"
  - "Gunnar (core developer), FPU precision targets, 2026-10-30"
---

## Symptom

Floating-point results differ from a 68881/68882 or from C on another
platform: transcendentals are accurate to about 32 bits, `fdiv` and `fsqrt`
to about 33–42 bits, `fadd` is 1 ulp low, single-precision instructions
return double results, and `fint` rounds ties away from zero.

## Cause

Precision is a design choice (G, 2026-10-30): most games need 23 bits, and
more precision costs cycles and FPGA space. The targets are full 64 bits on
`fmul` and `fadd`, and about 40 bits on `fsqrt` and `fdiv`. Measured on Core
12841:

| Operation | Behaviour |
|---|---|
| `fmul` | Correctly rounded |
| `fadd` | Rounds toward zero: 1 ulp low when the exact sum needs rounding up (0.1 + 0.2 = `...3333`, not `...3334`). Asked whether intended |
| FPU arithmetic and `fmove.s` stores | Truncate, whatever the FPCR mode. `fmove.s` differs from C round-to-nearest by 1 ulp |
| `fdiv` | 40.6–41.8 good bits (1/3 = `$3FD5555555555000`, about 1400 ulp) |
| `fsqrt` | 32.6–36.4 good bits (sqrt 2 = `$3FF6A09E66800000`); exact squares are exact |
| Transcendentals (fsin, fcos, ftan, fasin, facos, fatan, fsinh, fcosh, ftanh, fatanh, fetox, ftwotox, ftentox, flogn, flog10, flog2) | About 31–33 good bits (10^5 to 4x10^6 ulp) on ordinary arguments; only tiny arguments come out exact |
| FPCR rounding precision, and `fs*`/`fd*` (`fsmove`, `fsmul`, `fsadd`, `fsdiv`, `fssqrt`) | Ignored: all return the double result |
| `fint` in RN | Ties away from zero: 2.5 → 3, −2.5 → −3, 0.5 → 1 (68881: 2, −2, 0) |
| `fmovecr` | Within 1 ulp, truncated. 1e512 to 1e4096 (`$3C`–`$3F`) give +inf: they do not fit in a double |
| Older cores (official) | Older V4 cores use 11 nibbles of fraction; V2 core 2.17 about 8 |

## Wrong

```asm
    fmove.d #2.0,fp0
    fsqrt.x fp0             ; assumes 53 correct bits
    fsmul.x fp1,fp0         ; assumes single-precision rounding
```

## Right

- Add a Newton step after `fsqrt`/`fdiv` when you need more than about 33/40
  bits.
- Use your own polynomial or table for transcendentals when you need 53
  bits.
- Round to single with an `fmove.s` store and reload.
- Use your own rounding when `fint` ties matter.
- Discuss precision requirements with the Apollo team (G).

## Detection

Compare results with a reference implementation on the full input range, in
ulp. Check code that relies on exact rounding (interval arithmetic, financial
code, bit-exact codecs).

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Precision targets: 64 bits on fmul/fadd, about 40 on fsqrt/fdiv | (G, 2026-10-30) | Core 12841 | Statement |
| The values in the table above | (M) | Core 12841 | FPU test suite, against reference values |
| Older V4 cores 11 nibbles fraction, V2 2.17 about 8 | (official) PRM, FPU unit page | Older cores | Manual |
