---
title: Use AMMX where it wins
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080, saga-video-isabelle]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, ammx, simd, blit, fill, p96]
related:
  - core/cpu-68080/prm/ammx-unit.md
  - core/best-practices/align-copy-destination.md
  - core/pitfalls/ammx-pc-relative-source.md
  - core/pitfalls/ammx-upper-32-bits.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 6, 11 and 12"
---

## Goal

Speed for fills, masked stores, pattern fills, format conversion and
decimation, where AMMX gives 1.8x to 11x.

## Technique

- Use aligned AMMX stores for fills, `storem` masked stores for template
  (text) blits, and preload pattern rows into registers for pattern fills.
- Use AMMX for byte and word lanes: format conversion and decimation.
- Keep a plain 68k path for tiny shapes:
  - EOR invert for rows of 64 bytes or less;
  - a dedicated column path for widths of 8 pixels or less.
- Record the real call shapes before optimising: in real GUI FillRects, 86 %
  of rows were 1–4 pixels wide (M).
- Prefer arithmetic over lookup tables: a table that wins in a hot benchmark
  can lose when the real workload evicts it.
- Enable AMMX register saving with the Apollo bit: `ori #$800,sr` /
  `andi #$f7ff,sr` (about 8 cycles for the pair, user mode). The OS
  `V_EnableAMMX` pair cost 248 cycles (M).

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Aligned fills | x1.84 | Core 12841 | CCC (M) |
| P96 FillRect, real workload | 1.80 M → 0.60 M cycles | Core 12841 | Aligned AMMX stores + 68k column path |
| P96 BlitTemplate (text) | 2.38 M → 1.59 M cycles | Core 12841 | AMMX `storem` |
| P96 BlitPattern | 307 K → 28 K cycles | Core 12841 | AMMX, two pattern rows preloaded |
| 1-pixel rows, generic vs column path | 14.6 → 2.25 cycles | Core 12841 | Same |
| 6 KB colour lookup table | 1.4x faster in the benchmark, 3–10 % slower on the real console | Core 12841 | Real workload |

## When not to use

- **Lanes are bytes or words only.** `pmul*` is 4 x 16x16 (high, low or bits
  23..8); there is no 32-bit add and no MAC. AMMX does not suit 24/32-bit
  audio maths: FLAC LPC, Rice decoding, or lossless MP3 synthesis (a 16-bit
  window gave 46 dB SNR).
- There is one AMMX unit, so the floor is about IPC 1.0; the second pipe
  accepts AMMX stores only.
- A 128-bit AMMX unit is in development (G, 2026-10-29); released cores
  (12841) have the 64-bit unit.
