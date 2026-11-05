---
title: Benchmark 68080 code so the result is real
type: guide
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [benchmark, measuring, ccc, method, noise, placement]
related:
  - core/cpu-68080/performance-counters.md
  - core/best-practices/code-size-and-placement.md
  - os/pitfalls/ramlib-reuses-library-by-name.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 8.1 and 8.2"
---

## Goal

A speed comparison between two versions of 68080 code that you can trust:
the difference you report is the code's, not that of the cache, the
placement or the machine's mood. Most "gains" TuKo1982 first saw were wrong
for one of the reasons below (M).

## Prerequisites

- Timing with the CCC cycle counter (`movec $809,Dn`), see
  [performance-counters.md](../core/cpu-68080/performance-counters.md).
- Two or more builds of the code to compare, and a way to run each one many
  times in one boot.

## Steps

1. **Know what you measure.** One dependency chain measures latency; N
   independent chains, N at least the latency, measure throughput. A wrong
   chain count once made the FPU look "no better than integer" (M).
2. **Train the loop.** Run it once before you time it, and discard that
   first pass.
3. **Alternate the variants in one boot**, rotating the order: A B A B A B.
   Run back to back, a second run gets a warm cache: a 35 % "gain" was
   really 14 % (M).
4. **Vary the placement.** Build several copies and load them at different
   addresses. Differences under 5 % on a single build are noise (see
   [code-size-and-placement.md](../core/best-practices/code-size-and-placement.md)).
   For library tests, give the test version a name of the **same length**
   as the real one: the name string shifts the code.
5. **Measure the real workload 3 times** for table-driven code. Its noise is
   about ±10 % (M).
6. **Record real call shapes first** (hook the calls and log their
   arguments), then test with those, plus random sizes to expose
   branch mispredictions.
7. **Test worst-case data:** very loud audio, maximum-range inputs. "Bit
   exact with the C" proves nothing when the C has the same overflow.
8. **Run with nothing else active.** One session on a V4 ran 15–36 % slower
   for 15 minutes for no visible reason, then recovered by itself (M).
9. **Give each variant a unique library name**, or flush between runs:
   ramlib returns the library already in memory (see
   [ramlib-reuses-library-by-name.md](../os/pitfalls/ramlib-reuses-library-by-name.md)).

## Verification

- The alternated runs agree with each other within the noise of step 4 or 5.
- The same result holds for several builds and load addresses.
- Report gains as positive percentages ("26 % fewer cycles") and slowdowns
  in words, and state the core, the board and the data you used.
