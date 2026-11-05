---
title: ARNE audio registers (partial)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [core-developer, measured]
components: [saga-audio-arne]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [arne, audio, saga, registers, dma, interrupts]
related:
  - core/saga-audio-arne/index.md
  - core/cpu-68080/core-at-a-glance.md
  - core/saga-registers/arne-channels.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 1 and 13"
  - "Gunnar (core developer, BigGun), Apollo chat, 2026-11-04 (relayed by WDrijver): Paula clock, 60 kHz max mode, no minimum rate, HDMI resampling, 44.1 kHz for games"
---

## Summary

A partial register reference for SAGA audio (ARNE), from driver work on the
V4. It covers the values and registers the guide uses; the full register map
is not documented here yet.

## Details

### Channel registers

| Register | Meaning |
|---|---|
| PER (period) | Minimum period (MINPER) is 65 |
| LEN | 32-bit count of **sample pairs** |
| VOL | Left volume in bits 15–8, right volume in bits 7–0 |

The channel base addresses are in the official register map:
[core/saga-registers/arne-channels.md](../saga-registers/arne-channels.md).

### Control and interrupt registers

| Register | Address | Meaning |
|---|---|---|
| DMACON2R | `$DFF202` | DMA control, read |
| INTENA2R | `$DFF21C` | Interrupt enable, read |
| INTREQ2R | `$DFF21E` | Interrupt request, read |

- In `INTENA2`/`INTREQ2`, bit n is the interrupt of channel AUD(n+4).
- The ARNE audio interrupt vector offset is `$50`.

### Behaviour

- Arne runs in a 60 kHz max mode (G, 2026-11-04): decimate input above
  that. The guide gave about 66 kHz (decimate above 64 kHz); the core
  developer's figure is leading. There is no minimum sample rate, and the
  HDMI audio output resamples down for compatibility with all monitors
  (G, 2026-11-04).
- For games, use 44.1 kHz (period 80), the CD standard (G, 2026-11-04).
- ARNE can DMA from Fast RAM.
- Periods are based on the PAL colour clock of 3546895 Hz, as on Paula:
  the period coding is Paula-compatible (G, 2026-11-04).

## Differences from AmigaOS / AROS / 68060

- Paula has 4 channels with registers for channels 0–3; ARNE's extra
  channels are controlled through the second set of DMA and interrupt
  registers (`DMACON2`, `INTENA2`, `INTREQ2`).
- Paula can only DMA from Chip RAM; ARNE can DMA from Fast RAM.

## Do / Don't

- DO keep the period at 65 or higher.
- DO use 44.1 kHz for game audio (G).
- DO give LEN in sample pairs, not words.
- DON'T guess ARNE registers: use the official map in
  `core/saga-registers/`.
