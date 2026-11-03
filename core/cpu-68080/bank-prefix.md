---
title: 68080 BANK prefix and register naming (measured)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, bank, e-registers, b-registers, encoding]
related:
  - core/cpu-68080/prm/integer/bank.md
  - core/cpu-68080/prm/b-registers.md
  - core/pitfalls/bank-prefix-pitfalls.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 7.1"
---

## Summary

The BANK prefix (`$71xx`) gives legacy instructions access to E0–E23. On a
single-register operand both bank fields must be set. Banking works for a
list of instructions and is still wrong for another list.

## Details

### Register naming

- Team naming (G): D0–D31 and A0–A15, where E0–E7 = D8–D15, E8–E15 =
  D16–D23, E16–E23 = D24–D31, and B0–B7 = A8–A15.
- vasm still wants `e0`–`e23` and `b0`–`b7`.

### Encoding

- BANK prefix `$71xx`, layout `0111 ccc1 SSCC AABB`.
- AA banks the register **source**, BB the register **destination**:
  `01` = E0–E7, `10` = E8–E15, `11` = E16–E23.
- `$71xx` with SS ≠ 0 is illegal.
- BANK runs in pipe 2 at full speed and fuses. It counts as one instruction
  in IEP1/IEP2 (M).

### Single register operand

For instructions with one register operand (tst, clr, neg, not, ext, swap,
scc, bitfields, the dbcc counter) and for `#imm,Rn`: **AA must equal BB**,
for example `$7105`, `$710A`, `$710F` (official, M).

- AA alone: the plain Dn is used.
- BB alone: looks right on a cold pass, but in a trained loop pipe 2 reads the
  plain Dn (M).

### What works and what does not (Core 12830–12841, M)

| Banking works | Banking does not work yet |
|---|---|
| move, moveq, addi, subi, eor, eori, ori, andi, not, neg, negx, btst, tst, bclr, clr, bset, bchg, swap, scc, bfclr, bfset, bftst, bfchg, bfffo, ext, extu, cmpi, shifts and rotates (a banked shift count too), moviw.l, perm | add, sub, and, or, cmp, addx, subx, mul, div, abcd, sbcd, pack, unpk, exg, bfextu, bfexts, bfins |

Examples of the failures:

- `add.l e6,d1` computed d6 + d6.
- `exg Dn,En` writes En, but Dn gets the plain register.
- `cmp.l En,Dn` (`$7104`, AA = source) uses the plain Dn on the first two
  passes and the right En from the third pass on (Core 12841).
- `add.l #imm,En` works with AA = BB (`$7105`, `$D2BC`) on every pass.

### B registers

- Supported forms: `movea.l <ea>,Bn`, `move.l Bn,<ea>` (ea not An/Bn),
  `lea <ea>,Bn`, `lea (Bn),An`, `addq/subq #,Bn` (CCR unchanged) and
  `cmp.l Bn,Dn`. B registers are fully usable as AMMX address registers.
- On Core 12841 all these forms give the right result on every pass of a
  5-pass loop, including `addq` after `movea.l` or `lea`, and AMMX
  `load (Bn)` (M).
- `add.l Bn,Dn` and `move.l An,Bn` are not supported.

### Task switches

E and B registers survive task switches only with the Apollo bit set (SR
bit 11, per program) or under ApolloOS. See
[prm/apollo-bit.md](prm/apollo-bit.md).

### FPU

The team has decided: **no BANK prefix on FPU instructions** in future cores
(G, 2026-10-26). A new FPU encoding with 32 FP registers is planned.

## Differences from AmigaOS / AROS / 68060

- The 68000–68060 have no BANK prefix, no E and no B registers.
- The PRM's BANK page says AA = BB for single operands; vasm 2.0f/2.0g does
  not follow that. See [bank-prefix-pitfalls.md](../pitfalls/bank-prefix-pitfalls.md).

## Do / Don't

- DO set AA = BB for single-register operands and `#imm,Rn`.
- DON'T bank the instructions in the "does not work yet" column. Do the
  arithmetic in a plain Dn.
- DON'T put a BANK prefix on FPU instructions in new code.
