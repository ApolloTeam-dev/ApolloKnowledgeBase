---
title: SAGA PIP in overlay and chroma-key mode (from the SAGAPiP example)
type: example
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [saga-video-isabelle, toolchain]
applies_to:
  core: "Core 12000+"
  os: [any]
tags: [saga, isabelle, pip, overlay, chroma-key, apollolib, example]
related:
  - core/saga-registers/pip.md
  - core/saga-registers/colour-ports.md
  - toolchain/apollolib/picture.md
  - core/best-practices/prefer-library-calls-for-saga-chips.md
sources:
  - "Example SAGAPiP.c, github.com/WDrijver/ApolloCrossDev Projects/SAGAPiP, commit 5ad4035 (2026-11-04)"
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib, commit 639e195 (2026-11-04)"
---

## Purpose

Show a picture-in-picture (PIP) window on top of the screen (overlay mode)
and behind it (chroma-key mode), with ApolloLib. The code below is the PIP
part of ApolloCrossDev's SAGAPiP example, in three functions:

- `ShowPiP1Overlay`: an 8-bit PIP in front of the screen; palette index
  `$FF` is transparent.
- `ShowPiP1Behind`: a 16-bit PIP behind the screen, visible where the
  screen is purple (the chroma key).
- `HidePiP1`: PIP 1 off.

The full SAGAPiP program does more: it plays a soundtrack, shows a
1280x720 background, opens a Workbench window, lays PIP 1 and PIP 2 over
it and follows the window when it moves (see "The full example" below).

## Build

The functions compile as a library unit. In a project that uses ApolloLib
(see [toolchain/apollolib/index.md](../toolchain/apollolib/index.md)):

```sh
m68k-amigaos-gcc -noixemul -O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer -Wall \
  -I$APOLLOLIB -c pip.c -o pip.o
```

The full example builds in ApolloCrossDev with `make` in
`Projects/SAGAPiP` (which also uploads it to the Apollo V4), or
`make cleanbefore build` to only build.

## Code

```c
// kb:compile
/* SAGA PIP with ApolloLib: overlay and chroma-key mode, after the SAGAPiP
   example in ApolloCrossDev Projects/SAGAPiP. Needs ApolloLib 639e195+. */
#include "ApolloCrossDev_Lib.h"

#define PIP1_REG(a) (*(volatile UWORD *)(a))

/* Load the palette of an 8-bit picture into PIP 1's colour port. */
static void LoadPiP1Palette(const struct ApolloPicture *pic)
{
    for (ULONG i = 0; i < pic->palettesize; i++)
        *(volatile ULONG *)APOLLO_SAGA_PIP1CHK_COL = (i << 24) | (pic->palette[i] & 0xFFFFFF);
}

/* Overlay mode: PIP 1 lies in front of the screen at (left, top). With the
   transparency bit, palette index $FF is transparent. */
void ShowPiP1Overlay(struct ApolloPicture *pic, WORD left, WORD top)
{
    LoadPiP1Palette(pic);
    *(volatile ULONG *)APOLLO_SAGA_PIP1_POINTER = (ULONG)(pic->buffer + pic->position);
    PIP1_REG(APOLLO_SAGA_PIP1_X_START) = left + 16;             /* +16 and -1: as in SAGAPiP */
    PIP1_REG(APOLLO_SAGA_PIP1_X_STOP)  = left + pic->width + 16;
    PIP1_REG(APOLLO_SAGA_PIP1_Y_START) = top - 1;
    PIP1_REG(APOLLO_SAGA_PIP1_Y_STOP)  = top + pic->height - 1;
    PIP1_REG(APOLLO_SAGA_PIP1_GFXMODE) = APOLLO_SAGA_PIP_TRANSON | APOLLO_SAGA_8_INDEX;
    PIP1_REG(APOLLO_SAGA_PIP1_MODULO)  = 0;
    PIP1_REG(APOLLO_SAGA_PIP1_CLRKEY)  = 0x0000;                /* 0 = overlay mode */
    ApolloShowPiP1(pic);                                        /* DMA row length last: PIP on */
}

/* Chroma-key mode: PIP 1 lies behind the screen and shows only where the
   screen has the key colour, here purple ($F0F in RGB444). */
void ShowPiP1Behind(struct ApolloPicture *pic16, WORD width, WORD height)
{
    *(volatile ULONG *)APOLLO_SAGA_PIP1_POINTER = (ULONG)(pic16->buffer + pic16->position);
    PIP1_REG(APOLLO_SAGA_PIP1_X_START) = 16;
    PIP1_REG(APOLLO_SAGA_PIP1_X_STOP)  = width + 16;
    PIP1_REG(APOLLO_SAGA_PIP1_Y_START) = 0;
    PIP1_REG(APOLLO_SAGA_PIP1_Y_STOP)  = height;
    PIP1_REG(APOLLO_SAGA_PIP1_GFXMODE) = APOLLO_SAGA_16_R5G6B5;
    PIP1_REG(APOLLO_SAGA_PIP1_MODULO)  = 0;
    PIP1_REG(APOLLO_SAGA_PIP1_CLRKEY)  = 0x8F0F;                /* bit 15 = on, R=$F G=$0 B=$F */
    ApolloShowPiP1(pic16);
}

/* Switch PIP 1 off: DMA row length 0. */
void HidePiP1(void)
{
    ApolloHidePiP1();
}
```

Load the pictures with `ApolloLoadPicture` first: an 8-bit BMP for the
overlay, a 16-bit DDS (R5G6B5) for the background.

## Expected result

- **Overlay:** after `ShowPiP1Overlay(&pic, left, top)` the 8-bit picture
  appears over the screen, its top-left corner at (`left`, `top`) in
  screen pixels. Pixels with palette index `$FF` show the screen behind.
- **Chroma key:** after `ShowPiP1Behind(&bg, 1280, 720)` the screen looks
  unchanged, except where it is purple (`$F0F`): there the PIP shows
  through. SAGAPiP fills a Workbench window with purple to look through it.
- **Off:** after `HidePiP1()` the PIP is gone.

## The full example

`Projects/SAGAPiP/SAGAPiP.c` (ApolloCrossDev commit 5ad4035) shows more than
the code above, but has these problems. Keep them out of your own code:

| Problem | Effect | Do instead |
|---|---|---|
| It never loads the PIP palettes | The 8-bit overlays show whatever palette was in the PIP colour ports. ApolloLib's older version did this in `ApolloLoadPicture`; the current one only loads the chunky palette, in `ApolloShowPicture`. | Write the palette to `$DFF38C` (PIP 1) or `$DFF37C` (PIP 2), as `LoadPiP1Palette` does |
| `if (!&pipwindow)` | Tests the address of the variable, which is never NULL: a failed `OpenWindowTags` goes unnoticed | `if (!pipwindow)` |
| `AllocBitMap(..., BMF_DISPLAYABLE \| BMB_CLEAR \| BMB_HIJACKED \| ...)` | `BMB_…` are bit numbers (0, 7, 2, 9), not flags: ORed with `BMF_DISPLAYABLE` (2) they give `$F` = CLEAR, DISPLAYABLE, INTERLEAVED and STANDARD, not the HIJACKED and RTGCHECK the code names | Use only `BMF_…` flags |
| Restores the Workbench as GFXMODE `$0A04` | Works only on a 1280x720, 24-bit Workbench | Save GFXMODE and the pointer from `$DFE1F4`/`$DFE1EC` first, restore those |
| `struct ApolloSound soundtrack;` not cleared | `fadeout` is read uninitialized at exit | `struct ApolloSound soundtrack = {0};` |
| `goto exit4` from early errors | Frees picture buffers that were never loaded | Clear the structures first, or free only what was loaded |
| cybergraphics.library and the "Workbench" screen lock are never released | Resource leak | `CloseLibrary`, `UnlockPubScreen` |
| `ApolloCPUDelay(2000)` in a Workbench program | Busy-waits two seconds | `Delay()` from dos.library |

The +16 (X) and −1 (Y) corrections place the PIP exactly over a Workbench
window in SAGAPiP; they are not documented elsewhere.
