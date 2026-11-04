---
title: ApolloLib serial debug output
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [apollolib, debug, serial, rawdofmt, logging]
related:
  - toolchain/apollolib/index.md
  - toolchain/project-makefile.md
sources:
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib (ApolloCrossDev_Debug.h, _Debug.c, _Defines.h), commit 639e195 (2026-11-04)"
---

## Summary

ApolloLib writes debug text straight to the serial port at 115200 baud,
without OS calls, so it also works without a console and with the OS
taken over. Two macro sets use it: `AD()`/`ADX()` around `sprintf`, and
the levelled `Debug_Info()` … `Debug_Flag()` macros.

## Details

### Functions (ApolloCrossDev_Debug.c)

| Function | What it does |
|---|---|
| `ApolloDebugInit()` | Sets DTR and RTS on CIA-B and SERPER to 115200 baud (PAL clock) |
| `ApolloDebugPutChar(c)` | Waits for TBE, writes one character to SERDAT; `\n` becomes `\r\n` |
| `ApolloDebugMayGetChar()` | Returns a received character, or −1 |
| `ApolloDebugPutStr(s)` | Writes a string |
| `ApolloDebugPutDec(label, v)`, `ApolloDebugPutHex(label, v)`, `ApolloDebugPutHexVal(v)` | Write `label: value` in decimal or hex |
| `WriteRegisterWord(reg, v)`, `ReadRegisterWord(reg)` | Write and read a 16-bit hardware register |

`char ApolloDebugMessage[256]` is the shared buffer for `sprintf`.

### Macros, set 1: AD and ADX (ApolloCrossDev_Defines.h)

| Macro | Active with |
|---|---|
| `AD(x)` | `-DAPOLLO_DEBUG` |
| `ADX(x)` | `-DAPOLLO_DEBUG -DAPOLLO_DEBUGEXTRA` |
| `ADXX(x)` | Never (always empty) |

```c
AD(sprintf(ApolloDebugMessage, "loaded %s\n", name);)
AD(ApolloDebugPutStr(ApolloDebugMessage);)
```

ApolloLib's own code uses this set. The example Makefiles build with
`-DAPOLLO_DEBUG -DAPOLLO_DEBUGEXTRA`.

### Macros, set 2: levels (ApolloCrossDev_Debug.h)

Set `DEBUG` to a sum of levels, for example `-DDEBUG=7`:

| Level | Value | Macro |
|---|---|---|
| `DBG_INFO` | 1 | `Debug_Info(fmt, ...)` |
| `DBG_WARN` | 2 | `Debug_Warn(...)` (yellow) |
| `DBG_ERROR` | 4 | `Debug_Error(...)` (red) |
| `DBG_FLAG` | 8 | `Debug_Flag(...)` (blinking magenta) |
| `DBG_TRACE` | 16 | `Debug_Trace(...)` (grey) |
| `DBG_CMD` | 32 | `traceCommand(req)`: device drivers only, not in ApolloLib |
| `DBG_MEM` | 64 | `AllocMem`/`FreeMem` wrappers: device drivers only, not in ApolloLib |

The macros print `[project][file][function][line] [LEVEL]` and the
message through exec `RawDoFmt` inside `Forbid()`/`Permit()`. They need
`PROJECT_NAME` and `BASE_FILE_NAME` defined, for example by the Makefile.
`RawDoFmt` formats: use `%ld` for 32-bit values.

`BUG_RED`, `BUG_BOLD` … are ANSI colour codes for your own messages.

## Differences from AmigaOS / AROS / 68060

- `kprintf`/debug.lib need the OS and go through exec; ApolloLib writes
  SERDAT directly and works in takeover code and interrupts.
- The serial port is shared: don't use the debug output while serial.device
  owns the port.

## Do / Don't

- DO call `ApolloDebugInit()` once before the first output.
- DO use `%ld` in `Debug_…` formats (`RawDoFmt`) and the C types in `AD()`
  (`sprintf`).
- DON'T set `DBG_CMD` or `DBG_MEM` in an ApolloLib program: their code is
  not in ApolloLib.
