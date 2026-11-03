---
title: What a maggie.library call does to your task
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured, source-code]
components: [libraries, saga-3d-maggie, cpu-68080]
applies_to:
  core: "Core 12841+"
  os: [amigaos-3.9]
tags: [maggie, fpcr, rounding, e-registers, apollo-bit, bank, fpu]
related:
  - os/libraries/maggie-library.md
  - core/cpu-68080/prm/apollo-bit.md
  - core/cpu-68080/bank-prefix.md
  - core/pitfalls/fpu-float-to-integer-conversion.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 15.2"
  - "maggie.library source, github.com/RMortenB/MaggieLibrary, commit 64c78ef (2026-08-17)"
---

## Symptom

After the first frame drawn with maggie.library:

- every FP-to-integer conversion in your own code truncates;
- values you kept in E registers (D8–D31) are gone;
- with the OS running, a task switch in the middle of a draw corrupts the
  frame;
- on a machine without Maggie, nothing is drawn and nothing reports why.

## Cause

- **FPCR is left at round-to-zero.** `magBeginScene` (and library init) set
  FPCR bits 5–4 to RZ in **your** task and do not restore them (SRC).
- **D8–D31 are destroyed.** Some functions clobber all E registers: the
  raster and setup code use them as FPU registers (SRC). d0/d1/a0/a1 are
  scratch as usual.
- **The library uses E registers but never sets the Apollo bit** (SR bit
  11), so on AmigaOS a task switch during a draw loses them.
- **No hardware check:** `hasMaggie` is hard-wired to 1 (a TODO in the
  source). Without a bound texture, nothing is drawn (`CanDraw`).
- **Scene lock:** `magBeginScene`/`magEndScene` take a library-wide
  semaphore and reset the matrices, lights, depth state and draw mode.
- **BANK-prefixed FPU instructions:** about 470 in the setup and raster
  assembler, for example `fdiv e0,e4,e0` = `$7905 $F200 $0220`,
  `fmove.s (a2)+,e18`, and `fmoverz.l e13,d3` (which does not exist on the
  V2). They work on Core 12841 (M), but the team has decided not to support
  BANK on FPU instructions in future cores (G, 2026-10-26).

## Wrong

```c
magBeginScene();
draw_scene();
magEndScene();
ix = (LONG)my_float;    /* now truncates: FPCR left at RZ */
```

## Right

```c
/* GetFPCR/SetFPCR: your own helpers (fmove.l fpcr,d0 / fmove.l d0,fpcr) */
ULONG fpcr = GetFPCR();
SetSR(0x800, 0x800);             /* Apollo bit: keep E registers across task switches */
magBeginScene();
draw_scene();
magEndScene();
SetFPCR(fpcr);                   /* restore your rounding mode */
```

- Keep nothing in E registers across a `mag*` call.
- Check for a V4 yourself before using the library.
- Wrap each frame in `magBeginScene`/`magEndScene`. Under a full takeover you
  may skip them, but then FPCR is not set to RZ for you.
- Check the library on every new core: the BANK-prefixed FPU code will need
  a port when the new FPU encoding arrives.

## Detection

Read FPCR before and after a scene. Test E-register values across a `mag*`
call. Run a draw with other tasks active.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| FPCR set to RZ and not restored; E registers clobbered; Apollo bit not set; `hasMaggie` = 1 | (SRC) | any | maggie.library source, commit 64c78ef |
| The windowed sample sets the Apollo bit with `SetSR(0x800, 0x800)` | (SRC) | any | samples/Windowed |
| BANK-prefixed FPU instructions work | (M) | Core 12841 | Library running on the V4 |
| No BANK prefix on FPU instructions in future cores | (G, 2026-10-26) | Future core | Statement |
