---
title: TEX does not match the PRM
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, official]
components: [cpu-68080]
applies_to:
  core: "Core 12846"
  os: [any]
tags: [68080, ammx, tex, texture, bug]
related:
  - core/cpu-68080/prm/ammx/tex.md
  - core/cpu-68080/core-bugs-by-revision.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 6 (measured 2026-10-31)"
---

## Symptom

`TEX (An,Ax,Ay*Dm),Dn` reads the wrong texel: x/y coordinates in 16.16 and
the line width have no effect. `x 1, y 1, m 256` reads offset 0.

## Cause

On Core 12846 the third word of the instruction acts as a plain brief
extension word: bit 15 D/A, bits 14–12 register, bit 11 W/L, bits 10–9
scale. The core reads the byte at `An + Xn.W/L * scale`.

- Ax (word 3 bits 2–0), Dm (word 2 bits 14–12) and the displacement byte are
  not used.
- The older `TEX8/16/24.size (An,(Av,Au)),Dn` encodings decode the same way.
  There is no word, 24-bit, DXT1 or 32-bit fetch, and no modular map.
- The texel replaces the low byte of Dn. The other 56 bits are kept, not
  shifted up.
- vasm 2.0g has no syntax for TEX: it needs `dc.w`.

## Wrong

```asm
    ; per the PRM: byte at (a0) + y*width + x, with x in a1, y in a2 (16.16)
    ; and the line width in d7. Hand-encoded with dc.w (vasm has no syntax).
    ; On Core 12846 the coordinates and width are ignored.
    ; tex (a0,a1,a2*d7),d4
```

## Right

Don't use TEX until the Apollo team settles its behaviour (question Q6 to the
core developer). Compute the address yourself and use `move.b`.

## Detection

Search for TEX, REX and `dc.w` sequences starting with `$FE`.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| TEX byte form with 16.16 coordinates and line width Dm | (official) PRM, TEX page | Core 12540+ | Manual |
| The core reads `An + Xn.W/L * scale`; Ax, Dm and displacement unused | (M) | Core 12846 | mh groups 25/26, 2026-10-31 |
