---
title: GCC 6.5 crashes on sinf and cosf of the same value with -ffast-math
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, fpu, fsincos, fast-math, ice]
related:
  - toolchain/compiler-variants.md
  - toolchain/c-compiler-options.md
sources:
  - "github.com/WDrijver/ApolloCrossDev pull request #8 (merged on 2026-11-03)"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh (2026-11-03)"
---

## Symptom

The compiler stops with:

```text
internal compiler error: in print_operand_address2, at config/m68k/m68k.c:5457
```

It shows with `-m68881 -ffast-math` on 68020, 68030 and 68080 targets, when
a function computes `sinf(x)` and `cosf(x)` of the same value under some
register pressure. 68040 and 68060 targets don't hit it: GCC does not use
`fsincos` for them.

## Cause

In `m68k.md`, the input operand of `sincos<mode>2_68881` has an empty
constraint. When the pointer in its address gets no hard register, the
operand becomes a memory-indirect address that the backend rejects.

The fix, `m68k-sincos-constraint-fix.patch` from ApolloCrossDev pull
request #8, was merged on 2026-11-03. Only GCC-6.50-Dev applies it. It
changes no code that compiled before: 69 C files with 3 flag sets gave
byte-identical assembly.

## Wrong

```c
float fx = sinf(w->heading), fy = -cosf(w->heading);   /* ICE with -ffast-math */
```

## Right

Use GCC-6.50-Dev installed on or after 2026-11-03. With another variant,
compiling the affected file without `-ffast-math` should avoid the `fsincos`
pattern (not yet tested).

## Detection

The ICE above, with `-m68881 -ffast-math` in the flags.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| ICE before the fix, builds with it | (M) | any | Failing project file and a 30-line reproducer, rebuilt cc1 |
| No other code change | (M) | any | 69 C files x 3 flag sets, byte-identical assembly |
