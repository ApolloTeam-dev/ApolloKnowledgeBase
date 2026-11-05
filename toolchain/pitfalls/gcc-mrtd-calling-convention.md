---
title: GCC 6.5 crashes or miscompiles with -mrtd
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, mrtd, rtd, calling-convention, ice, miscompile]
related:
  - toolchain/compiler-variants.md
  - toolchain/pitfalls/calling-assembler-from-gcc.md
sources:
  - "github.com/WDrijver/ApolloCrossDev pull request #9 (merged on 2026-11-03)"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh (2026-11-03)"
---

## Symptom

With `-mrtd` (the callee pops its stack arguments with `rtd #n`), the first
call to any function with stack arguments stops the compiler, at every `-O`
level:

```text
internal compiler error: in invalid_rtx_rtx_rtx_rtx_rtx, at ./insn-target-def.h:130
```

## Cause

The m68k backend of GCC 6.5 had no `call_pop` patterns. Two more defects
showed once those were added: bebbo's bbb pass did not count the stack
adjustment inside such a call (stack pointer wrong at `rts` in functions
without a frame pointer), and the cc0 tracking dropped a `tst.l d0` after a
call (seen at `-Os`).

The fix, `m68k-mrtd-call-pop.patch` from ApolloCrossDev pull request #9, was
merged on 2026-11-03. Only GCC-6.50-Dev applies it.

## Wrong

```sh
m68k-amigaos-gcc -O2 -m68080 -mrtd ...   # GCC-6.50-Base or -Stable: ICE
```

## Right

- Use `-mrtd` only with GCC-6.50-Dev installed on or after 2026-11-03.
- `-mrtd` changes the calling convention: build everything you link with it
  (startup code, libnix or clib2, static libraries). GCC may call
  `memcpy`/`memset` for block copies, so they must come from a C library
  built with `-mrtd`. libgcc helpers such as `__udivdi3` keep the normal
  convention, so an unmodified libgcc works.

## Detection

The ICE above, or a link of `-mrtd` objects with a C library that was not
built with `-mrtd`.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| ICE on every call before the fix | (M) | any | Test case in ApolloCrossDev PR #9 |
| Correct with the fix | (M) | any | Test program built entirely with `-mrtd`, 10 tests, `-O0` to `-O3` and `-Os`, 68020/68040/68080, under vamos and on a V4 (3 rounds) |
| No change in code built without `-mrtd` | (M) | any | 400 C and 38 C++ files, byte-identical assembly |
