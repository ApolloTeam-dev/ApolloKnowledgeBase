---
title: 68080 caches and memory access (measured)
type: reference
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, cache, line-size, prefetch, alignment, miss]
related:
  - core/cpu-68080/prm/specs.md
  - core/best-practices/memory-access-patterns.md
  - core/best-practices/align-copy-destination.md
  - core/pitfalls/self-modifying-code-and-caches.md
  - core/pitfalls/touch-misuse.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 5.1 and 5.2"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
  - "Gunnar (core developer), memory controller width, 2026-11-04"
  - "WDrijver (maintainer), same core on every V4 model, 2026-11-04"
---

## Summary

Cache lines are 64 bytes. The data cache serves one 8-byte access per cycle.
Sequential reads are prefetched and nearly as fast as warm data; a random
miss costs about 27 extra cycles and misses do not overlap. Misaligned reads
are nearly free; misaligned writes are not.

## Details

### Line size

Measured with a random-order pointer chase over 4 MB, 8192 blocks, CCC
counter, median of 7, two identical runs (M, Core 12841, 2026-10-29):

| Block | 1st read (offset 0) | 2nd read (offset block/2) | Means |
|---|---|---|---|
| 32 B | 30.3 cycles | +3.0 (hit) | Same line |
| 64 B | 30.6 | +3.0 (hit) | Same line: **the line is 64 bytes** |
| 128 B | 30.6 | +16.5 | Next line, already partly on its way |
| 256 B | 30.6 | +29.4 | Full miss |

- A miss on one line seems to bring the next 64-byte line in early: reading
  it right after cost about half a miss.
- Two lines 128 bytes or more apart are fully independent misses.
- Older notes (Core 12798–12824) gave "sequential about 2 cycles per line,
  random about 60". They assumed 32-byte lines and their method is lost; the
  figures here replace them.

### Streaming and random access

- Reading every long of cold memory: about 10.2 cycles per line, nearly the
  warm speed (9.1).
- One long per line: 14.4 cycles per line. One per 128 bytes: 27.2.
- Random access: about 27 cycles per new line, and misses do not overlap.
- Aliasing: rows exactly 64 KB apart cost about 10 %, and 8 lookups 64 KB
  apart gave 8 misses.
- Store-to-load forwarding works, but a counter kept in memory with
  read-modify-write in a loop serialises (M). Gunnar expects a loop of
  `add.l #1,memcounter` + `dbra` to run at about 1 iteration per cycle (G,
  2026-11-03). Measured on Core 12556, the loop takes 2 cycles per
  iteration, and 20–23 when the counter is in the same 64-byte line as the
  loop code; `dbra` alone and `addq.l #1,Dn` + `dbra` take 1 cycle
  (M, Core 12556, V4 UniCorn, `tools/v4/tests/add-mem-dbra`, 2026-11-09). Not yet measured on Core 12841.

### What a miss costs (G, 2026-11-03)

There is no single number. A miss loads a 64-byte burst: the memory
latency plus the burst cycles, 4 on a 128-bit bus and 8 on a 64-bit bus.
The memory controller is 128-bit from Core 12600 and 64-bit on older cores
(G, 2026-11-04). On top of that it depends on:

- whether the access hits the same row, page or bank as the last one;
- whether the last access was a read or a write;
- the CPU itself: when it reads and writes at the same time, the write goes
  first;
- other memory users (Copper, Blitter, Maggie, Arne, HDMI), which can be
  served before the CPU.

The memory controller is part of the core, so it is the same on every V4
model that runs the same core (see
[hardware/index.md](../../hardware/index.md)).

The 27 cycles above are one case: dependent random reads over 4 MB. When
you measure a miss, state these conditions.

Memory-bound measurements from a core before 12600 (64-bit controller) are
not comparable with those from Core 12600 and later. All measurements in
this knowledge base are from Core 12798 or later.

### Alignment

Copy of a 156 x 2464-byte shape (M):

| Method | Aligned | Misaligned |
|---|---|---|
| AMMX `load`/`store` | 3.2–3.5 bytes/cycle (8-byte aligned) | About 1.8 |
| `move16` | 3.1–3.2 (16-byte aligned) | About 1.75 |
| `move.l` loop | 1.7–2.0 | |
| AMMX `storem` (masked) | About 1.85 cycles per quad, whatever the alignment | |

- Alignment is not needed for correctness: misaligned reads that hit the
  cache are free (official).
- A misaligned **destination** costs 1.7–1.8x; a misaligned source only
  0–13 %.
- Copies are memory-bound at about 3 bytes per cycle: optimising a blit copy
  gained only 3–10 %.
- A `.b`/`.w` write into a register also reads its old value: an extra
  dependency. Prefer `.l` or quad register updates.

### Cache control

- `CacheClearU`/`CacheClearE` do nothing on the 68080 under AmigaOS; see
  [self-modifying-code-and-caches.md](../pitfalls/self-modifying-code-and-caches.md).
- Evicting the D-cache takes 128–256 KB of reads.

## Differences from AmigaOS / AROS / 68060

- 64-byte lines instead of 16 bytes on the 68040/68060. Data used together
  should sit in the same 64-byte line.
- On the 68080 a misaligned read that hits the cache is free; only the write
  side needs alignment for speed.

## Do / Don't

- DO align the destination of copies and fills.
- DO read memory densely and in address order.
- DON'T chase pointers over large data, or use big lookup tables read at
  random.
- DON'T use a table for anything you can compute in 16 cycles or less (G).
- DON'T keep a loop counter in memory.
- DON'T write data in a loop that sits in the same 64-byte line as the
  loop's code: a read-modify-write there cost 10 times as much (M, Core
  12556).
- DON'T compare memory-bound timings across Core 12600: the memory
  controller doubled from 64 to 128 bits there.
