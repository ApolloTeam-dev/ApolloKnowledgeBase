---
title: vasm assembler options
type: reference
owner: WDrijver
status: reviewed
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
  - "lessons/2026-11-akb-verification.md"
---

## Summary

Assemble 68080 code with `vasmm68k_mot`: vasm built for m68k with Motorola
syntax. Standard options: `-Fhunk -m68080 -m68881 -opt-speed`, with the DevPac
includes on the include path. **ApolloCrossDev ships vasm 2.0f, which with
`-m68080` silently creates PC-relative destinations that the 68080 can
miscompute:** read [vasm-pc-relative-destination.md](pitfalls/vasm-pc-relative-destination.md).

## Details

### Binary

ApolloCrossDev builds vasm 2.0f from `Compilers/_archives/vasm` with
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

Other useful options:

| Option | Meaning |
|---|---|
| `-no-opt` | Turn off all optimizations, including the PC-relative destination rewrite. Use it for byte-exact round trips and CPU tests; optimize by hand |
| `-L <file>` | Write a listing: use it to check encodings |
| `-devpac` | Devpac compatibility mode |

Use `machine ac68080` in the source for AMMX instructions.

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
- With `-m68080`, vasm rewrites absolute destinations into PC-relative ones
  and encodes some 68080 forms wrongly (BANK single operands, AMMX
  PC-relative sources). See [vasm-68080-encoding-issues.md](pitfalls/vasm-68080-encoding-issues.md).

## Do / Don't

- DO use Motorola syntax.
- DO pass `-m68080` so 68080 instructions are accepted.
- DO check the listing of code that writes to labels after a
  full-extension-format source, or address such destinations through a
  register.
- DO write the word immediate of `moviw.l`, `addiw.l` and `cmpiw.l` as the
  signed value it stands for: `moviw.l #-32477,d0` or
  `moviw.l #$FFFF8123,d0`, not `#$8123`. vasm encodes all three the same
  (`$303D 8123`), but warns about `#$8123` ("using signed operand as
  unsigned", warning 2028).
- DON'T invent AMMX mnemonics. Check `core/cpu-68080/`, or the `AMMX` folder
  in ApolloCrossDev `Docs/`.
