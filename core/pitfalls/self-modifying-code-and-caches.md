---
title: CacheClearU does nothing; writes near code are slow
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12841"
  os: [amigaos-3.9, amigaos-3.2]
tags: [68080, cache, self-modifying-code, cacheclearu, cinva, 68040-library]
related:
  - core/cpu-68080/caches-and-memory.md
  - core/cpu-68080/prm/specs.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 0 (rule 18) and 5.2"
---

## Symptom

- Patched or generated code runs the old instructions, although the program
  called `CacheClearU()` after writing it.
- Writes to buffers placed next to running code are about 3 times slower
  than expected.

## Cause

- Under AmigaOS the 68080's 68040.library patches `CacheClearU` and
  `CacheClearE` to a bare `rts`. They also never flush the 68080 data cache.
- The core detects writes into cached or in-flight code (official: "080 has
  selfmodify detection"), but patched code still ran stale without an
  instruction-cache flush (M).
- The self-modify detection slows every write near running code.

## Wrong

```asm
    move.w  #$4e71,(a0)     ; patch code
    movea.l 4.w,a6
    jsr     _LVOCacheClearU(a6)  ; does nothing on the 68080
    jmp     (a0)            ; may run the old instruction
```

## Right

Flush the instruction cache with `cinva ic` in supervisor mode, for example
through `Supervisor()`:

```asm
    lea     .flush(pc),a5
    movea.l 4.w,a6
    jsr     _LVOSupervisor(a6)
    ; ...
.flush:
    cinva   ic
    rte
```

- Keep benchmark buffers and written data away from running code.
- Evicting the data cache takes 128–256 KB of reads.

## Detection

Search for `CacheClearU`/`CacheClearE` used after writing code. Check that
data written in hot loops is not linked into the code section next to the
loop.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| The 080 has self-modify detection | (official) PRM, specs page | any | Manual |
| `CacheClearU`/`CacheClearE` are a bare `rts` under the 080 68040.library | (M) | Core 12841 | AmigaOS 3.9 with the 080 68040.library |
| Patched code ran stale without `cinva ic` | (M) | Core 12841 | Test program |
| A store + 2 `add.l` took 9 cycles next to running code instead of about 3 | (M) | Core 12841 | CCC |
