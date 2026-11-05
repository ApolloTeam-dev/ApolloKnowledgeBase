---
title: Read memory densely and in order; keep random-access data small
type: best-practice
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured]
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
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03)"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
---

## Goal

Memory throughput: sequential reads are prefetched and cost almost nothing
extra; every random cache miss costs about 27 cycles, and misses do not
overlap.

## Technique

- Read every word of the data, in address order, through `(An)+`. The
  prefetcher predicts increasing addresses best; `-(An)` is less good, and
  random access (pointer chasing) is very bad (G).
- Read one stream at a time where you can: several streams in parallel, such
  as comparing two memory regions, can confuse the prefetcher (G).
- Put data that is used together in the same 64-byte line.
- Don't use a table for anything you can compute in 16 cycles or less (G,
  2026-11-03). MUL and DIV beat a table; a SIN table makes sense. Keep the
  tables you do use small and hot.
- Avoid rows exactly 64 KB apart: they alias in the cache.
- Use `touch d8(An,Dn)` 12–15 cycles ahead only for random accesses, never
  on a sequential stream.
- Don't keep a loop counter or accumulator in memory with read-modify-write:
  store-to-load forwarding works, but it serialises (M). Gunnar expects such a
  loop to run at about 1 iteration per cycle (G); this is still to be
  measured.
- Write in address order too. The cache is write-through with write
  combining: the CPU collects writes for a few cycles before committing them,
  which makes memclr and memcopy loops efficient (G).

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
| Table against computation | Compute anything that takes 16 cycles or less | any | Statement (G, 2026-11-03) |

## When not to use

- A hot-cache microbenchmark of table-driven code does not predict the real
  program: confirm on the real workload, three times (real-workload noise is
  about ±10 %).
