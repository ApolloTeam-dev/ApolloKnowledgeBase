---
title: Memory indirect addressing blocks the core (except in JMP and JSR)
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [68080, addressing-modes, memory-indirect, stall, jmp, jsr]
related:
  - core/pitfalls/alu-to-ea-bubble.md
  - core/cpu-68080/execution-units.md
  - core/cpu-68080/branches-and-prediction.md
  - toolchain/compiler-variants.md
sources:
  - "Gunnar (core developer), Simply 68080 coding guidelines, draft (2026-11-03), coding rules 2 and 6"
  - "Gunnar (core developer), answers to questions on the guidelines, 2026-11-03"
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 2.1"
---

## Symptom

Code that uses the memory indirect modes `([bd,An],Xn,od)` or
`([bd,An,Xn],od)` runs very slowly, and the instructions around it stall
too.

## Cause

In a memory indirect mode the address comes from memory. The EA unit has to
wait for that load, which is by definition an ALU-to-EA dependency stall
(G). The mode is very slow and blocks the core. It never goes to the second
pipe (see [superscalar-issue.md](../cpu-68080/superscalar-issue.md)).

`jmp` and `jsr` through this mode are the exception: technically they work
differently, as a special form of an `rts` (G). A jump through a table of
pointers is fine.

## Wrong

```asm
    move.l  ([table,a0],d0.l*4),d1  ; blocks the core
```

## Right

Load the pointer into an address register first, well before it is used,
and then address through it:

```asm
    movea.l (table,a0),a1           ; load the pointer early
    ; ... other work ...
    move.l  (a1,d0.l*4),d1
```

A jump table may keep the mode:

```asm
    jmp     ([disptab,pc,d0.l*4])   ; fine: jmp through memory indirect
```

## Detection

Search the assembly for `([`. Every hit outside `jmp` and `jsr` is a
candidate.

GCC-6.50-Dev applies `double-indirect-fix.patch`, which stops GCC from
generating this mode. On 2026-11-03 that patch is suspected of a compiler
crash on computed gotos (`goto *disptab[i]`), which are exactly the allowed
`jmp` form; Gunnar confirms GCC may keep that form (see
[compiler-variants.md](../../toolchain/compiler-variants.md)).

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Memory indirect is slow and blocks the core; don't use it | (G) | any | Statement |
| In instructions other than `jmp`/`jsr` it is an ALU-to-EA stall by definition | (G) | any | Statement, 2026-11-03 |
| `jmp`/`jsr` through it are fine; GCC may generate them | (G) | any | Statement, 2026-11-03 |
| `jmp`/`jsr ([An])` costs about +7 cycles against an absolute or PC-relative target | (M) | Core 12841 | CCC, see superscalar-issue.md |
