---
title: ApolloCrossDev compiler variants and patches
type: reference
owner: WDrijver
status: draft
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
---

## Summary

ApolloCrossDev has one install script per compiler variant. All GCC 6.5
variants build the `amiga-gcc-stable` branch of github.com/WDrijver/amiga-gcc
and differ mainly in which Apollo 68080 patches they apply. Use GCC-6.50-Dev.

## Details

### GCC 6.5 variants

| Variant | Script | Apollo patches applied | Use |
|---|---|---|---|
| GCC-6.50-Dev | `GCC-6.50-Dev-Linux.sh`, `-MacOS.sh` | 13 (see below) | Default, latest |
| GCC-6.50-Stable | `GCC-6.50-Stable-Linux.sh`, `-MacOS.sh` | 5 | Fallback if GCC-6.50-Dev gives problems |
| GCC-6.50-Base | `GCC-6.50-Base-Linux.sh`, `-MacOS.sh` | none | Original baseline (November 2024) |

Each variant installs into its own folder `Compilers/<variant>`, so several
can be installed side by side. All three set `MUIMASTER_VMIN` to 19 in
`mui.h`, so MUI programs also open on MUI 3.8 (from 2026-11-03).

Patches applied by GCC-6.50-Dev on 2026-11-03, from
`Compilers/_archives/patches/`:

| Patch | Author |
|---|---|
| `q4d-candidate.patch` | Ioannis Kouretsidis (JohnStuggi) |
| `q7k-post-q4d-candidate.patch` | Ioannis Kouretsidis (JohnStuggi) |
| `opt-absolute-volatile-fix.patch` | Morten |
| `opt-pipeline-cc0-fix.patch` | Morten |
| `opt-shift-lsr-signext-fix.patch` | Morten |
| `postinc-size-fix.patch` | Morten |
| `double-indirect-fix.patch` | Marcel (RedBug) |
| `bbb-autoinc-direct-add-fix.patch` | TuKo1982 |
| `opt-shift-jump-fix.patch` | TuKo1982 |
| `opt-elim-shift-count-fix.patch` | TuKo1982 |
| `m68k-mrtd-call-pop.patch` | TuKo1982 |
| `m68k-sincos-constraint-fix.patch` | TuKo1982 |
| `m68k-dbra-hi-addrreg-fix.patch` | TuKo1982 |

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

"Fixed" means the install script applies the patch on 2026-11-03. A fix only
reaches you when you reinstall the variant; an older install still has the
bug.

### 68080 instructions the compiler generates

According to the ApolloCrossDev README, the patched GCC 6.5 generates these
68080 instructions: `cmpiw.l`, `addiw.l`, `dbra.l`, `moviw.l`, `bcc.s`.
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
