---
title: I2C header (5-pin) for I2C chips such as an RTC
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
basis: [other]
components: [hardware]
applies_to:
  core: "any"
  os: [any]
  board: [any]
tags: [hardware, header, i2c, rtc, clock, i2clock, i2c-library, pinout, breakout-garden]
related:
  - hardware/index.md
sources:
  - "WDrijver (maintainer), 2026-11-04 and 2026-11-05: every V4 has a 5-pin I2C header for I2C chips such as an RTC; usually used with i2clock (i2c.library)"
  - "WDrijver (maintainer), 2026-11-05: the header's pinout, the Breakout Garden standard (3V3, SDA, SCL, INT, GND)"
  - "ApolloUpdate software list, apolloteam-dev.github.io/ApolloSoftware/, 2026-11-05: i2clock 0.7 (Tools) and i2c.library 40.0 (Libraries), for ApolloOS and AmigaOS"
---

## Summary

Every V4 board has a 5-pin I2C header for I2C chips, such as a real-time
clock (RTC) module. Its pinout is the Breakout Garden standard, 3.3 V only.
The usual software for an RTC on it is i2clock, which uses i2c.library.

## Details

- **Header:** 5 pins, I2C, on every V4 model (WDrijver, 2026-11-05).
- **Pinout:** the Breakout Garden standard (WDrijver, 2026-11-05):

  | Pin | Signal | Meaning |
  |---|---|---|
  | 1 | 3V3 | Power supply, 3.3 V only |
  | 2 | SDA | Serial data line |
  | 3 | SCL | Serial clock line |
  | 4 | INT | Interrupt / data-ready signal line |
  | 5 | GND | Ground |

- **Modules:** a Breakout Garden style I2C module with the same pin order
  fits directly, if it runs on 3.3 V.
- **Typical use:** an RTC module, read and set with i2clock through
  i2c.library (WDrijver, 2026-11-04). Both are in ApolloUpdate: i2clock 0.7
  (Tools) and i2c.library 40.0 (Libraries), for ApolloOS and AmigaOS.
- **Not in the knowledge base yet:** the header's designator on each board,
  which pin is pin 1 on the board, and whether the V4 uses the INT line.

## Differences from AmigaOS / AROS / 68060

- A classic Amiga keeps its RTC on the motherboard or the trapdoor
  expansion, read by battclock.resource. On the V4, an RTC is an I2C chip
  on this header.

## Do / Don't

- DO use i2clock (i2c.library) for an RTC module on this header.
- DO check pin 1 on the board and on the module before connecting: a
  module plugged in the wrong way round puts 3.3 V on GND.
- DON'T connect a 5 V module: the header supplies 3.3 V only.
