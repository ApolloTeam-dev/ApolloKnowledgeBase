---
title: C and C++ compiler options
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [toolchain, cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, flags, libnix, clib2, linking]
related:
  - toolchain/index.md
  - toolchain/target-os-headers.md
  - toolchain/project-makefile.md
sources:
  - "github.com/WDrijver/ApolloCrossDev Projects/_makefiles/Makefile"
  - "WDrijver (ApolloCrossDev maintainer), 2026-11-02"
---

## Summary

Compile C with `m68k-amigaos-gcc` and C++ with `m68k-amigaos-g++`, using
`-O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer` and the libnix
runtime (`-noixemul`). Link with `m68k-amigaos-gcc` and the same flags.

## Details

### Standard options

| Option | Meaning |
|---|---|
| `-O2` | Advanced optimization. Default and advised. |
| `-m68080` | Target the Apollo 68080. Default and advised. |
| `-m68881` | Use the FPU. Default and advised. **Required for FPU code:** `-m68080` alone gives soft-float (see [float-settings-mismatch.md](pitfalls/float-settings-mismatch.md)) |
| `-ffast-math` | Faster, less accurate floating-point math |
| `-fomit-frame-pointer` | Frees the frame pointer register for general use |

Other optimization levels: `-O` (basic), `-O3` (aggressive), `-Os` (small
size). `-O3` gave no gain over `-O2` in measured projects.

Don't add `-mtune=68060`: it stops GCC from using the 64-bit `muls.l` (FLAC
3x slower). See [gcc-misc-traps.md](pitfalls/gcc-misc-traps.md) and, for
more on code generation, [gcc-code-generation-for-68080.md](best-practices/gcc-code-generation-for-68080.md).

### C runtime

| Runtime | Option | Include path |
|---|---|---|
| libnix (default) | `-noixemul` | `<prefix>/m68k-amigaos/libnix/include` |
| clib2 | `-mcrt=clib2` | `<prefix>/m68k-amigaos/clib2/include` |

Pass the runtime option both when compiling and when linking.

### Include paths

The project Makefile template passes these with `-I`, with the libnix runtime
and NDK 3.2:

```sh
-I. \
-I<prefix>/m68k-amigaos/libnix/include \
-I<prefix>/m68k-amigaos/sys-include \
-I<prefix>/m68k-amigaos/ndk32-include/Include_H
```

For other target operating systems, see `toolchain/target-os-headers.md`.
Optional include folders: `<prefix>/m68k-amigaos/include/GL`, `.../SDL`,
`.../MUI`.

### Extra libraries

| Library | Link options |
|---|---|
| SDL | `-lSDL -lSDL_ttf -lfreetype` |
| MUI | `-lmui` |
| Math | `-lm` |

### Other options in the Makefile template

- `-g`: debug information, for remote debugging with bgdbserver.
- `-DREGPARM=4`: ignore it. It is not part of the standard options.

### Compile and link

```sh
m68k-amigaos-gcc -noixemul -O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer \
  -I<include paths> -c main.c -o main.o
m68k-amigaos-gcc main.o -noixemul -O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer \
  -o program
```

## Differences from AmigaOS / AROS / 68060

- DON'T use `-m68060` or `-m68040` for Apollo V4 code. `-m68080` is the
  target, provided by the ApolloCrossDev patches.
- DON'T assume `-ffast-math` and `-fomit-frame-pointer` are optional extras.
  They are part of the standard Apollo V4 flags.

## Do / Don't

- DO use the standard options above unless the user or project says
  otherwise.
- DO use libnix (`-noixemul`) unless the project uses clib2.
- DON'T mix libnix and clib2 objects in one program.
- DON'T mix objects built with and without `-m68881`, and link with the same
  flags you compile with.
- DO link with `-lm` when you use `sprintf` with libnix (see
  [libnix-and-header-traps.md](pitfalls/libnix-and-header-traps.md)).
