---
title: ApolloCrossDev toolchain overview
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [apollocrossdev, gcc, vasm, install]
related:
  - toolchain/compiler-variants.md
  - toolchain/c-compiler-options.md
  - toolchain/vasm-assembler.md
  - toolchain/target-os-headers.md
  - toolchain/project-makefile.md
  - toolchain/apollolib/index.md
sources:
  - "github.com/WDrijver/ApolloCrossDev README.md"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh"
  - "WDrijver (ApolloCrossDev maintainer), 2026-11-02"
---

## Summary

ApolloCrossDev (github.com/WDrijver/ApolloCrossDev) is the single toolchain
for all Apollo V4 development. It cross-compiles on Linux or macOS and
produces Amiga hunk executables for the 68080. Its C/C++ compiler is a fork of
GCC 6.5.0 with Apollo 68080 patches, based on Amiga-GCC by Stefan "Bebbo"
Franke.

## Details

### Binaries

All binaries are in `<prefix>/bin`, where the prefix is
`Compilers/GCC-6.50-Dev` inside the ApolloCrossDev checkout.

| Binary | Purpose |
|---|---|
| `m68k-amigaos-gcc` | C compiler, also used as linker |
| `m68k-amigaos-g++` | C++ compiler |
| `vasmm68k_mot` | Assembler, Motorola syntax (see `toolchain/vasm-assembler.md`) |
| `vobjdump` | vasm object file dump |
| `m68k-amigaos-ar`, `-ld`, `-nm`, `-objdump`, `-ranlib` | GNU binutils |
| `fd2pragma` | Generates proto/inline headers from `.fd` files |

`m68k-amigaos-gcc --version` reports `m68k-amigaos-gcc (GCC) 6.5.0b`.

### Standard flags

C and C++: `-O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer`. Details in
`toolchain/c-compiler-options.md`.

### What else is installed

- Amiga NDKs 1.3, 3.9 and 3.2 (3.2 is the default), see
  `toolchain/target-os-headers.md`
- C runtimes libnix (default) and clib2
- Libraries and headers: MUI 5, SDL (base, mixer, ttf, image), Vorbis, Ogg,
  GL, FreeType, Timidity, zlib, minizip, Lua, MPEGA, P96 headers
- DevPac includes for assembly, in `<prefix>/m68k-amigaos/DevPac`
- ApolloExplorer (`acp`) to upload files to an Apollo V4 over the network
- bgdbserver, a GDB server that runs on the Apollo V4 for remote debugging
- ApolloLib in `Projects/ApolloLib`: sound, picture, PIP, pointer, input,
  copy and blit routines and serial debug output for SAGA and the 68080,
  see [toolchain/apollolib/](apollolib/index.md)

### Host requirements

- Linux: Ubuntu 24.04 LTS amd64. Other distributions may fail unless the host
  GCC is downgraded to version 12.
- macOS: Apple Silicon (M1–M4). Intel Macs are not tested.
- 8 GB RAM or more, 50 GB disk or more, 4 cores or more.

### Install

```sh
git clone https://github.com/WDrijver/ApolloCrossDev
cd ApolloCrossDev
./GCC-6.50-Dev-Linux.sh      # or ./GCC-6.50-Dev-MacOS.sh
```

The script builds everything from source and installs it in
`Compilers/GCC-6.50-Dev`. It needs `sudo` for host packages. It writes errors
to `Compilers/GCC-6.50-Dev/_logs/*_err.log` and does not stop on errors, so
check that the binaries above exist afterwards. A full build takes about
25 minutes on a 4-core GitHub Actions runner.

For uploading to the Apollo V4, set its IP address in `~/.bashrc`:

```sh
export AMIGAHOST="192.168.2.100"
```

### Reference manuals

The `Docs/` folder of ApolloCrossDev contains `AC68080PRM.pdf`,
`M68000PRM.pdf` and folders `AMMX`, `FPU` and `Integer`.

### In this knowledge base's CI

`kb:compile` code blocks are built with GCC-6.50-Dev and the standard flags,
see `tools/compile-snippets.sh`.

## Differences from AmigaOS / AROS / 68060

- DON'T assume the generic Amiga-GCC (bebbo) toolchain. ApolloCrossDev adds
  Apollo 68080 patches and the `-m68080` target, see
  `toolchain/compiler-variants.md`.
- There is no other supported toolchain for Apollo V4 work in this knowledge
  base: not SAS/C, not VBCC, not the native AROS toolchain.

## Do / Don't

- DO use the GCC-6.50-Dev variant unless told otherwise.
- DO check that `m68k-amigaos-gcc`, `m68k-amigaos-g++` and `vasmm68k_mot`
  exist after an install. The install script does not report failures.
- DON'T invent compiler or assembler flags. Use the ones documented in
  `toolchain/`, or say that you don't know.
