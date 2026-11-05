---
title: Running on Apollo V4 under ApolloOS and AmigaOS
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [general]
applies_to:
  core: "any"
  os: [apolloos-r10, amigaos-3.9, amigaos-3.2]
sources:
  - "Not yet collected"
---

## Summary

Guidelines for programs that run on Apollo V4 hardware under ApolloOS R10,
AmigaOS 3.9 or AmigaOS 3.2. Read this for every Apollo V4 project.

**This file is only partly covered.** It points to the files that exist so
far. For anything else, tell the user that the knowledge base does not cover
OS-specific guidelines yet.

## Details

### Detecting Apollo V4 hardware

Gate 68080 code on AttnFlags bit 10 and FPU code on the 68881 flag at run
time: see [best-practices/detect-68080-and-fpu-at-run-time.md](best-practices/detect-68080-and-fpu-at-run-time.md).

### OS functions per target OS

No content yet.

### Using SAGA features through the OS

- Maggie 3D: [libraries/maggie-library.md](libraries/maggie-library.md),
  and read [pitfalls/maggie-library-side-effects.md](pitfalls/maggie-library-side-effects.md)
  first.

### Known traps on V4 under AmigaOS

See `os/pitfalls/`: stack patches hiding small-stack bugs, library globals
shared between tasks, V4 ROM modules and soft resets, and `ramlib` reusing a
library by name. `CacheClearU` doing nothing on the 68080 is in
[core/pitfalls/self-modifying-code-and-caches.md](../core/pitfalls/self-modifying-code-and-caches.md).

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DO check the project's target OS list (its AGENTS.md) before using an OS
  function, and use only functions available in every target OS.
- DON'T work around ApolloOS behavior that differs from AmigaOS. Report it as
  an issue in github.com/ApolloTeam-dev/ApolloOS.R10 instead.
