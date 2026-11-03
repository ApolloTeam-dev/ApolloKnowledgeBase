---
title: 68080 pipeline, 15 stages
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, pipeline, stages, hazards, latency]
related:
  - core/cpu-68080/prm/pipeline.md
  - core/pitfalls/alu-to-ea-bubble.md
  - core/cpu-68080/superscalar-issue.md
sources:
  - "Apollo team diagram \"APOLLO 68080 CPU Architecture\", 2026-10-23"
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 1.1"
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03)"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
---

## Summary

The PRM's 7 pipeline stages are a summary. The Apollo team's architecture
diagram shows 15 stages (L00 to L14). They explain the one memory access per
cycle, the ALU-to-EA bubble, and why FPU and AMMX run in pipe 1 only.

## Details

### Stages

| Stage | What happens there |
|---|---|
| 0 | BTC + PC → I-cache read (can stall) |
| 1 | Mux and rotate the instruction words |
| 2 | 3 decoders in parallel: operation size (decoder 1 can stall the front end) |
| 3 | Pre-mux, sort the EA |
| 4 | Decode the operands |
| 5 | Immediate mux, sort the #imm |
| 6 | **Schedule unit** (can stall): one group of up to 3 instructions goes out |
| 7 | 3 address-register reads |
| 8 | **3 EA units (A, B, C) + one EAMEM**, the single memory address of the cycle |
| 9 | **Hazard unit** (can stall) |
| 10 | 3 data-register reads, **D-cache read**, FP register read, vector register read |
| 11 | **3 ALUs (A, B, C)**, FPU (64-bit), AMMX (drawn as 128-bit: a beta unit not in released cores) |
| 12 | **Write stage** (G): all registers are written here (address, data, FP, vector), plus the **D-cache write**. The diagram labels the address boxes "ADDR REG RE", but they are writes |
| 13 | Write combining |
| 14 | Write FIFO → memory (can stall) |

The stall points are the I-cache read, decoder 1, the schedule unit, the
hazard unit, the D-cache read and the write FIFO.

### What the diagram explains

- **One memory address per cycle.** There is one EAMEM, shared by all
  pipes. Two loads in one cycle are impossible by design. The data cache does
  one read and one write per cycle, so a read-modify-write such as
  `add.l #1,mem` runs at about 1 per cycle (G, 2026-11-03).
- **The ALU-to-EA bubble.** Addresses are computed at stage 8; an ALU result
  arrives at stage 11/12. A Dn produced by the ALU and used for an address by
  a following instruction arrives 3–4 stages too late (M: write it about 4
  cycles earlier). A load into An used as an address waits the same way
  (D-cache read at 10, register write at 12): load → indexed load measured
  about 4 cycles (M). See [alu-to-ea-bubble.md](../pitfalls/alu-to-ea-bubble.md).
- **Load then use is cheap.** The D-cache read (10) sits right before the ALU
  (11), so a loaded value feeds the ALU without a bubble.
- **FPU and AMMX only in pipe 1.** Only decoder 1 feeds the FPU and AMMX. This
  matches the counters: every FPU instruction counts in IEP1 (M).
- **Three ALUs, three EA units.** The hardware for 3 pipes is drawn; Core
  12798–12841 enables 2 (IEP3 = 0, M).
- **Write-through cache with write combining** (G). Writes go to memory
  through write combining and a write FIFO: for a few cycles the CPU collects
  writes, then commits them to the memory controller. That makes loops such
  as memclr and memcopy efficient, and fits quad-store fusing and contiguous
  writes.
- **Branches are checked after the ALU** (G). There the CPU redirects the PC
  when a Bcc or an RTS was mispredicted, and feeds the outcome back to the
  BTC.

### How a group is issued (G, 2026-10-29)

- Several instructions travel down the pipeline together as one group.
- The schedule stage checks that every register the group uses is ready. If
  one is not, the whole group waits. The hazard unit repeats the check before
  the ALU.
- So one late register (a load or multiply in flight, or a Dn needed by the
  EA stage) holds back every instruction paired with it. Dependency chains and
  the ALU-to-EA bubble cost whole cycles, not single slots.

## Differences from AmigaOS / AROS / 68060

- The PRM ([prm/pipeline.md](prm/pipeline.md)) lists 7 stages and a 2-cycle
  ALU-to-EA bubble. The diagram shows 15 stages. Gunnar counts the bubble as
  2 cycles and says it may grow in future cores (G, 2026-11-03); to hide it
  fully, the measurements needed the Dn written about 4 cycles earlier (M).
- The 68060's pipelines are not a model for the 68080: its EA and ALU stages
  and its memory port differ.

## Do / Don't

- DO compute addresses at least 4 cycles before use, or keep them in An.
- DON'T plan for two memory accesses in one cycle.
- DON'T expect FPU or AMMX instructions in pipe 2.
