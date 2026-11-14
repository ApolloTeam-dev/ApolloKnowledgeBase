---
title: Real-time 2D sprite blending and alpha modulation with AMMX
type: best-practice
owner: Rudi7503
status: draft
origin: human
basis: [measured]
components: [cpu-68080, saga-video-isabelle]
applies_to:
  core: "any"
  os: [any]
tags: [68080, ammx, blit, sprite, alpha, blending, games, hurrican]
related:
  - core/best-practices/ammx-where-it-wins.md
  - core/best-practices/align-copy-destination.md
sources:
  - "Hardware measurement on Vampire V4 Standalone (Core 11350 at 92 MHz), Harness v6 suite (BLT-006..021)"
---

## Goal

Achieve high frame-rate 2D sprite rendering, alpha blending, dynamic lighting, and particle effects in games without frame drops or blitter stalls.

## Technique

- **Vectorized Color-Key Transparency (`BLT-013`):**
  - Compare 8 pixels (or 4 words) in parallel using `pcmpccw` / `pcmpccb`.
  - Use the resulting bitmask to conditionally mask pixel writes with `storem` or `storeilm`.
- **Fast Alpha Blending via `pmula` (`BLT-006`):**
  - Use `pmula` (multiply-accumulate with alpha scaling) to blend source and destination color channels in parallel.
- **Fast Additive/Particle Blending (`BLT-018`):**
  - For light, glow, and fire particles, use saturating addition `paddusw` / `paddusb` across 64-bit qwords.
  - Saturated SIMD math prevents color wrapping artifacts without branch checks.
- **Branchless Row Tails (`BLT-012`):**
  - Terminate sprite rows with `storeilm` using a preloaded lane mask instead of branching to scalar cleanup loops.

```asm
; kb:compile
	section	code,code
	; Example: Fast 64-bit additive particle blend step
	load	(a0),e0		; Load 4 source pixels (RGB565 or 8-bit)
	load	(a1),e1		; Load 4 destination pixels
	paddusw	e0,e1,e2	; Saturated vector add (no color wrap)
	store	e2,(a1)		; Write back blended pixels
```

## Evidence

Measured on physical Vampire V4 Standalone hardware (Core 11350 at 92 MHz, Harness v6 suite, 10-iteration loop baseline 3.0 cycles):

| Blit / Blend Operation | Kernel ID | Net Cycles / Iteration | Fill Rate (92 MHz) | Architectural Feature |
|---|:---:|:---:|:---:|---|
| **Ultra-Fast Qword Blend** | `BLT-018` | **0.6 cyc** | **1,226.7 Mpx/s** | Saturating SIMD add, > 1.2 GPx/s throughput |
| **Color-Key Transparency Filter** | `BLT-013` | **1.6 cyc** | **460.0 Mpx/s** | 1-cycle parallel color key match for 4/8 pixels |
| **Alpha Blit Basic Step** | `BLT-006` | **1.6 cyc** | **460.0 Mpx/s** | Parallel channel modulation |
| **Masked Qword Blit** | `BLT-012` | **2.6 cyc** | **283.1 Mpx/s** | Tail masking via `storeilm` |
| **Subtractive Blend (Shadows)** | `BLT-014` | **4.6 cyc** | **160.0 Mpx/s** | Saturating vector subtraction `psubusw` |
| **Multiplicative Blend (Darkening)**| `BLT-015` | **4.6 cyc** | **160.0 Mpx/s** | Fixed-point darkening |
| **Particle Shading (8 Pixels)** | `BLT-016` | **12.6 cyc** | **58.4 Mpx/s** | 8 particles rendered simultaneously |

### Key Engine Insights

- **Eliminating Blitter Wait States**: Unlike the classic Amiga blitter which halts CPU execution or requires busy-wait polling (`btst #6,$DFF002`), CPU-driven AMMX blits execute asynchronously out of L1 cache and stream directly to DDR3 video memory.
- **Saturating Math**: `paddusw` and `psubusw` provide hardware clipping at `$FFFF` (white) and `$0000` (black) with zero branch penalties.

## When not to use

- When using the SAGA 3D hardware rasterizer (Maggie): if Maggie spans and textured polygons are already active, let Maggie handle depth-tested surfaces instead of software AMMX spans.
- For small 1-to-2 pixel wide vertical blits: scalar 16-bit stores avoid SIMD masking overhead.
