---
title: vasm 68080 encodings that are wrong or missing
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain, cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [vasm, bank, ammx, encoding, branches, listing]
related:
  - core/pitfalls/bank-prefix-pitfalls.md
  - core/pitfalls/ammx-pc-relative-source.md
  - core/pitfalls/tex-does-not-match-prm.md
  - toolchain/vasm-assembler.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 9.4"
  - "ApolloCrossDev Compilers/_archives/vasm/vasm.tar.tar: vasm 2.0f"
---

## Symptom

Assembled 68080 code does something else than the source says, or the
binary differs from what another assembler (Devpac, ASM1) produces, without
any error or warning from vasm.

## Cause

vasm 2.0f/2.0g (ApolloCrossDev ships 2.0f) handles these 68080 cases
differently from the core:

| Source | What vasm does | Effect |
|---|---|---|
| BANK single operand (`tst e6`, `clr e2`) | Sets AA only | Uses the plain Dn: `tst e6` tests d6 |
| `add.l #imm,En` | Sets BB only (`$7101`) | Writes plain Dn + imm into En |
| `add.l b1,d0` | Emits `$71F1`, a BANK word with SS ≠ 0 | Illegal instruction |
| `move.l a0,b1` | Rejects it | Not a supported form anyway |
| AMMX PC-relative source (`load .k(pc),d0`) | Counts the displacement from the third word; the core counts from the second | Reads 2 bytes early |
| An out-of-range `.s` branch with `-m68080` | Silently emits the 080-only `.s+` | Runs only on the 68080 |
| abs, min, max, andn | Assembles them | They do nothing on the core and raise no exception |
| TEX | No syntax in 2.0g | Needs `dc.w` |
| movz2, moveh, some `touch (An,Xn)` forms | Not available | Needs `dc.w` |
| `load` at the top of a file | Taken as a directive | Assembly error or wrong code |

Without `-no-opt`, vasm also emits `and/or/sub #imm` instead of
`andi/ori/subi`, rewrites branch sizes and turns `move.l #imm` into `moveq`,
so binaries are not byte-identical to Devpac builds.

## Wrong

```asm
    tst.l   e6              ; assembles as tst.l d6
    load    .k(pc),d0       ; reads .k - 2
```

## Right

- Hand-encode BANK single-operand and `#imm,Rn` forms with AA = BB (see
  [bank-prefix-pitfalls.md](../../core/pitfalls/bank-prefix-pitfalls.md)).
- Load AMMX data through `lea .k(pc),An` + `load (An),Dn`.
- Don't use abs/min/max/andn.
- Use `-no-opt` for byte-exact round trips and for CPU tests.
- Decode every hand-encoded `dc.w` back with an 080-aware disassembler and
  check its length.

## Detection

Assemble with `-L file.lst` and check:

- BANK words (`$71xx`) in front of single-operand and `#imm` instructions;
- odd displacement bytes in `.s` branches (the `.s+` form);
- `(pc)` source operands on AMMX instructions.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Encodings in the table above | (M) | Core 12841 | vasm 2.0f/2.0g listings run on the V4 |
| ApolloCrossDev ships vasm 2.0f | (SRC) | any | `vasm.c`: `_VER "vasm 2.0f"` |
| The vasm opcode table (`cpus/m68k/opcodes.h`, "apollo" entries) is a good encoding reference | (SRC) | any | vasm source |
