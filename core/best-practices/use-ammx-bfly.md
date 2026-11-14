---
title: Use BFLY for paired vector addition and subtraction
type: best-practice
owner: Rudi7503
status: draft
origin: human
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [68080, ammx, bfly, butterfly, fft, dct, dwt]
related:
  - core/cpu-68080/prm/ammx/bfly.md
  - core/best-practices/ammx-where-it-wins.md
sources:
  - "Hardware measurement on Vampire V4 Standalone (Core 11350 at 92 MHz), Harness v6 suite (BFLY-001..005)"
---

## Goal

Accelerate symmetric butterfly stages in FFT, DCT, DWT (Haar, LeGall, Daubechies) and audio downmixing by calculating vector addition and subtraction in a single instruction.

## Technique

- Replace explicit pairs of `paddw`/`psubw` (or `paddb`/`psubb`) with `bflyw` (or `bflyb`).
- Fold memory operand access directly into `bfly`: the effective address calculation is folded with zero cycle penalty (`bflyw (a0),e8,e0:e1`).
- Ensure the destination register pair is consecutive and starts with an even register (e.g. `e0:e1`, `e2:e3`).

```asm
; kb:compile
    bflyw    e2,e8,e0:e1
    bflyw    (a0),e8,e2:e3
```

## Evidence

Measurements on Vampire V4 Standalone (Core 11350 at 92 MHz, 10-iteration loop baseline 3.0 cycles):

| Operation | Code | Net Cycles / Iteration | Pipe 1 (Anton) | Pipe 2 (Bruno) | Note |
|---|---|---|---|---|---|
| Split vector add + sub | `paddw e2,e0` + `psubw e2,e1` | 3.6 cyc | 50% | 50% | Dual-issue paired |
| **BFLY vector register** | `bflyw e2,e8,e0:e1` | **2.6 cyc** | 0% | 100% | **-1.0 cyc (-28%)** |
| Memory load + split add/sub | `load (a0),e2` + `paddw` + `psubw` | 4.6 cyc | 76% | 24% | Load in Pipe 1 |
| **BFLY memory folded** | `bflyw (a0),e8,e0:e1` | **2.6 cyc** | 0% | 100% | **-2.0 cyc (-43%) zero overhead load** |
| **BFLY 8-byte vector** | `bflyb e2,e8,e0:e1` | **2.6 cyc** | 0% | 100% | 8 additions + 8 subtractions |

## When not to use

- When saturation arithmetic is strictly required: `bfly` wraps around on overflow and does not saturate.
- When operands are 32-bit: `bfly` supports only byte (`bflyb`, 8 lanes) and word (`bflyw`, 4 lanes).
