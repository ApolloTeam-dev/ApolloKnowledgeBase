---
title: ApolloLib memory, endian and blit routines
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain, cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, memcpy, fill, endian, blit, alpha, ammx, move16]
related:
  - toolchain/apollolib/index.md
  - core/cpu-68080/measured-instruction-costs.md
  - core/best-practices/align-copy-destination.md
  - toolchain/pitfalls/apollolib-known-bugs.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_LibASM.s, _Lib.h), commit 639e195 (2026-11-04)"
---

## Summary

ApolloLib's assembly file has copy, fill and endian-swap routines for
memory, and copy, fill and alpha-blit routines for pixel rectangles. They
use 68080 instructions (`dbra.l`, `move16`, AMMX `load`/`store`/`vperm`).
Most ignore a remainder: give sizes that are a multiple of the chunk size.

## Details

All take their arguments in registers; the prototypes in
`ApolloCrossDev_Lib.h` declare them with `_A0(...)` … `_D7(...)`.

### Memory

| Routine | Arguments | Chunk | Remainder |
|---|---|---|---|
| `ApolloCopyBlock(s, d, size)` | a0, a1, d3 = bytes | 16 bytes with `move16`, then bytes | Copied |
| `ApolloCopyBlock32(s, d, size)` | a0, a1, d3 = bytes | 32 bytes (2 × `move16`) | **Ignored** |
| `ApolloCopyLongs(s, d, size)` | a0, a1, d3 = bytes | 4 bytes | **Ignored** |
| `ApolloFillLongs(d, value, size)` | a1, d4, d3 = bytes | 4 bytes | **Ignored** |
| `ApolloFillBlock(d, count, value)` | a0, d3 = bytes, d4 | 32 bytes (4 × AMMX `store`), 32-byte aligned | **Ignored** |

`move16` needs no alignment on the 68080, but is never faster than
aligned AMMX or quad moves (see
[measured-instruction-costs.md](../../core/cpu-68080/measured-instruction-costs.md)).

### Endian swap

| Routine | What it does |
|---|---|
| `ApolloSwapWord(w)`, `ApolloSwapLong(l)`, `ApolloSwapOcta(q)` | Return the value with its bytes reversed (d0) |
| `ApolloEndianSwapWordBuffer(s, length)` | Byte-swaps 16-bit words in place, 8 bytes per AMMX step; buffer ≥ 8 bytes, 2-byte aligned |
| `ApolloEndianSwapLongBuffer(s, length)` | Byte-swaps 32-bit longs in place, 8 bytes per AMMX step; buffer ≥ 8 bytes, 4-byte aligned. Before 639e195 it swapped words. |
| `ApolloEndianSwap2Loop`, `ApolloEndianSwap8Loop` | Older swap loops, used by `ApolloShowFile` |

### Pixel rectangles

| Routine | What it does |
|---|---|
| `ApolloFillBitMap(dst, w, h, depth, dstmod, value)` | Fills a rectangle with a 32-bit value; modulo in pixels |
| `ApolloFillColor(dst, w, h, depth, dstmod, value)` | As above, value given byte-reversed |
| `ApolloCopyPicture(s, d, w, h, smod, dmod)` | Copies a rectangle; sizes and modulos in bytes |
| `ApolloCopyPicture32(...)` | As above, 32-byte aligned |
| `ApolloCopyLoop`, `ApolloCopy32Loop`, `ApolloBlitLoop` | Copy, aligned copy and copy with transparency; pitches in words |
| `ApolloFillLoop(d, w, h, dpitch, colour)` | Fills with an R5G6B5 colour |
| `ApolloBlitAlphaConstLoop(s, d, w, h, sp, dp, alpha)` | Blends with a constant alpha 0–255 (0 = transparent) |
| `ApolloBlitAlphaKeyTransLoop(..., alpha, key)` | Blends with alpha and skips the R5G6B5 key colour |
| `ApolloBlitAlphaHorizontalLineLoop(s, d, w, colour, alpha)` | Blends one line with an R8G8B8 colour |
| `ApolloBlitRed/Green/BlueAlphaBGLoop`, `ApolloBlitBlueAlphaUILoop` | Blend through a separate alpha map, one colour channel at a time |
| `ApolloUncompressLoop`, `ApolloUncompressVectorLoop` | Unpack sprites, with endian and colour swap (`$07C0` green becomes the key `$F81F`) |

The blit routines work on R5G6B5 pixels (16-bit modes).

## Differences from AmigaOS / AROS / 68060

- `CopyMem`/`CopyMemQuick` and the classic blitter are not used; these are
  CPU loops for the 68080.
- AMMX (`load`, `store`, `vperm`) doesn't exist on the 68060: these
  routines need a 68080.

## Do / Don't

- DO give sizes in multiples of 32 (`ApolloCopyBlock32`, `ApolloFillBlock`)
  or 4 (`ApolloCopyLongs`, `ApolloFillLongs`).
- DO align the destination of large copies (see
  [align-copy-destination.md](../../core/best-practices/align-copy-destination.md)).
- DON'T use `ApolloEndianSwapLongBuffer` from an ApolloLib older than
  639e195: it swapped words, not bytes.
