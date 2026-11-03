---
title: 68080 core bugs by core revision
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080, saga-3d-maggie]
applies_to:
  core: "Core 12001-12847"
  os: [any]
tags: [68080, bugs, core-revision, regression]
related:
  - core/pitfalls/fpu-broken-instructions.md
  - core/pitfalls/ammx-pc-relative-source.md
  - core/pitfalls/ammx-upper-32-bits.md
  - core/pitfalls/bank-prefix-pitfalls.md
  - core/pitfalls/tex-does-not-match-prm.md
  - core/pitfalls/maggie-depth-test-colour-write.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 4.2, 6, 7.3 and 15.7"
---

## Summary

Core bugs seen on V4 cores 12001 to 12847, and which are fixed. Each open bug
has its own pitfall file. Check this list against your core: a new core can
fix or add bugs.

## Details

### Fixed

| Bug | Fixed in |
|---|---|
| `cmp.l Bn,Dn` ignored Bn | Core 12840 |
| `move En,Dn` in pipe 2 paired with a pipe-1 instruction writing the same register | Fixed (core not recorded) |
| `FDBcc` never decremented and always branched (Core 12830/12840) | Core 12841 |
| `move2.l (An),Dx:Dy` loaded the second register wrong (Core 12001) | Checked fixed on Core 12841 |
| `addq.l #n,Bn` added to a hidden register (Core 12001) | Checked fixed on Core 12841 |
| `lea (Bn),An`, AMMX `(Bn)` wrong (Core 12001) | Checked fixed on Core 12841 |

### Still wrong on Core 12841

| Area | Bug | Pitfall |
|---|---|---|
| FPU | FScc to `d16(An)`/`d8(An,Xn)`, FTRAPcc, `flognp1`, dynamic `fmovem` list, `fmove.x` memory operands | [fpu-broken-instructions.md](../pitfalls/fpu-broken-instructions.md) |
| FPU | Transcendental, `fdiv` and `fsqrt` precision; `fadd` rounds toward zero; FPCR precision ignored; `fint` ties | [fpu-precision-and-rounding.md](../pitfalls/fpu-precision-and-rounding.md) |
| FPU | FPSR exception bytes and traps never set | [fpu-exceptions-never-trap.md](../pitfalls/fpu-exceptions-never-trap.md) |
| AMMX | PC-relative sources read 2 bytes early | [ammx-pc-relative-source.md](../pitfalls/ammx-pc-relative-source.md) |
| AMMX | `move.l #imm` clears the upper 32 bits on trained passes | [ammx-upper-32-bits.md](../pitfalls/ammx-upper-32-bits.md) |
| BANK | `cmp.l En,Dn` uses the plain Dn on cold passes | [bank-prefix-pitfalls.md](../pitfalls/bank-prefix-pitfalls.md) |
| TEX | Does not match the PRM's byte form (Core 12846) | [tex-does-not-match-prm.md](../pitfalls/tex-does-not-match-prm.md) |
| Maggie | Depth test does not gate the colour write; the last 8 bytes of a span stay in the unit (Core 12847) | [maggie-depth-test-colour-write.md](../pitfalls/maggie-depth-test-colour-write.md), [maggie-span-tail.md](../pitfalls/maggie-span-tail.md) |

## Differences from AmigaOS / AROS / 68060

These are 68080 core bugs. The same code runs correctly on a 68060; do not
work around them on other CPUs.

## Do / Don't

- DO note the core revision with every measurement and bug report.
- DO recheck this list when you move to a new core.
- DON'T rely on a fix from a core you have not tested on.
