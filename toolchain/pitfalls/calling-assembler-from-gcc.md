---
title: Calling assembler from GCC (registers, movem order, FPU ABI)
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [toolchain, cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, assembler, abi, registers, movem, fpu]
related:
  - toolchain/vasm-assembler.md
  - toolchain/c-compiler-options.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 9.3"
---

## Symptom

The machine hangs or C code misbehaves after calling an assembler routine.
It looks like a hardware bug: a clobbered a2 hung the machine three times
before it was found.

## Cause

- GCC expects d2–d7 and a2–a6 to be preserved by the callee.
- `movem.l` loads registers in register-mask order, not in the order you list
  them. Loading arguments from the stack with one `movem.l` can put them in
  the wrong registers.
- Which FPU registers a routine must preserve depends on the ABI you use, and
  is easy to get wrong when it is not written down.

## Wrong

```asm
_routine:
    movem.l 4(sp),a2/d1     ; loads d1 first, then a2: not "a2 then d1"
    move.l  (a2)+,d0        ; a2 clobbered and not restored
    rts
```

## Right

```asm
_routine:
    move.l  a2,-(sp)        ; save a callee-saved register
    movea.l 8(sp),a2        ; load arguments with separate moves
    move.l  12(sp),d1
    move.l  (a2)+,d0
    movea.l (sp)+,a2
    rts
```

- Document the FPU registers your routine keeps, for example "keeps
  FP2–FP7/FPCR".

## Detection

Review every assembler routine called from C for writes to d2–d7/a2–a6
without a save and restore, and for `movem.l` used to load arguments.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| A clobbered a2 hung the machine three times | (M) | any | Project debugging on the V4 |
| `movem.l` loads in register-mask order | (M) | any | Same |
