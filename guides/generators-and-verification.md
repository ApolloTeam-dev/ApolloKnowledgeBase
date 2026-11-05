---
title: Write big 68080 kernels with a generator, and verify them in five steps
type: guide
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [generator, scheduling, verification, testing, emulator, dct, imdct]
related:
  - core/best-practices/fixed-point-and-bitstreams.md
  - core/best-practices/fpu-schedule-by-completion-slot.md
  - guides/benchmark-method.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 10"
---

## Goal

A large hand-tuned kernel (a transform such as a DCT or IMDCT) that is
faster than the compiler's code and proven bit-exact against a C
reference.

## Prerequisites

- A C reference of the kernel.
- A host scripting language for the generator (TuKo1982 used Python).
- A 68k emulator for the generic parts (vamos or Musashi) and a V4 for the
  080-specific build.

## Steps

1. **Generate the code, don't schedule it by hand.** A generator with a
   dependency graph, a register allocator and a list scheduler (optionally
   local search on a cycle model) gave a 32-point DCT 20 % faster than the
   C and an IMDCT 21 % faster than GCC, both bit-exact (M).
2. **Keep the generator in the source tree.** Let the Makefile regenerate the
   `.s` file, and check that it reproduces the shipped one.
3. **Use the cycle model to check a schedule, not only to find one.** A
   greedy list scheduler on the FPU model was worse than a hand-designed
   modulo rhythm: 2222 against 1644 cycles (M). The models still missed by
   10–20 % on some kernels, unexplained: always confirm with CCC on the
   hardware (see [benchmark-method.md](benchmark-method.md)).
4. **Climb the verification ladder:**
   1. Simulate the generated assembler (a small 68k simulator) before the
      first run.
   2. Run the generic 68k parts under an emulator and compare with the C
      reference: random cases including ±2^31, exhaustive where possible
      (4.2 million cases for one requantiser).
   3. Mutation-check the test: a 1-LSB change to one constant must be
      caught.
   4. Run the 080-specific build on the V4 and compare checksums with the
      emulator's 68020 build of the same configuration.
   5. Run full-file corpora plus fuzzed (randomly damaged) inputs, and
      compare the output **and** the return codes.

The fixed-point and bitstream techniques from the same work are in
[fixed-point-and-bitstreams.md](../core/best-practices/fixed-point-and-bitstreams.md).

## Verification

- Every rung of the ladder passes, including the mutation check.
- The checksums of the V4 build and the emulator's 68020 build match.
- The speed gain holds under [benchmark-method.md](benchmark-method.md).
