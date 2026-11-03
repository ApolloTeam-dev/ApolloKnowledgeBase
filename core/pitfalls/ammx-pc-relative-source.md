---
title: AMMX PC-relative sources read 2 bytes early
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080, toolchain]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, ammx, pc-relative, vasm, bug]
related:
  - core/cpu-68080/prm/ammx/ammx-format.md
  - core/cpu-68080/core-bugs-by-revision.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 6 and 9.4"
---

## Symptom

An AMMX instruction with a PC-relative source (`load .k(pc),d0`,
`paddw .k(pc),...`) reads data 2 bytes before the label.

## Cause

vasm counts the displacement from the third word of the instruction; the
core counts it from the second word. The two disagree by 2 bytes. The bug is
open on Core 12841.

## Wrong

```asm
    load    .k(pc),d0       ; reads .k - 2
    ; ...
.k: dc.w    $0001,$0002,$0003,$0004
```

## Right

Load the address into a register first:

```asm
    lea     .k(pc),a0
    load    (a0),d0
```

## Detection

Search for AMMX instructions with a `(pc)` source operand.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| PC-relative AMMX sources read 2 bytes early | (M) | Core 12841 | Test program, 2026-10-30 |
| vasm counts from the third word, the core from the second | (M) | Core 12841 | Comparing vasm output with core behaviour |
