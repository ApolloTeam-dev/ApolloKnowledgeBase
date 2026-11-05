---
title: P21 serial console header (UART)
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
tags: [hardware, header, uart, serial, debug, p21]
related:
  - hardware/index.md
  - toolchain/apollolib/debug.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 8.3"
  - "Apollo diagram \"Apollo V4 UniCorn - P21\" (as quoted in the guide)"
  - "WDrijver (maintainer), 2026-11-05: all V4 boards have P21 except the V4 IceDrake"
---

## Summary

Every V4 board except the IceDrake has a 10-pin UART header, **P21**
(WDrijver, 2026-11-05), for debug output from a driver or from code that
runs before or without the screen. Only pins 7 (TX) and 9 (RX) are
connected.

## Details

| Pin | Signal | Note |
|---|---|---|
| 7 | UART-TX | The V4 transmits: connect to the cable's RX |
| 9 | UART-RX | The V4 receives: connect to the cable's TX |
| 1–6, 8, 10 | NC | Not connected |

- **Layout, as in the diagram:** even pins 2–10 on the top row, odd pins
  1–9 on the bottom row, with the key notch under pin 5. TX (7) and RX (9)
  are the two right-hand pins of the bottom row.
- **Settings:** a USB TTL serial cable at **115200 baud, 8 data bits,
  1 stop bit**. The diagram doesn't give the parity: use none.
- **Ground:** the diagram shows no ground pin on P21, so the cable's ground
  must go to a board ground elsewhere.
- **Logic level:** not given in the diagram either.

ApolloLib's debug output writes to the serial port at 115200 baud (see
[debug.md](../../toolchain/apollolib/debug.md)).

## Differences from AmigaOS / AROS / 68060

- A classic Amiga has its serial port on a DB25 connector at RS-232 levels.
  P21 is a TTL header. The V4 IceDrake has no P21: use the Amiga's own
  serial port there. (The guide said all accelerator cards lack P21; the
  Firebird and Manticore do have it.)

## Do / Don't

- DO cross TX and RX: the V4's TX (7) goes to the cable's RX.
- DO connect the cable's ground to a board ground, and check the logic
  level before you wire it.
- DON'T look for P21 on a V4 IceDrake.
