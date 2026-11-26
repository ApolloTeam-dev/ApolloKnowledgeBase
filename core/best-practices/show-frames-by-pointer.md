---
title: Show frames by pointer - three buffers in rotation, paced by a VERTB counter
type: best-practice
owner: slaapliedje
status: draft
origin: ai-assisted
basis: [measured, other]
components: [saga-video-isabelle]
applies_to:
  core: "Core 12846"
  os: [any]
tags: [chunky, framebuffer, triple-buffering, page-flip, vblank, vertb, frame-pacing, rgb565]
related:
  - core/saga-registers/chunky-plane.md
  - toolchain/apollolib/system-and-timing.md
  - core/best-practices/prefer-library-calls-for-saga-chips.md
sources:
  - "Advice from the Apollo team to the developer, 2026-11-26 (to be confirmed by the core developer in review): three 64-byte aligned buffers, write the address to $DFF1EC, rotate, do not wait for the vertical blank; pace the game with a VBL counter from an interrupt server"
  - "vidprobe through an HDMI capture card, V4 Standalone, Core 12846, 2026-11-17: chunky pointer swapped 40 times a second at arbitrary moments, 240 captured frames"
  - "sagaprobe, V4 Standalone, Core 12846, 2026-11-17: vertical blank interrupts counted against the E clock in each chunky mode"
  - "VCMI port, V4 Standalone, Core 12846, CoffinOS R65, 2026-11-26: 800x600 RGB565 on an Intuition screen, frame counter per 10 s"
  - "ApolloLib ApolloTimer (ApolloCrossDev Projects/ApolloLib, ApolloCrossDev_LibASM.s): INTB_VERTB server that counts frames"
---

## Goal

No copy of the frame to video memory, no tearing, and no CPU time lost
waiting for the display.

## Technique

- **Allocate three frame buffers**, 64-byte aligned, in any RAM. Draw a frame
  into one, write its address to `$DFF1EC` and go on with the next buffer
  (other: Apollo team advice, 2026-11-26).
- **DON'T wait for the vertical blank after the write.** The chipset takes the
  new address at the next frame boundary by itself (other: Apollo team advice, 2026-11-26): with the
  pointer swapped 40 times a second at arbitrary moments, all 240 captured
  frames showed one picture each (M).
- **Pace the game with a VERTB counter** (other: Apollo team advice, 2026-11-26): an interrupt server
  adds 1 at each vertical blank. Before showing a frame, compare the counter
  with its value at the last frame shown: if it has moved, show the frame at
  once; if not, wait for it. A difference of more than 1 tells the game logic
  that frames were missed. ApolloLib's `ApolloTimer` is such a server.
- **Wait with a signal, not a loop** (M): let the server also `Signal()` the
  drawing task, and `Wait()` for it. A busy loop at the same priority takes
  the CPU from the program's other tasks.
- **The vertical blank interrupt follows the chunky mode's refresh** (M): 60
  a second in 800x600, 50 in the 50 Hz modes. exec's `VBlankFrequency` says 50
  whatever the mode, so count interrupts, don't compute from it.
- **Under the OS**, keep an Intuition screen of the same mode open, so that
  input reaches your window and nothing else draws: check that `$DFE1F4`
  (GFXMODE read back) holds the mode and pixel format you draw in, write
  `$DFF1EC` only while that screen is the front screen
  (`IntuitionBase->FirstScreen`), and write the screen's own address
  (`$DFE1EC` read when you started) back before you close it.
- **DO draw every frame whole.** The buffer you draw into shows the frame from
  three frames ago. A program that only redraws what changed must redraw the
  change into all three buffers, for example by drawing everything for the
  next two frames after each change.

```asm
; VERTB server (AddIntServer(INTB_VERTB, ...)): counts display frames and wakes
; the drawing task. is_Data points at: frames.l, task.l, signal mask.l
VBlankServer:
        addq.l  #1,(a1)         ; frames + 1
        move.l  8(a1),d0        ; signal mask
        move.l  4(a1),a1        ; drawing task
        move.l  4.w,a6          ; SysBase: a6 is scratch in a server
        jsr     -324(a6)        ; Signal(task, mask), allowed in interrupts
        moveq   #0,d0           ; Z set: the rest of the chain runs
        rts
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| New pointer at arbitrary moments | No torn frame in 240 captured frames | Core 12846, V4 Standalone | vidprobe, pointer swapped 40 times a second, HDMI capture at 60 Hz (2026-11-17) |
| Vertical blank interrupt rate | 60 a second in the 60 Hz modes, 50 in 640x512, 1280x720, 720x576 and other 50 Hz modes | Same | sagaprobe, interrupts counted against the E clock |
| VCMI title screen, three buffers, no frame cap | 79.5 frames/s, 12.4 ms per frame drawn | Same, CoffinOS R65 | 800x600 RGB565, every frame drawn whole, frame counter per 10 s |
| Same, frame cap by `sleep_for` | 58.5 frames/s | Same | The C library's sleep, timer.device based |
| Same, paced by the VERTB counter with `Signal()`/`Wait()` | 60.0 frames/s (598–601 per 10 s) | Same | Server as above; the counter is compared before each new pointer is written |

## When not to use

- Copying into a P96 screen bitmap is the portable path; this technique needs
  SAGA and the screen's mode at `$DFE1F4` to match the buffers.
- A program that cannot redraw whole frames, or redraw its changes into every
  buffer, shows old pictures every second or third frame. Use one buffer and
  accept tearing, or redraw whole frames.
- If the game draws faster than the display refreshes, pace it: without the
  counter it can write two pointers in one refresh and then draw into the
  buffer still on screen.
