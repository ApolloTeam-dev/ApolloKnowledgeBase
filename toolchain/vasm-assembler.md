---
title: vasm assembler options
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [toolchain, cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [vasm, assembly, ammx, devpac]
related:
  - toolchain/index.md
  - toolchain/project-makefile.md
sources:
  - "github.com/WDrijver/ApolloCrossDev Projects/_makefiles/Makefile"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh"
  - "vasm documentation (Volker Barthelmann, Frank Wille)"
---

## Summary

Assemble 68080 code with `vasmm68k_mot`: vasm built for m68k with Motorola
syntax. Standard options: `-Fhunk -m68080 -m68881 -opt-speed`, with the DevPac
includes on the include path.

## Details

### Binary

ApolloCrossDev builds vasm from `Compilers/_archives/vasm` with
`make CPU=m68k SYNTAX=mot` and installs `vasmm68k_mot` and `vobjdump` in
`<prefix>/bin`.

### Standard options

| Option | Meaning |
|---|---|
| `-Fhunk` | Output AmigaOS hunk object files, linkable with `m68k-amigaos-gcc` |
| `-m68080` | Accept the 68080 instruction set |
| `-m68881` | Accept FPU instructions |
| `-opt-speed` | Prefer optimizations for speed, even if code gets larger |
| `-I<prefix>/m68k-amigaos/DevPac/Include` | DevPac include files |

Debug options in the Makefile template: `-linedebug` (source line debug
information) and `-kick1hunks` (only hunk types that Kickstart 1.x
understands).

```sh
vasmm68k_mot -Fhunk -m68080 -m68881 -opt-speed \
  -I<prefix>/m68k-amigaos/DevPac/Include file.s -o file.o
```

### Source files

Assembly sources use the `.s` extension. The Makefile template assembles
every `.s` file in the project folder and links the objects together with
the C objects.

### Linking with C

Symbols called from C need a leading underscore and an `xdef`:

```asm
; kb:compile
	section	code,code
	xdef	_my_function
_my_function:
	moveq	#0,d0
	rts
```

## Differences from AmigaOS / AROS / 68060

- DO use `vasmm68k_mot` for 68080 assembly. Whether the GNU assembler
  (`m68k-amigaos-as`) accepts 68080 instructions is not documented here.
- DON'T use `-m68060` or lower. Without `-m68080`, 68080 and AMMX
  instructions are rejected.

## Do / Don't

- DO use Motorola syntax.
- DO pass `-m68080` so 68080 instructions are accepted.
- DON'T invent AMMX mnemonics. Check `core/cpu-68080/`, or the `AMMX` folder
  in ApolloCrossDev `Docs/`.
