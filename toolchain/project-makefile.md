---
title: ApolloCrossDev project Makefile template
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [makefile, build, upload, debug, apolloexplorer, bgdbserver]
related:
  - toolchain/c-compiler-options.md
  - toolchain/vasm-assembler.md
sources:
  - "github.com/WDrijver/ApolloCrossDev Projects/_makefiles/Makefile (template v1.0, 2025-11-28)"
  - "github.com/WDrijver/ApolloCrossDev README.md"
---

## Summary

New ApolloCrossDev projects copy `Projects/_makefiles/Makefile`. It compiles
all `.c` and `.s` files in the project folder, links them into one
executable, and uploads it to the Apollo V4 with ApolloExplorer.

## Details

### Project setup

1. Create a folder `Projects/<project-name>` in the ApolloCrossDev checkout.
2. Copy `Projects/_makefiles/Makefile` into it.
3. Set `PROJECT_NAME` in the Makefile.
4. Add sources: `.c` for C, `.s` for assembly. For C++, see the Do / Don't
   section.
5. Run `make` in the project folder.

The template finds the compiler at `../../Compilers/GCC-6.50-Dev`, so the
project folder must be two levels below the ApolloCrossDev root.

### Main variables

| Variable | Default | Purpose |
|---|---|---|
| `C_COMPILER` | `m68k-amigaos-gcc` | Switch to `m68k-amigaos-g++` for C++ |
| `C_LIB` | `-noixemul` | C runtime (libnix); alternative `-mcrt=clib2` |
| `C_INCL_NDK` | NDK 3.2 | NDK headers, see `toolchain/target-os-headers.md` |
| `C_OPTIONS` | `-O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer -DREGPARM=4` | Compiler options. Ignore `-DREGPARM=4`. |
| `C_DEBUG` | `-g` | Debug information |
| `S_FLAGS` | `-Fhunk -m68080 -m68881 -opt-speed -linedebug -kick1hunks -I<DevPac includes>` | Assembler options |
| `C_LIBS_SDL`, `C_LIBS_MUI`, `C_LIBS_MATH` | off | Extra libraries, enable by removing `#` |

The template only collects `.c` and `.s` files (`C_FILES`, `S_FILES`). It
also links every `.o` file in `Projects/ApolloLib` (see
[apollolib/index.md](apollolib/index.md)).

### Targets

| Command | What it does |
|---|---|
| `make` | Compile, link, upload executable and icon to `RAM Disk:` on the Apollo V4, clean up |
| `make debug` | As `make`, and also uploads bgdbserver and a `<name>_Debug` script that starts the program under bgdbserver |

Upload uses ApolloExplorer's `acp` to `"${AMIGAHOST}:Ram Disk/"`. Set
`AMIGAHOST` to the Apollo V4's IP address.

### Remote debugging

1. Run `make debug`.
2. Set breakpoints in VS Code on the host.
3. Start debugging in VS Code (F5) and select the project.
4. On the Apollo V4, double-click the program's `_Debug` icon in `RAM Disk:`.

## Differences from AmigaOS / AROS / 68060

- The build runs on the host (Linux or macOS), not on the Amiga. The Apollo
  V4 only receives the executable.

## Do / Don't

- DO start new projects from the Makefile template.
- DO add `.cpp` files to the template's file lists yourself when using C++.
  The template does not collect them.
- DON'T remove `-m68080` from `C_OPTIONS` or `S_FLAGS`.
