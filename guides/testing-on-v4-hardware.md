---
title: Run and check programs on a V4 from another computer
type: guide
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [general, toolchain, hardware]
applies_to:
  core: "any"
  os: [any]
  mode: [any]
tags: [testing, remote, ash, acp, apolloexplorer, serial, capture, ffmpeg, power-cycle]
related:
  - guides/benchmark-method.md
  - guides/writing-cpu-tests.md
  - core/cpu-68080/performance-counters.md
sources:
  - "lessons/2026-11-akb-verification.md"
  - "ApolloKnowledgeBase tools/v4/v4test.py and tools/v4/tests/ (2026-11-09)"
  - "ApolloOS-Port project, mk/card.mk and tools/ (WDrijver, 2026-10)"
  - "github.com/WDrijver/ApolloCrossDev Projects/ApolloLib/ApolloCrossDev_Debug.c"
---

## Goal

Copy a program to a V4, run it, and collect its text output, its serial
output and a picture of the screen, all from another computer and without
touching the V4. A V4 that hangs is switched off and on again remotely.
This is how the knowledge base's own hardware tests run (`tools/v4/`).

## Prerequisites

- A V4 on the network with **ApolloExplorerSrv** running, started at boot.
  It must be recent: on a V4 with ApolloOS R9.5, `ash` connected but never
  returned output until the server was updated, while `acp` worked (M).
- On the other computer: `ash` and `acp` from ApolloExplorer.
- For serial output: a USB-to-serial cable on the V4's serial port (the
  ApolloCrossDev README names a PL2303 cable), at 115200 8N1 without flow
  control.
- For pictures: an HDMI capture device and ffmpeg. The commands below are
  for macOS (`avfoundation`).
- For power cycling: a smart plug that switches the V4's power over HTTP.
  The tested setup uses a plug with Tasmota firmware.

## Steps

1. **Check the V4 answers.** Every remote command needs a timeout and
   stdin from `/dev/null`: a hung V4 never answers, and `ash` waits
   forever.

   ```sh
   ash <v4-address> "C:Echo up" </dev/null     # prints: up
   ```

2. **Record the core number** with every result: `ash <v4-address>
   "ApolloControl CO"` prints it, for example `12556`. The SAGA register
   `$DFF3EA` (CORE REVISION) has no documented format.
3. **Copy the program.** In `acp`'s destination, put a slash after the
   volume name:

   ```sh
   acp program <v4-address>:RAM/akb/
   ```

   The folder must exist: `ash <v4-address> "C:MakeDir RAM:akb"`.
4. **Run it.** `ash <v4-address> "RAM:akb/program"` returns the program's
   output when it ends. Let the program print its results as text: the
   knowledge base tests print `PASS`, `FAIL` and `VALUE` lines and end with
   `AKB-DONE`, so a crash shows as a missing last line.
5. **Collect serial output.** Write to the Paula UART directly at 115200
   baud, as ApolloLib's `ApolloDebugPutChar()` does: set `SERPER`
   (`$DFF032`), wait for `TBE` in `SERDATR` (`$DFF018`), write `SERDAT`
   (`$DFF030`). This needs no OS, so it also works in `os-takeover` code.
   `Echo >SER:`, which goes through serial.device, did not reach the cable
   at any baud rate between 9600 and 115200 (M).
6. **Take a picture or a video** of the HDMI output. The tested capture
   device rejects ffmpeg's default pixel format, so name one:

   ```sh
   ffmpeg -f avfoundation -pixel_format uyvy422 -framerate 30 \
     -i "USB Video:none" -frames:v 1 screen.png
   ffmpeg -f avfoundation -pixel_format uyvy422 -framerate 60 \
     -i "USB Video:USB Digital Audio" -t 10 -c:v libx264 -pix_fmt yuv420p run.mp4
   ```

   `ffmpeg -f avfoundation -list_devices true -i ""` lists the device
   names. ffmpeg needs about a second to start: start it before the
   program.
7. **Recover a hung V4.** Switch the plug off, wait 10 s, switch it on, and
   wait until step 1 answers again. The tested V4 answered 15 s after
   power-on (M).

`tools/v4/v4test.py` in the knowledge base does all of this: it builds the
test with ApolloCrossDev, runs variants alternately (see
[benchmark-method.md](benchmark-method.md)), and stores output, serial log,
picture and core number per run.

## Verification

- Step 1 prints `up`, and step 2 prints a core number.
- A program that writes a known line to the UART (the knowledge base test
  `serial-out`) shows that line in the serial log.
- After a power cycle, `RAM:` is empty and step 1 answers again.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `ash` hangs with the older ApolloExplorerSrv, works after the update; `acp` works with both | (M) | Core 12556 | V4 UniCorn, ApolloOS R9.5, 2026-11-09 |
| Direct UART writes at 115200 arrive; `Echo >SER:` does not | (M) | Core 12556 | `tools/v4/tests/serial-out`; `SER:` listened for at 9600, 19200, 38400, 57600, 115200 |
| The V4 answers `ash` 15 s after power-on | (M) | Core 12556 | `v4test.py power-cycle`, Tasmota plug |
| The capture device needs `-pixel_format uyvy422` and offers 1920x1080 at up to 60 fps | (M) | any | ffmpeg 9.0.2, macOS |
