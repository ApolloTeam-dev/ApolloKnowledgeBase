---
title: Changing a return address defeats the return cache
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, rts, return-cache, jump, patching]
related:
  - core/cpu-68080/branches-and-prediction.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 2.6 and 12"
---

## Symptom

Subroutine calls or patch stubs are several times slower than expected:
about 9.5 extra cycles per return, or about 45 cycles for an `rtd` used as a
jump.

## Cause

Returns are predicted by a return cache for rts/rtd/rtr. When code changes
the return address on the stack, or uses a return instruction as a jump, the
prediction is wrong and the CPU redirects after the ALU stage.

## Wrong

```asm
routine:
    addq.l  #2,(sp)         ; skip an inline parameter word
    rts                     ; mispredicted

dispatch:
    pea     target          ; "jump" through the stack
    rts                     ; mispredicted
```

## Right

- Pass parameters in registers, and return to the real return address.
- Jump directly with `jmp` or `bra`.
- To fall back to an original (patched) routine, use `jmp ([ptr,pc])`, which
  is predicted.

```asm
    jmp     ([oldvector,pc])
```

## Detection

Look for writes to `(sp)` before `rts`, `pea` + `rts`, and `rtd` used for
dispatch. Measure a call with CCC: more than about 5 cycles per bsr + rts
points here.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| bsr + rts: 4.6 cycles normally, 14.0 when the routine did `addq.l #2,(sp)` | (M) | Core 12841 | CCC |
| `rtd` used as a jump: about 45 cycles | (M) | Core 12841 | CCC |
| A computed-jump CopyMem was slower than a plain one | (M) | Core 12841 | Real workload |
