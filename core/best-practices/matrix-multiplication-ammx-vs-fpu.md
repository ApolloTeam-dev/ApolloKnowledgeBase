---
title: Choose between AMMX fixed-point and FPU for matrix multiplication
type: best-practice
owner: Rudi7503
status: draft
origin: human
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [68080, ammx, fpu, matrix, 3d, fixed-point, simd]
related:
  - core/best-practices/fpu-when-it-pays.md
  - core/best-practices/ammx-where-it-wins.md
  - core/cpu-68080/superscalar-issue.md
sources:
  - "Hardware measurement on Vampire V4 Standalone (Core 11350 at 92 MHz), Harness v5 suite (MAT-001..003, FIX-001..003)"
---

## Goal

Maximize throughput for matrix multiplication (2x2, 3x3, and 4x4) in 3D geometry transformations, camera projections, and game engines.

## Technique

Choose between **AMMX 16-bit fixed-point** and **FPU single-precision float** based on whether the geometry pipeline requires wide dynamic range or maximum transformation speed:

- **Use AMMX 16-bit fixed-point for real-time 3D pipelines:**
  - Pack an entire 4-element row into a single 64-bit register (`E0`).
  - Broadcast each row element across all lanes using `vperm`.
  - Calculate four parallel 16-bit multiplies in 1 cycle using `pmulh` (Q15 fixed-point).
  - Sum partial vectors with `paddw`.
  - Store results with 64-bit `store` instructions (which can issue on Pipe 2).
- **Use FPU single-precision float for camera/world matrix inversion or wide dynamic range:**
  - FPU instructions (`fmul`, `fadd`, `fmove`) are restricted to Pipe 1 (maximum 1 FPU op per cycle).
  - Interleave independent multiply-accumulate chains to hide the 5-cycle `fmul` and 6-cycle `fadd` completion latency.

```asm
; kb:compile
    ; Example: AMMX 4x4 row multiplication step
    ; Broadcast element A[0][0] to all lanes:
    vperm   #$01010101,e0,e0,e8
    ; Multiply 4 parallel lanes by row B[0]:
    pmulh   e8,e4,e12
    ; Accumulate partial row product:
    paddw   e12,e13,e12
    ; Store transformed 64-bit row:
    store   e12,(a2)
```

## Evidence

Measured on physical Vampire V4 Standalone (Core 11350 at 92 MHz, 100 runs under `Forbid()` with hardware performance counter CCC, stable across 100/100 passes):

| Matrix Size | GCC -O2 C Reference | FPU Single-Precision (Opt) | AMMX 16-Bit Fixed-Point | Speedup vs C | Speedup vs FPU |
|:---|:---:|:---:|:---:|:---:|:---:|
| **2x2** | 111 cycles | 27 cycles | **17 cycles** | **6.5x** | 1.6x |
| **3x3** | 301 cycles | 87 cycles | **34 cycles** | **8.8x** | 2.6x |
| **4x4** | 599 cycles | 184 cycles | **54 cycles** | **11.1x** | **3.4x** |

### Architectural Insights

- **Why 184 cycles is the FPU limit:** A 4x4 matrix multiplication requires 64 multiplications (`fmul`), 48 additions (`fadd`), and 48 loads/stores (`fmove.s`) = 160 FPU instructions. Since all FPU operations are restricted to Pipe 1 and cannot pair, plus pipeline drain and 6-byte BANK prefix prefetch costs, 184 cycles represents the hardware floor.
- **Why AMMX achieves 54 cycles:** AMMX computes 4 multiplications per cycle via `pmulh` and 4 additions per cycle via `paddw`. Furthermore, AMMX `store` instructions can issue on Pipe 2 alongside arithmetic instructions on Pipe 1.

## When not to use

- **Do NOT use 16-bit AMMX** when accumulated numerical drift is critical (e.g. hierarchical bone transforms across many joints, matrix inversions, or very large world coordinates).
- **Do NOT use FPU** in tight per-vertex vertex transformation loops where 16-bit fixed point provides sufficient visual precision.
