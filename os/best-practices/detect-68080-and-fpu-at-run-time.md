---
title: Detect the 68080 and the FPU at run time
type: best-practice
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [general, cpu-68080]
applies_to:
  core: "Core 12798-12841"
  os: [amigaos-3.9, amigaos-3.2]
tags: [attnflags, detection, 68080, fpu, execbase, libraries]
related:
  - core/cpu-68080/core-at-a-glance.md
  - toolchain/best-practices/gcc-code-generation-for-68080.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 1, 9.1 and 13"
---

## Goal

Correctness and portability: run 080-specific and FPU code only where it
works, and keep one binary usable on other CPUs or with the FPU switched off.

## Technique

- Gate 080 code paths on `AttnFlags & (1 << 10)` in ExecBase.
- Gate FPU code paths on the 68881 flag **at run time**. The FPU can be
  switched off (vampiresupport.resource); AttnFlags then reads `$040f`
  instead of `$847f`.
- In a library, do the check in LibInit, and build that object with
  `-m68020` so it runs on any CPU before it decides.

```c
#include <exec/execbase.h>
#include <proto/exec.h>

extern struct ExecBase *SysBase;

BOOL has_68080(void) { return (SysBase->AttnFlags & (1 << 10)) != 0; }
BOOL has_fpu(void)   { return (SysBase->AttnFlags & AFF_68881) != 0; }
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| FPU on | AttnFlags = `$847f` | Core 12798-12841 | AmigaOS 3.9 (M) |
| FPU off | AttnFlags = `$040f` | Core 12798-12841 | Same |

## When not to use

- In an os-takeover program that you only ship for the V4, a single check at
  start-up is enough; don't test in inner loops.
- The DevPac include set redefines `AFB_68080`; use the NDK includes (plus
  DevPac `funcdef.i`) so the flag name matches.
