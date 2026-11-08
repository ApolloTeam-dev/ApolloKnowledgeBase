---
title: ApolloCrossDev compiler variants and patches
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [toolchain, cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [apollocrossdev, gcc, patches]
related:
  - toolchain/index.md
  - toolchain/c-compiler-options.md
sources:
  - "github.com/WDrijver/ApolloCrossDev README.md"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Base-Linux.sh, GCC-6.50-Stable-Linux.sh, GCC-6.50-Dev-Linux.sh, GCC-13.3.sh, GCC-15.2.sh"
  - "WDrijver (ApolloCrossDev maintainer), 2026-11-02"
  - "github.com/WDrijver/ApolloCrossDev pull requests #5 to #10, #12 and #13 (merged on 2026-11-03)"
  - "github.com/WDrijver/ApolloCrossDev pull request #15 (removes double-indirect-fix.patch) and issue #14"
  - "WDrijver (ApolloCrossDev maintainer), 2026-11-04"
---

## Summary

ApolloCrossDev has one install script per compiler variant. All GCC 6.5
variants build the `amiga-gcc-stable` branch of github.com/WDrijver/amiga-gcc
and differ mainly in which Apollo 68080 patches they apply. Use GCC-6.50-Dev.

## Details

### GCC 6.5 variants

| Variant | Script | Apollo patches applied | Use |
|---|---|---|---|
| GCC-6.50-Dev | `GCC-6.50-Dev-Linux.sh`, `-MacOS.sh` | 12 (see below) | Default, latest |
| GCC-6.50-Stable | `GCC-6.50-Stable-Linux.sh`, `-MacOS.sh` | 5 | Fallback if GCC-6.50-Dev gives problems |
| GCC-6.50-Base | `GCC-6.50-Base-Linux.sh`, `-MacOS.sh` | none | Original baseline (November 2024) |

Each variant installs into its own folder `Compilers/<variant>`, so several
can be installed side by side. All three set `MUIMASTER_VMIN` to 19 in
`mui.h`, so MUI programs also open on MUI 3.8 (from 2026-11-03).

Patches applied by GCC-6.50-Dev from ApolloCrossDev pull request #15
(2026-11-04), from
`Compilers/_archives/patches/`:

| Patch | Author |
|---|---|
| `q4d-candidate.patch` | Ioannis Kouretsidis (JohnStuggi) |
| `q7k-post-q4d-candidate.patch` | Ioannis Kouretsidis (JohnStuggi) |
| `opt-absolute-volatile-fix.patch` | Morten |
| `opt-pipeline-cc0-fix.patch` | Morten |
| `opt-shift-lsr-signext-fix.patch` | Morten |
| `postinc-size-fix.patch` | Morten |
| `bbb-autoinc-direct-add-fix.patch` | TuKo1982 |
| `opt-shift-jump-fix.patch` | TuKo1982 |
| `opt-elim-shift-count-fix.patch` | TuKo1982 |
| `m68k-mrtd-call-pop.patch` | TuKo1982 |
| `m68k-sincos-constraint-fix.patch` | TuKo1982 |
| `m68k-dbra-hi-addrreg-fix.patch` | TuKo1982 |

Until then GCC-6.50-Dev also applied `double-indirect-fix.patch` by Marcel
(r3dbug). It stopped GCC from generating memory indirect addressing, and
made GCC crash on computed gotos through a table (`jmp ([table,dN.l*4])`,
for example in Lua's `lvm.c`). It was removed because the 68080 has full
double indirect addressing (WDrijver, 2026-11-04).

GCC-6.50-Stable applies `q2g-stable.patch` and the four patches by Morten,
none by TuKo1982.

### Known GCC bugs and which variant fixes them

| Bug | Pitfall | Dev | Stable | Base |
|---|---|---|---|---|
| bbb pass counts a post-increment twice | [gcc-bbb-autoinc.md](pitfalls/gcc-bbb-autoinc.md) | Fixed | Not fixed | Not fixed |
| bbb pass deletes needed instructions around shifts | [gcc-bbb-shift-wrong-code.md](pitfalls/gcc-bbb-shift-wrong-code.md) | Fixed | Not fixed | Not fixed |
| ICE with `-mrtd` | [gcc-mrtd-calling-convention.md](pitfalls/gcc-mrtd-calling-convention.md) | Fixed | Not fixed | Not fixed |
| ICE on `sinf`/`cosf` with `-ffast-math` | [gcc-fsincos-ice.md](pitfalls/gcc-fsincos-ice.md) | Fixed | Not fixed | Not fixed |
| 16-bit loop counter in an address register runs away | [gcc-dbra-address-register-loop.md](pitfalls/gcc-dbra-address-register-loop.md) | Fixed | Not fixed | Not fixed |
| ICE in `print_operand_address2` on computed gotos (Dev builds of 2026-11-03 only) | [double-memory-indirect.md](../core/pitfalls/double-memory-indirect.md) | Fixed (patch removed) | Not affected | Not affected |

"Fixed" means the install script applies the patch on 2026-11-03. A fix only
reaches you when you reinstall the variant; an older install still has the
bug.

### 68080 instructions the compiler generates

The ApolloCrossDev README lists `cmpiw.l`, `addiw.l`, `dbra.l`, `moviw.l`
and `bcc.s+`. The GCC source has output patterns for three of them (SRC,
WDrijver/gcc branches `gcc-stable` and `68080regs`, 2026-11-08):

| Instruction | GCC emits it for | Where |
|---|---|---|
| `cmpiw.l` | comparing a long with a 16-bit immediate | `m68k.md` |
| `addiw.l` | adding a 16-bit immediate to a long | `m68k.c` |
| `dbra.l` (`dbral`) | a loop with a 32-bit counter | `m68k.md` |

DON'T expect `moviw.l` or `bcc.s+` from GCC. Neither the GCC branches nor
the patches in ApolloCrossDev's `Compilers/_archives/patches/` have a
pattern for them; GCC-6.50-Dev emits a 6-byte `move.l #imm` for a 16-bit
constant. Write them in assembly when you need them. CI checks this:

```c
// kb:compile
// kb:expect cmpiw.l #1000,
// kb:expect addiw.l #1000,
// kb:expect dbral
// kb:expect move.l #1000,d0
// kb:expect-not moviw
int is_k(long x) { return x == 1000; }
void add_k(long *p) { *p += 1000; }
long k(void) { return 1000; }
long sum(const long *p, long n)
{
    long s = 0, i;
    for (i = 0; i < n; i++)
        s += p[i];
    return s;
}
```

Planned, not yet supported: `mov3q`, `clr.q`, `move2.b`, `movs.b/w`,
`movz.b/w`.

`mov3q`, `clr.q`, `movs` and `movz` are LineA instructions that exist only
on cores 10280–10904 (official, see [core/cpu-68080/isa-notes-measured.md](../core/cpu-68080/isa-notes-measured.md)).
Code generated with them would not run on current cores; the fused pairs
(`moveq #0` + `move.b`, `move.w` + `ext.l`) give the same effect.

### GCC 13 and 15 (beta)

Scripts `GCC-13.1.sh`, `GCC-13.2.sh`, `GCC-13.3.sh` and `GCC-15.2.sh` build
the branches `amiga-gcc-13.x` and `amiga-gcc-15.2`. They are beta and their
scripts apply none of the Apollo patches above, and they do not support
`-m68080`.

## Differences from AmigaOS / AROS / 68060

- The Apollo patches exist only for GCC 6.5. A newer GCC is not automatically
  better for Apollo V4: it lacks these patches.

## Do / Don't

- DO use GCC-6.50-Dev for Apollo V4 code.
- DO try GCC-6.50-Stable when you suspect a compiler bug in GCC-6.50-Dev, and
  report the difference.
- DON'T use the GCC 13 or 15 beta for Apollo V4 code. They cannot target the
  68080.
