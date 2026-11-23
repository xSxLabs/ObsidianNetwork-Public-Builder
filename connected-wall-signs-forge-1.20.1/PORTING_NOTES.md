# Original JAR inspection (2026-11-23)

Input: `connected-wall-signs-1.0.0.jar` (NeoForge 1.21.1, compiled Java 21).

Inspected directly with `unzip` and `javap -p -c` rather than relying on the filename.

## Original classes and behavior
- `ConnectedWallSigns`: mod entrypoint.
- `WallSignGroup`: record with `members, anchor, facing, right, width, height`.
- `WallSignGroupResolver`: breadth-first search along **facing.getCounterClockWise()**, checking identical horizontal facing. Calculates min/max horizontal coordinates and rejects nonrectangular groups. Original has per-level, per-tick caches.
- `SignBlockEntityMixin`: shares group text, replicates edited group text, changes maximum sign line width.
- `SignRendererMixin`: groups sign rendering, transforms board geometry and canvas text, calculates text layout based on line count and canvas size.

## Work completed
- Standalone Forge 47.3.0 Gradle scaffold and Java 17 entrypoint.
- Reconstructed group resolution using horizontal BFS, matching facing and contiguous rectangular validation. Bounded to 64 signs for safety pending a closer bytecode comparison.
- No server-side text propagation or renderer port committed yet.

## Important differences to resolve
- 1.21.1 SignBlockEntity and SignRenderer methods differ from 1.20.1; do not copy the original mixin injections blindly.
- Need a Forge-compatible Mixin registration strategy and explicit mapping verification.
- Test group order for all four wall orientations, independent edits, front/back text, unloaded chunks and 1-sign fallback.
- Original code uses a tick cache; current port recomputes until correctness is verified.

## Status
**NOT BUILD-VERIFIED. NOT FEATURE-COMPLETE.** No working 1.20.1 JAR should be released from this branch yet.
