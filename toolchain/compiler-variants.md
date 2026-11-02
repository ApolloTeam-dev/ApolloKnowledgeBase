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
---

## Summary

ApolloCrossDev has one install script per compiler variant. All GCC 6.5
variants build the `amiga-gcc-stable` branch of github.com/WDrijver/amiga-gcc
and differ mainly in which Apollo 68080 patches they apply. Use GCC-6.50-Dev.

## Details

### GCC 6.5 variants

| Variant | Script | Apollo patches applied | Use |
|---|---|---|---|
| GCC-6.50-Dev | `GCC-6.50-Dev-Linux.sh`, `-MacOS.sh` | 7 (see below) | Default, latest |
| GCC-6.50-Stable | `GCC-6.50-Stable-Linux.sh`, `-MacOS.sh` | 5 | Fallback if GCC-6.50-Dev gives problems |
| GCC-6.50-Base | `GCC-6.50-Base-Linux.sh`, `-MacOS.sh` | none | Original baseline (November 2024) |

Each variant installs into its own folder `Compilers/<variant>`, so several
can be installed side by side.

Patches applied by GCC-6.50-Dev, from `Compilers/_archives/patches/`:

| Patch | Author |
|---|---|
| `q4d-candidate.patch` | Ioannis Kouretsidis (JohnStuggi) |
| `q7k-post-q4d-candidate.patch` | Ioannis Kouretsidis (JohnStuggi) |
| `opt-absolute-volatile-fix.patch` | Morten |
| `opt-pipeline-cc0-fix.patch` | Morten |
| `opt-shift-lsr-signext-fix.patch` | Morten |
| `postinc-size-fix.patch` | Morten |
| `double-indirect-fix.patch` | Marcel (RedBug) |

GCC-6.50-Stable applies `q2g-stable.patch` and the four patches by Morten.

### 68080 instructions the compiler generates

According to the ApolloCrossDev README, the patched GCC 6.5 generates these
68080 instructions: `cmpiw.l`, `addiw.l`, `dbra.l`, `moviw.l`, `bcc.s`.
Planned, not yet supported: `mov3q`, `clr.q`, `move2.b`, `movs.b/w`,
`movz.b/w`.

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
