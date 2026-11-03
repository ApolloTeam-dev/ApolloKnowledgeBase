---
title: The last 8 bytes of a Maggie span stay in the unit
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [saga-3d-maggie]
applies_to:
  core: "Core 12847"
  os: [any]
tags: [maggie, 3d, span, flush, memory-corruption, bug]
related:
  - core/saga-3d-maggie/registers.md
  - core/pitfalls/maggie-span-usage.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 15.7 (regression test test-maggieend, 2026-11-01)"
---

## Symptom

- A CPU read-back right after the last span misses up to 2 pixels (32-bit),
  4 pixels (16-bit) or 4 depth words.
- After a program that used Maggie exits, the next Maggie user's first span
  writes 8 bytes into memory that may have been freed. On the V4 this
  overwrote the next program's code.

## Cause

On Core 12847 the last 8-byte group of a span stays inside Maggie, separately
for the colour stream and the depth stream. It is written only when a later
span writes elsewhere; for depth, that must be a depth-mode span. Waiting
does not flush it, and neither does reading a register.

## Wrong

```c
draw_frame();               /* last span leaves 8 bytes in Maggie */
FreeMem(target, size);      /* the next user's first span writes into it */
```

## Right

Not yet tested; derived from the measured behaviour:

- After the last real span, start a flush span to a small scratch buffer you
  own: one with depth mode on if you used depth. Free that scratch buffer
  only after the flush span.
- Before reading back a target, start such a flush span first.

## Detection

Read back the last pixels of a frame right after drawing. Check for memory
corruption after a Maggie program exits.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| The last 8-byte group stays in the unit; waiting or a register read does not flush it | (M) | Core 12847 | Register-level test test-maggieend, 2026-11-01 |
| The leftover bytes overwrote the next program's code | (M) | Core 12847 | Observed on the V4 |
