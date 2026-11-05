---
title: SAGA 3D (Maggie) overview
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [saga-3d-maggie]
applies_to:
  core: "any"
  os: [any]
sources:
  - "Not yet collected"
---

## Summary

Maggie, the SAGA 3D chip.

**This folder is only partly covered.** It has the official register names
([core/saga-registers/maggie-3d.md](../saga-registers/maggie-3d.md)), the
span registers as maggie.library uses them (`registers.md`) and the pitfalls in
`core/pitfalls/maggie-*.md`. For anything else, tell the user that the
knowledge base does not cover it yet. Do not fill the gap with classic Amiga
or 68060 knowledge.

## Details

### Planned files

- `registers.md`: the span unit registers as maggie.library uses them, with
  measured behaviour (exists; the official names are in
  `core/saga-registers/maggie-3d.md`)
- One file per feature, for example texture mapping
- Using maggie.library: [os/libraries/maggie-library.md](../../os/libraries/maggie-library.md)

### For contributors

Check the SAGA coding pages on apollo-core.com. Start new files from `templates/files/reference.md`.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DO prefer the library calls (maggie.library) to direct register access: a best
  practice, not a forced rule (see
  [prefer-library-calls-for-saga-chips.md](../best-practices/prefer-library-calls-for-saga-chips.md)).
- DON'T invent register addresses, bit meanings or instruction behavior for
  the SAGA 3D (Maggie). Say that the knowledge base does not cover it.
