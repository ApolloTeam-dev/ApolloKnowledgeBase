---
title: Mixed float settings and hidden soft-float break programs and libraries
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [amigaos-3.9, amigaos-3.2]
tags: [gcc, soft-float, hard-float, m68881, libnix, printf, nostartfiles]
related:
  - toolchain/c-compiler-options.md
  - toolchain/best-practices/gcc-code-generation-for-68080.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rules 19 and 21) and 9.1-9.2"
  - "WDrijver/gcc, gcc/config/m68k/m68k.c (branch gcc-6-base-amiga): no 680x0 CPU option sets FL_68881 for the AmigaOS target"
---

## Symptom

- `printf` prints garbage for doubles, while the calculations are right.
- A library built with `-nostartfiles` crashes (CHK error) on some inputs
  only, for example when a ReplayGain value has to be computed.
- C code with floats runs slowly although it targets the 68080.

## Cause

- For the AmigaOS target, `-m68080` alone does **not** turn on the FPU: no
  680x0 CPU option does (SRC). Hardware floating point comes from `-m68881`
  (M: on Core 12556 a float loop built with `-m68080 -m68881` ran 7.9
  times faster than with `-m68080` alone). `-m68080`
  alone compiles float work into calls such as `__floatsisf` (M).
- Objects built with different float settings, linked together (for example
  `-m68080` objects with a libnix `printf` built for the other setting), pass
  doubles in a way the other side does not expect.
- Any `double` or `exp()` in a `-nostartfiles` library pulls in `__divdf3`
  and friends, which call mathieeedoub* libraries through a base that was
  never opened.

## Wrong

```sh
m68k-amigaos-gcc -noixemul -O2 -m68080 -c lib.c         # soft-float
m68k-amigaos-gcc -noixemul -O2 -m68080 -m68881 -c app.c  # hard float
m68k-amigaos-gcc lib.o app.o -noixemul -o app            # mixed
```

## Right

- Compile **and** link everything with the same flags, including `-m68881`:
  the standard set is in [c-compiler-options.md](../c-compiler-options.md).
- A program built for soft-float on purpose links with `-lm`: libnix keeps
  `__mulsf3` and the other soft-float routines in its `libm` (M).
- Keep library code (`-nostartfiles`) integer (fixed point), and check its
  objects for soft-float symbols.
- Write FPU kernels in assembler when you need full control over the FPU
  code.

## Detection

- `m68k-amigaos-nm *.o | grep -E '__(add|sub|mul|div)[sd]f3|__floatsi|__fix'`
  lists objects that use soft-float.
- Compile one float function with `-S` and check for `fmul`/`fadd` instead
  of calls.

CI checks both cases on every run. With the standard flags
(`-m68080 -m68881`) GCC emits an FPU multiply:

```c
// kb:compile
// kb:expect fsmul.s
// kb:expect-not ___mulsf3
float scale(float a, float b) { return a * b; }
```

With `-m68080` alone it calls the soft-float routine:

```c
// kb:compile
// kb:opts -O2 -m68080 -ffast-math -fomit-frame-pointer
// kb:expect ___mulsf3
// kb:expect-not fsmul
float scale(float a, float b) { return a * b; }
```

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `-m68080` emits no FPU instructions | (M) | any | Project builds |
| No 680x0 CPU option sets the FPU flag for AmigaOS; `-m68881` sets hard float explicitly | (SRC) | any | GCC source, `m68k.c` |
| `-m68080` objects with libnix `printf` printed garbage doubles | (M) | any | MP3 project |
| Soft-float in a `-nostartfiles` library crashed with a CHK error | (M) | any | MP3 library, ReplayGain path |
| `-m68080 -m68881` runs FPU code on a V4: 8 cycles per element of a float dot product, 63 with `-m68080` alone | (M) | Core 12556 | `tools/v4/tests/fpu-m68881`, V4 UniCorn, 3 alternating rounds, 2026-11-09 |
