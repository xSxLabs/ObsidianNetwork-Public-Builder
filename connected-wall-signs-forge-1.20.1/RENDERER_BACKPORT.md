# Renderer backport: source-backed mapping inventory

Inspected `SignRendererMixin.class` in the supplied NeoForge 1.21.1 JAR using `javap -p -c -v`.

Original injections target:
- `render` (HEAD and RETURN): initialize and clear the model context
- `renderSignModel` (HEAD and RETURN): transform connected board
- `renderSignText` (HEAD and RETURN): calculate and apply canvas layout
- `translateSignText` (HEAD): shift and scale text pose

Original layout algorithm (now in `client/CanvasTextLayout.java`):
1. Find first and last nonblank sign lines; measure maximum formatted line width with Minecraft Font.
2. Compute total occupied height as `9 + (last - first) * lineSpacing`.
3. Choose `max(0.01, min(45 / occupiedHeight, maxWidth / widestLine))`.
4. Vertically center via `(1.5 - (first + last) / 2) * lineSpacing`.

Do not attach these injections to Forge 1.20.1 until the actual `SignRenderer` method descriptors and invocation paths are checked against the Forge 47.x development classpath. Rendering methods and parameters changed between versions; blindly copying the original 1.21.1 annotations would likely crash at startup.

## Verification gate
- [ ] Resolve Forge 47.x MDK and dependencies
- [ ] Verify sign renderer method descriptors against Forge 1.20.1 mappings
- [ ] Implement and register client-only mixin
- [ ] Compile, inspect mixin refmap and test all orientations
- [ ] Verify connected board rendering, text placement and single-sign fallback

No release artifact is available yet.
