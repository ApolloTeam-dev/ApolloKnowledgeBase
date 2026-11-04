---
title: ApolloLib picture, PIP and pointer functions (Isabelle)
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain, saga-video-isabelle]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, isabelle, picture, bmp, dds, pip, pointer, sprite]
related:
  - toolchain/apollolib/index.md
  - core/saga-registers/chunky-plane.md
  - core/saga-registers/pip.md
  - core/saga-registers/pointer.md
  - toolchain/pitfalls/apollolib-known-bugs.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_LibC.c, _Lib.h, _Defines.h), commit 639e195 (2026-11-04)"
  - "Example ApolloPiP.c (formerly SAGAPiP), github.com/WDrijver/ApolloCrossDev Projects/ApolloPiP, commit ad7f0b4"
  - "Example ApolloPointer.c, github.com/WDrijver/ApolloCrossDev Projects/ApolloPointer, commit 639e195"
---

## Summary

ApolloLib loads BMP and DDS files into a 32-byte aligned buffer
(`ApolloLoadPicture`) and shows them on the SAGA chunky plane by picking
the GFXMODE that matches width, height and depth (`ApolloShowPicture`).
It switches PIP 1 and 2 on and off and loads the 32x32 pointer sprite of
Core 12500 and later.

## Details

### struct ApolloPicture

| Field | Set by | Meaning |
|---|---|---|
| `filename[256]`, `format` | Caller | `APOLLO_BMP_FORMAT` (3), `APOLLO_DDS_FORMAT` (2), or raw (0: the whole file) |
| `endian` | Caller | `true`: swap the byte order of each 16-, 24- or 32-bit pixel after loading |
| `buffer`, `position`, `size` | `ApolloLoadPicture` | Allocated buffer; pixels at `buffer + position` (32-byte aligned) |
| `width`, `height`, `depth` | `ApolloLoadPicture` | From the header |
| `palette[256]`, `palettesize` | `ApolloLoadPicture` | For depth ≤ 8 |
| `modulo` | Caller | Bytes skipped after each row (BPLHMOD) |
| `fullscreen`, `target` | Caller | `target`: 0 SAGA screen, 1 PIP 1, 2 PIP 2, 3 pointer sprite |

### Functions

| Function | What it does |
|---|---|
| `ApolloLoadPicture(pic)` | BMP: uncompressed (or BI_BITFIELDS), 1 plane; bottom-up rows are flipped. DDS: the data after the header as it is, without a compression check, so only uncompressed DDS works; depth = pitch / width × 8. Returns an `APOLLO_PICTURE_…` code. |
| `ApolloAllocPicture(pic)` | Allocates an aligned buffer of `width × height × depth / 8` bytes (or `size`) |
| `ApolloFreePicture(pic)` | `FreeVec` of the buffer |
| `ApolloShowPicture(pic)` | Picks the GFXMODE from width × height (see below) and depth 8, 15, 16, 24 or 32, loads the chunky palette for depth ≤ 8, writes GFXMODE (`$DFF1F4`), modulo (`$DFF1E6`) and pointer (`$DFF1EC`) |
| `ApolloShowPiP1(pic)` / `ApolloShowPiP2(pic)` | Writes the PIP's DMA row length (`width × depth / 8`), which switches it on. Set position, pointer, format and modulo first (see [pip.md](../../core/saga-registers/pip.md)). For an 8-bit picture it first loads `pic->palette` into the PIP colour port (from ApolloLib a9a994f). See [the example](../../examples/saga-pip-overlay-and-chroma-key.md). |
| `ApolloHidePiP1()` / `ApolloHidePiP2()` | Writes 0 to the DMA row length: the PIP goes off |
| `uint8_t ApolloLoadPointer(ptr, pic)` | Loads a 32x32 BMP (8-bit with palette, 24-bit or 32-bit ARGB) and converts it into pointer sprite data: colour index + transparency byte per pixel and a 256-entry palette. Frees the BMP again. Returns `APOLLO_PICTURE_OK`, a load error, `W_ERROR`/`H_ERROR` (not 32x32) or `D_ERROR`; sets `ptr->bLoaded`. |
| `ApolloShowPointer(ptr)` | If `ptr->bLoaded`: writes the palette (`$DFF3A8` index, `$DFF3AA` colour) and copies the 2048-byte image to `$DFD000` |
| `ApolloShowFile(filename, &draw, &live, length, offset, gfx_mode, modulo, endianswap)` | Reads a raw frame into `draw`, swaps `draw` and `live`, and shows `live`: double buffering for streamed frames |
| `ApolloShowPattern(buffer, w, h, depth)` | Fills a buffer with a test pattern |

### Screen modes of ApolloShowPicture

| Width | Heights |
|---|---|
| 304 | 224 |
| 320 | 200, 240, 256 |
| 480 | 270 |
| 640 | 200, 360, 400, 480, 512 |
| 720 | 405, 576 |
| 800, 848, 960, 1024 | 600, 480, 540, 768 (height not checked) |
| 1280 | 720, 800, 1024 |
| 1440, 1920 | 900, 1080 (height not checked) |

Another width returns `APOLLO_PICTURE_W_ERROR`, another height of a
checked width `APOLLO_PICTURE_H_ERROR`. Before ApolloLib 639e195 the
320-pixel modes were broken (see
[apollolib-known-bugs.md](../pitfalls/apollolib-known-bugs.md)).

### Pointer

`ApolloLoadPointer` accepts a 32x32 BMP (from ApolloLib b9891d9; before,
it returned nothing, ignored 24-bit BMPs and kept the BMP allocated):

- 8-bit: the BMP palette becomes the sprite palette; every pixel is
  opaque. Colour index 0 is transparent (see
  [pointer.md](../../core/saga-registers/pointer.md)).
- 24-bit: every pixel opaque; colours are gathered into a palette.
- 32-bit ARGB: alpha 0 becomes index 0 (transparent), alpha `$FF` opaque,
  any other alpha semi-transparent (50 %). Colours are gathered into a
  palette of up to 255 entries; further colours use entry 255.

It loads the BMP with `endian` off and reads the bytes in BMP order, so the
caller doesn't set `endian`.

`ApolloMouse` (see [input.md](input.md)) moves the pointer. A complete,
checked use of both functions is in
[the pointer example](../../examples/saga-pointer-sprite.md).

### Example

```c
struct ApolloPicture pic = {0};
strcpy(pic.filename, "title.dds");
pic.format = APOLLO_DDS_FORMAT;                /* 1280x720, 16-bit */
if (ApolloLoadPicture(&pic) == APOLLO_PICTURE_OK) {
    pic.modulo = 0;
    ApolloShowPicture(&pic);
    /* ... */
    ApolloFreePicture(&pic);                  /* after switching the mode back */
}
```

## Differences from AmigaOS / AROS / 68060

- No graphics.library or cybergraphics: `ApolloShowPicture` writes
  GFXMODE and the chunky pointer directly, behind Intuition's back. Save
  the old mode and pointer at `$DFE1F4`/`$DFE1EC` and restore them on exit.
- BMP pixels are little-endian. Use `endian` or the swap routines when the
  SAGA format needs big-endian pixels.

## Do / Don't

- DO set the PIP registers before `ApolloShowPiP1/2`: they only write the
  DMA row length.
- DO load an 8-bit PIP's palette yourself (`$DFF38C` for PIP 1, `$DFF37C`
  for PIP 2) with an ApolloLib older than a9a994f.
- DO restore GFXMODE and the chunky pointer before the program exits.
- DON'T free a picture that is still shown.
- DON'T use `ApolloShowPicture` for 320-pixel-wide or 8-bit pictures with
  an ApolloLib older than 639e195.
