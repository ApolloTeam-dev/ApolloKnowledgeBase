---
title: 68080 ISA notes beyond the PRM (measured)
type: reference
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [core-developer, measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [68080, isa, instructions, exceptions, linea]
related:
  - core/cpu-68080/prm/index.md
  - core/cpu-68080/bank-prefix.md
  - core/pitfalls/pc-relative-destination.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 7.2"
  - "WDrijver (maintainer), 2026-11-11: LineA instructions are not yet implemented; only a few unreleased test cores had them"
---

## Summary

What the 68080 instruction set does in practice, where it adds to or
corrects the PRM: no 64-bit integer arithmetic, no explicit 3-operand
integer form, instructions that do nothing, and 68060-style exception frames.

## Details

- **New instructions in the PRM** ([prm/index.md](prm/index.md)):
  `addiw.l` (no subiw: use a negative value), `cmpiw.l`, `moviw.l`,
  `extub.l`/`extuw.l`, `move2`/`movz2 <ea>,Da:Db` (memory only; movz2 is not
  on the V2), `movex`, `moveh`, `perm`, `touch`, `bcc.s+`, `dbcc.l`, `tex`,
  `rex`.
- `move2.l (An),Dx:Dy` loads both registers correctly on Core 12841 (on Core
  12001 the second was wrong) (M).
- **LineA instructions** (`clr.q`, `mov3q`, `movs`, `movz`) are not yet
  implemented in any released core: don't use them. The manual lists them
  for cores 10280–10904 (official); those were a few unreleased test
  cores, for test purposes only (WDrijver). Use the fused pairs instead
  (`moveq #0` + `move.b`, `move.w` + `ext.l`).
- **abs/min/max/andn** (`$0E81 $20xx`) do nothing and raise no exception
  (M). vasm still assembles them.
- **No 64-bit integer arithmetic.** The "quad" add/sub described on the
  website does not exist. For 64-bit work, use AMMX or the 64-bit multiply.
- **No explicit 3-operand integer form yet.** You get 3-operand behaviour
  through fusing.
- `move sr,<ea>` and `movec Rc,Rn` (reads) work in user mode. A `movec` read
  does not sync the pipeline; a write waits.
- **PC-relative destination:** PC = the address of the destination's
  extension word. It is computed wrongly after a full-extension-format
  source, see [pc-relative-destination.md](../pitfalls/pc-relative-destination.md).
- Shift and rotate register counts are taken modulo 64.
- Exceptions use 68060-style frames. For divide by zero and `chk`, the frame
  PC points to the next instruction.
- **No emulator implements the 68080.** Only the V2 and V4 run 080 code, so
  test 080 code paths on hardware.

## Differences from AmigaOS / AROS / 68060

- The 68000–68060 have no 64-bit integer arithmetic either; the 68080 does
  not add it, despite what some web pages suggest.
- abs/min/max/andn are accepted by vasm but have no effect: a silent bug, not
  an illegal instruction trap.

## Do / Don't

- DON'T use LineA instructions, abs/min/max/andn, or the website's "quad"
  add/sub.
- DON'T rely on an emulator to test 68080-specific code.
- DO expect 68060-style exception frames in handlers.
