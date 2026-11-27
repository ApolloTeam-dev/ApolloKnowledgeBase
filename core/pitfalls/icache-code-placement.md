---
title: Code placement decides speed in the 1-way I-cache
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, core-developer]
components: [cpu-68080, libraries, toolchain]
applies_to:
  core: "Core 12870"
  os: [apolloos-r10]
  mode: [any]
  board: [v4-unicorn]
tags: [68080, icache, direct-mapped, layout, rom, benchmark]
related:
  - core/cpu-68080/core-at-a-glance.md
sources:
  - "Willem Drijver (2026-11-26): Core 12870 has a 1-way I-cache and a 2-way D-cache"
  - "ApolloOS-Port docs/perf/finding-code-layout.md and plan-code-layout.md (2026-11-26/27)"
  - "ApolloOS-Port tools/icachemap.py, C:LineCheck RECT, C:MemLoop CYCLES"
---

## Symptom

- **A small call gets much slower after an unrelated change:** RectFill
  10x10 went from 18 to 28 us after an edit to a file that is not on its
  path.
- **The work is the same:** the instruction counters IEP1/IEP2 show the
  same number of instructions, but the cycle counter shows 58 % more
  cycles.
- **A single before/after benchmark of a ROM change can show a gain or a
  loss of up to ~50 %** that has nothing to do with the change.

## Cause

- **The cache:** the I-cache of Core 12870 is 32 KB and direct-mapped
  (1-way), with 64-byte lines: 512 sets. Code whose addresses differ by
  a multiple of 32 KB uses the same set and evicts the other.
- **How it bites:** when two functions on one hot path share sets, every
  call misses on both, at about 40-60 cycles a line.
- **Every link shifts the code:** a change anywhere moves everything
  linked after it, so which paths collide is luck.
- **Code in RAM counts too:** jump tables of libraries in RAM count as
  well. Exec's table below SysBase holds code (Forbid is inline there) and
  is passed on every exec call. A ROM function on the same sets
  (`nommu_AllocMem` on ApolloOS) made AllocMem 1.6x slower.

## Wrong

```c
/* measure once, link, measure again, conclude */
before = rectfill_cycles(rom_a);
after  = rectfill_cycles(rom_b);    /* rom_b: one unrelated file changed */
/* "my change made RectFill 50 % slower" - or faster */
```

## Right

- **Place the hot code on purpose.**
  - **What goes together:** the functions of the hot paths (from
    profiles) in one region, at most ~30 KB.
  - **Where:** placed so that it starts after the cache sets of the hot
    RAM jump tables, with the ROM's two halves following each other in
    the cache.
  - **How ApolloOS R10 does it:** `-ffunction-sections`, a list
    `rom.hot`, and a generated linker script (tools/romhot.py) that also
    checks the result.
- **Keep the boot entry in place.** On AROS/ApolloOS, ColdReboot jumps to
  `rom_init` - 2 after `reset`. That code must stay right after the ROM
  header, so the hot region goes after it.
- **Judge a code change by IEP and CCC together:** fewer instructions is
  the change; more cycles at the same instruction count is placement.

## Detection

- **IPC:** the same instruction count (IEP1+IEP2) with a clearly
  different cycle count (CCC) between two builds.
- **A tool that maps the hot set:** one like tools/icachemap.py maps the
  functions of a PC profile onto the 512 sets and lists pairs that share
  sets.
- **For a quick proof:** padding before one function (code that never
  runs) changes the speed. A 1 KB pad made AllocMem 1.6x faster.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| I-cache 32 KB, 1-way; D-cache 2-way | (G) Willem Drijver 2026-11-26 | Core 12870 | core developer information |
| Same 1,131-1,154 instructions per RectFill 10x10; 1,815 vs 2,864 cycles in two layouts | (M) ApolloOS-Port finding-code-layout.md | Core 12870 | C:LineCheck RECT, 6,000 calls, CCC + IEP1/IEP2, 2 runs each |
| The colliding pair: gfx.hidd FillRect on 8 sets of graphics' do_render_with_gc | (M) tools/icachemap.py | Core 12870 | PerfSample profile at 500 Hz + vlink map |
| AllocMem 8 B 648 -> ~410 cycles from 1 KB of never-executed padding | (M) C:MemLoop CYCLES | Core 12870 | median of 2,000 calls, trial ROM |
| With a placed hot region: RectFill 10x10 28.0 -> 13.6 us, Signal+Wait 14.4 -> 12.0 us, no PerfSuite test slower than +3 % | (M) ApolloOS-Port runs/2026-11-27-0245-hot6-* | Core 12870 | C:PerfSuite, median of 31 samples |
