---
title: Struct-returning calls into ApolloOS stack-call libraries corrupt the library base
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [libraries, toolchain]
applies_to:
  core: "any"
  os: [apolloos-r10]
tags: [stdc, posixc, genmodule, stack-call, struct-return, a0, cexp, sincos, ldiv]
related:
  - os/pitfalls/library-globals-shared-between-tasks.md
sources:
  - "ApolloOS source arch/m68k-all/include/aros/genmodule.h (master @ 0645ecc524): AROS_GM_LIBFUNCSTUB, AROS_GM_RELLIBFUNCSTUB, AROS_GM_STACKCALL"
  - "github.com/ApolloTeam-dev/ApolloOS.R10 issue #6"
  - "ApolloOS R10 port (ApolloOS-Port), 2026-11-17: Zune clock crash, test program StructRet"
---

## Symptom

A program built against ApolloOS's shared C libraries (stdc.library,
posixc.library and the other stack-call libraries made by genmodule):

- gets garbage from `ldiv()`, `div()`, `lldiv()`, `imaxdiv()` or any
  `double complex` function;
- crashes later, often a few seconds afterwards and in another function.
  One example is a Software Failure (Line 1010 at PC 0x26 in supervisor
  mode) at a task switch, followed by a reset that looks like a freeze.

Code that never calls such a function by name is hit too. GCC turns
`sin(x)` and `cos(x)` of the same `x` into a single `cexp()` call.

## Cause

On m68k, ApolloOS's genmodule stubs load the library base into `%a0`
before they jump to the library vector:

```text
cexp:   move.l  StdCBase,a0
        jmp     -372(a0)
```

GCC passes the hidden result pointer of a struct-returning function
(`ldiv_t`, `double complex`) in `%a0` too, so the stub destroys it. The
library function then writes its result to the library base and corrupts
its first bytes, and the caller reads uninitialised stack.

Functions that return scalars (`int`, `double`, pointers) are not
affected.

## Wrong

```c
/* linked with -lstdc stubs (uselibs stdc) on an affected ApolloOS */
#include <math.h>
x = cx + (WORD)(cos(a) * r);   /* with sin(a) nearby GCC emits cexp() */
y = cy - (WORD)(sin(a) * r);
```

## Right

Until the stubs are fixed (ApolloOS.R10 issue #6, fixed in the R10 port
on 2026-11-17), keep struct returns away from the stubs:

- Link the static C library for the affected functions.
- Or stop GCC from merging `sin` and `cos`:
  `-fno-builtin-sin -fno-builtin-cos` stops the `cexp` transformation.
  Calling them on separately computed (`volatile`) values also works.
- Do not call `div`-family or `complex.h` functions through the shared
  library.

The fix itself carries the base in `%a1` and keeps `%a0` in all three
macros. Stubs and libraries must be rebuilt together.

## Detection

Run `m68k-amigaos-nm` on the objects. An undefined `cexp`, `cexpf`,
`ldiv`, `div` or `lldiv` (or another struct-returning libc function) in a
program linked against the shared C library is a candidate.

A minimal check: print `ldiv(17, 5)` through stdc.library. It must print
quotient 3 and remainder 2.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| The stub loads the base into `%a0` | (SRC) `arch/m68k-all/include/aros/genmodule.h` | any | Source and `objdump` of `stdc_cexp_stub.o`: `movea.l StdCBase,a0; jmp -372(a0)` |
| GCC passes the result pointer in `%a0` | (M) 2026-11-17 | any | `objdump` of Zune's clock.c: `lea 84(sp),a0; jsr (a3)` with a3 = `cexp` |
| GCC merges `sin` and `cos` into `cexp` | (M) 2026-11-17 | any | clock.o references `cexp`, not `sin` or `cos` (GCC 6.5, `-O2`) |
| Results are lost and the base is corrupted | (M) 2026-11-17 | Core 12856, V4 UniCorn | Test StructRet: no output and RC 16688456 with the old stubs; `3 rem 2` and `cexp(0) = 1 + 0i` with the fixed stubs |
| It crashes the machine | (M) 2026-11-17 | Core 12856, V4 UniCorn | Zune clock in Prefs/Time and Utilities/Clock: Software Failure, PC 0x26, within seconds; 90 s without failure after the fix |
