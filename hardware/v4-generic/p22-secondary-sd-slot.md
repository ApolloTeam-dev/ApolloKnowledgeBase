---
title: P22 secondary SD slot header (SPI)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [official]
components: [hardware]
applies_to:
  core: "any"
  os: [any]
  board: [v4-standalone, v4-unicorn, v4-firebird, v4-manticore]
tags: [hardware, header, spi, sd, storage, p22, sagasd]
related:
  - hardware/index.md
  - hardware/v4-unicorn/p21-serial-console.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 8.4"
  - "Apollo diagram \"Apollo V4 - Secondary SD-Slot (SPI)\" (as quoted in the guide)"
  - "WDrijver (maintainer), 2026-11-04: the V4 IceDrake has no second SPI port"
---

## Summary

Most V4 models have a 10-pin SPI header, **P22**, for a second SD card
slot: useful when you write or test a storage driver, or need a second
card. The V4 IceDrake doesn't have it.

## Details

| Pin | Signal | Function |
|---|---|---|
| 2 | GND1 | Ground |
| 4 | VDD | 3.3 V |
| 5 | SCK | Serial clock |
| 6 | DETECT | SD card detect |
| 7 | MOSI | Master out, slave in |
| 8 | CS | Chip select |
| 9 | MISO | Master in, slave out |
| 1, 3, 10 | NC | Not connected |

- **Layout:** as P21: even pins 2–10 on top, odd pins 1–9 below, key notch
  under pin 5.
- **Boards:** the diagram names the V4 Standalone, Firebird and Manticore.
  On the UniCorn the slot is factory-fitted. The IceDrake has no second SPI
  port (WDrijver, 2026-11-04).
- **Cable:** at most **10 cm**.
- **Software:** AmigaOS needs **sagasd.device 2.8 or newer**.
- **Power:** the VDD pin gives 3.3 V; the diagram itself says "work
  carefully!".

## Differences from AmigaOS / AROS / 68060

- Classic Amigas have no SD or SPI header; storage is IDE, SCSI or floppy.

## Do / Don't

- DO keep the cable at 10 cm or shorter.
- DO use sagasd.device 2.8 or newer.
- DON'T look for P22 on a V4 IceDrake.
- DON'T connect anything but a 3.3 V SD slot to VDD.
