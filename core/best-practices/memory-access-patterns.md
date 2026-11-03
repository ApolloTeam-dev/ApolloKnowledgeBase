---
title: Read memory densely and in order; keep random-access data small
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, cache, prefetch, tables, random-access]
related:
  - core/cpu-68080/caches-and-memory.md
  - core/pitfalls/touch-misuse.md
  - core/pitfalls/alu-to-ea-bubble.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 16), 5.2 and 12"
---

## Goal

Memory throughput: sequential reads are prefetched and cost almost nothing
extra; every random cache miss costs about 27 cycles, and misses do not
overlap.

## Technique

- Read every word of the data, in address order, through `(An)+`.
- Put data that is used together in the same 64-byte line.
- Keep lookup tables small and hot. Avoid pointer chasing over large data.
- Avoid rows exactly 64 KB apart: they alias in the cache.
- Use `touch d8(An,Dn)` 12–15 cycles ahead only for random accesses, never
  on a sequential stream.
- Don't keep a loop counter or accumulator in memory with read-modify-write:
  store-to-load forwarding works, but it serialises.

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Cold sequential read of every long | 10.2 cycles per 64-byte line | Core 12841 | CCC (M) |
| Warm sequential read of every long | 9.1 cycles per line | Core 12841 | Same |
| One read per 64-byte line | 14.4 cycles per line | Core 12841 | Same |
| One read per 128 bytes | 27.2 cycles | Core 12841 | Same |
| Random miss (dependent load) | About 30 cycles total, 27 more than a hit | Core 12841 | Pointer chase over 4 MB |
| Rows 64 KB apart | About 10 % slower | Core 12841 | Same |
| A 256-byte lookup table instead of `bfffo` for Rice codes | Slower | Core 12841 | Real decode |

## When not to use

- A hot-cache microbenchmark of table-driven code does not predict the real
  program: confirm on the real workload, three times (real-workload noise is
  about ±10 %).
