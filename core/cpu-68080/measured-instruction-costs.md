---
title: 68080 instruction costs measured on Core 12841
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, timing, cycles, multiply, bitfield, cache]
related:
  - core/cpu-68080/prm/instruction-timing.md
  - core/cpu-68080/prm/instruction-efficiency.md
  - core/cpu-68080/fpu-performance-model.md
  - core/pitfalls/multiply-and-bfffo-block-both-pipes.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 3"
---

## Summary

Cycle costs measured with the CPU counters on trained loops. Several are
higher than the PRM states: multiply is about 3 cycles and blocks both pipes,
FP-to-integer conversion 3 cycles, a random cache miss about 27 extra cycles.

## Details

Method (M): `movec` CCC/IEP1/IEP2 in user mode, under `Disable()`, trained
loops, best of 5, Core 12841.

| Operation | Cost |
|---|---|
| Simple ALU/EA operations | Up to 2 per cycle (2 pipes) |
| add/addx pairs (64-bit sums) | About 1 per cycle (addx in pipe 1 only) |
| `muls.l`/`mulu.l` 32 and 64-bit, `muls.w`, `mulu.w` | **3.04–3.13 cycles each, issue-bound** (same with 1 or 7 independent chains). Nothing pairs with it: mul + an independent op = 4.0–4.08. Result usable about 3 cycles later |
| mul + add/addx rounding chain | About 5–6 cycles per product |
| `bfextu` (memory or register) | 1.5 cycles throughput, pipe 1 only, latency 4 in an offset chain |
| `bfffo` (memory or register) | 3 cycles and **blocks both pipes**, latency 6 when it feeds the next offset |
| Mispredicted Bcc / RTS | About 7 / about 9.5 cycles (see [branches-and-prediction.md](branches-and-prediction.md)) |
| `bcc.s` over 1 instruction (predicated) | No penalty, whatever the pattern |
| Dependent indexed loads | About 4 cycles each |
| One memory access per cycle | 16 x `add.l d16(sp),Dn` = 15 cycles |
| Store then reload of the same slot | No extra penalty |
| `move2.l (An)+,d0:d4` in a muls-bound loop | 11 % slower than two `move.l (An)+` |
| fmul / fadd | Latency 5 / 6; 1 per cycle with at least 5 / 6 independent chains |
| FPU source conversion | Free for .s/.d/.x; about +1 latency for integer sizes (.l/.w) |
| `fmove.s`/`.d` FP to memory | 1 per cycle, pairs with integer instructions |
| `fmove.l`/`.w` FP to integer | 3.08 cycles, blocks both pipes |
| `movem` | 1 + n/2 (official) |
| `div` | Under 18 cycles (official). Divide by zero traps unless a NoMoreDiv0 patch is loaded |
| `move16` | 4 cycles, no alignment required (official). Never faster than aligned AMMX or quad moves (M) |
| `ori/andi #$800,sr` (Apollo bit, user mode) | About 8 cycles for the pair |
| D-cache hit (dependent load) | About 3.6–3.7 cycles |
| D-cache miss, random line (dependent load) | About 30 cycles in total, about 27 more than a hit. Independent random misses do not overlap: also 27 extra cycles each |
| Streaming cold reads, every long | 10.2 cycles per 64-byte line (about 6.2 bytes per cycle), about 1.2 cycles more than the same loop on warm data |
| One read per 64-byte line, sequential | 14.4 cycles (the prefetcher helps less with sparse reads) |
| One read per 128 bytes, sequential | 27.2 cycles, almost a random miss |

## Differences from AmigaOS / AROS / 68060

- The PRM gives MUL = 2 or 3 cycles ([prm/instruction-timing.md](prm/instruction-timing.md)).
  Measured: 3.04–3.13, and it blocks both pipes.
- The 68060 emulates 64-bit `muls.l`/`mulu.l` in software; the 68080 runs them
  in hardware at the same cost as 32-bit.

## Do / Don't

- DO count multiply, `bfffo` and FP-to-integer conversion as about 3 cycles
  that nothing pairs with.
- DO keep data that is read at random small and hot: every new line costs
  about 27 cycles.
- DON'T use `move2` or `move16` for speed without measuring.
