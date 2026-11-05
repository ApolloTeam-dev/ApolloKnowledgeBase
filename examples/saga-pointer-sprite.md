---
title: SAGA hardware pointer from a 32x32 BMP (from the ApolloPointer example)
type: example
owner: WDrijver
status: reviewed
origin: ai-assisted
basis: [source-code]
components: [saga-video-isabelle, toolchain]
applies_to:
  core: "Core 12500+"
  os: [any]
tags: [saga, isabelle, pointer, sprite, bmp, apollolib, example]
related:
  - core/saga-registers/pointer.md
  - toolchain/apollolib/picture.md
  - toolchain/apollolib/input.md
  - core/best-practices/prefer-library-calls-for-saga-chips.md
sources:
  - "Example ApolloPointer.c, github.com/WDrijver/ApolloCrossDev Projects/ApolloPointer, commit ad7f0b4 (2026-11-04)"
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloLoadPointer, ApolloShowPointer), commit ad7f0b4 (2026-11-04)"
---

## Purpose

Replace the SAGA hardware pointer (the 32x32 sprite of Core 12500 and
later) with an image from a BMP file, and move it, with ApolloLib.
ApolloCrossDev's ApolloPointer example does the first part as a command:
`ApolloPointer sprite.bmp`.

## Build

The functions compile as a library unit. In a project that uses ApolloLib
(see [toolchain/apollolib/index.md](../toolchain/apollolib/index.md)):

```sh
m68k-amigaos-gcc -noixemul -O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer -Wall \
  -I$APOLLOLIB -c pointer.c -o pointer.o
```

The full example builds in ApolloCrossDev with `make` in
`Projects/ApolloPointer` (which also uploads it to the Apollo V4), or
`make cleanbefore build` to only build. Its folder has seven 32x32 8-bit
pointer images (`ApolloPointer_*_32x32x8.bmp`).

## Code

```c
// kb:compile
/* Replace the SAGA hardware pointer with a 32x32 BMP, after the ApolloPointer
   example in ApolloCrossDev Projects/ApolloPointer. Core 12500+ (32x32
   sprite), ApolloLib b9891d9+ (ApolloLoadPointer returns a result code). */
#include "ApolloCrossDev_Lib.h"

static struct ApolloPointer pointer;        /* over 5 KB: keep it off the stack */

/* Load a 32x32 BMP (8-bit with palette, 24-bit, or 32-bit ARGB) and show it
   as the pointer. Returns APOLLO_PICTURE_OK or the error code. */
uint8_t SetPointerFromBMP(const char *filename)
{
    struct ApolloPicture bmp = {0};
    uint8_t result;

    strncpy(bmp.filename, filename, sizeof(bmp.filename) - 1);
    bmp.format = APOLLO_BMP_FORMAT;
    bmp.target = APOLLO_PIC_TARGET_SPRITE;

    result = ApolloLoadPointer(&pointer, &bmp); /* loads, converts and frees the BMP */
    if (result == APOLLO_PICTURE_OK)
        ApolloShowPointer(&pointer);            /* palette to $DFF3A8/$DFF3AA, image to $DFD000 */
    return result;
}

/* Move the pointer to screen position (x, y), with the offsets ApolloMouse uses. */
void MovePointer(WORD x, WORD y)
{
    *(volatile UWORD *)APOLLO_POINTER_SET_X = x + 16;
    *(volatile UWORD *)APOLLO_POINTER_SET_Y = y + 8;
}
```

## Expected result

- `SetPointerFromBMP("ApolloPointer_Gold_32x32x8.bmp")` returns
  `APOLLO_PICTURE_OK`, and the pointer on screen changes to the image at
  once, at its current position.
- Pixels with colour index 0 are transparent. In an 8-bit or 24-bit BMP
  every other pixel is opaque. In a 32-bit ARGB BMP, alpha 0 is
  transparent, alpha `$FF` opaque, and any other alpha 50 %
  semi-transparent (see [pointer.md](../core/saga-registers/pointer.md)).
- A BMP that isn't 32x32 returns `APOLLO_PICTURE_W_ERROR` or `H_ERROR`,
  another depth `D_ERROR`, a missing file the load error; the pointer
  stays as it was.
- `MovePointer(x, y)` places it; `ApolloMouse` (see
  [input.md](../toolchain/apollolib/input.md)) does the same from the
  mouse every frame.

## The full example

`Projects/ApolloPointer/ApolloPointer.c` (ApolloCrossDev commit ad7f0b4)
calls `ApolloLoadPointer` and `ApolloShowPointer` on the file named on the
command line, prints an error and returns 10 if the file can't be used,
and exits; the new pointer stays.

ApolloCrossDev pull request #21 (2026-11-04) fixed `ApolloLoadPointer`.
With an older ApolloLib, keep these in mind:

| Before b9891d9 | Effect |
|---|---|
| `ApolloLoadPointer` returned `void` and never set `bLoaded` | A caller couldn't see whether loading worked; `ApolloShowPointer` showed whatever was in the struct |
| 24-bit BMPs were accepted but not converted | An empty (transparent) pointer |
| The loaded BMP was not freed | About 1–4 KB stayed allocated |
| 32-bit alpha read correctly only with `endian = true` | Wrong transparency otherwise |
| The example's text said colour 1 was semi-transparent | Not true: only the transparency byte decides (WDrijver, 2026-11-04) |

`hotspotX`/`hotspotY` in `struct ApolloPointer` are still not used by
ApolloLib.
