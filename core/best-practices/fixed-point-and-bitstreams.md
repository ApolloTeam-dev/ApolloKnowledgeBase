---
title: Fixed-point multiplies and bitstream decoding on the 68080
type: best-practice
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, fixed-point, muls, bfextu, bfffo, huffman, codecs]
related:
  - core/cpu-68080/measured-instruction-costs.md
  - core/pitfalls/multiply-and-bfffo-block-both-pipes.md
  - core/pitfalls/alu-to-ea-bubble.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 10 and 11"
---

## Goal

Speed in codecs (MP3, FLAC) and other fixed-point or bitstream code.

## Technique

### Fixed point

- Keep only the high longword of a 64-bit `muls.l` (Q30/Q31 coefficients).
- For rounding, split a constant c = m + c' with |c'| ≤ 0.5 in Q32. Rounding
  then costs `add.l lo,lo` / `addx.l d7,hi` (2 instructions instead of 4) and
  stays exact.
- Keep 64-bit sums in a register pair with `add`/`addx`. Plain 68020
  assembler with unrolled blocks and a computed entry beat GCC, which spills
  every 64-bit product in multiply-heavy loops.

### Bitstreams

- Use `bfextu` at a bit position, and `bfffo` for unary codes.
- Memory bitfields cost the same as register bitfields on the 68080. Keeping
  a 32-bit window in a register was slower.
- `bfextu` width 0 means 32: guard it.
- Put the sign in the table row index: it removes a dependent smi/eor/sub
  chain.
- Read table fields as bytes with `moveq #0` + `move.b` (a fused zero-extending
  load), and write both outputs adjacent (a fused quad store).

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Huffman pair, sign handled with smi/eor/sub | 34.6 cycles per pair | Core 12841 | CCC, MP3 decode (M) |
| Sign in the table row index | 22 cycles per pair | Core 12841 | Same |
| Plus byte fields with fused movz and adjacent outputs | 15.8 cycles per pair | Core 12841 | Same |
| A 256-byte lookup table instead of `bfffo` for Rice unary codes | Slower | Core 12841 | FLAC decode (M) |

Results in context: MP3 decode went from 23.2 % to 15.7 % of real time at
258 kbps, FLAC 96/24 decode from 30.3 % to about 12–14 % CPU (M, V4 at
99 MHz).

## When not to use

- `bfffo` costs 3 cycles and blocks both pipes; `bfextu` runs in pipe 1
  only. In an offset chain they add latency (4 and 6 cycles): see
  [multiply-and-bfffo-block-both-pipes.md](../pitfalls/multiply-and-bfffo-block-both-pipes.md).
- A bit position that feeds the next address hits the ALU-to-EA bubble:
  `bfextu` → `move.b 2(a1,d5*4)` → `add` took 7.4 cycles per link, 9.1 when
  the bit position advances.
