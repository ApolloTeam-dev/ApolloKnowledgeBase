---
title: NDK headers per target OS
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [toolchain]
applies_to:
  core: "any"
  os: [apolloos-r10, amigaos-3.9, amigaos-3.2]
tags: [ndk, headers, target-os]
related:
  - toolchain/c-compiler-options.md
  - os/apolloos-and-amigaos-on-v4.md
sources:
  - "github.com/WDrijver/ApolloCrossDev Projects/_makefiles/Makefile"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh"
---

## Summary

ApolloCrossDev installs the Amiga NDK headers for versions 1.3, 3.9 and 3.2.
NDK 3.2 is the default. Choose the NDK that matches the oldest target OS of
the project.

## Details

### Installed NDKs

| NDK | Include path | Target OS |
|---|---|---|
| 3.2 (default) | `<prefix>/m68k-amigaos/ndk32-include/Include_H` | `amigaos-3.2` |
| 3.9 | `<prefix>/m68k-amigaos/ndk39-include` | `amigaos-3.9` |
| 1.3 | `<prefix>/m68k-amigaos/ndk13-include` | none of the supported targets |

ApolloCrossDev builds its runtime libraries against NDK 3.2
(`make all NDK=3.2`).

### Which NDK for which target

- Target `amigaos-3.2` only: NDK 3.2.
- Target includes `amigaos-3.9`: NDK 3.9, so functions that AmigaOS 3.9 does
  not have are not declared, and calling them gives a compiler warning or
  error instead of a crash at run time.
- Target `apolloos-r10`: not documented here yet.

### Why it matters

The NDK 3.2 headers declare functions added in AmigaOS 3.2. A program built
against them for AmigaOS 3.9 compiles and links without errors, but fails at
run time when it calls a function that 3.9 does not have.

## Differences from AmigaOS / AROS / 68060

- DON'T use the AROS SDK headers for Apollo V4 programs. Use the NDK that
  matches the target OS.

## Do / Don't

- DO pick the NDK from the project's target OS list.
- DON'T call a function that is missing in one of the project's target
  operating systems.
