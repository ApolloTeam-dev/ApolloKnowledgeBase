---
title: 68080 CPU overview
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
sources:
  - "Not yet collected"
---

## Summary

The Apollo 68080 CPU, successor of the Motorola 68000 family, with the AMMX SIMD extension.

**This folder has no content yet.** If your task depends on it, tell the
user that the knowledge base does not cover the 68080 CPU yet. Do not fill the
gap with classic Amiga or 68060 knowledge.

## Details

### Planned files

- `isa.md`: instruction set additions beyond the 68060
- `ammx.md`: AMMX SIMD instructions and registers
- `pipeline-and-timing.md`: pipeline, cycle counts, pairing rules
- `differences-from-68060.md`: what a 68060 programmer would wrongly assume

### For contributors

Check the ApolloCrossDev `Docs/` folder (`AC68080PRM.pdf`, `AMMX/`, `FPU/`, `Integer/`) and the 68080 coding pages on apollo-core.com. Start new files from `templates/files/reference.md`.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DON'T invent register addresses, bit meanings or instruction behavior for
  the 68080 CPU. Say that the knowledge base does not cover it.
