---
title: V4 memory (Chip, Fast and video RAM)
type: reference
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [other]
components: [hardware]
applies_to:
  core: "any"
  os: [any]
tags: [hardware, memory, chip-ram, fast-ram, dma]
related:
  - hardware/index.md
  - core/cpu-68080/caches-and-memory.md
  - core/saga-registers/index.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 1"
---

## Summary

On the V4, Chip, Fast and video RAM are the same memory chips at the same
speed. Putting a buffer in Fast RAM rather than Chip RAM gains nothing.

## Details

- Chip, Fast and video RAM are the same chips and run at the same speed
  (TuKo1982's guide; the guide gives no source tag for this fact).
- So there is no faster memory to move DMA buffers into.
- SAGA's DMA reaches all RAM: the classic pointer registers are 32 bits
  wide on SAGA (see [core/saga-registers/index.md](../../core/saga-registers/index.md)),
  and Arne plays from any RAM.
- How the CPU sees the memory (cache lines, bursts, the 128-bit memory
  controller from Core 12600) is in
  [caches-and-memory.md](../../core/cpu-68080/caches-and-memory.md).

## Differences from AmigaOS / AROS / 68060

- On a classic Amiga, Chip RAM is slower for the CPU than Fast RAM, and the
  custom chips reach only Chip RAM. On the V4 both differences are gone.

## Do / Don't

- DO allocate with `MEMF_ANY`, unless the OS or an API you call expects
  `MEMF_CHIP` memory.
- DON'T move buffers to Fast RAM for speed: it is the same memory.
