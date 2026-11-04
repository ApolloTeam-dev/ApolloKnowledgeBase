---
title: Memory indirect addressing blocks the core (except in JMP and JSR)
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [core-developer, measured, source-code]
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
  - "WDrijver (ApolloCrossDev maintainer), 2026-11-04"
  - "lvm.c compiled to assembly with GCC 6.5 (GCC-6.50-Patched, June 2026 build), -O2, 2026-11-04"
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

GCC generates this mode. Compiled with GCC 6.5 at `-O2`, Lua's `lvm.c`
contains 110 memory indirect operands (118 with `-m68080`): 82 are the
allowed `jmp ([disptab,d0.l*4])`, the others are data accesses such as
`move.l ([12,a4],164),-(sp)` (2026-11-04). In hot code, check the
generated assembly and rewrite such accesses.

The 68080 has full double indirect addressing, so the code is correct; the
cost is speed. GCC-6.50-Dev briefly applied `double-indirect-fix.patch`,
which stopped GCC from generating the mode but crashed on computed gotos.
It was removed on 2026-11-04 (see
[compiler-variants.md](../../toolchain/compiler-variants.md)).

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Memory indirect is slow and blocks the core; don't use it | (G) | any | Statement |
| In instructions other than `jmp`/`jsr` it is an ALU-to-EA stall by definition | (G) | any | Statement, 2026-11-03 |
| `jmp`/`jsr` through it are fine; GCC may generate them | (G) | any | Statement, 2026-11-03 |
| GCC 6.5 `-O2` emits it in data accesses (28 of 110 in Lua's `lvm.c`) | (SRC) | any | Generated assembly, 2026-11-04 |
| `jmp`/`jsr ([An])` costs about +7 cycles against an absolute or PC-relative target | (M) | Core 12841 | CCC, see superscalar-issue.md |
