# Verified source JAR audit

Examined the uploaded `connected-wall-signs-1.0.0.jar` directly with `javap -p -c` on 2026-11-23.

## Grounded findings
- Original resolver only traverses horizontal neighbors along `facing.getCounterClockWise()` and its opposite. Height is always 1.
- Original resolver checks every member of the contiguous interval and returns a singleton for invalid groups.
- Original renderer has a distinct `CanvasRenderContext` and `TextLayout`, and injects into `render`, `renderSignModel`, `renderSignText`, `translateSignText`.
- Original server mixin has three injection methods for `getText`, `setText`, and `getMaxTextLineWidth`.
- Original mixin config requires Java 21 and includes a client mixin.

## Deviations and risks in the draft port
- The Forge resolver has a 64-member safety cap not found in the original; this is a deliberate deviation.
- The Forge resolver has a reconstructed cache whose precise invalidation semantics need to be compared to original bytecode.
- `SignBlockEntityMixin` is **uncompiled**; its injected method descriptor and the superclass constructor need validation with 1.20.1.
- The client renderer is not ported. `CanvasTextLayout` is a provisional helper, not confirmed feature parity.
- No Minecraft 1.20.1/Forge dependencies have been resolved; no successful build or game test has occurred.

## Release gate
Do not ship this project as a working port until Forge compilation, Mixin application, client rendering, and editing tests pass.
