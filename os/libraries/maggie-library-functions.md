---
title: maggie.library function reference
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
basis: [source-code]
components: [libraries, saga-3d-maggie]
applies_to:
  core: "Core 12841+"
  os: [any]
tags: [maggie, 3d, library, functions, registers, lighting, textures]
related:
  - os/libraries/maggie-library.md
  - os/pitfalls/maggie-library-side-effects.md
  - core/saga-3d-maggie/registers.md
  - core/best-practices/prefer-library-calls-for-saga-chips.md
sources:
  - "maggie.library, github.com/RMortenB/MaggieLibrary (golden source), commit 64c78ef (2026-08-18): MaggieLibrary_API.md, fd/maggie.fd, include/maggie_flags.h, maggie_transform.c, maggie_lighting.c"
---

## Summary

Every maggie.library function with its argument registers, grouped as in
the author's `MaggieLibrary_API.md`, plus the constants. Where the API
document and the source disagree, this file follows the source and says
so. The overview, frame setup and performance notes are in
[maggie-library.md](maggie-library.md); read
[maggie-library-side-effects.md](../pitfalls/maggie-library-side-effects.md)
first.

## Details

### Conventions (SRC)

- The library base goes in `a6` (`MaggieBase`); the bias is 30.
- d0, d1, a0 and a1 are scratch. Some functions also destroy all E
  registers (D8–D31).
- Floats go in fp0–fp2, as `maggie.fd` lists them.
- Only the Maggie registers are written; no other hardware register.
- The library expects the FPU rounding mode round-to-zero (RZ) and sets it
  in your task (see the side-effects pitfall).
- Buffers and textures are global handles: free each one before the
  program exits.

### Context (static build only)

| Function | Registers | What it does |
|---|---|---|
| `struct Library *magCreateContext(void)` | – | Replaces `OpenLibrary` for `libmaggie.a`: sets RZ, opens graphics.library, creates the scene semaphore, the depth buffer and the handle tables. Store the result in `MaggieBase`. NULL on failure. |
| `void magDeleteContext(struct Library *base)` | – | Replaces `CloseLibrary`: frees the depth buffer and any buffers and textures still allocated, closes graphics.library. NULL is ignored. |

### Scene

| Function | Registers | What it does |
|---|---|---|
| `magBeginScene()` | – | Takes the library lock (no other program draws until `magEndScene`); resets matrices, lights, depth state and draw mode |
| `magEndScene()` | – | Releases the lock |

### Screen, texture and draw state

| Function | Registers | What it does |
|---|---|---|
| `magSetScreenMemory(pixels, xres, yres)` | a0, d0, d1 | Render target; up to 1920x1080 |
| `magSetDrawMode(mode)` | d0 | OR of the `MAG_DRAWMODE_…` flags (table in [maggie-library.md](maggie-library.md)); `BLEND_REPLACE` and `TEXGEN_UV` are 0 |
| `magSetRGB(rgb)` | d0 | Tint, multiplied with texture and lighting |
| `magSetTexture(unit, txtr)` | d0, d1 | Binds a texture handle; `unit` must be 0 |
| `magSetVertexBuffer(vBuffer)` | d0 | Active vertex buffer |
| `magSetIndexBuffer(iBuffer)` | d0 | Active index buffer |
| `magScissor(x0, y0, x1, y1)` | d0, d1, d2, d3 | Scissor rectangle by its **inclusive corners**, in pixels; `x1`/`y1` are clamped to the resolution − 1 |
| `UWORD *magGetDepthBuffer()` | → d0 | The live 16-bit depth buffer (internal memory, not a copy). Maggie doesn't snoop the CPU data cache, so CPU reads and writes can be stale. |

### Matrices

| Function | Registers | What it does |
|---|---|---|
| `magSetWorldMatrix(m)` | a0 | 4x4 floats; lighting is done after this matrix |
| `magSetViewMatrix(m)` | a0 | Usually the inverse camera matrix; texgen is done after this one |
| `magSetPerspectiveMatrix(m)` | a0 | For the 16-bit w-buffer: build it with `mat4_perspective` from `maggie_vec.h` |

### Drawing

| Function | Registers | What it does |
|---|---|---|
| `magDrawTriangles(startVtx, nVtx)` | d0, d1 | From the active vertex buffer |
| `magDrawIndexedTriangles(firstVtx, nVtx, startIndx, nIndx)` | d0, d1, d2, d3 | `firstVtx`…`firstVtx + nVtx` must cover every vertex used: those are transformed |
| `magDrawIndexedPolygons(firstVtx, nVtx, startIndx, nIndx)` | d0, d1, d2, d3 | As above; `$FFFF` in the index list starts a new polygon |
| `magDrawTrianglesUP(vtx, nVerts)` | a0, d0 | Your own `struct MaggieVertex` array, converted on every call |
| `magDrawIndexedTrianglesUP(vtx, nVtx, indx, nIndx)` | a0, d0, a1, d1 | As above, indexed |
| `magDrawIndexedPolygonsUP(vtx, nVtx, indx, nIndx)` | a0, d0, a1, d1 | As above, polygons separated by `$FFFF` |
| `magDrawSprites(startVtx, nSprites, size)` | d0, d1, fp0 | Camera-facing sprites from the vertex buffer (position and colour only) |
| `magDrawSpritesUP(vtx, nSprites, size)` | a0, d0, fp0 | As above, from a `struct MaggieSpriteVertex` array |
| `magDrawSpan(start, end)`, `magDrawLinearSpan(start, end)` | a0, a1 | Disabled: do nothing |

### Immediate mode (slowest)

| Function | Registers | What it does |
|---|---|---|
| `magBegin()` / `magEnd()` | – | Collect triangles, then draw them with `magDrawTrianglesUP` |
| `magVertex(x, y, z)` | fp0, fp1, fp2 | Position; submits the vertex |
| `magNormal(x, y, z)` | fp0, fp1, fp2 | Normal |
| `magTexCoord(reg, u, v)` / `magTexCoord3(reg, u, v, w)` | d0, fp0, fp1 (, fp2) | Texture coordinates |
| `magColour(rgba)` | d0 | Colour |

### Buffers and textures

| Function | Registers | What it does |
|---|---|---|
| `UWORD magAllocateVertexBuffer(nVerts)` | d0 → d0 | Handle of a buffer for up to `nVerts` vertices |
| `magUploadVertexBuffer(vBuffer, vtx, startVtx, nVerts)` | d0, a0, d1, d2 | Converts and copies `struct MaggieVertex` data |
| `magUploadVertexPositions/Normals/TexCoords2/TexCoords3(vBuffer, data, startVtx, nVerts)` | d0, a0, d1, d2 | One attribute: float xyz, xyz, uv or uvw |
| `magUploadVertexColours(vBuffer, colours, startVtx, nVerts)` | d0, a0, d1, d2 | `ULONG` colours, turned into grey (intensity) at upload |
| `magFreeVertexBuffer(vBuffer)` | d0 | |
| `UWORD magAllocateIndexBuffer(nIndx)` | d0 → d0 | Handle of a buffer for up to `nIndx` indices |
| `magUploadIndexBuffer(iBuffer, indx, startIndx, nIndx)` | d0, a0, d1, d2 | |
| `magFreeIndexBuffer(iBuffer)` | d0 | |
| `UWORD magAllocateTexture(log2size)` | d0 → d0 | Square texture of 2^`log2size` pixels (5–10), with its full mip chain |
| `magUploadTexture(txtr, mipLog2, data, format)` | d0, d1, a0, d2 | `MAG_TEXFMT_DXT1`, `_RGB` or `_RGBA` (+ `MAG_TEXCOMP_HQ`); stored as DXT1 |
| `magFreeTexture(txtr)` | d0 | |

### Clearing

| Function | Registers | What it does |
|---|---|---|
| `magClearColour(rgba)` | d0 | Clear colour |
| `magClearDepth(depth)` | d0 | Clear depth, usually `$FFFF` |
| `magClear(buffers)` | d0 | `MAG_CLEAR_COLOUR` (1), `MAG_CLEAR_DEPTH` (2), or both in one call |

### Lighting (with `MAG_DRAWMODE_LIGHTING`)

| Function | Registers | What it does |
|---|---|---|
| `magSetLightType(light, type)` | d0, d1 | Light 0–7 (`MAG_MAX_LIGHTS` = 8); all lights are off after `magBeginScene` |
| `magSetLightPosition(light, x, y, z)` | d0, fp0, fp1, fp2 | Not used by directional and ambient lights |
| `magSetLightDirection(light, x, y, z)` | d0, fp0, fp1, fp2 | Not used by point and ambient lights |
| `magSetLightCone(light, phi)` | d0, fp0 | Spot lights: cone angle in radians |
| `magSetLightAttenuation(light, a)` | d0, fp0 | Reach; the light falls off with the square of the distance |
| `magSetLightColour(light, rgba)` | d0, d1 | Turned into grey: Maggie interpolates intensity only |

| Light type | Value | Light |
|---|---|---|
| `MAG_LIGHT_OFF` | 0 | Off |
| `MAG_LIGHT_POINT` | 1 | From a position |
| `MAG_LIGHT_DIRECTIONAL` | 2 | From a direction |
| `MAG_LIGHT_SPOT` | 3 | Position, direction and cone |
| `MAG_LIGHT_AMBIENT` | 4 | The same intensity added to every vertex (not in the API document; used by the samples) |

Lighting replaces the vertex colour.

### Where the API document differs from the source

| API document | Source |
|---|---|
| `magScissor(x, y, width, height)`; "x/y > `$7fff` clamps to 0" | `magScissor(x0, y0, x1, y1)`: two corners. Only `x1`/`y1` are clamped; the `< 0` tests on the `UWORD` arguments never fire. |
| Light types without `MAG_LIGHT_AMBIENT` | `MAG_LIGHT_AMBIENT` = 4 exists and works |
| `magUploadVertexColours`: "colours … in float uvw triplets" | `ULONG` colours (the text is copied from the texture coordinates) |
| `magUploadIndexBuffer` parameters named `vBuffer`, `vtx`, `startVtx`, `nVerts` | `iBuffer`, `indx`, `startIndx`, `nIndx` |

## Differences from AmigaOS / AROS / 68060

- There is no classic AmigaOS 3D library; the API resembles fixed-function
  OpenGL (matrices, `glBegin`-style immediate mode, fixed lights), but runs
  on the Maggie span unit and the 68080 FPU.

## Do / Don't

- DO pass `magScissor` two corners, not a width and height.
- DO free every buffer and texture handle before exit, or use
  `magDeleteContext` in the static build.
- DON'T read or write the depth buffer from the CPU while Maggie draws: it
  isn't cache coherent.
- DON'T expect coloured lights or vertex colours: they become intensities.
