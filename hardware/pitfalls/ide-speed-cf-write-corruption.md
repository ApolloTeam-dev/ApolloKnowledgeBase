---
title: ApolloControl IDESPEED 3 can corrupt writes to a CF card
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, other]
components: [hardware]
applies_to:
  core: "Core 12846-12856"
  os: [apolloos-r10, amigaos-3.9]
  board: [v4-unicorn, v4-standalone]
tags: [ide, cf, apollocontrol, idespeed, timing, corruption]
related:
  - guides/testing-on-v4-hardware.md
sources:
  - "ApolloOS R10 port (ApolloOS-Port), 2026-11-17: CF card SanDisk SDCFXS 128 GB on the V4 IDE port, SFS volume"
  - "github.com/ApolloTeam-dev/ApolloSoftware Tools/ApolloControl/2.21: ID=IDESPEED/N - 0=Slow, 1=Fast, 2=Faster, 3=Fastest"
  - "VCMI port, V4 Standalone, Core 12846, CoffinOS R65, 2026-11-26: CF card SanDisk SDCFXS-128G (SCSI INQUIRY through scsi.device), SFS volumes; diskprobe (dos.library Read() of whole files, E clock timing) and a 16 MB SHA-256 write check"
  - "Disassembly of ApolloControl 2.21 (identical to the published binary): ID=n writes $0000/$4000/$8000/$C000 to $DD1020"
---

## Symptom

After `ApolloControl ID=3`, a filesystem on a CF card reports checksum
errors on blocks written since the change, for example SFS: "DH0 has a
checksum error in block 9223". The error is still there after a reread
at a slower speed: the block was **written** wrong.

## Cause

`ID=3` (fastest IDE timing) is faster than this CF card handles. Reads
may still look fine, but writes are corrupted.

## Wrong

```text
C:ApolloControl ID=3        ; in S:Startup-Sequence, untested card
```

## Right

Measure the card before setting a speed in the Startup-Sequence. Write a
large file at each level, check it by hash, reread it at a lower level,
and use the highest level that passes. On the tested cards `ID=2` passed.

Set the level explicitly; don't rely on the speed after boot. On a V4
UniCorn levels 0–2 were about equally fast (SFS, 16 MB: write ~8 MB/s). On a
V4 Standalone with the same card model and nothing setting the level, cold
reads ran at 3.2 MB/s, and at 16.1 MB/s after `ID=2`: 5x faster (M). Why the
two boards differ is not known; the UniCorn reads were timed right after
writing the file.

```text
C:ApolloControl ID=2 >NIL:  ; at the top of S:User-Startup, after the write check passed
```

`ApolloControl` writes the level to `$DD1020` (`$0000`, `$4000`, `$8000`,
`$C000` for 0–3) and never reads it, so there is no way to show the current
level with it; measure reads instead.

## Detection

Before you trust an IDE speed level: copy a 16 MB file to the card, check
its SHA-256 on the V4, set a lower level, and check it again.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| ID=3 corrupts writes | (M) 2026-11-17 | Core 12856, V4 UniCorn | SanDisk SDCFXS 128 GB, SFS: checksum error on block 9223 (SFS NodeContainer) written at ID=3; raw read 3× at ID=2 identical, checksum still wrong |
| ID=0, 1, 2 correct and equally fast | (M) 2026-11-17 | Core 12856, V4 UniCorn | 16 MB written and SHA-256-checked on the V4 at each level: write 2.7–2.9 s, read 0.6–0.7 s |
| ID=2 writes correctly | (M) 2026-11-26 | Core 12846, V4 Standalone | SanDisk SDCFXS-128G, SFS: 16 MB random file copied from RAM: at ID=2, SHA-256 identical when read back at ID=2 and after a cold reboot at the boot default |
| Boot default reads 5x slower than ID=2 | (M) 2026-11-26 | Core 12846, V4 Standalone | Cold reads (files not read since boot), `Read()` in 64 KB pieces, ~7 MB per run: 3.15–3.17 MB/s after boot (also 2.8 MB/s with 4 KB and 3.2 MB/s with 1 MB pieces), 16.1–16.2 MB/s at ID=2, before and after a reboot with `ID=2` in User-Startup |
| Level register | (other) 2026-11-26 | any | Disassembly of ApolloControl 2.21: `ID=n` writes `$DD1020`, nothing reads it |
| Two cards of one model | (M) | | Other cards may tolerate ID=3; measure each card |
