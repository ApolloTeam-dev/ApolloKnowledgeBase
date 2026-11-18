---
title: WBConfig() in workbench.library 45 (backdrop and icon font of the AmigaOS 3.9 Workbench)
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, other]
components: [libraries]
applies_to:
  core: "any"
  os: [amigaos-3.9, apolloos-r10]
  mode: [os-friendly]
tags: [workbench, wbconfig, iprefs, wbpattern, backdrop, wallpaper, icon-font, font-prefs, prefs]
sources:
  - "Disassembly of AmigaOS 3.5 C:IPrefs 44.23 (30.11.1999) and AmigaOS 3.9 workbench.library 45.102, 2026-11-18"
  - "ApolloOS-Port commits 2e09af9, cfe53b4 and 2a68741 (2026-11-18): workbench/c/iprefs/wbpatternprefs.c, fontprefs.c, workbench/prefs/wbpattern/"
  - "File format measured with R9.6's Prefs/WBPattern on an Apollo V4, ApolloOS R10 dev card, 2026-11-18 (one option per save, file compared)"
  - "Hardware test on an Apollo V4, ApolloOS R10 dev card, 2026-11-18: wallpaper and XEN 9 icon labels at boot with only R10's IPrefs"
---

## Summary

The AmigaOS 3.5/3.9 Workbench does not read `WBPattern.prefs` or the icon
font from `font.prefs` itself. IPrefs loads them and hands them over through
the private, undocumented `WBConfig()` call of workbench.library. ApolloOS
R10 runs the AmigaOS 3.9 workbench.library (45.102), so its own IPrefs uses
the same call; this file documents it, and the `WBPattern.prefs` format of
the 3.5+ WBPattern editor.

## Details

### The call

| LVO | Name | Registers |
|---|---|---|
| -84 | `WBConfig(code, data)` | `code` in D0, `data` (a pointer) in D1, library base in A6 |

- **Result (D0):** the pointer that was set before for this `code` (or
  NULL). The caller owns it from then on and frees it (see the structs).
- **`data = NULL`** removes the setting: no backdrop, default font.
- The Workbench keeps using `data` until the next `WBConfig()` with the same
  code returns it; do not free or change it before that.
- It may be called before `LoadWB` (IPrefs runs first in the
  Startup-Sequence; the settings are stored) and while the Workbench runs
  (it is passed to the Workbench task, which redraws).
- The AROS headers declare it as `BOOL WBConfig(ULONG unk1, ULONG unk2)`
  (D0, D1). The return value is a pointer, not a BOOL: call it through
  `AROS_LC2(IPTR, WBConfig, ..., 14, Workbench)` or an equivalent that keeps
  all 32 bits.

| code | Sets | `data` |
|---|---|---|
| 1 | Workbench (root window) backdrop | backdrop struct |
| 2 | Drawer window backdrop | backdrop struct |
| 3 | Icon font (`font.prefs`, type 0, `FP_WBFONT`) | font struct |
| 4 | Workbench text font (`font.prefs`, type 1, `FP_SYSFONT`) | font struct |

The screen backdrop (`WBP_SCREEN`) is not set through `WBConfig()`: IPrefs
draws it itself as a backfill hook on the Workbench screen's LayerInfo.
IPrefs 44.23 also calls code 5 with NULL; its meaning is not known.

### Backdrop struct (codes 1, 2)

| Offset | Size | Contents |
|---|---|---|
| +0 | 4 | `struct BitMap *`: the picture, remapped to the Workbench screen |
| +4 | 2 | width in pixels (`bmh_Width`) |
| +6 | 2 | height in pixels (`bmh_Height`) |
| +8 | 5 | 0 |
| +13 | 1 | flags: bit 0 = centre (else tile), bit 1 = fill the border |
| +14 | 1 | pen for the border (bit 1): the remapped pen of `bmh_Transparent` |
| +15 | 1 | 0 |
| +16 | 4 | the picture.datatype `Object *` that owns the bitmap |

IPrefs 44.23 loads the picture with `NewDTObject(name, DTA_GroupID,
GID_PICTURE, PDTA_Remap, TRUE, PDTA_Screen, <Workbench screen>,
PDTA_FreeSourceBitMap, TRUE, OBP_Precision, ..., TAG_DONE)`, then
`DoMethod(o, DTM_PROCLAYOUT, NULL, 1)`, then reads `PDTA_BitMapHeader` and
`PDTA_BitMap`. To free a returned struct: `DisposeDTObject()` on +16 (this
frees the bitmap), then the struct (`AllocVec`/`FreeVec` in 44.23).

### Font struct (codes 3, 4)

| Offset | Size | Contents |
|---|---|---|
| +0 | 4 | `struct TextAttr *`, pointing to +12 |
| +4 | 4 | `struct TextFont *` from `OpenDiskFont()` |
| +8 | 2 | draw mode (`fp_DrawMode`; 0 = JAM1, labels without background) |
| +10 | 1 | front pen (`fp_FrontPen`): colour of the icon label text |
| +11 | 1 | back pen (`fp_BackPen`) |
| +12 | 8 | `struct TextAttr`, `ta_Name` pointing to +20 |
| +20 | n | font name, NUL-terminated (`AllocVec(strlen(name) + 21, MEMF_PUBLIC | MEMF_CLEAR)`) |

To free a returned struct: `CloseFont()` on +4, then the struct.

### WBPattern.prefs (AmigaOS 3.5+ editor format)

`ENV:Sys/WBPattern.prefs`, `FORM PREF` with these chunks in this order:

| Chunk | Size | Contents |
|---|---|---|
| `PRHD` | 6 | prefs header, all 0 |
| `FIP0` | 4 | one option byte per placement (Workbench, Windows, Screen), then one global byte |
| `WPOS` | 4 | `$0000000B` as the editor writes it; meaning unknown, keep it as read |
| `PTRN` | 24 + n | one per placement: `struct WBPatternPrefs` (`prefs/wbpattern.h`), then n data bytes |

`FIP0` option byte of a placement:

| Bits | Meaning |
|---|---|
| `$0F` | precision: 0 Image, 1 Icon, 2 GUI, 3 Exact, 4 True-color, 5 None |
| `$10` | "Standard" (set in all four bytes by the editor's Standard gadget) |
| `$20` | centre the picture |
| `$40` | tile the picture |
| `$80` | fill the border (only together with `$20`) |

The global (4th) byte: `$02` = "Lock pens 4-7".

`PTRN`: `wbp_Which` = 0 Workbench, 1 Windows, 2 Screen. A picture has
`wbp_Flags` bit `WBPF_PATTERN` clear and the file name (with its NUL) as data.
A pattern has `WBPF_PATTERN` set and the planar 16x16 pattern as data; the
editor writes an all-zero 96-byte pattern for "no backdrop". The centre /
tile / fill options are **not** in `wbp_Flags`; they are in `FIP0`.

## Differences from AmigaOS / AROS / 68060

- **AROS:** `WBConfig()` is a stub in AROS's workbench.library, and AROS's
  IPrefs never called it. It set the root backdrop as a screen backfill and
  ignored `FP_WBFONT`. With the AmigaOS 3.9 Workbench that gives no wallpaper
  and no icon font, without an error.
- **picture.datatype:** `PDTA_BitMap` must return the remapped bitmap
  after `DTM_PROCLAYOUT`, as AmigaOS's picture.datatype does. If it returns
  the source bitmap, the Workbench shows no backdrop (fixed in ApolloOS R10,
  ApolloOS-Port commit 9617ad6).
- **The prefs file** of the 3.5+ editor keeps its options in `FIP0`; reading
  `wbp_Flags` for them (as older code does) finds 0.

## Do / Don't

- DO run `AddDataTypes` before IPrefs in the Startup-Sequence: IPrefs loads
  the PNG backdrop at once, and without the descriptors the load fails.
- DO free only what `WBConfig()` returns, never the struct you just passed.
- DO open workbench.library yourself for the call; `WBConfig()` is safe to
  call before `LoadWB`.
- DON'T call `WBConfig()` with a struct on the stack or in memory you free
  while the Workbench may still use it.
- DON'T expect `WBConfig()` from AROS's workbench.library; it does nothing
  there.
