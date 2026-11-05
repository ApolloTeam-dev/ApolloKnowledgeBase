---
title: ApolloLib, the ApolloCrossDev library for SAGA and the 68080
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
basis: [source-code]
components: [toolchain, saga-audio-arne, saga-video-isabelle]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, library, saga, arne, isabelle, pip, pointer, debug]
related:
  - core/best-practices/prefer-library-calls-for-saga-chips.md
  - core/saga-registers/index.md
  - toolchain/project-makefile.md
  - toolchain/pitfalls/apollolib-known-bugs.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib, commit 639e195 (2026-11-04)"
  - "WDrijver (maintainer), library calls for the SAGA chips, 2026-11-04"
---

## Summary

ApolloLib is the C and assembly library that ships with ApolloCrossDev in
`Projects/ApolloLib`. It loads and plays sounds on Arne, loads and shows
pictures on the SAGA chunky plane, PIP and pointer sprite, reads mouse,
USB joypad and keyboard, and has fast copy, fill and blit routines and a
serial debug output. Until the official libraries for Arne and Isabelle
are released, ApolloLib is the preferred way to use them (see
[prefer-library-calls-for-saga-chips.md](../../core/best-practices/prefer-library-calls-for-saga-chips.md)).

## Details

### Using it in a project

ApolloLib is not a link library: a project compiles its sources. The
example Makefiles (ApolloPointer, ApolloPiP) set
`APOLLOLIB = $(PWD)/../../Projects/ApolloLib`, add `-I$(APOLLOLIB)`,
and compile every `.c` and `.s` file there into the program (see
[project-makefile.md](../project-makefile.md)).

```c
#include "ApolloCrossDev_Lib.h"   /* includes _Defines.h and _Debug.h */
```

| File | Content |
|---|---|
| `ApolloCrossDev_Lib.h` | Structures and prototypes |
| `ApolloCrossDev_Defines.h` | SAGA addresses, modes, formats, return codes, debug switches, Amiga includes |
| `ApolloCrossDev_LibC.c` | Files, sound, picture, PIP, pointer, input |
| `ApolloCrossDev_LibASM.s` | Copy, fill, blit, endian swap, timing, takeover (vasm, 68080 and AMMX) |
| `ApolloCrossDev_Debug.h`, `_Debug.c` | Serial debug output |

The assembly functions take their arguments in registers, declared with
the macros `_A0(...)` … `_D7(...)` from `_Defines.h`.

### Areas

| Area | Functions | File |
|---|---|---|
| Sound on Arne | `ApolloLoadSound`, `ApolloPlaySound`, `ApolloStopSound`, `ApolloVolume…`, fades; the channel API `ApolloPlay`, `ApolloPlayFile`, `ApolloStartChannel`, `ApolloStopChannel` | [sound.md](sound.md) |
| Pictures, PIP, pointer | `ApolloLoadPicture`, `ApolloShowPicture`, `ApolloShowPiP1/2`, `ApolloHidePiP1/2`, `ApolloLoadPointer`, `ApolloShowPointer`, `ApolloShowFile` | [picture.md](picture.md) |
| Input | `ApolloMouse`, `ApolloJoypad`, `ApolloKeyboard`, `ApolloKeyboardToUnicode`, `ApolloGetMouseDelta` | [input.md](input.md) |
| Memory and blit | `ApolloCopyBlock`, `ApolloFillLongs`, `ApolloSwapLong`, `ApolloBlit…Loop` and others | [memory-and-blit.md](memory-and-blit.md) |
| System and timing | `ApolloWaitVBL`, `ApolloCPUTick`, `ApolloCPUDelay`, `ApolloTimer`/`ApolloTimerStop`, `ApolloTakeOver`/`ApolloRelease`, `ApolloForbid`/`ApolloPermit`, `ApolloDisable`/`ApolloEnable` | [system-and-timing.md](system-and-timing.md) |
| Debug | `ApolloDebugInit`, `ApolloDebugPutStr`, `AD()`, `Debug_Info()` … | [debug.md](debug.md) |
| Files | `ApolloLoadFile`, `ApolloCacheFile` | this file |

### Files

`ApolloLoadFile(struct ApolloFile *file)` reads `file->filename` from byte
`file->offset` to the end into `file->buffer`, which the caller allocates,
and sets `file->size`. `ApolloCacheFile(filename, &cache, &length, offset)`
does the same with plain arguments. Both use libnix `fopen`/`fread`.

### Return codes

| Value | Sound (`APOLLO_SOUND_…`) | Picture (`APOLLO_PICTURE_…`) |
|---|---|---|
| `$00` | OK | OK |
| `$01` | NOCHANNEL | W_ERROR (width has no SAGA mode) |
| `$02` | – | H_ERROR (height has no SAGA mode) |
| `$03` | ENDOFFILE | D_ERROR (depth not supported) |
| `$04` | LOADERROR | LOADERR |
| `$05` | NOHEADER | NOHEADER |
| `$06` | – | PLANEERR |
| `$07` | – | COMPRERR |
| `$09` | MEMERROR | MEMERROR |
| `$0A` | OPENERR | OPENERR |
| `$0B` | CLOSEERR | CLOSEERR |
| `$0C` | COMPRERR | – |

`ApolloLoadFile` returns the sound codes.

### Versions

Many bugs were fixed on 2026-11-04 (commit 639e195): use that version or
later. An older copy has the bugs listed in
[apollolib-known-bugs.md](../pitfalls/apollolib-known-bugs.md), among them
broken 320-pixel modes and no way to undo `ApolloTakeOver` or
`ApolloTimer`. From commit a9a994f, `ApolloShowPiP1/2` also load the
palette of an 8-bit picture.

## Differences from AmigaOS / AROS / 68060

- ApolloLib programs the SAGA registers directly, without graphics.library,
  audio.device or input.device. Most functions are OS-takeover style:
  under a running OS, `ApolloMouse` and `ApolloShowPicture` compete with
  Intuition for the pointer and the screen.
- The assembly uses 68080 and AMMX instructions (`load`, `store`, `vperm`,
  `dbra.l`, `move16`): it doesn't run on a 68060.

## Do / Don't

- DO use ApolloLib for Arne and Isabelle instead of programming the
  registers yourself (a best practice, not a forced rule).
- DO build against ApolloLib 639e195 or later.
- DO check the limits that remain before you rely on a function:
  [apollolib-known-bugs.md](../pitfalls/apollolib-known-bugs.md).
- DON'T copy an old ApolloLib into a project: compile the one in
  `Projects/ApolloLib`.
