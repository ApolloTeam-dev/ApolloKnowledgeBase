---
title: V4 ROM modules, soft resets and avail flush
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [devs, general]
applies_to:
  core: "any"
  os: [amigaos-3.9]
tags: [loadmodule, rom, resident, reset, dma, ethernet, audio-device, avail]
related:
  - os/apolloos-and-amigaos-on-v4.md
  - core/saga-audio-arne/registers.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 13"
---

## Symptom

- A module loaded with LoadModule is not used: the ROM version stays active.
- The machine boots into a corrupted state after a soft reset while a
  network driver was running.
- Audio interrupts break after `avail flush`.

## Cause

| Trap | Cause |
|---|---|
| LoadModule does not replace a module | Modules with priority 105 or more cannot be replaced by LoadModule on the V4: its stub has priority 104 |
| Corruption after a soft reset | Devices whose DMA survives a soft reset (V4 Ethernet RX) keep writing into memory while the next boot runs |
| Audio broken after `avail flush` | ROM audio.device 37.10 writes −1 into all Paula interrupt vectors on expunge |

## Wrong

```text
LoadModule DEVS:mydriver.device   ; priority 110: silently not used
Avail FLUSH                       ; expunges audio.device 37.10
```

## Right

- Flash modules with priority 105 or more into the ROM instead of using
  LoadModule. Check the live vectors, not the resident list, to see which
  version is active.
- Stop the DMA of such devices in a ColdReboot patch.
- Avoid `avail flush` on the V4.

## Detection

After LoadModule, compare the library or device vectors with the new
module's code. After a soft reset with networking active, check for memory
corruption early in the boot.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| LoadModule stub priority 104 | (M) | any | AmigaOS 3.9 on the V4 |
| Ethernet RX DMA survives a soft reset | (M) | any | Network driver work on the V4 |
| audio.device 37.10 writes −1 into the Paula interrupt vectors on expunge | (M) | any | AmigaOS 3.9 ROM on the V4 |
