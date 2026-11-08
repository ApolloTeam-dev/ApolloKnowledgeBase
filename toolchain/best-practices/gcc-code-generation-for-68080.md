---
title: Get the most from GCC 6.5 on the 68080
type: best-practice
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain, cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [gcc, m68080, code-generation, portable, assembler, fpu]
related:
  - toolchain/c-compiler-options.md
  - toolchain/pitfalls/float-settings-mismatch.md
  - toolchain/pitfalls/gcc-misc-traps.md
  - core/best-practices/fixed-point-and-bitstreams.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 9.1 and 15.1"
---

## Goal

Speed with GCC 6.5 (ApolloCrossDev), and knowing where hand-written assembler
pays off.

## Technique

- **`-m68080`** (and `-mtune=68080`) makes GCC emit 080-only integer opcodes
  (`addiw.l`, `cmpiw.l`, `dbra.l`; objdump shows them as `.short`). The
  binary then crashes on 68020/030 and under emulators; no switch turns this
  off.
- **FPU**: `-m68080` alone gives soft-float; add `-m68881` for FPU code
  (see [float-settings-mismatch.md](../pitfalls/float-settings-mismatch.md)).
  For full control, write FPU kernels in assembler.
- **Multiply-heavy loops**: GCC spills every 64-bit product. Plain 68020
  assembler with the 64-bit sum in a register pair (add/addx) and unrolled
  blocks with a computed entry beats it clearly.
- **Float-heavy C with `-std=c11`**: add `-fexcess-precision=fast`.
  `-std=c11` alone forces `-fexcess-precision=standard`, which rounds every
  float temporary through a Dn; in maggie.library that caused about 1320
  spills of 12-byte values (SRC).
- **Libraries that may run on other CPUs**: check AttnFlags bit 10 (68080) in
  LibInit, and build that object with `-m68020`. CI checks that `-m68020`
  emits none of the 080-only opcodes that `-m68080` gives for the same code
  (see [compiler-variants.md](../compiler-variants.md)):

```c
// kb:compile
// kb:opts -O2 -m68020 -fomit-frame-pointer
// kb:expect cmp.l #1000,
// kb:expect-not cmpiw
// kb:expect-not addiw
// kb:expect-not dbral
int is_k(long x) { return x == 1000; }
void add_k(long *p) { *p += 1000; }
long sum(const long *p, long n)
{
    long s = 0, i;
    for (i = 0; i < n; i++)
        s += p[i];
    return s;
}
```

- **Portable builds**: one code base can ship a 68020 build (`-m68020`, soft
  float at compile and link time, assembler limited to 68020) and an 080
  build.

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| MP3 decoder, 68020 build vs 080 build, on the 080 | 080 build 0–8 % faster | Core 12841 | Full decode (M) |
| `-m68080` vs `-m68020` code generation alone | About 2 % on an MP3 decoder | Core 12841 | Same |
| `-O3` vs `-O2` | No gain | Core 12841 | Same |
| Hand-written 68020 multiply loops vs GCC | Clearly faster | Core 12841 | MP3/FLAC kernels |

## When not to use

- Don't expect much from `-m68080` itself: about 2 % on its own. The large
  gains came from hand-written or generated assembler kernels.
- A `-m68080` binary does not run on other CPUs or emulators: keep a 68020
  build if the program must run elsewhere.
