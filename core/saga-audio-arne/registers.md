---
title: ARNE audio registers (partial)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [saga-audio-arne]
applies_to:
  core: "Core 12841"
  os: [any]
tags: [arne, audio, saga, registers, dma, interrupts]
related:
  - core/saga-audio-arne/index.md
  - core/cpu-68080/core-at-a-glance.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 1 and 13"
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

The base addresses of the channel registers are not given in the source.

### Control and interrupt registers

| Register | Address | Meaning |
|---|---|---|
| DMACON2R | `$DFF202` | DMA control, read |
| INTENA2R | `$DFF21C` | Interrupt enable, read |
| INTREQ2R | `$DFF21E` | Interrupt request, read |

- In `INTENA2`/`INTREQ2`, bit n is the interrupt of channel AUD(n+4).
- The ARNE audio interrupt vector offset is `$50`.

### Behaviour

- The high-quality rate caps at about 66 kHz: decimate input above 64 kHz.
- ARNE can DMA from Fast RAM.
- Periods are based on the PAL colour clock of 3546895 Hz, as on Paula.

## Differences from AmigaOS / AROS / 68060

- Paula has 4 channels with registers for channels 0–3; ARNE's extra
  channels are controlled through the second set of DMA and interrupt
  registers (`DMACON2`, `INTENA2`, `INTREQ2`).
- Paula can only DMA from Chip RAM; ARNE can DMA from Fast RAM.

## Do / Don't

- DO keep the period at 65 or higher.
- DO give LEN in sample pairs, not words.
- DON'T guess the remaining ARNE registers: the knowledge base does not
  cover them yet.
