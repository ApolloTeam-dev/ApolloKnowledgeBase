---
title: Use the FPU when results stay floating point
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fpu, integer, dsp, audio, mac]
related:
  - core/best-practices/fpu-schedule-by-completion-slot.md
  - core/pitfalls/fpu-float-to-integer-conversion.md
  - core/pitfalls/fpu-47-bit-context-save.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 4.3 and 12"
---

## Goal

Speed in DSP-style code (filters, synthesis windows, prediction): a
well-scheduled float MAC beats the integer one, as long as the values do not
have to become integers often.

## Technique

- Move multiply-accumulate loops to the FPU when the inputs can be stored as
  floats (coefficient streams as `.s`) and the output stays float, or becomes
  an integer only once per many operations.
- Use doubles for exact integer arithmetic only up to 47 significant bits
  (see [fpu-47-bit-context-save.md](../pitfalls/fpu-47-bit-context-save.md)).
- For 16-bit output, convert with `fmove.w` straight from the FPU: it
  saturates and follows the rounding mode
  (see [fpu-float-to-integer-conversion.md](../pitfalls/fpu-float-to-integer-conversion.md)).

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| MP3 synthesis window (512 terms), integer `muls.l` | 2185 cycles (4.27 per term) | Core 12841 | CCC (M) |
| Same, FPU with float coefficient streams | 1729 cycles; full decode 5 % faster, quality within dither | Core 12841 | Same |
| FLAC LPC order 8, integer | 46 cycles per sample | Core 12841 | Same |
| FLAC LPC order 8, FPU doubles (values ≤ 44 bits) | 35.5 cycles per sample; full decode 10 % faster | Core 12841 | Same |

## When not to use

- When every output must become an integer: each FP-to-integer conversion
  costs 3 cycles and blocks both pipes. That rules out IMDCT outputs.
- A 32-point DCT gains at most about 1.7 %: 2-address code and 8 registers
  force about 100 spills.
- A hybrid integer + FPU window was worse than either: each FPU term costs
  about as much as an integer term once operands come from memory, plus about
  4 cycles of conversion per sample.
- Interleaving float-to-integer conversion with FPU instructions that use
  `(An)+` operands cost 320–440 extra cycles: they did not pair for free.
- Converting through the `1.5*2^52` magic number: +250 cycles, and unsafe
  because of the 47-bit context save.
