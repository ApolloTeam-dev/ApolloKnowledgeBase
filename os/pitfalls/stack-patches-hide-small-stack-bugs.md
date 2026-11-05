---
title: Stack patches hide small-stack code paths
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [general]
applies_to:
  core: "any"
  os: [amigaos-3.9, amigaos-3.2]
tags: [stack, stackattack, stackswap, testing, libraries]
related:
  - toolchain/pitfalls/gcc-stackswap-defer-pop.md
  - os/pitfalls/library-globals-shared-between-tasks.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 13"
---

## Symptom

A library or program works on the developer's machine but crashes for some
users, typically callers with a small stack.

## Cause

StackAttack-style patches give every process a large stack. On machines with
such a patch, the code paths for small stacks (a `StackSwap()` to a private
stack, stack checks) never run, so their bugs stay hidden.

## Wrong

Testing only on a system with a stack patch installed.

## Right

Test the small-stack paths on a stack you allocate yourself and swap to with
`StackSwap()`, so they run whatever patches are installed:

```c
struct StackSwapStruct sss;
UBYTE *stack = AllocVec(4096, MEMF_ANY);   /* deliberately small */
sss.stk_Lower   = stack;
sss.stk_Upper   = (ULONG)(stack + 4096);
sss.stk_Pointer = (APTR)(stack + 4096);
StackSwap(&sss);
run_test();
StackSwap(&sss);
FreeVec(stack);
```

## Detection

Check whether a stack patch is active on the test machine, and test library
entry points with a small caller stack.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Small-stack code paths never run on machines with a stack patch | (M) | any | Library testing on AmigaOS 3.9 on the V4 |
