---
title: Maggie span unit registers (as used by maggie.library)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [saga-3d-maggie]
applies_to:
  core: "Core 12847"
  os: [any]
tags: [maggie, 3d, registers, span, texture, dxt1]
related:
  - core/saga-3d-maggie/index.md
  - core/pitfalls/maggie-depth-test-colour-write.md
  - core/pitfalls/maggie-span-tail.md
  - core/pitfalls/maggie-span-usage.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 15.7"
  - "maggie.library source, github.com/RMortenB/MaggieLibrary, commit 64c78ef (2026-08-17)"
  - "Regression tests test-maggie, test-maggiez, test-maggieend, test-maggiecnt, Core 12847, 2026-11-01"
---

## Summary

Maggie is the V4's texture-mapping span unit: the CPU sets up one span per
scanline in registers at `$DFF250`, and writing the length starts it. There
is no public documentation beyond this; the layout below is how
maggie.library uses it (SRC), checked by register-level tests on Core 12847
(M).

## Details

### Span registers at `$DFF250`

| Offset | Size | Register |
|---|---|---|
| 0 | L | Texture address (DXT1, mip chain) |
| 4 | L | Destination pixel address (start of span) |
| 8 | L | Depth buffer address (start of span) |
| 14 | W | **Start + length: writing it starts the span**, so write it last |
| 16 | W | Texture size log2 (5–10); + `$10` = mipmapping |
| 18 | W | Mode: bit 0 bilinear, 1 depth, 2 16-bit output, 3 depth mask, 6 add, 7 multiply |
| 22 | W | Bytes per pixel (2 or 4) |
| 24 / 28 | L | Second-order dU / dV. Zero them once: they keep stale values otherwise |
| 32 / 36 | L | U / V, 8:24, normalised to the texture |
| 40 / 44 | L | dU / dV per pixel, 8:24 |
| 48 / 50 | W | Light 8:8 / dLight per pixel |
| 52 | L | Light colour (ARGB) = the draw tint |
| 56 / 60 | L | Depth 16:16 / delta 16:16 |

### Performance counters at `$DFF300`

Read-only and free-running in the library's description (SRC): `+0` texture
fetches, `+4` depth fetches, `+8` destination fetches, `+12` pixels started
(including pixels later killed by the depth test or alpha). **On Core 12847
they read 0 and never move** (M).

### Usage

- Per span: convert with `fmove.l` (RZ) straight into the U/V registers, set
  destination, U, V and light, then `move.w len,14(a0)`.
- Per polygon or batch: dU, dV, dLight, mode, texture and size.
- The library's perspective path splits each span into runs of 16 pixels
  with affine interpolation inside each run.

### Behaviour measured on Core 12847 (test-maggie: 0 failures)

- Length 1 to 64 writes exactly that many pixels, at any start pixel.
- U/V: 8:24, 1.0 = one texture width, point sampled. Negative dU works; U and
  V wrap at 1.0.
- DXT1 blocks are row-major, colours and indices little-endian. Index 3 with
  col0 ≤ col1 leaves the target pixel unchanged.
- Light 0 gives black. 16-bit output is RGB565.
- 32-bit colours with light `$FFFF` and tint `$FFFFFFFF`: RGB565 `$F800`
  gives `$00FC0000`, white gives `$00FCFCFC`. The alpha byte is 0; full light
  gives `$FC`, not `$FF`.

## Differences from AmigaOS / AROS / 68060

Classic Amiga chipsets have no texture-mapping unit. Maggie is SAGA specific
and not covered by the classic hardware reference.

## Do / Don't

- DO write the start + length register last: it starts the span.
- DO zero the second-order dU/dV registers once.
- DON'T use the counters at `$DFF300` for timing or sync on Core 12847.
- See the pitfalls: depth test, the last 8 bytes of a span, and span usage.
