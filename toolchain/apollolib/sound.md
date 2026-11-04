---
title: ApolloLib sound functions (Arne)
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain, saga-audio-arne]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, arne, audio, wav, aiff, sound]
related:
  - toolchain/apollolib/index.md
  - core/saga-registers/arne-channels.md
  - core/saga-registers/arne-dma-and-interrupts.md
  - toolchain/pitfalls/apollolib-known-bugs.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_LibC.c, _Lib.h), commit ce1fcbf (2026-11-04)"
---

## Summary

ApolloLib loads WAV and AIFF files into a 32-byte aligned buffer and plays
them on an Arne channel: `ApolloLoadSound`, then `ApolloPlaySound`. A
second, older API (`ApolloPlay`, `ApolloPlayFile`) takes a channel number
and a buffer instead of a `struct ApolloSound`. Both always play 16-bit
stereo.

## Details

### struct ApolloSound

| Field | Set by | Meaning |
|---|---|---|
| `filename[256]`, `format` | Caller | File and format: `APOLLO_WAV_FORMAT` (4), `APOLLO_AIFF_FORMAT` (1), or raw (`APOLLO_RAW_FORMAT`, 0: the whole file) |
| `buffer`, `position` | `ApolloLoadSound` | Allocated buffer; the data starts at `buffer + position` (32-byte aligned) |
| `size` | `ApolloLoadSound` | Data size in bytes |
| `period` | `ApolloLoadSound` | `3546895 / sample rate` (PAL clock) |
| `stereo`, `datarate`, `bitspersample` | `ApolloLoadSound` (WAV) | Read from the header, but not used for playback |
| `channel` | Caller or `ApolloPlaySound` | Arne channel 0–15 |
| `staticchannel` | Caller | `true`: play on `channel`; `false`: `ApolloPlaySound` picks the first free channel from 1 to 15 |
| `loop`, `fadein`, `volume_left`, `volume_right` | Caller | Playback; volume `$00`–`$FF` per side |
| `fadeout`, `pan` | Caller | Not used by the library |

### Functions

| Function | What it does |
|---|---|
| `ApolloLoadSound(sound)` | Parses the WAV or AIFF header, allocates `buffer` (`AllocVec`, `MEMF_ANY`), reads the data. WAV: PCM only. Returns an `APOLLO_SOUND_…` code. |
| `ApolloAllocSound(sound)` | Allocates an aligned buffer of `sound->size` bytes for data you fill yourself |
| `ApolloFreeSound(sound)` | `FreeVec` of the buffer |
| `ApolloPlaySound(sound)` | Picks a channel if `staticchannel` is false, sets pointer, length (`size / 8`), volume 0, CTRL and period, starts DMA (DMACON for 0–3, DMACON2 for 4–15), then sets the volume or fades in |
| `ApolloStopSound(sound)` / `ApolloStartSound(sound)` | Clears or sets the channel's DMA bit |
| `ApolloVolumeSound(sound)` | Writes `volume_left << 8 \| volume_right` to AUDxVOL |
| `ApolloFadeInSound(sound)` / `ApolloFadeOutSound(sound)` | Steps the volume by 1 per VBlank (`ApolloWaitVBL`) to or from the average of left and right; fade-out then stops the channel. Both block the caller. |

`ApolloPlaySound` writes CTRL `$0005` (16-bit, stereo, looping) when
`loop` is set and `$0007` (16-bit, stereo, one-shot) when not, whatever the
file contains.

### Channel API (older, from the RHLOS project)

| Function | What it does |
|---|---|
| `ApolloPlay(channel, vol_l, vol_r, loop, buffer, length, offset)` | Plays `buffer + offset`, length `(length - offset) / 8 - 32` pairs, at period 80 (44.1 kHz). Returns `false` if the channel is busy. |
| `ApolloPlayFile(filename, buffer, offset, channel, vol_l, vol_r, loop)` | Reads the file into `buffer` and plays it on `channel`, stopping the channel first if it runs |
| `ApolloCacheFile(filename, &cache, &length, offset)` | Reads a file into `cache` for `ApolloPlay` |
| `ApolloVolume(channel, vol_l, vol_r)` | Sets the volume |
| `ApolloStartChannel(channel)` / `ApolloStopChannel(channel)` | Starts or stops a channel's DMA |
| `ApolloFadeOut(channel, from, to)` | Steps the volume down per VBlank, then stops the channel |

### Example

```c
struct ApolloSound music = {0};
strcpy(music.filename, "music.wav");
music.format = APOLLO_WAV_FORMAT;              /* 16-bit stereo PCM */
if (ApolloLoadSound(&music) == APOLLO_SOUND_OK) {
    music.volume_left = music.volume_right = 0x80;
    music.loop = true;
    if (ApolloPlaySound(&music) == APOLLO_SOUND_OK) {
        /* ... */
        ApolloStopSound(&music);
    }
    ApolloFreeSound(&music);
}
```

## Differences from AmigaOS / AROS / 68060

- No audio.device or AHI: the functions write the Arne registers at
  `$DFF400 + n × $10` and DMACON/DMACON2 directly. Don't use them on a
  channel that audio.device or AHI also uses.
- Arne plays from any RAM, so `MEMF_ANY` buffers work; Paula needs Chip RAM.

## Do / Don't

- DO give `ApolloPlaySound` 16-bit stereo data: it always programs 16-bit
  stereo.
- DO set `staticchannel` and `channel` if you need channel 0: the
  automatic search starts at 1.
- DO call `ApolloFreeSound` when you are done.
- DON'T expect `stereo`, `bitspersample`, `fadeout` or `pan` to change
  playback.
- DON'T use the channel API and audio.device on the same channel.
