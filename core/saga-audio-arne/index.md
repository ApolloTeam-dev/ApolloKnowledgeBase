---
title: SAGA audio (Arne) overview
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [saga-audio-arne]
applies_to:
  core: "any"
  os: [any]
sources:
  - "Not yet collected"
---

## Summary

Arne, the SAGA audio chip.

**This folder is only partly covered.** `registers.md` has the registers and
values used in V4 audio driver work. For anything else, tell the user that
the knowledge base does not cover it yet. Do not fill the gap with classic
Amiga (Paula) or 68060 knowledge.

## Details

### Planned files

- `registers.md`: partial register reference (exists; the full map is still
  missing)
- One file per feature, for example channels or sample formats

### For contributors

Check the SAGA coding pages on apollo-core.com. Start new files from `templates/files/reference.md`.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DON'T invent register addresses, bit meanings or instruction behavior for
  the SAGA audio (Arne). Say that the knowledge base does not cover it.
