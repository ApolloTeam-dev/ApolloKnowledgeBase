---
title: Keep code small and hot code together; don't unroll by default
type: best-practice
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080, toolchain]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, icache, unrolling, code-size, link-order, placement]
related:
  - core/cpu-68080/core-at-a-glance.md
  - core/best-practices/close-loops-with-dbra.md
  - core/cpu-68080/prm/optimizing.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rules 14-15), 5.3 and 12"
  - "Gunnar (core developer), statements on unrolling and padding, 2026-10-29 and 2026-10-30"
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03)"
---

## Goal

Speed of the whole program: hot code that stays in the I-cache. Fat code
evicts other code, and reloading it costs hundreds of cycles.

## Technique

- **Don't unroll by default** (G): "DBRA is fast and nearly free." "If you
  can loop 512 times, loop 512 times." "10 lines made into 6 KB = big
  mistake."
- **Unroll copies only a little** (G): 4 x `move.l (a0)+,(a1)+` (16 bytes) or
  2 x `move16 (a0)+,(a1)+` (32 bytes) per loop turn, and not much more.
- **Share code** instead of duplicating variants.
- **Keep code and data apart** (G). Code and read-only constants may share a
  4 KB page, in two blocks: 2 KB code, then 2 KB constants is fine. Finely
  interleaved code and constants (20 bytes of code, 16 bytes of constants,
  50 bytes of code, ...) is bad. Never put writable data in a code page (see
  [self-modifying-code-and-caches.md](../pitfalls/self-modifying-code-and-caches.md)).
- **Keep hot code contiguous.** Link the assembler routine right after the C
  code that calls it, and put cold objects first. Profile builds must keep
  the release link order: use `-fno-toplevel-reorder` and the same object
  order.
- **Read memory in address order through `(An)+`** (G). Re-lay tables in the
  order you read them instead of keeping a C layout; `d16(An)` everywhere
  makes code fat.
- **Don't pad code to move it in the I-cache** (G: "a terrible idea"). Tune
  the code for size; if it still does not fit, raise it with the Apollo team
  (for example more I-cache ways in the release core).

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Six IMDCT copies (12.9 KB) | Baseline | Core 12841 | Full MP3 decode, CCC (M) |
| One shared transform + 3 short windows (3.8 KB) | Full decode 0.2–0.6 % faster | Core 12841 | Same |
| Profile build with default link order | Synthesis 10.1 % of time | Core 12841 | Same |
| Profile build with release link order | Synthesis 7.3 % of time | Core 12841 | Same |
| Same binary, different load addresses | Up to about 5 % apart (41.6–49.9 cycles on one loop) | Core 12841 | Same |

- Unrolled variants that won alone (an 8 KB FPU window, a 15-row integer
  window) lost in the full decoder (M).
- Shrinking one 2.4 KB routine moved the code linked after it and cost 1.7 %
  on the full decode, while the routine itself got 2 % faster (M).

## When not to use

- A short scheduled tail can still win: turning a **multiply-bound**
  scheduled tail into a dbra loop cost about 30 % per element (14 vs 11
  cycles per sample). "Never unroll" holds for duplicated copies.
- Measure any unrolling in the full program, never in a microbenchmark.
- Core 12841 has an I-cache with few ways; 1-way builds alias code bigger
  than the cache by design. Note the core build with every measurement.
