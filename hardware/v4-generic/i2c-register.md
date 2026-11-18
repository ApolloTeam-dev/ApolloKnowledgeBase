---
title: I2C bus register $DE0080 (software I2C for the RTC header)
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [hardware, libraries]
applies_to:
  core: "any"
  os: [any]
  board: [v4-unicorn]
tags: [i2c, rtc, ds3231, ds1307, i2clock, i2c-library, battclock, bit-banging]
related:
  - hardware/v4-generic/i2c-header.md
sources:
  - "i2clib source (i2c.library 40.0 'for Apollo Core boards', BSD licence): src/apollo.i and i2cbootrom.s"
  - "ApolloOS-Port commit 3b151de (2026-11-18): arch/m68k-amiga/battclock/ds3231.c and test/tools/RTCTest.c"
  - "Hardware test on a V4 Unicorn, Core 12856, ApolloOS R10 dev card, 2026-11-18"
---

## Summary

The V4 has no I2C controller with a FIFO: software drives the two I2C lines
of the RTC header through one word register at `$DE0080` (bit-banging).
i2c.library 40.0 "for Apollo Core boards" and ApolloOS R10's
battclock.resource both use it to reach an RTC chip such as the DS3231.

## Details

| Access | Address | Bit | Meaning |
|---|---|---|---|
| write (word) | `$DE0080` | 1 | SCL: 1 = released (high), 0 = pulled low |
| write (word) | `$DE0080` | 0 | SDA: 1 = released (high), 0 = pulled low |
| read (byte) | `$DE0081` | 0 | SDA as seen on the bus (for ACK and data from the chip) |

- **Initial state:** write `$0003` (both lines released), as i2c.library's
  `INITPORT` does.
- **Timing:** i2c.library and ApolloOS R10 hold each bus phase with reads of
  CIA-B `$BFD000`; one CIA access takes an E-clock cycle (about 1.4 us).
  ApolloOS R10 uses two reads per phase, which keeps the bus clock below
  200 kHz; a DS3231 allows up to 400 kHz.
- **RTC address:** a DS3231 or DS1307 answers at `$D0` (write) / `$D1`
  (read). Registers 0..6 are seconds, minutes, hours, weekday, date, month
  and year in BCD.
- **Year and weekday as C:I2Clock 0.7 stores them** (measured 2026-11-18):
  year register = year - 1976 (so 1976..2075; the DS3231 century bit is not
  used), weekday register = the Amiga weekday (0 = Sunday). A program that
  writes the DS3231 standard (year - 2000) makes I2Clock show the year 24
  years too early, and the other way round.

## Differences from AmigaOS / AROS / 68060

- A classic Amiga reads its clock from a memory-mapped chip at `$DC0000`
  through battclock.resource. The V4 has no chip there; the RTC is an I2C
  chip reached through `$DE0080`. Until ApolloOS R10, only C:I2Clock (through
  i2c.library) read and set it, so Prefs/Time and `SetClock SAVE` did not
  reach it.
- ApolloOS R10's battclock.resource probes `$D0` when `$DC0000` has no clock
  and then reads and writes the RTC itself, in I2Clock's year format.

## Do / Don't

- DO keep I2Clock's year format (year - 1976) when writing the RTC, so the
  chip stays usable from AmigaOS, ApolloOS R9.x and R10.
- DO run a whole transfer (start to stop) without other tasks touching
  `$DE0080` in between, e.g. under `Disable()`; a transfer of the 7 time
  registers takes well under a millisecond.
- DON'T write `$DE0080` as a byte: the lines are in the word (bits 1 and 0
  of the word written at `$DE0080`).

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| SCL bit 1, SDA bit 0 written as a word at `$DE0080`; SDA read at bit 0 of `$DE0081` | (SRC) i2clib `src/apollo.i` | any | source reading |
| A DS3231 answers at `$D0` and reads/writes correctly with this protocol | (M) 2026-11-18 | Core 12856 | C:RTCTest PROBE/READ/WRITE on a V4 Unicorn, compared with C:I2Clock SHOW |
| I2Clock stores year - 1976 and the Amiga weekday | (M) 2026-11-18 | Core 12856 | RTCTest wrote 2026 as standard (26), I2Clock showed 2002; I2Clock's own 2026 read back as register 50 |
