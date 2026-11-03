---
title: The ALU-to-EA bubble
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, pipeline, addressing, latency, index]
related:
  - core/cpu-68080/pipeline-15-stages.md
  - core/cpu-68080/prm/pipeline.md
  - core/best-practices/close-loops-with-dbra.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rules 2-3) and 2.5"
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03)"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
---

## Symptom

Code that computes an index or address in a data register and uses it right
away runs 2–3 cycles slower per use than expected, and the instructions
paired with it wait too. It is the most common hidden cost on the 68080.

## Cause

The EA unit owns the address registers and computes addresses at stage 8;
the ALU owns the data registers and delivers its result at stage 11/12. A Dn
written by any instruction and then used for addressing arrives 3–4 stages
too late. EA to EA and ALU to ALU have no latency.

- Producers that cause it: add, moveq, `move.l Dn,Dn`, a load into Dn,
  bfextu, any write to Dn.
- Consumers that suffer: indexed loads, `lea (An,Dn)`, `move.l Dn,An`, a `*4`
  scaled index, the Dn offset of a memory bitfield.

## Wrong

```asm
loop:
    addq.l  #4,d0           ; ALU writes d0 ...
    move.l  (a0,d0.l),d1    ; ... EA needs d0 now: bubble
    add.l   d1,d2
    dbra    d7,loop
```

## Right

Keep pointers and counters that drive addressing in An, and update them with
`addq`/`subq`/`lea`/`adda`, or walk memory with `(An)+`:

```asm
loop:
    move.l  (a0)+,d1        ; address register updated in the EA unit
    add.l   d1,d2
    dbra    d7,loop
```

Other fixes:

- Keep every register of an indexed mode `(d8,An,Xn)` updated by the EA
  unit: then the mode is safe and good (G). Use an address register as the
  index counter and step it with `addq`, `adda` or `lea`.
- Write `clr.l (a0)+`, or use `(a0,a1)` + `addq.l #4,a1`.
- Compute offsets at least 4 cycles (about 8 paired instructions) before
  use, or have the caller pass ready-made pointers loaded straight into An.
- Test an An with `tst.l An` or `move.l An,Dn`.

## Detection

Look for a Dn written by an ALU instruction and used as an index, base or
bitfield offset within the next few instructions. Measure with CCC: a chain
that costs 3 or more cycles per link instead of 1 points here.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| ALU to EA costs a bubble of 2 cycles | (official) PRM pipeline page | any | Manual |
| A Dn written 3 cycles before the EA use gives a 2-cycle bubble; future cores may make it longer, so always avoid it | (G) | any | Statement, 2026-11-03 |
| An indexed mode is safe when the ALU last changed its registers 2 cycles ago (up to 12 instructions on a core with 3 pipes and fusing) | (G) | any | Coding guidelines draft |
| Adjacent: +2 to 3 cycles; 4 paired fillers: +2; 6: +1; 8 or more: 0 | (M) | Core 12841 | Producer + consumer with fillers, CCC |
| add → `(a,d0)` load → add: 3 cycles per link | (M) | Core 12841 | Chain, CCC |
| load → indexed load: 4 cycles per link | (M) | Core 12841 | Chain, CCC |
| add d0 → `bfextu (a0){d0:w}` → add: 5 cycles per link | (M) | Core 12841 | Chain, CCC |
| A table lookup whose index was just computed: about 5.4 cycles per iteration | (M) | Core 12841 | Hot loop, CCC |
| Keeping values in a3–a6 inside generated arithmetic code cost about 6 % (992 vs 931 cycles, IMDCT) | (M) | Core 12841 | CCC |
