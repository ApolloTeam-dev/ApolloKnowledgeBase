---
title: GCC 6.5 16-bit loop counter in an address register runs away
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, ivopts, dbra, loop, miscompile, address-register]
related:
  - toolchain/compiler-variants.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 9.2"
  - "github.com/WDrijver/ApolloCrossDev pull requests #7 (merged on 2026-11-03) and #12 (open on 2026-11-03)"
  - "github.com/WDrijver/gcc issue #1 (open on 2026-11-03)"
---

## Symptom

A loop with a 16-bit counter runs about 4 billion times instead of the
intended count, at `-O2`. It always shows on real Fast RAM; under emulators
only when the low word of the pointer is `$8000` or higher.

## Cause

GCC's m68k patterns `*dbne_hi`/`*dbge_hi` emit `subq.w #1,An; cmp.w #-1,An`,
which is a 32-bit operation on an address register. After ivopts builds a
UWORD counter from a pointer, the high word never reaches −1. The bug is
GCC's, not the core's: the same loop also runs away on a real 68060.

The fix (`tst.w An; subq.w #1,An; jne`, also faster) is
`m68k-dbra-hi-addrreg-fix.patch` from ApolloCrossDev pull request #7, merged
on 2026-11-03. A later merge dropped the step that applies it, so on
2026-11-03 no install script applies it. ApolloCrossDev pull request #12
puts it back in GCC-6.50-Dev (open on 2026-11-03). The pattern is latent in
GCC 15.2 too (WDrijver/gcc issue #1).

## Wrong

A UWORD loop counter that ivopts derives from a pointer can be compiled into
this pattern:

```asm
.loop:
    ; ... body ...
    subq.w  #1,a2           ; 16-bit decrement of an address register
    cmp.w   #-1,a2          ; compares all 32 bits (sign-extended)
    bne.s   .loop           ; high word is never -1: runs about 4 G times
```

## Right

Until your GCC-6.50-Dev install applies `m68k-dbra-hi-addrreg-fix.patch`
(check the install log), and with every other variant:

- compile with `-fno-ivopts` (3–6 % slower on the tested code), or
- mark the affected function `__attribute__((noinline))`.

## Detection

Compile with `-S` and look for `subq.w #1,aN` followed by `cmp.w #-1,aN`.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Loop runs away on Fast RAM | (M) | any | Real project, V4 |
| `tst.w An` tests only bits 15–0; `subq` to An leaves the CCR alone | (M) | Core 12841 | Self-checking test tstan, 252 checks x 3 passes; 0 failures on the 080 and on a real 68060 |
| The old GCC loop also runs away on a real 68060 | (M) | 68060 | Same test |
| Fix in ApolloCrossDev PR #7; applied again by PR #12 | (SRC) | any | Pull requests, install scripts |
