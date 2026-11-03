---
title: Maggie's depth test does not gate the colour write
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [saga-3d-maggie]
applies_to:
  core: "Core 12847"
  os: [any]
tags: [maggie, 3d, depth-buffer, z-buffer, bug]
related:
  - core/saga-3d-maggie/registers.md
  - core/cpu-68080/core-bugs-by-revision.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 15.7 (regression test test-maggiez, 2026-11-01)"
---

## Symptom

Depth-buffered scenes drawn in arbitrary order show far polygons on top of
near ones: draw near, then far, and far wins.

## Cause

On Core 12847 the depth write is gated correctly (smaller = nearer wins), but
the colour is written on every pixel, whatever the depth test says. Core bug,
reported to the core developer.

## Wrong

```c
/* relies on the depth buffer for visibility */
magSetDrawMode(MAG_DRAWMODE_DEPTHBUFFER);
draw_objects_in_any_order();
```

## Right

Until the bug is fixed, sort polygons back to front (painter's algorithm) so
that the colour of the nearest polygon is written last. This is a general
workaround, not tested in the guide.

## Detection

Draw a near quad, then a far quad over it, with the depth buffer on. If the
far quad is visible, the core has this bug.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Depth write gated, colour write not | (M) | Core 12847 | Register-level test test-maggiez, 2026-11-01 |
