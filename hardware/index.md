---
title: Apollo V4 hardware overview
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [hardware]
applies_to:
  core: "any"
  os: [any]
tags: [v4, boards, models, standalone, unicorn, icedrake, manticore, firebird]
sources:
  - "WDrijver (maintainer), V4 models and abbreviations, 2026-11-03"
  - "WDrijver (maintainer), same core on every V4 model, 2026-11-04"
---

## Summary

The V4 models share the same FPGA core (68080 CPU and SAGA chipset, see
`core/`) but differ as boards. This pillar holds the board knowledge:
connectors, headers, memory and model differences.

## Details

### Models

| Model | Abbreviations | Folder | `applies_to.board` |
|---|---|---|---|
| V4 Standalone | SA | `hardware/v4-standalone/` | `v4-standalone` |
| V4 UniCorn | UNI, A6000 | `hardware/v4-unicorn/` | `v4-unicorn` |
| V4 IceDrake | ICE | `hardware/v4-icedrake/` | `v4-icedrake` |
| V4 Manticore | MC | `hardware/v4-manticore/` | `v4-manticore` |
| V4 Firebird | FB | `hardware/v4-firebird/` | `v4-firebird` |

The V4 Standalone and the V4 UniCorn are different models.

### One core architecture for all models (rule)

All V4 boards share the same core architecture. A core number has exactly
the same features and architecture on every model: Core 12600 on the V4
UniCorn is the same as Core 12600 on the V4 IceDrake, including the 68080,
SAGA and the memory controller. Models differ only in small physical
properties, for example: the V4 IceDrake has no second SPI port.

So a fact about the core (`core/`) holds for every model; give the core
number, not the model. Put a physical difference in `hardware/`.

### Where things go

- `hardware/v4-generic/`: knowledge that holds for every V4 model.
- `hardware/v4-<model>/`: only what is specific to that model. A fact that
  holds for several, but not all, models goes in `v4-generic/` with
  `applies_to.board` listing those models.
- `hardware/best-practices/` and `hardware/pitfalls/`: as in the other
  pillars.

### Files

| Topic | File | Boards |
|---|---|---|
| Memory: Chip, Fast and video RAM | [v4-generic/memory.md](v4-generic/memory.md) | All |
| P22 secondary SD slot (SPI) | [v4-generic/p22-secondary-sd-slot.md](v4-generic/p22-secondary-sd-slot.md) | SA, UNI, FB, MC (not ICE) |
| P20 I2S audio header (PCM5102A DAC) | [v4-standalone/p20-i2s-audio-header.md](v4-standalone/p20-i2s-audio-header.md) | SA |
| I2C header (5-pin), for an RTC module | [v4-generic/i2c-header.md](v4-generic/i2c-header.md) | All |

For anything else on the boards, tell the user that the knowledge base does
not cover it yet.

## Differences from AmigaOS / AROS / 68060

Classic Amiga hardware knowledge (Zorro, Gayle, the A1200 trapdoor) does not
tell you what a V4 model has. Check the model's folder.

## Do / Don't

- DO check `applies_to.board` before using a board fact for your target
  model.
- DON'T assume a connector or header exists on every V4 model.
