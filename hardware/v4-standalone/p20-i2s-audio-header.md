---
title: P20 I2S audio header with a PCM5102A DAC (V4 Standalone)
type: reference
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [other]
components: [hardware, saga-audio-arne]
applies_to:
  core: "any"
  os: [any]
  board: [v4-standalone]
tags: [hardware, header, i2s, audio, dac, pcm5102a, p20]
related:
  - hardware/index.md
  - core/saga-registers/arne-channels.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 8.5"
  - "Wiring sketch PCM5102A to P20 (author not stated), as quoted in the guide"
  - "TI PCM5102A datasheet (SCK tied low: system clock from BCK by the internal PLL)"
---

## Summary

A wiring sketch connects a PCM5102A I2S DAC board to the **P20** header of
the V4 Standalone. Only the odd pins are used. The sketch's author is not
known, and it leaves the supply voltage open: check before you connect.

## Details

| DAC board pin | P20 pin | Signal |
|---|---|---|
| GND and SCK (joined) | 1 | Ground |
| VIN | 3 | DAC supply |
| LCK | 5 | LRCK, the word (left/right) clock |
| BCK | 7 | Bit clock |
| DIN | 9 | Serial audio data |

- Tying SCK to ground makes the PCM5102A build its system clock from BCK
  with its internal PLL (datasheet), so the V4 doesn't need to supply a
  master clock.
- Not in the sketch: the voltage on pin 3, the even pins, and which
  software drives P20.

## Differences from AmigaOS / AROS / 68060

- Classic Amigas have only analogue audio out from Paula; there is no I2S
  header.

## Do / Don't

- DO measure the voltage on pin 3 and compare it with the DAC board's VIN
  range before connecting.
- DON'T treat this as an official pinout: it is a sketch of unknown origin.
