---
title: SAGA audio (Arne) overview
type: reference
owner: WDrijver
status: reviewed
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

**This folder is only partly covered.** The official register map is in
[core/saga-registers/arne-channels.md](../saga-registers/arne-channels.md)
and [arne-dma-and-interrupts.md](../saga-registers/arne-dma-and-interrupts.md).
`registers.md` has the values measured in V4 audio driver work. For anything
else, tell the user that the knowledge base does not cover it yet. Do not
fill the gap with classic Amiga (Paula) or 68060 knowledge.

## Details

### Planned files

- `registers.md`: values measured in driver work (exists); the official map
  is in `core/saga-registers/`
- One file per feature, for example channels or sample formats

### For contributors

Check the SAGA coding pages on apollo-core.com. Start new files from `templates/files/reference.md`.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DO prefer the library calls (ApolloLib) to direct register access: a best
  practice, not a forced rule (see
  [prefer-library-calls-for-saga-chips.md](../best-practices/prefer-library-calls-for-saga-chips.md)).
- DON'T invent register addresses, bit meanings or instruction behavior for
  the SAGA audio (Arne). Say that the knowledge base does not cover it.
