---
title: SAGA video (Isabelle) overview
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [saga-video-isabelle]
applies_to:
  core: "any"
  os: [any]
sources:
  - "Not yet collected"
---

## Summary

Isabelle, the SAGA video chip: screen modes and video features.

**This folder has no content of its own yet.** The official register map
is in `core/saga-registers/`: [chunky-plane.md](../saga-registers/chunky-plane.md)
(GFXMODE, screen modes), [colour-ports.md](../saga-registers/colour-ports.md),
[pip.md](../saga-registers/pip.md), [pointer.md](../saga-registers/pointer.md),
[display-control.md](../saga-registers/display-control.md) and
[sprite-collision.md](../saga-registers/sprite-collision.md). For anything
else, tell the user that the knowledge base does not cover it yet. Do not
fill the gap with classic Amiga or 68060 knowledge.

## Details

### Planned files

- One file per feature, for example screen modes or sprites, built on the
  register map in `core/saga-registers/`

### For contributors

Check the SAGA coding pages on apollo-core.com. Start new files from `templates/files/reference.md`.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DO prefer the library calls (ApolloLib) to direct register access: a best
  practice, not a forced rule (see
  [prefer-library-calls-for-saga-chips.md](../best-practices/prefer-library-calls-for-saga-chips.md)).
- DON'T invent register addresses, bit meanings or instruction behavior for
  the SAGA video (Isabelle). Say that the knowledge base does not cover it.
