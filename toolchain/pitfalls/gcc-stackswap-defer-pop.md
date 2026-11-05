---
title: GCC pops call arguments after StackSwap
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [toolchain]
applies_to:
  core: "any"
  os: [amigaos-3.9, amigaos-3.2]
tags: [gcc, stackswap, stack, defer-pop, crash]
related:
  - toolchain/c-compiler-options.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 20) and 9.2"
---

## Symptom

A program or library that calls `StackSwap()` crashes callers with small
stacks. The caller's stack is corrupted after the call returns.

## Cause

GCC defers popping call arguments and may emit `lea N(sp),sp` *after* the
code has swapped the stack back. It then adjusts the caller's stack instead
of the private one. This crashed an MP3 library for callers with small
stacks.

## Wrong

```c
StackSwap(&sss);
result = decode(frame, len);   /* arguments popped later ... */
StackSwap(&sss);               /* ... after this swap back */
```

## Right

Build every file that uses `StackSwap()` with `-fno-defer-pop` (or with a
frame pointer), and read the generated code around the swap.

```sh
m68k-amigaos-gcc -noixemul -O2 -m68080 -m68881 -fno-defer-pop -c player.c
```

## Detection

Compile with `-S` and check that no `lea N(sp),sp` or `addq.l #N,sp` follows
the second `StackSwap` call for arguments pushed before it.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `lea N(sp),sp` emitted after the swap back; crashes with small caller stacks | (M) | any | MP3 library, AmigaOS 3.9 |
