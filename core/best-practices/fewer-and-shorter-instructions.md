---
title: Use fewer instructions, then shorter encodings
type: best-practice
owner: WDrijver
status: draft
origin: ai-assisted
basis: [core-developer]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [68080, code-size, encoding, immediates, addressing-modes]
related:
  - core/cpu-68080/execution-units.md
  - core/best-practices/code-size-and-placement.md
  - core/cpu-68080/prm/integer/moviw.md
  - core/cpu-68080/prm/integer/addiw.md
sources:
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03), coding rules 1 and 2"
---

## Goal

Speed and code size: each instruction takes a slot in a group, and a group
is at most 16 bytes. Fewer instructions fill fewer slots; shorter encodings
fit more instructions in a group and in the I-cache.

## Technique

1. **Do it with fewer instructions, even if one is longer** (G).

   ```asm
       add.l   #9,d0           ; good: one instruction
   ```

   is better than

   ```asm
       addq.l  #8,d0           ; two dependent instructions
       addq.l  #1,d0
   ```

2. **Then use the shortest encoding available** (G):

   | Operation | Longest to shortest |
   |---|---|
   | Load an immediate | `move.l #imm` → `moviw.l #imm` → `moveq #imm` |
   | Add an immediate | `addi.l #imm` → `addiw.l #imm` → `addq.l #imm` |
   | Walk memory | `d16(An)` → `(An)+` |

   `(An)+` is often better than `d16(An)`: it is shorter, and the EA unit
   updates the pointer for free.

The guideline writes `MOVI.L`; the PRM names the instruction `MOVIW.L` (see
[prm/integer/moviw.md](../cpu-68080/prm/integer/moviw.md), and don't use its
LineA encoding).

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| `add.l #9,d0` against `addq.l #8,d0` + `addq.l #1,d0` | The single instruction is better | any | Statement (G) |

No measurement in the knowledge base yet.

## When not to use

- When the shorter form needs an extra instruction (rule 1 comes first).
- `(An)+` changes the pointer: when the code reads the same fields again,
  `d16(An)` can be the better choice.
