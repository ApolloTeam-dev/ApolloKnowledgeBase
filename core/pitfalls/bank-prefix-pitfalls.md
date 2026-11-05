---
title: BANK prefix traps (single operands, unsupported instructions, B registers)
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080, toolchain]
applies_to:
  core: "Core 12830-12841"
  os: [any]
tags: [68080, bank, e-registers, b-registers, vasm, encoding]
related:
  - core/cpu-68080/bank-prefix.md
  - core/cpu-68080/prm/integer/bank.md
  - core/cpu-68080/prm/b-registers.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 23), 7.1 and 9.4"
---

## Symptom

Code with E registers silently uses a plain D register instead: `tst e6`
tests d6, `add.l e6,d1` computes d6 + d6, or a loop gives the right result on
its first pass and the wrong one when trained.

## Cause

- For a single-register operand (tst, clr, neg, not, ext, swap, scc,
  bitfields, the dbcc counter) and for `#imm,Rn`, both bank fields must be
  set: AA = BB (official). With AA alone the plain Dn is used; with BB alone
  the cold pass looks right, but in a trained loop pipe 2 reads the plain Dn.
- **vasm 2.0f/2.0g puts single operands in AA only**, so `tst e6` silently
  becomes `tst d6`. For `add.l #imm,En` it sets BB only (`$7101`), which
  writes plain Dn + imm into En.
- Banking does not work yet for add, sub, and, or, cmp, addx, subx, mul,
  div, abcd, sbcd, pack, unpk, exg, bfextu, bfexts, bfins (official list,
  confirmed on Core 12830/12840).
- `cmp.l En,Dn` uses the plain Dn on the first two passes and the right En
  from the third pass on (Core 12841).
- `add.l Bn,Dn` and `move.l An,Bn` are not supported B-register forms. vasm
  2.0g rejects `move.l a0,b1` and turns `add.l b1,d0` into `$71F1`, a BANK
  word with SS ≠ 0, which is illegal.

## Wrong

```asm
    tst.l   e6              ; vasm: AA only -> tests d6
    add.l   #1,e3           ; vasm: BB only -> e3 = d3 + 1
    add.l   e6,d1           ; banking not supported -> d1 = d6 + d6 ... wrong
    cmp.l   e2,d0           ; plain d0 on cold passes
```

## Right

- Hand-encode single-operand and `#imm,Rn` BANK forms with AA = BB, for
  example `$7105`, `$710A`, `$710F` as the prefix word, and `$7105`, `$D2BC`
  for `add.l #imm,En`.
- Do arithmetic and compares in a plain Dn: move the E register into a Dn,
  operate, move it back.
- Use only the supported B-register forms (see
  [bank-prefix.md](../cpu-68080/bank-prefix.md)).

## Detection

Decode every hand-encoded `dc.w` with an 080-aware disassembler and check its
length. Check vasm listings (`-L`) for BANK words on single-operand and
`#imm` instructions. Test banked code over several passes: the cold pass
hides the error.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| AA = BB for single operands; list of instructions where banking is not handled correctly | (official) PRM, BANK and integer-unit pages | any | Manual |
| BB alone fails in trained loops; `add.l e6,d1` = d6 + d6; `cmp.l En,Dn` wrong on cold passes | (M) | Core 12830-12841 | Regression tests, cold and trained passes |
| vasm 2.0f/2.0g encodes single operands with AA only, `add.l #imm,En` with BB only | (M) | any | vasm listings |
