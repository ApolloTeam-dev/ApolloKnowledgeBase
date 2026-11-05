---
title: libnix and header traps
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured]
components: [toolchain]
applies_to:
  core: "any"
  os: [amigaos-3.9, amigaos-3.2]
tags: [libnix, sprintf, stdio, stack, headers, mui, stdint]
related:
  - toolchain/c-compiler-options.md
  - toolchain/target-os-headers.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 9.5"
  - "github.com/WDrijver/ApolloCrossDev pull request #6 (merged on 2026-11-03)"
---

## Symptom

- `sprintf` prints 16-bit numbers for `%d` and returns no length.
- GCC 6 fails on `stdint.h` from an SDK.
- A MUI 3.8 system refuses to open muimaster.library.
- Output from worker processes is garbled; a requested stack size is
  ignored; `memset`/`memcmp` are slow; `%p` prints wrongly.

## Cause

| Trap | Cause |
|---|---|
| `sprintf` behaves like RawDoFmt | libnix `sprintf` lives in `libm.a`. Without `-lm`, amiga.lib's `sprintf` (RawDoFmt: `%d` = 16 bits, no length returned) is linked silently |
| SDK `stdint.h` breaks GCC 6 | The SDK's header conflicts with GCC 6's own |
| muimaster.library does not open | GCC 6 `mui.h` sets `MUIMASTER_VMIN` to 20 (MUI 4). ApolloCrossDev installs from 2026-11-03 lower it to 19 in all GCC 6.5 variants |
| Worker process output | libnix stdio is not safe from worker processes |
| Stack size ignored | libnix does not honour `__stack` |
| Slow `memset`/`memcmp` | libnix works byte by byte |
| `%p` | Misprints in libnix |

## Wrong

```sh
m68k-amigaos-gcc main.o -noixemul -o app              # amiga.lib sprintf
m68k-amigaos-gcc -I sdk/include -c main.c             # SDK stdint.h first
```

## Right

```sh
m68k-amigaos-gcc main.o -noixemul -lm -o app          # libnix sprintf
m68k-amigaos-gcc -idirafter sdk/include -c main.c     # SDK headers last
```

- Open muimaster.library with version 19 for MUI 3.8. An install from
  2026-11-03 does this through `MUIMASTER_VMIN`; with an older install, pass
  19 yourself.
- Do stdio from the main process only.
- Swap to your own stack with `StackSwap()` when you need a larger one (see
  [gcc-stackswap-defer-pop.md](gcc-stackswap-defer-pop.md)).
- Write your own `memset`/`memcmp` for hot paths.

## Detection

Check the link line for `-lm`, the include order for SDK folders, and the
muimaster version you open.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| All items in the table | (M) | any | Project builds on AmigaOS 3.9 |
