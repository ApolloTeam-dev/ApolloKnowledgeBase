---
name: apollo-build
description: Build an Apollo V4 program with ApolloCrossDev (GCC 6.5 with 68080 patches, vasm) and fix every error and warning. Use whenever code for the Apollo V4 is compiled, linked or assembled, a Makefile or build command is written or changed, compiler or assembler flags come up, or a build fails or crashes the compiler, even when it looks like an ordinary m68k GCC build, because ApolloCrossDev's variants, flags and known compiler bugs differ. Also use before presenting Apollo V4 code, to prove it builds.
---

# apollo-build

Build an Apollo V4 program the way ApolloKnowledgeBase prescribes, and leave
no error or warning behind.

**The knowledge base (KB):** in a project, the `ApolloKnowledgeBase/`
submodule; use it, it is the commit the project relies on. Otherwise the
repository this skill is in (two folders above this file). KB paths below
are relative to its root.

## 1. Know the target

Read the project's `AGENTS.md`: target OS, execution mode, languages. If it
is missing, ask; don't guess the target OS, it decides the headers.

## 2. Check the toolchain

```sh
sh <this skill's folder>/scripts/find-acd.sh <project folder>
```

It prints `ACD_ROOT`, `PREFIX`, `GCC`, the template and project Makefile
versions, and `PROBLEM=` lines. Fix every `PROBLEM` before building, with
the user: a missing toolchain means installing ApolloCrossDev
(`KB toolchain/index.md`, section Install), a wrong `APOLLOCROSSDEV` means
correcting it. Act on the `NOTE=` lines too.

## 3. Build

The project's Makefile comes from ApolloCrossDev's template
(`Projects/_makefiles/Makefile`, see `KB toolchain/project-makefile.md`).

| Goal | Command |
|---|---|
| Compile and link only | `make compile` (template v1.2 and later); with an older Makefile `make cleanbefore build` |
| Also upload to the V4 (`$AMIGAHOST`) | `make` |
| Upload with the remote debugger | `make debug` |

- Run `make compile` yourself. Run `make` or `make debug` only when the user
  asks: they copy files to the user's Apollo V4 over the network.
- The Makefile hides compiler stdout; errors and warnings arrive on stderr.
  Read all of it.
- Without a Makefile (a quick test), use the flags from
  `KB toolchain/c-compiler-options.md` exactly, and the NDK from step 4.

## 4. Settings: take them from the KB, never from memory

| Setting | Rule | KB file |
|---|---|---|
| Compiler variant | GCC-6.50-Dev; GCC-6.50-Stable only to test a suspected compiler bug; never GCC 13/15 | `toolchain/compiler-variants.md` |
| C/C++ flags | `-O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer`, libnix (`-noixemul`) | `toolchain/c-compiler-options.md` |
| NDK headers | NDK 3.2 for AmigaOS 3.2 and ApolloOS R10; NDK 3.9 as soon as AmigaOS 3.9 is a target | `toolchain/target-os-headers.md` |
| Assembler | vasm, `-Fhunk -m68080 -m68881` | `toolchain/vasm-assembler.md` |
| ApolloLib | compiled from its sources by the template (`APOLLOLIB`) | `toolchain/apollolib/index.md` |

Don't add `-m68060`, `-m68040` or `-mtune=68060`, don't drop `-m68881` from
code that uses floats, and don't mix libnix and clib2 objects. Don't invent
flags: if the KB doesn't document one, say so.

## 5. Fix errors and warnings

Fix the cause in the code, not by silencing the warning. Before you change
code around a symptom, check whether it is a known trap:

| Symptom | Read in the KB |
|---|---|
| Internal compiler error, or wrong code that looks like a compiler bug | `toolchain/compiler-variants.md` (bug table: fixed only in a reinstalled GCC-6.50-Dev), then the pitfall it names |
| Floats wrong, or link errors about float functions | `toolchain/pitfalls/float-settings-mismatch.md` |
| `sprintf`, headers or libnix surprises | `toolchain/pitfalls/libnix-and-header-traps.md` |
| Other GCC oddities | `toolchain/pitfalls/gcc-misc-traps.md` |
| C calling assembler, registers lost | `toolchain/pitfalls/calling-assembler-from-gcc.md` |
| vasm rejects or mis-encodes a 68080 instruction | `toolchain/pitfalls/vasm-68080-encoding-issues.md`, `toolchain/pitfalls/vasm-pc-relative-destination.md` |
| A function missing on one target OS | `toolchain/target-os-headers.md` (build against the oldest target's NDK) |
| ApolloLib misbehaves | `toolchain/pitfalls/apollolib-known-bugs.md` |

Other files in `KB toolchain/pitfalls/` cover single GCC bugs; list the
folder when a symptom doesn't match the table.

## 6. Report

Say which command you ran, the variant and Makefile version, and that the
build ended with no errors and no warnings, or what is left and why. If the
KB was wrong or missing something on the way, tell the user and offer a
lesson (the akb-lesson skill) or a KB change.
