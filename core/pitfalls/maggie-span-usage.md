---
title: Maggie span traps (zero length, no cache snoop, one user, counters)
type: pitfall
owner: TuKo1982
status: reviewed
origin: ai-assisted
basis: [measured, source-code]
components: [saga-3d-maggie]
applies_to:
  core: "Core 12847"
  os: [any]
tags: [maggie, 3d, span, cache, arbitration, counters]
related:
  - core/saga-3d-maggie/registers.md
  - core/pitfalls/maggie-span-tail.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 15.7"
---

## Symptom

- Memory gets overwritten after a span with length 0.
- The CPU reads stale pixels or depth values from a buffer Maggie has just
  drawn.
- Two programs drawing with Maggie at once spoil each other's spans.
- The performance counters at `$DFF300` never change.

## Cause

- A span with length 0 overwrote memory on the V4, probably as 65536 pixels
  (M).
- Maggie does not snoop the CPU data cache (SRC): a CPU read of the depth
  buffer or of a target Maggie has just drawn can hit stale cache lines.
- There is one register set. Neither AmigaOS nor maggie.library arbitrates
  between programs; the library's semaphore covers only its own callers.
- The counters at `$DFF300` read 0 on Core 12847 (M).

## Wrong

```asm
    move.w  d0,14(a0)       ; d0 may be 0: never start a span with length 0
```

## Right

```asm
    tst.w   d0
    beq.s   .skip           ; skip empty spans
    move.w  d0,14(a0)
.skip:
```

- Make sure the CPU does not read a Maggie target or the depth buffer
  through stale data-cache lines. The guide gives no tested method. Note that
  `CacheClearU` does nothing on the 68080 (see
  [self-modifying-code-and-caches.md](self-modifying-code-and-caches.md))
  and that evicting the data cache takes 128–256 KB of reads.
- Let one program at a time use Maggie.
- Don't use the counters as a sync source.

## Detection

Check every write to the start + length register for a possible 0. Look for
CPU reads of Maggie targets or the depth buffer without a cache flush.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| A length-0 span overwrote memory | (M) | Core 12847 | Observed on the V4 |
| Maggie does not snoop the CPU data cache | (SRC) | any | maggie.library source and docs |
| Counters at `$DFF300` read 0 | (M) | Core 12847 | Register-level test test-maggiecnt, 2026-11-01 |
| No arbitration between programs | (SRC), (M) | Core 12847 | Library source; two programs observed |
