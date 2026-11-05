---
title: 68080 core at a glance (measured)
type: reference
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12798-12847"
  os: [any]
tags: [68080, pipes, caches, clock, attnflags, overview]
related:
  - core/cpu-68080/pipeline-15-stages.md
  - core/cpu-68080/superscalar-issue.md
  - core/cpu-68080/caches-and-memory.md
  - core/cpu-68080/prm/specs.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 1"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
  - "Gunnar (core developer), memory controller width, 2026-11-04"
---

## Summary

The key numbers of the 68080 as measured on V4 cores 12798 to 12847. Where
they differ from the PRM, the measured value or the core developer's
statement wins.

## Details

| Item | Value |
|---|---|
| Clock (V4) | 14 x 7.09379 MHz = 99.31 MHz. The PAL colour clock of 3546895 Hz drives the Paula/ARNE periods |
| Pipeline | The PRM summarizes it in 7 steps (I-fetch, decode, register fetch, EA, D-cache, ALU, write back). The real depth is 15 stages, see [pipeline-15-stages.md](pipeline-15-stages.md) |
| Pipes | PRM: 3 (Anton, Bruno, Cesar). **2 enabled on Core 12798-12841** (M): IEP3 always reads 0. A third pipe comes in a future core (G) |
| Decoders | 3. Only the first takes multi-cycle instructions (mul, div, movem, bitfields, FPU) and addx/subx/negx, which need the flags of the previous instruction |
| I-cache | 32 KB, **64-byte line** (G, 2026-10-29). Feeds the decoders **16 bytes per cycle**; a group of instructions that run together is at most 16 bytes (some I-cache variants: 18) (G, 2026-11-03), see [execution-units.md](execution-units.md). Few ways on Core 12841 (G); the number of ways is a build option: 4, 2 or 1 (G, 2026-10-30). Note the core build with every measurement |
| D-cache | 128 KB, **64-byte line** (G, 2026-10-29; M). **1 read and 1 write per cycle** (G, 2026-11-03): `add.l #1,mem` runs at about 1 per cycle. One memory address per cycle, so an instruction with two memory operands needs more than one |
| Bus and memory | Memory controller 128-bit from Core 12600, 64-bit before (G, 2026-11-04). 64-byte bursts (one cache line), about 12 cycles latency, automatic prefetch of sequential streams |
| Branch cache | 1024-entry BTC, a loop predictor, and a return cache for rts/rtd/rtr |
| MMU | None. PMMU and cp4–cp6 opcodes are illegal (`lpstop` remains) |
| FPU | 64-bit (double) internally, pipelined. Microcoded functions (trig, log, exp, fmod, frem, fscale, fgetexp/fgetman) take 100–200+ cycles and clobber E23 |
| AttnFlags | `$847f` with the FPU on, `$040f` with it off. **Bit 10 = 68080** |
| Context frames | AMMX 256 bytes, FPU 116 bytes |

Older notes and processor.resource up to version 44.6 give a 32-byte D-cache
line; 44.7 gives 64 bytes, which matches the measurement.

## Differences from AmigaOS / AROS / 68060

- The 68060 has two pipes and an MMU. Released V4 cores also run two pipes,
  but have no MMU: PMMU instructions are illegal.
- The cache lines are 64 bytes, not 16 as on the 68040/68060.
- 68080 detection uses AttnFlags bit 10, which classic AmigaOS does not
  define.

## Do / Don't

- DO gate 68080 code paths on AttnFlags bit 10, and FPU paths on the 68881
  flag at run time: the FPU can be switched off.
- DON'T assume three pipes because the PRM says so: measure IEP3 on your core.
- DON'T use MMU instructions on the 68080.
