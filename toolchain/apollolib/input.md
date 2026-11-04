---
title: ApolloLib input functions (mouse, USB joypad, keyboard)
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain, general]
applies_to:
  core: "any"
  os: [any]
  mode: [os-takeover]
tags: [apollolib, input, mouse, joypad, keyboard, pointer]
related:
  - toolchain/apollolib/index.md
  - core/saga-registers/input.md
  - core/saga-registers/pointer.md
  - toolchain/pitfalls/apollolib-known-bugs.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_LibC.c, _LibASM.s, _Defines.h), commit 639e195 (2026-11-04)"
---

## Summary

ApolloLib polls the mouse, the first USB joypad and the keyboard directly
from the hardware, and moves the SAGA pointer with the mouse. Call the
functions once per frame. They bypass input.device, so they belong in
OS-takeover code.

## Details

### Mouse: ApolloMouse(ApolloMouseState *m)

| Source | Register |
|---|---|
| X, Y counters | `$DFF00B`, `$DFF00A` (JOY0DAT) |
| Left button | CIA-A `$BFE001` bit 6 (0 = pressed) |
| Right button | POTINP `$DFF016` bit 10 (0 = pressed) |
| Middle button | POTINP `$DFF016` bit 8 (0 = pressed) |

Each call:

1. computes the X/Y delta since the last call (with wrap-around of the
   8-bit counters);
2. moves `MouseX_Pointer`/`MouseY_Pointer`, clamped to 1 …
   `MouseX_Pointer_Max`/`MouseY_Pointer_Max` (set these first);
3. writes the pointer position + 16 (X) and + 8 (Y) to `$DFF1D0`/`$DFF1D2`;
4. sets `Button_State` from the `APOLLOMOUSE_…` flags.

| Flag | Value | Set when |
|---|---|---|
| `APOLLOMOUSE_LEFTCLICK` / `RIGHTCLICK` / `MIDDLECLICK` | `$0001` / `$0002` / `$0004` | Button released |
| `APOLLOMOUSE_LEFTDOUBLECLICK` / `RIGHTDOUBLECLICK` / `MIDDLEDOUBLECLICK` | `$0008` / `$0010` / `$0020` | Released again within 15 calls (`APOLLOMOUSE_DOUBLECLICKCOUNTER`) |
| `APOLLOMOUSE_LEFTDOWN` / `RIGHTDOWN` / `MIDDLEDOWN` | `$0040` / `$0080` / `$0100` | Button held |

`ApolloGetMouseDelta(UWORD *old)` (assembly) is a smaller variant: it
returns the X and Y delta since the value in `*old`, and updates `*old`.

### USB joypad: ApolloJoypad(ApolloJoypadState *j)

Reads joypad 0 (`$DFF220`) into `Joypad_Value` and decodes it:

| Field | Bits |
|---|---|
| `Joypad_LeftX_Delta` | 15 → +1 (right), 14 → −1 (left) |
| `Joypad_LeftY_Delta` | 13 → +1 (down), 12 → −1 (up) |
| `Joypad_RightX_Delta` | 2 → +1, 3 → −1 |
| `Joypad_RightY_Delta` | 1 → +1, 4 → −1 |
| `Joypad_Start`, `Joypad_Back` | 10, 9 |
| `Joypad_TR`, `TL`, `BR`, `BL` | 8, 7, 6, 5 |
| `Joypad_Y`, `X`, `B`, `A` | 4, 3, 2, 1 |
| `Joypad_Connect` | 0 |

The right stick shares bits 1–4 with A, B, X and Y. Joypads 1–3
(`$DFF222`–`$DFF226`) need your own read.

### Keyboard: ApolloKeyboard(ApolloKeyBoardState *k)

Reads the raw key code from CIA-A `$BFEC01` (`not` and `ror #1`). A new
key below 127 goes to `Current_Key` (and `Previous_Key`); otherwise
`Current_Key` is 127. `ApolloKeyboardToUnicode(code)` maps a raw Amiga key
code to a character.

## Differences from AmigaOS / AROS / 68060

- input.device, Intuition and lowlevel.library are not used. Under a
  running OS, Intuition also moves the pointer and reads the keyboard: the
  two fight.
- The keyboard read doesn't handshake with the keyboard controller, as the
  OS keyboard interrupt does.

## Do / Don't

- DO set `MouseX_Pointer_Max` and `MouseY_Pointer_Max` before the first
  `ApolloMouse` call.
- DO call these functions once per frame, for example after `ApolloWaitVBL`.
- DON'T use them while Intuition owns the input.
- DON'T rely on the middle-button flags with an ApolloLib older than
  639e195: there they followed the wheel counter.
