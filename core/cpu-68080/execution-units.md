---
title: 68080 execution units and instruction groups
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [68080, superscalar, groups, ea-unit, alu, branches, decoders]
related:
  - core/cpu-68080/superscalar-issue.md
  - core/cpu-68080/pipeline-15-stages.md
  - core/cpu-68080/branches-and-prediction.md
  - core/pitfalls/alu-to-ea-bubble.md
  - core/cpu-68080/prm/b-registers.md
sources:
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03)"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
---

## Summary

The 68080 executes instructions in groups of up to 16 bytes that run in the
same cycle. Three kinds of units do the work: the branch path in the I-cache
and branch target cache, two EA units that own the address registers, and
the ALUs that own the data registers. Most cores run 2 pipes; 3 are planned.

## Details

### Instruction groups (G)

- The I-cache reads instructions in 64-byte lines and feeds the decoders
  16 bytes per cycle.
- The core identifies groups of instructions that can run in the same cycle,
  and fetches and executes each group together. A group is at most 16 bytes
  (some I-cache variants allow 18).
- A group holds 1 to 6 instructions: independent instructions, or fused pairs
  (see [prm/instruction-fusing.md](prm/instruction-fusing.md)).
- Depending on the core, 2 or 3 decoders are enabled, so 2 or 3 operations
  run per cycle. With fusing, a 3-decoder core peaks at 6 instructions per
  cycle. Most cores today have 2 pipes active; 3 are planned (G, 2026-11-03).
  Gunnar will update these guidelines when cores with 3 pipes are produced.

### The units (G)

| Unit | Owns | Executes | Inputs | Writes |
|---|---|---|---|---|
| Branch path (I-cache and branch target cache), early in the pipeline | | `bra`, `bsr`, `bcc`, `dbra`, `jsr $abs`, `jsr d16(pc)`, `jmp $abs`, `jmp d16(pc)`, `rts`, `rtd` | | The program counter |
| Two EA units | The 16 address registers (A0–A7 and B0–B7) | `lea (ea),An`, `adda.w #imm,An`, `suba.l An/Dn,An`, `addq #n,An`, `subq #n,An`, `movea #imm,An`; the updates of `(An)+` and `-(An)` | An, Dn, `#imm` | Only An, and the address of the memory access |
| ALUs (most instructions) | The data registers | Everything else | Registers, `#imm`, memory | Dn or memory |

- `jmp (An)` is computed by the EA unit and takes much longer than the
  branches in the first row.
- `rts` is very fast as long as the return address on the stack is not
  overwritten (see
  [return-address-patching.md](../pitfalls/return-address-patching.md)).
- The core does some EA updates for free each clock: `(An)+` and `-(An)` cost
  nothing extra and encode short.
- A data register that the ALU writes and an EA unit then reads costs a
  bubble (see [alu-to-ea-bubble.md](../pitfalls/alu-to-ea-bubble.md)).

### Memory per cycle (G, 2026-11-03)

- The data cache does one read and one write per cycle. A loop of
  `add.l #1,memcounter` + `dbra` should run about 100 million times a second
  at 100 MHz: 100 million reads and 100 million writes, here to the same
  address. Measured on Core 12556: 2 cycles per iteration, see
  [caches-and-memory.md](caches-and-memory.md) (M, Core 12556, V4 UniCorn, `tools/v4/tests/add-mem-dbra`, 2026-11-09).
- One memory address is computed per cycle (one EAMEM in
  [pipeline-15-stages.md](pipeline-15-stages.md)). An instruction with two
  memory operands, such as `move.l (a0)+,(a1)+`, needs two addresses. A
  second memory EA unit, which would run it in 1 cycle, is a proposed
  extension, not part of current cores.

## Differences from AmigaOS / AROS / 68060

- The 68060 has no B registers and no 16-byte group issue; its pipes are not
  a model for the 68080 (see
  [pipeline-15-stages.md](pipeline-15-stages.md)).
- The 68080 resolves `jsr`/`jmp` to absolute and PC-relative targets in the
  branch path, but `jmp (An)` in the EA unit.

## Do / Don't

- DO keep pointers in address registers and data, counters and arithmetic in
  data registers.
- DO update pointers with EA instructions (`addq`, `adda`, `lea`) or with
  `(An)+`, not with the ALU.
- DO call and jump through absolute or PC-relative targets in hot code, not
  through `(An)`.
- DON'T overwrite return addresses on the stack.
