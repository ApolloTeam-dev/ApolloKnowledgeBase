---
title: 68080 CPU overview
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
related:
  - core/cpu-68080/prm/index.md
sources:
  - "Apollo 68080 Programmer's Reference Manual, AC68080PRM.odt (update okt 2026)"
---

## Summary

The Apollo 68080 CPU, successor of the Motorola 68000 family, with the AMMX
SIMD extension. Its reference is the 68080 Programmer's Reference Manual,
converted in [prm/](prm/index.md).

## Details

### Where to look

| Topic | File |
|---|---|
| Any 68080 instruction, by mnemonic | [prm/index.md](prm/index.md) |
| Registers (D, A, B, E, FP) | [prm/programming-model.md](prm/programming-model.md) |
| Integer unit, BANK prefix, 3 operands | [prm/integer-unit.md](prm/integer-unit.md) |
| AMMX SIMD unit and its instruction format | [prm/ammx-unit.md](prm/ammx-unit.md), [prm/ammx/ammx-format.md](prm/ammx/ammx-format.md) |
| Floating point unit | [prm/fpu-unit.md](prm/fpu-unit.md) |
| Apollo bit (SR bit 11), LineA instructions | [prm/apollo-bit.md](prm/apollo-bit.md) |
| Superscalar pipes, fusing, pipeline | [prm/superscalar.md](prm/superscalar.md), [prm/instruction-fusing.md](prm/instruction-fusing.md), [prm/pipeline.md](prm/pipeline.md) |
| Cycle counts, benchmark, optimizing | [prm/instruction-timing.md](prm/instruction-timing.md), [prm/instruction-efficiency.md](prm/instruction-efficiency.md), [prm/optimizing.md](prm/optimizing.md) |
| Caches, bus, trace | [prm/specs.md](prm/specs.md), [prm/trace.md](prm/trace.md) |

### From the core developer and measured on V4 cores (rank above the PRM when they disagree)

| Topic | File |
|---|---|
| Key numbers: clock, pipes, caches, AttnFlags | [core-at-a-glance.md](core-at-a-glance.md) |
| The real 15-stage pipeline | [pipeline-15-stages.md](pipeline-15-stages.md) |
| Execution units (branch path, EA units, ALUs), 16-byte instruction groups | [execution-units.md](execution-units.md) |
| Second pipe, pairing, learning, fusing measured | [superscalar-issue.md](superscalar-issue.md) |
| Branch costs, prediction, predication | [branches-and-prediction.md](branches-and-prediction.md) |
| Cycle costs per instruction | [measured-instruction-costs.md](measured-instruction-costs.md) |
| FPU performance model | [fpu-performance-model.md](fpu-performance-model.md) |
| Cache lines, streaming, misses, alignment | [caches-and-memory.md](caches-and-memory.md) |
| BANK prefix, E and B registers | [bank-prefix.md](bank-prefix.md) |
| ISA notes beyond the PRM | [isa-notes-measured.md](isa-notes-measured.md) |
| CCC and IEP counters | [performance-counters.md](performance-counters.md) |
| Core bugs, by core revision | [core-bugs-by-revision.md](core-bugs-by-revision.md) |

Best practices and pitfalls for the 68080 are in `core/best-practices/` and
`core/pitfalls/`.

The files in `prm/` are generated from the original manual in
`sources/official/` and are never edited by hand. Other 68080 content goes
next to `prm/` in this folder.

### Not covered yet

- A full 68080 instruction set reference: the manual covers only what the
  68080 adds to the 68000 family. For the classic instructions, the Motorola
  manuals apply.
- `differences-from-68060.md`: what a 68060 programmer would wrongly assume,
  collected in one place. Until then, see the "Differences" section of each
  file.

### For contributors

Check the ApolloCrossDev `Docs/` folder (`AMMX/`, `FPU/`, `Integer/`) and the
68080 coding pages on apollo-core.com. Start new files from
`templates/files/reference.md`.

## Differences from AmigaOS / AROS / 68060

Each file in `prm/` states its differences from the 68000–68060.

## Do / Don't

- DO look up a 68080 instruction in [prm/index.md](prm/index.md) before
  using it.
- DON'T invent register addresses, bit meanings or instruction behavior for
  the 68080 CPU. If the knowledge base does not cover it, say so.
