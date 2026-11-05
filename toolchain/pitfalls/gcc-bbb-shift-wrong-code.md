---
title: GCC 6.5 bbb pass deletes needed instructions around shifts
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, bbb, optimizer, shift, miscompile]
related:
  - toolchain/compiler-variants.md
  - toolchain/pitfalls/gcc-bbb-autoinc.md
sources:
  - "github.com/WDrijver/ApolloCrossDev pull request #10 (merged on 2026-11-03)"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh, GCC-6.50-Stable-Linux.sh (after pull request #13, 2026-11-03)"
---

## Symptom

Wrong results, without any warning, at `-O2` and `-Os`, for 68000 to 68080:

- An addition or index that uses a shift count gives a result that depends
  on what was left in the register. A typical victim is a `BYTE` or `WORD`
  loop counter used both as a shift count and as an array index.
- A table-driven CRC loses its high byte (seen with `-O2 -m68080`).

## Cause

Two backward scans in bebbo's bbb pass (`bbb-opts.c`) delete instructions
that are still needed:

| Pass | What goes wrong |
|---|---|
| `opt_elim_dead_assign` (`-fbbb=e`) | Drops the `ext.l` of a shift count, because the shift only reads the low bits. It does not check that the register is dead after the shift, and its scan crosses jumps |
| `opt_shift` (`-fbbb=h`) | Deletes a `move.w dy,dx` in front of a conditional branch although the other path reads `dx`: the scan stops at labels but not at jumps |

The fixes, `opt-elim-shift-count-fix.patch` and `opt-shift-jump-fix.patch`
from ApolloCrossDev pull request #10, were merged on 2026-11-03.
Only GCC-6.50-Dev applies them.

## Wrong

```c
int f(const short *p, int x)
{
    int n = *p;
    return (x << n) + n;   /* add.l reads a high word that was never set */
}
```

```asm
    move.w  (a0),d1
    move.l  (8,sp),d0
    lsl.l   d1,d0           ; ext.l d1 was deleted before this
    add.l   d1,d0           ; uses all 32 bits of d1
```

## Right

Use GCC-6.50-Dev installed on or after 2026-11-03. With GCC-6.50-Stable,
GCC-6.50-Base or an older install, compile the affected file with `-fbbb=-`,
or leave the letter of the pass (`e` or `h`) out of `-fbbb=`.

## Detection

Compile with `-S` and look for a register that is loaded with `move.w`,
used as a shift count and then used as a 32-bit value with no `ext.l` in
between. Compare the results with the same code built with `-fbbb=-`.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Shift-count case: up to 20000 wrong results per function before the fix, 0 after | (M) | any | 20000 calls with garbage in the scratch registers, `-O2`/`-Os` 68020 and `-O2` 68080, on a V4 |
| CRC case: 99612 of 100000 calls wrong before the fix, 0 after | (M) | any | `-O2 -m68080` and `-O2 -m68020 -mtune=68080`, on a V4 |
| `-fbbb=-` or leaving out the pass letter hides each bug | (SRC) | any | ApolloCrossDev PR #10 |
