---
title: SAGA hardware pointer from a 32x32 BMP (from the ApolloPointer example)
type: example
owner: WDrijver
status: draft
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
  - "Example ApolloPointer.c, github.com/WDrijver/ApolloCrossDev Projects/ApolloPointer, commit 9e35355 (2026-11-04)"
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloLoadPointer, ApolloShowPointer), commit a9a994f (2026-11-04)"
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
   sprite), ApolloLib a9a994f+. */
#include "ApolloCrossDev_Lib.h"

static struct ApolloPointer pointer;        /* over 5 KB: keep it off the stack */

/* Load a 32x32 BMP (8-bit with palette, or 32-bit ARGB) and show it as the
   pointer. Returns false if the file is not a usable pointer image. */
bool SetPointerFromBMP(const char *filename)
{
    struct ApolloPicture bmp = {0};
    bool usable;

    strncpy(bmp.filename, filename, sizeof(bmp.filename) - 1);
    bmp.format = APOLLO_BMP_FORMAT;
    bmp.endian = true;                      /* 32-bit: ARGB byte order for ApolloLoadPointer */
    bmp.target = APOLLO_PIC_TARGET_SPRITE;

    ApolloLoadPointer(&pointer, &bmp);      /* loads the BMP, converts it into pointer */

    /* ApolloLoadPointer returns nothing: check the picture it loaded */
    usable = bmp.buffer && bmp.width == 32 && bmp.height == 32 &&
             (bmp.depth == 8 || bmp.depth == 32);
    ApolloFreePicture(&bmp);                /* pointer has its own copy */
    if (!usable)
        return false;

    ApolloShowPointer(&pointer);            /* palette to $DFF3A8/$DFF3AA, image to $DFD000 */
    return true;
}

/* Move the pointer to screen position (x, y), with the offsets ApolloMouse uses. */
void MovePointer(WORD x, WORD y)
{
    *(volatile UWORD *)APOLLO_POINTER_SET_X = x + 16;
    *(volatile UWORD *)APOLLO_POINTER_SET_Y = y + 8;
}
```

## Expected result

- `SetPointerFromBMP("ApolloPointer_Gold_32x32x8.bmp")` returns true, and
  the pointer on screen changes to the image at once, at its current
  position.
- Pixels with colour index 0 are transparent. In an 8-bit BMP every other
  pixel is opaque. In a 32-bit ARGB BMP, alpha 0 is transparent, alpha
  `$FF` opaque, and any other alpha 50 % semi-transparent (see
  [pointer.md](../core/saga-registers/pointer.md)).
- A BMP that isn't 32x32, or has another depth, returns false and leaves
  the pointer unchanged.
- `MovePointer(x, y)` places it; `ApolloMouse` (see
  [input.md](../toolchain/apollolib/input.md)) does the same from the
  mouse every frame.

## The full example and ApolloLib's pointer functions

`Projects/ApolloPointer/ApolloPointer.c` (ApolloCrossDev commit 9e35355)
calls `ApolloLoadPointer` and `ApolloShowPointer` on the file named on the
command line, and exits; the new pointer stays. These points are why the
code above looks the way it does:

| Point | Effect | In the code above |
|---|---|---|
| `ApolloLoadPointer` returns `void` and never sets `pointer.bLoaded` | A caller can't see whether loading worked; `ApolloShowPointer` shows whatever is in `pointer` | Checks the loaded picture's size and depth |
| `ApolloLoadPointer` accepts 24-bit BMPs, but has no 24-bit conversion | The pointer becomes empty (all index 0, transparent) | Accepts only 8 and 32 bits |
| `ApolloLoadPointer` loads the BMP through `ApolloLoadPicture` and doesn't free it; nor does the example | About 1–4 KB stays allocated | `ApolloFreePicture` |
| The 32-bit path reads `pixel >> 24` as alpha | Right only when the picture is loaded with `endian = true` | Sets `endian` |
| `hotspotX`/`hotspotY` in `struct ApolloPointer` | Not used by ApolloLib | – |
| `struct ApolloPointer` holds 4096 bytes of image data for a 2048-byte sprite | Harmless; `ApolloShowPointer` copies 2048 bytes | Static, off the stack |

The example's usage text says "Color #0 is transparent and Color #1 is
semi-transparent". For an 8-bit BMP, `ApolloLoadPointer` marks every
pixel opaque; whether colour index 1 is semi-transparent in the hardware
is not documented in the knowledge base.
