---
title: High-performance memory transfers (MEMSET and MEMCPY) with AMMX
type: best-practice
owner: Rudi7503
status: draft
origin: human
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [68080, ammx, memory, memset, memcpy, ddr3, bandwidth]
related:
  - toolchain/pitfalls/libnix-and-header-traps.md
  - core/best-practices/align-copy-destination.md
  - core/best-practices/ammx-where-it-wins.md
sources:
  - "Hardware measurement on Vampire V4 Standalone (Core 11350 at 92 MHz), Harness v6 suite (MEM-010..021)"
---

## Goal

Achieve maximum memory bandwidth for `memset` and `memcpy`, replacing slow standard library implementations (such as libnix byte-by-byte loops).

## Technique

- **AMMX Aligned MEMSET (Fill):**
  - Broadcast the 8-bit fill byte across a 64-bit AMMX register `E0` using `vperm` or `load`.
  - Unroll stores by 32 or 64 bytes per iteration using consecutive 64-bit `store` instructions.
  - Aligned 64-bit stores saturate the FPGA write-combining buffer, reaching peak DDR3 write throughput.
- **AMMX Aligned MEMCPY (Copy):**
  - Unroll in 32-byte chunks using 4 consecutive 64-bit `load` and `store` instructions.
  - Keep loads and stores grouped to allow the Apollo prefetcher and write-buffer to stream data without pipeline stalls.
- **Tail handling without branches:**
  - Handle remaining bytes (1 to 7) using `storeilm` with an index mask register, avoiding scalar cleanup branches.

```asm
; kb:compile
    ; Example: 32-byte aligned AMMX memset inner loop body
    store   e0,(a0)+
    store   e0,(a0)+
    store   e0,(a0)+
    store   e0,(a0)+
```

## Evidence

Measured on physical Vampire V4 Standalone hardware (Core 11350 at 92 MHz, Harness v6 suite, 10-iteration loop baseline 3.0 cycles):

| Benchmark Kernel | Chunk Size | Net Cycles / Iteration | Cycles / Byte | Memory Throughput | Total Bus Traffic |
|---|:---:|:---:|:---:|:---:|:---:|
| **AMMX Aligned MEMSET (`MEM-010`)** | 32 Bytes | **2.6 cyc** | **0.081 c/B** | **1,132.3 MB/s** | 1,132.3 MB/s |
| **AMMX Aligned MEMCPY (`MEM-011`)** | 32 Bytes | **6.6 cyc** | **0.206 c/B** | **446.1 MB/s** | **892.1 MB/s** |
| **Masked Tail-Store (`MEM-012`)** | 8 Bytes | **1.6 cyc** | **0.200 c/B** | **460.0 MB/s** | 920.0 MB/s |
| **MEMMOVE Streaming (`MEM-013`)** | 16 Bytes | **2.6 cyc** | **0.163 c/B** | **566.2 MB/s** | 1,132.3 MB/s |
| **Cacheline Burst MEMSET (`MEM-020`)** | 64 Bytes | **6.6 cyc** | **0.103 c/B** | **892.1 MB/s** | 892.1 MB/s |

### Architectural Insights

- **libnix Pitfall Addressed**: libnix `memset` and `memcpy` operate byte-by-byte or via unaligned 32-bit loops, often achieving less than 50 MB/s.
- **Write-Buffer Saturation**: 4 consecutive 64-bit `store` instructions sustain over 1.1 GB/s write throughput on the V4 92 MHz DDR3 memory controller.
- **Bus Saturation**: In `MEM-011`, moving 32 bytes involves reading 32 bytes and writing 32 bytes (64 bytes total bus traffic) in 6.6 cycles, effectively utilizing **892.1 MB/s** of combined DDR3 read/write bandwidth.

## When not to use

- For blocks smaller than 16 bytes: the loop setup and alignment check overhead outweighs SIMD throughput; use unrolled scalar `move.l` instructions instead.
- When source and destination pointers are misaligned relative to each other: align the destination pointer first and stream unaligned loads with scalar shifts or unaligned AMMX loads.
