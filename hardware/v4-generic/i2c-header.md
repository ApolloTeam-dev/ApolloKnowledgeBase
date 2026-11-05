---
title: I2C header (5-pin) for I2C chips such as an RTC
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [other]
components: [hardware]
applies_to:
  core: "any"
  os: [any]
  board: [any]
tags: [hardware, header, i2c, rtc, clock, i2clock, i2c-library]
related:
  - hardware/index.md
sources:
  - "WDrijver (maintainer), 2026-11-04 and 2026-11-05: every V4 has a 5-pin I2C header for I2C chips such as an RTC; usually used with i2clock (i2c.library)"
---

## Summary

Every V4 board has a 5-pin I2C header for I2C chips, such as a real-time
clock (RTC) module. The usual software for an RTC on it is i2clock, which
uses i2c.library.

## Details

- **Header:** 5 pins, I2C, on every V4 model (WDrijver, 2026-11-05).
- **Typical use:** an RTC module, read and set with i2clock through
  i2c.library (WDrijver, 2026-11-04).
- **Not in the knowledge base yet:** the header's designator on the board,
  its pinout, its voltage, and where i2clock and i2c.library come from.

## Differences from AmigaOS / AROS / 68060

- A classic Amiga keeps its RTC on the motherboard or the trapdoor
  expansion, read by battclock.resource. On the V4, an RTC is an I2C chip
  on this header.

## Do / Don't

- DO use i2clock (i2c.library) for an RTC module on this header.
- DON'T wire a module to it before you know the pinout and voltage: the
  knowledge base doesn't document them yet.
