---
title: ApolloLib known bugs (commit ce1fcbf)
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain, saga-audio-arne, saga-video-isabelle]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, bugs, showpicture, timer, takeover, endian, mouse]
related:
  - toolchain/apollolib/index.md
  - toolchain/apollolib/picture.md
  - toolchain/apollolib/sound.md
  - toolchain/apollolib/system-and-timing.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib, commit ce1fcbf (2026-11-04), read on 2026-11-04"
---

## Symptom

A program built with ApolloLib shows a wrong screen mode or wrong colours,
crashes some time after it exits, never gets the Workbench back, or plays
a sound wrongly, while the calls look right.

## Cause

ApolloLib at commit ce1fcbf has bugs and gaps, found by reading the code
on 2026-11-04. "Confirmed" means the code shows it; "suspected" means the
code suggests it and a test on a V4 is still needed. None has been tested
on hardware.

### Serious

| Function | Problem | Status |
|---|---|---|
| `ApolloShowPicture` | `case 320:` has no `break` after its inner switch and falls into `case 480`, which ORs in `$0800`. 320x200 becomes `$0900` (304x224); 320x240 and 320x256 become `$0A00`/`$0B00` (1280x720, 640x360). | Confirmed |
| `ApolloTimer` | The VBlank interrupt server node lives in the program's code and is never removed. After the program exits and is unloaded, the next VBlank runs freed memory. | Confirmed (code); crash expected |
| `ApolloTakeOver`, `ApolloForbid`, `ApolloDisable` | No counterpart restores the Workbench, the task priority, `Permit()` or `Enable()`; the opened intuition.library is never closed | Confirmed |
| `ApolloShowPicture` | For depth ≤ 8 it reorders the bytes of each palette entry that `ApolloLoadPicture` already converted to `$IIRRGGBB`, which gives `$IIGGRRII` | Suspected: 8-bit pictures show wrong colours |

### Others

| Function | Problem | Status |
|---|---|---|
| `ApolloCrossDev_Lib.h` | Declares `ApolloShowPiP()`/`ApolloHidePiP()`, which don't exist; the real `ApolloShowPiP1/2`, `ApolloHidePiP1/2` are not declared | Confirmed |
| `ApolloMouse` | `Button_Middle` is the low byte of the wheel register `$DFF212` (the wheel counter), not a button | Suspected |
| `ApolloEndianSwapLongBuffer` | `vperm #$23016745` swaps the words of each long instead of reversing its bytes (`$32107654`); its remainder count (`and #5`) and that of `ApolloEndianSwapWordBuffer` (`and #3`) count bytes, not longs or words | Confirmed (code) |
| `ApolloCPUDelay` | Assumes 92 MHz (the V4 runs at 99.31 MHz); the 32-bit overflow check after `add.l` (`cmp.l #$FFFFFFFF`) can't detect a carry | Confirmed (code) |
| `ApolloPlaySound` | Always programs 16-bit stereo, LEN = size / 8, whatever the file contains; the free-channel search skips channel 0 | Confirmed |
| `ApolloPlayFile` | Applies `offset` twice (in `fseek` and again in pointer and length) | Confirmed |
| `ApolloPlay`, `ApolloPlayFile` | Subtract 32 from the length in sample pairs, without an explanation | Unclear |
| `ApolloLoadFile`, `ApolloLoadSound`, `ApolloLoadPicture` | Some error returns leave the file open (header checks, short reads) | Confirmed |
| `ApolloLoadPicture` | Reads the BMP palette from offset 54, right only for a 40-byte BITMAPINFOHEADER; uses `static` file state (not reentrant) | Confirmed |
| `ApolloShowPattern` | Writes only the first byte of each pixel for depths above 8 | Confirmed |

## Wrong

```c
pic.width = 320; pic.height = 200;   /* 8-bit, 320x200 */
ApolloShowPicture(&pic);             /* sets GFXMODE $0901, not $0101 */
ApolloTimer();                       /* never removed */
return 0;                            /* next VBlank jumps into freed code */
```

## Right

```c
/* Write the mode yourself for 320-pixel modes until the bug is fixed */
*(volatile uint16_t *)0xDFF1F4 = APOLLO_SAGA_320_200 | APOLLO_SAGA_8_INDEX;
/* Count VBlanks in your own interrupt server, and remove it before exit */
```

## Detection

- Read GFXMODE back at `$DFE1F4` after `ApolloShowPicture`: the high byte
  must match the picture's size (see
  [chunky-plane.md](../../core/saga-registers/chunky-plane.md)).
- Search the program for `ApolloTimer`, `ApolloTakeOver`, `ApolloForbid`
  and `ApolloDisable`, and check the exit path for the matching restore.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| All bugs in the tables | (SRC) | any | Code reading of commit ce1fcbf, 2026-11-04 |
| The 14 earlier `-Wall` warnings, 5 of them bugs, are fixed | (SRC) | any | ApolloCrossDev pull request #17, merged 2026-11-04 |
| None of these is tested on V4 hardware | – | – | – |
