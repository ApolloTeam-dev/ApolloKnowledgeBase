---
title: <short descriptive title>
type: best-practice
owner: <github-handle>
status: draft
origin: <human | ai-assisted | official>
basis: [<optional, one or more, highest rank first: core-developer, measured, official, source-code, other>]
components: [<one or more: cpu-68080, saga-video-isabelle, saga-audio-arne, saga-dma-anni, saga-3d-maggie, libraries, devs, filesys, commands, datatypes, toolchain, hardware, general>]
applies_to:
  core: "<any | Core 12841 | Core 12830-12840 | Core 12841+>"
  os: [<one or more: any, apolloos-r10, amigaos-3.9, amigaos-3.2>]
  mode: [<optional, one or more: any, os-friendly, os-takeover>]
  board: [<optional, one or more: any, v4-standalone, v4-unicorn, v4-icedrake, v4-manticore, v4-firebird>]
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
| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Baseline (generic 68k) | <...> | <...> | <...> |
| Optimized | <...> | <...> | <...> |

## When not to use
<Limits, trade-offs, conditions where it does not pay off.>
