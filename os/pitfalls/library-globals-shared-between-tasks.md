---
title: Library globals are shared between calling tasks
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [libraries]
applies_to:
  core: "any"
  os: [amigaos-3.9, amigaos-3.2]
tags: [libraries, reentrancy, race, tasks, stackswap]
related:
  - os/pitfalls/stack-patches-hide-small-stack-bugs.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 13"
---

## Symptom

A shared library works with one caller but crashes or mixes up data when
several tasks call it at the same time, for example several player tasks
using one decoder library.

## Cause

Library globals, and data in the library base, are shared by every task that
calls the library. A per-base `StackSwapStruct`, for example, is overwritten
by the second caller while the first is still using it.

## Wrong

```c
struct MyLibBase {
    struct Library lib;
    struct StackSwapStruct sss;   /* one for all callers */
};
```

## Right

Keep per-call state on the stack or in a block allocated per call (or per
opener), never in the library base or in globals:

```c
LONG decode(struct MyLibBase *base, struct Frame *f)
{
    struct StackSwapStruct sss;   /* per call */
    /* ... */
}
```

## Detection

Look for writable globals and writable fields in the library base that are
used during a call. Test with two or more tasks calling at once.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| A per-base StackSwapStruct raced with several player tasks | (M) | any | MP3 library on AmigaOS 3.9 |
