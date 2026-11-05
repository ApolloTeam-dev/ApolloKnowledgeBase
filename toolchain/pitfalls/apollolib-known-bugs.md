---
title: ApolloLib bugs fixed in 2026-11 and the limits that remain
type: pitfall
owner: WDrijver
status: reviewed
origin: ai-assisted
basis: [source-code]
components: [toolchain, saga-audio-arne, saga-video-isabelle]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, bugs, showpicture, timer, takeover, endian, mouse, sound]
related:
  - toolchain/apollolib/index.md
  - toolchain/apollolib/picture.md
  - toolchain/apollolib/sound.md
  - toolchain/apollolib/system-and-timing.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib, commit ce1fcbf (2026-11-04), read on 2026-11-04"
  - "ApolloCrossDev pull requests #17 and #18 (merged 2026-11-04), fixed in commit 639e195"
  - "ApolloCrossDev pull request #19 (merged 2026-11-04), PiP palette, commit a9a994f"
  - "ApolloCrossDev pull request #21 (merged 2026-11-04), ApolloLoadPointer, commit b9891d9"
---

## Symptom

A program shows a 320-pixel picture in the wrong mode or an 8-bit picture
in wrong colours, crashes some time after it exits, never gets the
Workbench back, or plays a mono sound too fast. It was built against
ApolloLib from before 2026-11-04.

## Cause

ApolloLib up to commit ce1fcbf had these bugs. They were found by reading
the code while documenting the library, and fixed in commit 639e195
(ApolloCrossDev pull request #18). None of the fixes is tested on V4
hardware yet.

### Fixed in 639e195

| Function | Bug before 639e195 |
|---|---|
| `ApolloShowPicture` | `case 320` fell through into `case 480`: 320x200 became 304x224, 320x240/256 became 1280x720/640x360 |
| `ApolloShowPicture` | The 8-bit palette was reordered a second time: wrong colours |
| `ApolloTimer` | The VBlank server was never removed; its node lives in the program, so the system crashed after the program exited. Now: `ApolloTimerStop()` |
| `ApolloTakeOver`, `ApolloForbid`, `ApolloDisable` | No way back. Now: `ApolloRelease()`, `ApolloPermit()`, `ApolloEnable()` |
| `ApolloCPUDelay` | Fixed 92 MHz; the overflow check could not work |
| `ApolloEndianSwapLongBuffer` | Swapped words instead of bytes; both buffer swaps counted their remainder wrongly |
| `ApolloPlaySound` | Always 16-bit stereo, whatever the file contained |
| `ApolloPlayFile` | Applied its offset twice |
| `ApolloMouse` | The "middle button" was the wheel counter |
| `ApolloLoadFile`/`Sound`/`Picture` | Left the file open on errors; BMP palette read from a fixed offset |
| `ApolloShowPattern` | Wrote only the first byte of each pixel |
| `ApolloCrossDev_Lib.h` | Declared `ApolloShowPiP`/`ApolloHidePiP`, which don't exist, and not `ApolloShowPiP1/2`/`ApolloHidePiP1/2` |
| `ApolloLoadPointer` (b9891d9, #21) | Returned nothing and never set `bLoaded`; accepted 24-bit BMPs without converting them (empty pointer); read 32-bit alpha correctly only with `endian` set; overwrote palette entry 255 when full; never freed the BMP it loaded. Now it returns an `APOLLO_PICTURE_…` code, converts 24-bit, reads BMP byte order, frees the BMP, and `ApolloShowPointer` does nothing without a loaded pointer. |
| PiP palette (a9a994f, #19) | From 789cbcc (2026-06-16) to a9a994f nothing loaded an 8-bit PiP palette: `ApolloLoadPicture` had stopped writing it into the port chosen by `picture->target`. Now `ApolloShowPiP1/2` load it. |
| Five functions (#17) | Wrong DMACON2R bit for channels 4–15, a write through an uninitialized pointer, missing return values, an always-on keyboard print |

### Limits that remain

| Function | Limit |
|---|---|
| `ApolloPlaySound` | 8-bit stereo can't play (Arne's stereo mode is 16-bit); 8-bit WAV samples are unsigned and are not converted to the signed format Arne expects |
| `ApolloPlaySound` | A sound without format information (`bitspersample` 0, for example RAW) plays as 16-bit stereo |
| `ApolloPlaySound` | The free-channel search starts at channel 1 |
| `ApolloPlay`, `ApolloPlayFile` | Subtract 32 sample pairs from the length, without an explanation |
| `ApolloLoadPicture` | Keeps its file state in `static` variables: not reentrant |
| `ApolloRelease` | Restores the priority saved by `ApolloTakeOver`; called without it, it sets priority 0 |

## Wrong

```c
ApolloTakeOver();
ApolloTimer();
/* ... */
return 0;                 /* Workbench stays closed; next VBlank jumps into freed code */
```

## Right

```c
ApolloTakeOver();
ApolloTimer();
/* ... */
ApolloTimerStop();        /* ApolloLib 639e195 or later */
ApolloRelease();
return 0;
```

## Detection

- Check which ApolloLib a project builds against: `ApolloRelease` and
  `ApolloTimerStop` exist only from 639e195. A build that fails on them
  uses an older copy.
- Read GFXMODE back at `$DFE1F4` after `ApolloShowPicture`: the high byte
  must match the picture's size (see
  [chunky-plane.md](../../core/saga-registers/chunky-plane.md)).

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| The bugs before 639e195 | (SRC) | any | Code reading of commit ce1fcbf, 2026-11-04 |
| Fixed in 639e195; builds without warnings | (SRC) | any | ApolloCrossDev #18: ApolloPointer, ApolloPiP (then SAGAPiP) and a link test build |
| None of the fixes is tested on V4 hardware | – | – | – |
