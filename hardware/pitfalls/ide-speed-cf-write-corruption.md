---
title: ApolloControl IDESPEED 3 can corrupt writes to a CF card
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured]
components: [hardware]
applies_to:
  core: "Core 12856"
  os: [apolloos-r10]
  board: [v4-unicorn]
tags: [ide, cf, apollocontrol, idespeed, timing, corruption]
related:
  - guides/testing-on-v4-hardware.md
sources:
  - "ApolloOS R10 port (ApolloOS-Port), 2026-11-17: CF card SanDisk SDCFXS 128 GB on the V4 IDE port, SFS volume"
  - "github.com/ApolloTeam-dev/ApolloSoftware Tools/ApolloControl/2.21: ID=IDESPEED/N - 0=Slow, 1=Fast, 2=Faster, 3=Fastest"
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
and use the highest level that passes. On the tested card `ID=2` passed,
and levels 0–2 were about equally fast (SFS, 16 MB: write ~8 MB/s), so
`ID=3` gained nothing.

## Detection

Before you trust an IDE speed level: copy a 16 MB file to the card, check
its SHA-256 on the V4, set a lower level, and check it again.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| ID=3 corrupts writes | (M) 2026-11-17 | Core 12856, V4 UniCorn | SanDisk SDCFXS 128 GB, SFS: checksum error on block 9223 (SFS NodeContainer) written at ID=3; raw read 3× at ID=2 identical, checksum still wrong |
| ID=0, 1, 2 correct and equally fast | (M) 2026-11-17 | Core 12856, V4 UniCorn | 16 MB written and SHA-256-checked on the V4 at each level: write 2.7–2.9 s, read 0.6–0.7 s |
| One card only | (M) | | Other cards may tolerate ID=3; measure each card |
