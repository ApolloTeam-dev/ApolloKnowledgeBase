---
title: VCMI (Heroes III engine) on the V4 - C++20 with GCC 16, AMMX sprites, Arne audio, frames by pointer
type: lesson
owner: slaapliedje
status: draft
origin: ai-assisted
basis: [measured, source-code, other]
components: [cpu-68080, saga-audio-arne, saga-video-isabelle, libraries, devs, toolchain, hardware]
applies_to:
  core: "Core 12846"
  os: [amigaos-3.9]
  mode: [os-friendly]
  board: [v4-standalone]
tags: [vcmi, c++20, gcc16, newlib, sdl2, arne, music, ammx, storem, apollo-bit, rgb565, chunky, vblank, ide, malloc, emutls]
related:
  - core/saga-registers/arne-channels.md
  - core/saga-registers/arne-dma-and-interrupts.md
  - core/saga-registers/chunky-plane.md
  - core/cpu-68080/prm/ammx/storem.md
  - core/cpu-68080/prm/ammx/storeilm.md
  - core/cpu-68080/prm/apollo-bit.md
  - toolchain/apollolib/system-and-timing.md
  - toolchain/compiler-variants.md
  - hardware/pitfalls/ide-speed-cf-write-corruption.md
sources:
  - "Local port of VCMI (github.com/vcmi/vcmi, develop branch of 2026-11-22), not yet published; 2026-11-22 to 2026-11-26"
  - "Measured on a V4 Standalone, Core 12846, CoffinOS R65, with pcsamp (CIA-B PC sampler, 1 kHz), the 68080 cycle counter (movec $809), a frame counter logged every 10 s, and small probe programs (diskprobe, wakeprobe, lsscreens, devof, inquiry)"
  - "Advice from the Apollo team to the developer, 2026-11-26 (to be confirmed by the core developer in review): frame buffers shown by pointer, pacing with a VBL counter"
  - "SDL2 AmigaOS 3 port (AmigaPorts SDL, branch feature/AmigaOS3): src/audio/SDL_audio.c, src/video/amigaos3/SDL_os3video.c, SDL_os3window.c, SDL_os3mouse.c"
  - "newlib of the AmigaPorts GCC 16.2 toolchain: libc.a objects sleep.o and gettimeofday, disassembled"
  - "OpenLara V4 port, src/platform/amiga/arne.h (effects one-shot per Arne channel, music as PCM from RAM)"
---

## Project

VCMI, the open-source Heroes of Might and Magic III engine (C++20, SDL2,
Boost, Lua), ported to the V4 Standalone from 2026-11-22 to 2026-11-26.
Headless AI games first, then the SDL2 GUI at 800 x 600 on an Intuition
screen, then sound and music, then frame rate. OS-friendly; the program runs
from the Workbench shell. Over the whole work the adventure map went from
about 10 to 23-31 frames/s and battles from about 3 to 11-12 frames/s on an
AI test map.

## What went well

- **C++20 with GCC 16.2.** VCMI needs C++20 (`std::ranges` in about 80
  files), which GCC 6.5 cannot compile. The AmigaPorts GCC 16.2 (`amiga16`
  branch, built with POSIX threads) with `-m68060` built VCMI and all its
  dependencies, and the result runs on the V4. `std::thread` on AmigaOS needs
  GCC 16.2 or later. The KB's toolchain pages cover GCC 6.5 only; for a C++20
  code base GCC 6.5 is not an option, and `-m68060` code plus hand-written
  AMMX worked.
- **AMMX for sprites.** Colour-keyed 8-bit sprites converted to RGB565 and
  drawn with `load (a0)+,e0` / `storem3 e0,#2,(a1)+`; shadows with
  `pand` / `lsrq #1` / `storem` and a one-bit-per-byte mask stream. Full
  800 x 600 frame: keyed sprites 4 ms (C: 35 ms), shadow 11 ms (C: 112 ms).
- **Frames shown by pointer** (the technique of
  `core/best-practices/show-frames-by-pointer.md`): three 64-byte aligned
  RGB565 buffers in fast RAM, the address written to `$DFF1EC` after each
  frame, no wait (other: Apollo team advice, 2026-11-26). This removed the copy of every frame into the
  P96 bitmap. Pacing with a VERTB interrupt server that counts frames and
  signals the drawing task gave a steady 60.0 frames/s on the title screen.
- **Sound effects and music on Arne only.** Each effect plays once on its own
  channel (4-15, skipping the busy ones in DMACON2R and channel 7, which AHI's
  Arne driver uses), polled every 10 ms. Music is 16-bit big-endian PCM AIFF
  (44.1 kHz stereo, Arne's format) on one more channel. MP3 decoding had cost
  about 30 % CPU; with PCM it is 0 %. SDL_mixer and AHI are no longer opened,
  so AHI's mixing task no longer runs.
- **Raising the IDE speed** (`ApolloControl ID=2`) after a 16 MB write check
  made every file read 5x faster on this CF card (3.2 to 16.1 MB/s).

## What went wrong

- **The C library's clock and sleep counted in 1/50 s.** newlib's
  `gettimeofday` (behind `std::chrono::steady_clock` and `system_clock`) is
  `DateStamp()`, and its `usleep`/`sleep` are `Delay()` rounded up to whole
  ticks. Frame pacing and animation timing were quantised to 20 ms, a 1 ms
  sleep slept 20 ms, and a 60 frames/s cap gave 40. Fixed with
  `-Wl,--wrap=gettimeofday` (date from newlib once, then timer.device's E
  clock, 709379 Hz) and a timer.device `usleep`/`sleep` (both in one newlib
  object, so both had to be replaced).
- **SDL2 on AmigaOS 3 left screens open at exit.** Restoring the desktop mode
  passes the desktop mode, not NULL, so the driver opened another screen
  instead of closing its own; and the display is added without driver data,
  so the screen opened for the display mode was never stored and never
  closed. Each run left an empty screen behind the Workbench, and later
  starts hung inside `OpenScreenTags`.
- **SDL2 on AmigaOS 3 drew the pointer as a 16-pixel, 3-colour classic
  sprite**, squeezing wider cursors to half width.
- **Slow SDL blitters on a 16-bit screen.** A 24-bit background picture went
  through SDL's generic per-pixel alpha blitter every frame (title screen
  1.9 frames/s; 79.5 after converting such pictures once to RGB565), and
  constant-alpha blits between two RGB565 surfaces (the map's fade between
  views) and scaled blits from 32-bit (the minimap) went through
  `SDL_Blit_Slow`.
- **Disk reads stopped the game.** Reads on the IDE drive hold up every task
  below priority 12 (`hardware/best-practices/disk-reads-stall-lower-priorities.md`).
  The music player read each new track (8-15 MB) at full speed at every
  AI-turn theme change: 4 s of reads in one 10 s window, 4.7 frames/s.
  Reading 4 s ahead of playback in 64 KB pieces fixed it. Archive entries were
  opened, sought and read in 10 KB pieces one by one, about 3 ms each.
- **A spin-and-`Delay(1)` lock in malloc stalled threads for a whole 20 ms
  tick** behind a lower-priority holder, and exec semaphores hand ownership
  over on release (lock convoy). A `Forbid()`/`Permit()` lock around the
  allocator removed both.
- **Thread-local storage in the AmigaPorts GCC 16 runtime:** at thread exit,
  emutls freed the TLS block before libstdc++ ran the `thread_local`
  destructors. Registering `__cxa_thread_atexit` from a `constructor(101)`
  before emutls creates its key fixed the order. newlib's `free()` silently
  ignores bad and double frees, which hid this until dlmalloc replaced it.
- **Run-to-run averages lie** for a game whose AI plays differently each run:
  averages of two runs of the same build differed by up to 8 frames/s.
  Compare slow and fast 10 s windows, and where the samples go in each.

## What the AI got wrong

- **Used the AMMX E registers without setting the Apollo bit.** The sprite
  kernels use E0-E7 in a normal task. The KB's
  [apollo-bit.md](../core/cpu-68080/prm/apollo-bit.md) says that on a
  ROM-patched AmigaOS or CoffinOS, E registers survive task switches only for a
  program that sets SR bit 11. The AI did not look there. Not fixed yet; no
  corruption seen.
- **Read the STOREM example as written.** The STOREM page's example uses the
  mnemonic `storeilm` and the STOREILM page's example uses `storem`; the data
  and results of each example match the other page's instruction. Checking on
  the hardware showed STOREM writes the bytes whose mask bit is 1, bit 7 of the
  mask's low byte being the first byte.
- **Drew every frame with total redraws without checking where the frame
  logic lives.** VCMI ends a hero's movement animation in `show()`, which a
  total redraw (`showAll()`) skips. With three buffers and a total redraw on
  every frame, the animation never ended, the network thread waited for it
  forever, and the game could not be quit; the V4 needed a reboot.
- **Called the IDE drive "the SD card"**, because the hot loop lay next to
  `sagasd.device` in ROM. The DOS device node showed `scsi.device`, the IDE
  driver, and the card answered SCSI INQUIRY as a CF card.
- **Hung the V4 with a measuring task.** To see whether reads hold up tasks
  above the reader, it ran a counting loop that never sleeps at priority 5:
  the reader, the network stack and the remote shell starved, and the
  developer had to reset the machine. A task that sleeps in 1 ms timer
  requests and records how late it wakes answered the question safely.
- **Made battles slower with a correct fix.** A blended rectangle fill that
  SDL had drawn opaque on RGB565 was made to blend; battles then spent 12 % in
  it, because the adventure map dimmed the whole screen under the full-screen
  battle window on every frame. Skipping the hidden map fixed it.
- **Probed a hardware register while the game ran** (an Arne test tone and
  repeated DMACON2R reads during play), which coincided with static, flicker
  and AHI's channel stopping; the machine had to be rebooted.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| `storem e3,d0,(a1)+` = `$FE19,$B005`; writes bytes whose bit in d0's low byte is 1; bit 7 is the first byte | (M) | Core 12846 | Test program on the V4: masks 0, $FF, single bits, compared with a C reference |
| AMMX encodings `load (a0)+,e0` `$FE18,$0801`; `storem3 e0,#2,(a1)+` `$FE19,$8226`; `pand (a1),e6,e3` `$FE11,$EB08`; `lsrq e5,e3,e3` `$FE0D,$BB39`; `paddw e4,e3,e3` `$FE0C,$BB11` | (M) | Core 12846 | Hand-assembled words in test programs, output compared with a C reference on the V4 |
| Keyed sprite blit 800 x 600: 4 ms AMMX, 35 ms C; shadow 11 ms vs 112 ms | (M) | Core 12846 | Timed full-screen test draws on the V4 |
| MP3 music decoding about 30 % CPU; 0 % with PCM AIFF on Arne | (M) | Core 12846 | pcsamp 1 kHz over 10-minute AI games, same map |
| newlib `gettimeofday` steps 20 ms; `sleep_for(1..10 ms)` sleeps 20 ms | (M), (SRC) | Core 12846 | Test program: smallest `steady_clock` step 20000 us, 20 sleeps timed; libc.a disassembled (`DateStamp`, `Delay((us + 19999) / 20000)`) |
| After the E clock wrap and timer.device sleep: clock step 22 us, `sleep_for(1 ms)` 2.8 ms; title screen 39.5 to 58.5 frames/s with a 60 cap | (M) | Core 12846 | Same test program; frame counter |
| VERTB server pacing: 60.0 frames/s; uncapped 79.5 frames/s (12.4 ms per frame) | (M) | Core 12846 | Frame counter per 10 s, 800 x 600 RGB565 |
| Leaked SDL screens: 1 screen before a run, 2 after; 1 after the fixes in 4 runs, same address reused | (M), (SRC) | Core 12846 | lsscreens (walks IntuitionBase->FirstScreen under LockIBase) before, during and after runs; logging in the SDL driver |
| 24-bit picture via SDL's alpha blitter: 540 ms per frame; converted once to RGB565: 12.4 ms | (M) | Core 12846 | pcsamp (90 % in one static blitter function); frame counter |
| Map 18.6 to 29.1-31.4 frames/s, battle 5.6 to 10.7-12.3 frames/s, after the blitter, dim, fade, minimap, music and archive fixes | (M) | Core 12846 | 10-minute AI games on one test map with pcsamp; slow and fast windows split by the frame counter |
| Music read whole: 12.8 MB in 4.1 s of read time in one 10 s window, 4.7 frames/s; paced: 1.7 MB in 0.56 s per 10 s | (M) | Core 12846 | Per-file read accounting in the game, boot-default IDE speed |
| `Delay(1)` lock stalled malloc callers 20 ms; Forbid/Permit lock removed the dos/timer time from the profile | (M) | Core 12846 | pcsamp profiles before and after |
| emutls frees TLS before `thread_local` destructors (AmigaPorts GCC 16.2) | (M), (SRC) | any | Trapping malloc in the volamos emulator with `--sanitize`; fixed by key order |

## Candidates for distillation

- `sources/official/AC68080PRM.odt` (STOREM and STOREILM): swap the two
  examples' mnemonics, then regenerate the two pages.
- `core/cpu-68080/prm/ammx-unit.md` or `core/pitfalls/`: "using E registers in
  a task without the Apollo bit", pointing to `apollo-bit.md`.
- `toolchain/pitfalls/`: newlib's 20 ms `gettimeofday` and tick-rounded
  `usleep`, for projects on the AmigaPorts GCC 16 toolchain (libnix of
  ApolloCrossDev not checked).
- `os/pitfalls/`: SDL2 on AmigaOS 3 leaves screens open at exit and draws the
  pointer as a classic 16-pixel sprite; list open screens before and after a
  run.
- `core/saga-video-isabelle/`: the chunky pointer is taken at the frame
  boundary, and the VERTB rate follows the chunky mode (see
  `core/best-practices/show-frames-by-pointer.md`).
- `core/best-practices/music-as-pcm-on-arne.md`: play music as big-endian PCM
  from RAM on one stereo channel, read at the rate it plays.
- `guides/benchmark-method.md`: map PC samples that fall outside the program
  to ROM modules by dumping the ROM and disassembling the hot addresses.
- `toolchain/compiler-variants.md`: C++20 projects can use the AmigaPorts GCC
  16.2 with `-m68060` (no Apollo patches, no `-m68080`), with the emutls trap
  above.
