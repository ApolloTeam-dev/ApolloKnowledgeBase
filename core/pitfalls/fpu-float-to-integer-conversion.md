---
title: FP-to-integer conversion rounds wrongly except in RZ mode
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12830-12841"
  os: [any]
tags: [68080, fpu, fmove, rounding, conversion, fpcr]
related:
  - core/cpu-68080/prm/fpu/fmove-dn.md
  - core/cpu-68080/prm/fpu/fmoverz.md
  - core/pitfalls/multiply-and-bfffo-block-both-pipes.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 4.2"
---

## Symptom

`fmove.l` from FP to an integer gives off-by-one results in round-to-nearest,
round-down and round-up modes: 4678528.501 becomes 4678528 in RN, −0.1
becomes 0 in RM, 0.1 becomes 0 in RP.

## Cause

`fmove.l` decides the rounding from only the 2 bits below the binary point;
the sticky bit is lost. RZ (round toward zero) is always right, and exact
integers always convert right.

Related behaviour:

- `fmove.w` FP to integer follows the FPCR rounding mode correctly (RN
  half-even, RZ, RM, RP) and **saturates** to 32767/−32768 without OPERR.
- `fmoveurz.l` of 3000000000.75 gives `$FFFFFFFF`.
- `fmoverz`/`fmoveurz` do not exist on the V2.
- Default task FPCR seen: `$0` or `$10`.

## Wrong

```asm
    fmove.l #0,fpcr         ; RN
    fmove.l fp0,d0          ; 4678528.501 -> 4678528
```

## Right

```asm
    fmove.l #$10,fpcr       ; RZ: always correct (floor for positive values)
    fmove.l fp0,d0
```

- Convert values that have a fraction only in RZ mode. For round-to-nearest,
  add 0.5 first (positive values) and convert in RZ.
- For 16-bit PCM output, `fmove.w` with FPCR = 0 (RN) is correct and
  saturates: handy, and set FPCR explicitly around the routine.
- Set FPCR explicitly when your routine depends on it; don't rely on the task
  default.

## Detection

Test conversions of values just above .5 and small negative and positive
fractions in each rounding mode.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| RN 4678528.501 → 4678528; RM −0.1 → 0; RP 0.1 → 0; RZ always right | (M) | Core 12830-12841 | Conversion tests |
| `fmove.w` follows FPCR and saturates without OPERR | (M) | Core 12830-12841 | Same |
| `fmoveurz.l` 3000000000.75 → `$FFFFFFFF` | (M) | Core 12830-12841 | Same |
