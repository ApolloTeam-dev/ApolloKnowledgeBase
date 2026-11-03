---
title: maggie.library (Maggie 3D on AmigaOS)
type: reference
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [libraries, saga-3d-maggie]
applies_to:
  core: "Core 12841+"
  os: [amigaos-3.9]
tags: [maggie, 3d, library, textures, dxt1, rendering]
related:
  - os/pitfalls/maggie-library-side-effects.md
  - core/saga-3d-maggie/registers.md
  - core/pitfalls/maggie-depth-test-colour-write.md
  - core/pitfalls/maggie-span-tail.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), sections 15.1 and 15.3-15.8"
  - "maggie.library source, github.com/RMortenB/MaggieLibrary, commit 64c78ef (2026-08-17), MaggieLibrary_API.md"
---

## Summary

Morten's maggie.library drives the V4's Maggie span unit: it does transform,
lighting, clipping and triangle/polygon setup on the CPU and FPU, and gives
Maggie one span per scanline. Read
[maggie-library-side-effects.md](../pitfalls/maggie-library-side-effects.md)
before using it: a call changes your task's FPCR and E registers.

## Details

Source: <https://github.com/RMortenB/MaggieLibrary>. These notes were read
against commit `64c78ef` (2026-08-17); the full API is in
`MaggieLibrary_API.md`. Version tested on a V4: `maggie 4.0 (Sep 9 2026)`,
AmigaOS 3.9.

### Linking and building (SRC)

- **Shared:** `OpenLibrary("maggie.library", 0)` + `<proto/Maggie.h>`.
- **Static:** `make static` gives `libmaggie.a`. Include
  `<proto/Maggie_static.h>`, replace OpenLibrary/CloseLibrary with
  `magCreateContext()` / `magDeleteContext(base)`, store the result in the
  global `MaggieBase`, and link the archive **before** `-lamiga -lm`.
- Both forms pass the base in `a6` (`##bias 30`; LVOs in
  `include/lvo/Maggie_lvo.i`).
- From assembler, arguments go in registers as `maggie.fd` lists them;
  floats go in `fp0`–`fp2` (for example `magVertex`, `magSetLightPosition`,
  the `magDrawSprites` size).
- Library build flags:

  ```sh
  -std=c11 -fexcess-precision=fast -noixemul -Ofast -fno-unsafe-math-optimizations
  -fomit-frame-pointer -m68080 -mregparm -mhard-float
  ```

  `-std=c11` alone forces `-fexcess-precision=standard`, which caused about
  1320 spills of 12-byte values in the library.
- Static objects must use the caller's ABI (`-m68080 -mhard-float`). Use
  `-fomit-frame-pointer` so that `a6` is free.
- The assembler reads `MaggieBase` at fixed offsets
  (`raster/raster_structs.i`), checked by `_Static_assert`s. After changing
  `maggie_internal.h`, do a clean rebuild.

### Frame setup

- **Render target:** `magSetScreenMemory(pixels, xres, yres)`. Up to
  1920x1080 in the source (the README still says 1280x720). 16-bit (default)
  or 32-bit (`MAG_DRAWMODE_32BIT`) pixels. Rows are packed: the pitch is
  `xres * bpp`, with no separate modulo. Align buffers to 32 bytes, as the
  samples do.
- **Full screen with SAGA, as in the samples** (os-takeover):
  1. `SystemControl(SCON_TakeOverSys)` and switch off the raster/copper DMA.
  2. Save the old mode and frame pointer from the read addresses `$DFE1F4`
     and `$DFE1EC`.
  3. Write the mode to `$DFF1F4` and the frame pointer to `$DFF1EC`. The
     samples use `$0B02` = 640x360x16 and `$0B05` = 640x360x32.
  4. Use triple buffering, flipped after a VBlank.
- **In a window:** render into a 32-bit buffer, then
  `WritePixelArray(..., RECTFMT_ARGB)` (samples/Windowed).
- **Depth buffer:** internal, allocated at 1920x1080 x 2 bytes = 4 MB. It is
  a **16-bit w-buffer**, not a z-buffer. Build the projection with
  `mat4_perspective` from `maggie_vec.h` so that w = view z. Call
  `magClearDepth($ffff)`, then `magClear(MAG_CLEAR_COLOUR | MAG_CLEAR_DEPTH)`
  (one call for both is faster).
- **Matrices:** world, view and projection are multiplied into one matrix.
  Lighting uses world space and texgen view space; if you use neither, put
  the whole transform in any one matrix. The viewport is fixed:
  `* halfres + halfres`. Front faces are clockwise (`MAG_DRAWMODE_CULL_CCW`
  swaps); culling is always on.
- **Scissor:** `magScissor(x, y, w, h)`, in pixels.

### Draw paths, fastest first

1. **Buffers:** `magAllocate*Buffer`, `magUpload*`, `magSet*Buffer`, then
   `magDrawTriangles`, `magDrawIndexedTriangles` or `magDrawIndexedPolygons`.
   Data is converted once at upload. Pass `firstVtx`/`nVtx` covering only the
   vertices used: those get transformed. To change one attribute, use
   `magUploadVertexPositions/Normals/TexCoords2/TexCoords3/Colours`.
2. **User pointers** (`...UP`): the same calls on your own arrays, converted
   on every draw.
3. **Immediate mode** (`magBegin/magVertex/.../magEnd`): triangles only; it
   collects vertices and calls `magDrawTrianglesUP`. The slowest path.

- **Polygons:** convex, planar, with a planar UV mapping, up to 256 sides.
  `$FFFF` in the index list starts a new polygon, so vertex index `$FFFF`
  cannot be used. A quad is cheaper than two triangles (one setup, one edge
  walk). Add collinear vertices to avoid T-junction cracks.
- **Sprites:** `magDrawSprites(start, n, size)` / `magDrawSpritesUP`
  (position + colour only), always facing the camera. Use
  `MAG_DRAWMODE_AFFINE_MAPPING` with them.
- **Vertex format** (`maggie_vertex.h`): `pos` vec3, `normal` vec3,
  `tex` {u, v, w}, then `colour` ULONG: 40 bytes. One texture unit; UV 0..1 =
  one tile.
- The span calls (`magDrawSpan`, `magDrawLinearSpan`) are disabled and do
  nothing.

### Draw modes (`magSetDrawMode`, OR the flags)

| Flag | Value | Effect |
|---|---|---|
| `DEPTHBUFFER` | `$0001` | 16-bit w-buffer test and write |
| `BILINEAR` | `$0002` | Bilinear filtering |
| `32BIT` | `$0004` | 32-bit target (default 16) |
| `LIGHTING` | `$0008` | Per-vertex lights (up to 8) replace the vertex colour |
| `CULL_CCW` | `$0010` | Counter-clockwise front faces |
| `TEXGEN_POS/NORMAL/REFLECT` | `$0020/$0040/$0060` | Texture coordinates from position, view normal, reflection |
| `MIPMAP` | `$0080` | Automatic mip selection, even when no mipmaps were uploaded |
| `BLEND_ADD` / `BLEND_MUL` | `$0100` / `$0200` | Add to or multiply with the target |
| `AFFINE_MAPPING` | `$1000` | No perspective correction: much faster for small triangles |
| `DEPTH_MASK` | `$2000` | Hardware mode bit 3 |

**Colour is intensity only.** Maggie interpolates one light value per pixel.
Vertex and light colours are turned into grey at upload. The tint is one RGB
per draw (`magSetRGB`), multiplied with the texture and the light.

### Textures

- Square, power of two, 32 to 1024 pixels: `magAllocateTexture(log2size)`
  takes 5–10.
- **Always stored as DXT1** (4 bits per texel) plus the full mip chain.
  `magUploadTexture(t, mipLog2, data, fmt)` takes `MAG_TEXFMT_DXT1`, `_RGB`
  or `_RGBA`, plus `MAG_TEXCOMP_HQ` for slower, better compression. RGB and
  RGBA are compressed on the CPU at upload: do it at load time, or ship DXT1
  (the samples load `.dds`).
- **Alpha is DXT1's 1 bit.** RGBA texels with alpha < 128 are transparent:
  Maggie leaves those target pixels unchanged. There is no alpha blending.
- Texture data is kept 32-byte aligned.

### Performance

- The library ranks the paths buffers > user pointers > immediate,
  quads/polygons over triangle pairs, and `AFFINE_MAPPING` as much faster for
  small triangles (SRC).
- Measure first with `make static PROFILE=1`: it prints frame, clear, spans
  and setup times per frame. "Spans" is the raster; "Setup" is the CPU work
  (transform, clipping, setup, edge walk). `PROFILE=2` adds a per-edge timer,
  which doubles the edge cost.
- The FPU rules apply to your own transform code: one FP register write per
  cycle, fmul 5 and fadd 6 cycles of latency, 3 cycles per FP-to-integer
  conversion (see [core/cpu-68080/fpu-performance-model.md](../../core/cpu-68080/fpu-performance-model.md)).

## Differences from AmigaOS / AROS / 68060

- Maggie is V4 hardware, so classic AmigaOS has no library for it.
  maggie.library is V4 specific.
- It relies on BANK-prefixed FPU instructions, which the Apollo team will not
  support in future cores; see the side-effects pitfall.

## Do / Don't

- DO read [maggie-library-side-effects.md](../pitfalls/maggie-library-side-effects.md)
  first.
- DO use uploaded buffers and quads/polygons for speed, and
  `AFFINE_MAPPING` for small triangles.
- DON'T use vertex index `$FFFF`, or expect alpha blending or coloured
  lighting.
- DON'T call `magDrawSpan`/`magDrawLinearSpan`: they do nothing.
