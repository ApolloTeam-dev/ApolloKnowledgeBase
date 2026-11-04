---
title: 68080 superscalar issue and pairing (measured)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, superscalar, pairing, pipes, fusing, learning]
related:
  - core/cpu-68080/prm/superscalar.md
  - core/cpu-68080/prm/instruction-fusing.md
  - core/cpu-68080/pipeline-15-stages.md
  - core/best-practices/use-fusable-pairs.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 2.1-2.4"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
---

## Summary

On released V4 cores, two pipes issue instructions. The second pipe takes
short single-cycle instructions only, two instructions pair only when they
are independent (or fuse) and need at most one data-cache access, and pairing
only starts on the second pass over the code.

## Details

### What can go in the second pipe (G)

- At most 8 bytes long, BANK prefix included.
- Single-cycle: no mul, div, movem or fmovem.
- Not a system instruction (reset, stop, cache flush, move to/from ccr/sr).
- In practice: move, and, or, add, sub, cmp, ori, andi, subi, eori, cmpi,
  btst/bclr/bset/bchg, movea, jsr, jmp, rts, bsr, not, neg, swap, pea, clr,
  ext, lea, dbra, bcc, bra, moveq, suba, adda, cmpa, tst and the shifts.
- Never in pipe 2:
  - addx, subx, negx (they need the flags from pipe 1, not ready mid-cycle);
  - bitfields;
  - memory-indirect modes `([bd,An],Xn,od)`;
  - all FPU instructions (M) and all AMMX instructions except stores (M).
- `jmp`/`jsr` to a PC-relative or abs.l target go to pipe 2. Through `(An)`,
  `d16(An)` or `(d8,An,Xn)` they stay in pipe 1 and cost about +5 cycles (+6
  on Core 12840); `([An])` costs +7 (M).

### Pairing conditions

- The two instructions are fully independent, or form a fused pair (see
  [prm/instruction-fusing.md](prm/instruction-fusing.md)).
- Together they fit in one group of at most 16 bytes (some I-cache variants:
  18) (G, 2026-11-03). See [execution-units.md](execution-units.md).
- Together they need at most one data-cache access.
- Measured pairs with an independent `add.l` (M): `smi`, `extb.l`, `ext.l`,
  `swap`, `asr/lsr #n`, `rol.l`, `move.w`, `move.b`, `eor`, `tst.b`,
  `and.l #imm`, `moveq`, `neg`, `addq`, `cmp.l An,Dn`, indexed loads,
  `move.l Dn,(An)+`.
- `nop` is a pipeline barrier.

### Learning

- The first time a piece of code runs, it issues on one pipe. From the second
  pass of a loop, the other pipe is used.
- Straight-line code that runs once (init code, a single table pass) never
  pairs.
- Routines called many times pair fine: 2048 straight `add`s, called
  repeatedly, ran at about 1.9 IPC (M).

### Fusing, measured

The PRM's fusing table holds, with these measurements (M, Core 12841):

- 16 instructions of `move.l dn,dm` + `add.l` ran in 5.1 cycles when adjacent
  and 9.1 cycles when split apart. The same pair with E registers fused at 1
  per cycle.
- `subq.l #1,dn` + `bne.s/.s+/.w` fuses; `bpl` does not.
- `moveq #0,dn` + `move.b/w (ea),dn` fuses into a zero-extending load.
- FPU: `fmove.x fpn,fpm` + `fmul.x`/`fadd.x fpx,fpm` fuses (registers only)
  with correct values and FPSR flags. Cycles per pair, adjacent / split:

  | | Independent pairs | Dependent chain |
  |---|---|---|
  | fmul | 1.12 / 2.25 | 5.00 / 6.00 (fuses) |
  | fadd | 1.12 / 2.62 | 6.00 / 7.00 (fuses) |
  | fsub | 2.62 / 2.62 | 7.00 / 7.00 (does not fuse; results still right) |

- IEP1/IEP2 count a fused FPU pair as 2 instructions: detect FPU fusing with
  CCC, not with IEP.
- Two fused `move.l (an)+,(am)+` read 8 bytes before writing. See
  [fused-copy-overlap.md](../pitfalls/fused-copy-overlap.md).

## Differences from AmigaOS / AROS / 68060

- The PRM ([prm/superscalar.md](prm/superscalar.md)) describes three pipes
  (Anton, Bruno, Cesar). Released cores up to 12841 enable two (M).
- Unlike the 68060, the 68080 pairs only after it has seen the code once.
- `fsub` does not fuse, although it is an FPU arithmetic instruction like
  fadd and fmul.

## Do / Don't

- DO judge pairing only on trained (second and later) passes.
- DO write the copy and the operation next to each other (`move.l d0,d1` +
  `add.l d2,d1`): they fuse into one 3-operand instruction.
- DON'T put `nop` in hot code: it is a pipeline barrier.
- DON'T call through `(An)` or `d16(An)` in hot code when a PC-relative or
  absolute target works: it costs about 5 cycles more.
- DON'T use `fsub` in a 3-operand fused pair: negate the operand and use
  `fadd`.
