---
title: <short descriptive title>
type: best-practice
owner: <github-handle>
status: draft
origin: <human | ai-assisted>
components: [<one or more: cpu-68080, saga-video-isabelle, saga-audio-arne, saga-dma-anni, saga-3d-maggie, libraries, devs, filesys, commands, datatypes, toolchain, general>]
applies_to:
  core: "<core revision or range>"
  apolloos: "<version or range>"
last_verified: <YYYY-MM-DD, required once status is verified>
tags: [<optional keywords>]
related: [<optional paths to related files>]
sources: [<spec, source file, hardware test, lesson>]
---

## Goal
<What this optimizes: speed, memory, bandwidth, latency.>

## Technique
<How to do it.>

```asm
; kb:compile
<short example>
```

## Evidence
| Variant | Measurement | Core revision | Test setup |
|---|---|---|---|
| Baseline (generic 68k) | <...> | <...> | <...> |
| Optimized | <...> | <...> | <...> |

## When not to use
<Limits, trade-offs, conditions where it does not pay off.>
