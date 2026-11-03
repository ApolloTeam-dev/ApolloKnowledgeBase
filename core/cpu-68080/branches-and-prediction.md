---
title: 68080 branch costs and prediction (measured)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, branches, prediction, btc, rts, predication]
related:
  - core/best-practices/predicated-bcc-over-one-instruction.md
  - core/best-practices/close-loops-with-dbra.md
  - core/pitfalls/alternating-branch-mispredicted.md
  - core/pitfalls/return-address-patching.md
  - core/cpu-68080/prm/integer/bcc-s-plus.md
  - core/cpu-68080/prm/integer/dbcc-l.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 2.6"
---

## Summary

A mispredicted Bcc costs about 7 cycles, a mispredicted RTS about 9.5. The
predictor does not learn a strict alternation. A `bcc.s` over one
single-cycle instruction is executed as a conditional instruction and is
never mispredicted.

## Details

### Costs

Test: forward `beq` over 2 instructions, flag from `tst.b (a0)+` on a table,
65536 branches, CCC counter, median of 7 (M, Core 12841, 2026-10-29).

| Direction pattern | `beq.w` / `beq.s` over 2 instructions | `beq.s` over 1 instruction | No branch |
|---|---|---|---|
| Always taken | 3.0 cycles per turn | 3.0 | 2.0 |
| Never taken | 4.0 | 3.0 | 2.0 |
| Random (50 %) | 7.0 (+3.5 = half of 7) | 3.0 | 2.0 |
| Alternating T/N/T/N | **10.5** (+7: every one mispredicted) | 3.0 | 2.0 |

- `.w` and `.s` cost the same here.
- A misprediction is detected after the ALU stage (G); a mispredicted RTS is
  caught there too.
- **Mispredicted RTS: about 9.5 cycles.** A `bsr` + `rts` turn took 4.6
  cycles normally and 14.0 when the routine moved its return address
  (`addq.l #2,(sp)`) (M).
- An inner `dbra` loop of random length 1–4 cost no more than the average of
  the fixed lengths. But each extra turn of such a tiny loop cost 3 cycles,
  and one turn about 12 (M).
- `rtd` used as a jump cost about 45 cycles (M).
- Computed and indirect jumps mispredict more. A table of `bra.s` through
  `jmp (table,pc,dn.w)`, or an address read from memory, is predicted;
  compute the index early.

### Predication

A `bcc.s` over **one** instruction is executed as a conditional instruction
when the skipped instruction:

- is at most 8 bytes long;
- is single-cycle;
- does not change an An. So `(An)+`, `-(An)`, `addq An` and `lea` are not
  predicated.

Measured: 3.0 cycles whatever the pattern, never mispredicted (M).

### 080 branch sizes

- `bcc.s+`: an odd displacement byte gives +128..+254 and −256..−132. −130 is
  impossible (`$FF` means `.l`). Byte = displacement − 127 forward, and
  displacement + 129 backward.
- `dbcc.l`: an odd displacement word means a 32-bit counter (displacement
  word = displacement + 1).

## Differences from AmigaOS / AROS / 68060

- A loop closed with `bne.w` is not accelerated on the 68080. Close loops
  with `dbra` or a fused `subq.l #1,Dn` + `bne.s`: loop overhead goes from 3
  cycles to 1 (M). Do not carry over 68060 loop-closing habits unmeasured.
- A `bcc.s` over one instruction becoming a conditional instruction is 68080
  specific.
- The return cache makes RTS cheap only when the return address is not
  changed.

## Do / Don't

- DO leave a `bcc.s` over one single-cycle instruction alone: do not replace
  it with Scc + mask.
- DO keep a `bcc.s *+4` and its skipped instruction adjacent when you
  interleave code. An FPU instruction inserted between them made the branch
  land inside it ("CHK instruction error").
- DON'T write branches that flip every iteration: unroll by 2, or compute the
  value without a branch.
- DON'T patch return addresses, `pea` + `rts`, or use `rtd` as a jump. To fall
  back to an original routine, use `jmp ([ptr,pc])`, which is predicted.
- DO special-case very short loops (1–4 turns) and pull small cases out of
  size-dispatch code: benchmark with random sizes.
