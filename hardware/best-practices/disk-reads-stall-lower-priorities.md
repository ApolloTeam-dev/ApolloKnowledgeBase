---
title: IDE reads stop every task below priority 12 - read in small, paced pieces
type: best-practice
owner: slaapliedje
status: draft
origin: ai-assisted
basis: [measured, other]
components: [hardware, devs]
applies_to:
  core: "Core 12846"
  os: [amigaos-3.9]
  mode: [os-friendly]
  board: [v4-standalone]
tags: [ide, cf, scsi.device, lide, pio, streaming, latency, music, file-io, task-priority]
related:
  - hardware/pitfalls/ide-speed-cf-write-corruption.md
sources:
  - "VCMI port, V4 Standalone, Core 12846, CoffinOS R65, 2026-11-26: CF card SanDisk SDCFXS-128G on the IDE port (scsi.device 48.13 in ROM, the lide.device Fast-IDE backend), SFS volume, files read cold through dos.library Read()"
  - "tools/v4/tests/ide-read-rate and tools/v4/tests/ide-read-stall (this knowledge base), run on the machine above on 2026-11-26; the boot-default rows come from diskprobe and wakeprobe, the programs these tests were made from"
  - "pcsamp (CIA-B PC sampler, 1 kHz) during VCMI AI turns, with the samples outside the program mapped to ROM modules by dumping $F00000-$F3FFFF and disassembling it"
---

## Goal

Smooth frames, music and input while a program reads files from the V4's IDE
drive.

## Technique

Measure your own drive with `tools/v4/tests/ide-read-rate` and
`tools/v4/tests/ide-read-stall` (set `AKB_READ_FILES` to cold files first).


- **A read holds up every task below priority 12 for its whole transfer.**
  The priority of the reading task does not matter. The data is moved by the
  CPU (`move16` and `move.l` loops in `scsi.device`, around `$F1D184` in ROM
  48.13) with no DMA, and the CPU is busy for the whole transfer: a counting
  task at priority -1 got 0–1 % of its idle rate while a file was read (M). A
  task at priority 5 woke up to 4.3 ms late during 64 KB reads, one piece's
  transfer time, and a task at priority 12 was not delayed (M). This fits the
  copy running in scsi.device's `lide ata task`, which runs at priority 11.
- **The stall per read is its size divided by the drive speed.** On the CF
  card above: 4 ms per 64 KB at 16 MB/s, 20 ms per 64 KB at the 3.2 MB/s the
  card read after boot. A 60 Hz frame is 16.7 ms.
- **DO set the IDE speed** after checking writes on the card (see
  [ide-speed-cf-write-corruption.md](../pitfalls/ide-speed-cf-write-corruption.md)).
  It divides every stall by the speed gained: 5x on this card.
- **DO stream large files at the rate you use them**, in pieces small enough
  for your frame budget, instead of loading them at full speed. 16-bit
  stereo music at 44.1 kHz uses 176 KB/s: one 64 KB piece every 0.37 s, kept
  a few seconds ahead of playback.
- **DO keep archive files open and read each entry with one `Read()`.** An
  open, a seek and several small reads per entry each pay the drive's
  per-request cost.
- **DON'T expect a higher priority for the drawing task to help** unless it
  is above the driver: everything at priority 11 or lower waits.

```c
/* Read the next piece of a stream only when the buffer runs low: one short
   stall every few hundred ms instead of seconds of stalls when the file opens */
#include <proto/dos.h>

#define PIECE (64 * 1024)

LONG feedStream(BPTR fh, UBYTE *buffer, LONG loaded, LONG total, LONG playedBytes, LONG aheadBytes)
{
	LONG got;
	if (loaded >= total || loaded - playedBytes > aheadBytes)
		return loaded;              /* enough buffered: no read, no stall */
	got = Read(fh, buffer + loaded, total - loaded < PIECE ? total - loaded : PIECE);
	return got > 0 ? loaded + got : total;
}
```

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Read rate after boot, nothing setting the IDE speed | 2.8 MB/s (4 KB pieces), 3.2 MB/s (64 KB), 3.2 MB/s (1 MB); CPU left 0 % | Core 12846, V4 Standalone | diskprobe (as `ide-read-rate`, with the piece size as a parameter), cold files of 2–3.5 MB, about 7 MB per run |
| Read rate at `ApolloControl ID=2` | 16.1–16.3 MB/s (64 KB pieces); CPU left 0–1 % | Same | Same, before and after a reboot with ID=2 in User-Startup |
| Read rate and CPU left at ID=2, published test | 16.1 MB/s, CPU left 0 % | Same | `tools/v4/tests/ide-read-rate`, three cold files, 2 MB |
| Task at priority -1 while reading at ID=2 | 4 wake-ups/s instead of 860, up to 224 ms late | Same | wakeprobe: 1 ms timer.device requests, reader at priority 0 |
| Task at priority 5 | 259 wake-ups/s instead of 862, mean 2.9 ms and max 4.3 ms late | Same | Same |
| Task at priority 12 | 858 wake-ups/s instead of 862, max 0.24 ms late | Same | Same |
| Same, published test | Priority 5: 293 wake-ups/s instead of 864, mean 2.4 ms, max 4.1 ms late; priority 12: 863 instead of 864, max 0.23 ms | Same | `tools/v4/tests/ide-read-stall`, four cold files, 14 MB/s while reading |
| VCMI music read whole on each AI-turn theme change | One 10 s window: 12.8 MB read in 4.1 s of read time, 4.7 frames/s | Same, boot-default IDE speed | Per-file read accounting in the game, frame counter per 10 s |
| Same music read 4 s ahead of playback in 64 KB pieces | 1.7 MB per 10 s, 0.56 s of read time | Same, boot-default IDE speed | Same |
| VCMI archive entries opened, sought and read in 10 KB pieces | 1480 entries of H3sprite.lod in 10 s: 979 KB in 4.6 s of read time, about 3 ms each | Same, boot-default IDE speed | Same; the whole-entry reads that replaced it were not timed separately |

## When not to use

- Small files and loading screens: when nothing on screen has to move, read
  at full speed and get it over with.
- Programs that take over the machine and drive the IDE port themselves are
  outside these measurements.
- Measured on one CF card with SFS. Other cards, other filesystems and the
  secondary SD slot (sagasd.device) were not measured; the SD card driver
  may behave differently.
