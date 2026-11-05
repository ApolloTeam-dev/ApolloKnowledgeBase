---
title: Smaller GCC 6.5 traps (-mtune=68060, NULL writes, -O3)
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, mtune, muls, null-pointer, trap, O3]
related:
  - toolchain/c-compiler-options.md
  - toolchain/best-practices/gcc-code-generation-for-68080.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 9.1 and 9.2"
---

## Symptom

- Multiply-heavy C code (FLAC) runs 3 times slower than expected.
- A deliberate write to address 0 ends in a guru 80000027 instead of the
  intended effect.
- `-O3` builds are not faster than `-O2`.

## Cause

- `-mtune=68060` stops GCC from using the 64-bit `muls.l`, because the 68060
  emulates it in software. The 68080 runs it in hardware.
- GCC treats `*(ULONG *)0` as undefined behaviour and turns it into
  `trap #7` (guru 80000027).
- `-O3` gave nothing over `-O2` in the measured projects.

## Wrong

```sh
m68k-amigaos-gcc -O2 -m68080 -mtune=68060 ...   # FLAC 3x slower
```

```c
*(ULONG *)0 = value;   /* becomes trap #7 */
```

## Right

- Don't tune for the 68060. Use the standard flags (`-m68080`, no `-mtune`).
- Make the NULL access in assembler, and compile with
  `-fno-delete-null-pointer-checks`.
- Stay at `-O2` unless a measurement shows otherwise.

## Detection

Check Makefiles for `-mtune=68060` and `-O3`. Grep `-S` output for
`trap #7`.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `-mtune=68060`: FLAC 3x slower | (M) | Core 12841 | FLAC decode |
| `*(ULONG*)0` becomes `trap #7` | (M) | any | `-S` output |
| `-O3` no gain over `-O2` | (M) | Core 12841 | MP3/FLAC projects |
