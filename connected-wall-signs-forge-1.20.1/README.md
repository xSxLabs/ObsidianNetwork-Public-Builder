# Connected Wall Signs — Forge 1.20.1 backport

Dedicated, isolated workspace for backporting the supplied `connected-wall-signs-1.0.0.jar` from NeoForge/Minecraft 1.21.1 to Forge/Minecraft 1.20.1.

## Source inventory (from supplied JAR)
- `com.xsxlabs.connectedwallsigns.ConnectedWallSigns`
- `com.xsxlabs.connectedwallsigns.WallSignGroup`
- `com.xsxlabs.connectedwallsigns.WallSignGroupResolver` (including `TickCache`)
- `com.xsxlabs.connectedwallsigns.mixin.SignBlockEntityMixin`
- `com.xsxlabs.connectedwallsigns.mixin.client.SignRendererMixin` (including `CanvasRenderContext` and `TextLayout`)
- `META-INF/neoforge.mods.toml`
- `xsxlabs_connected_wall_signs.mixins.json`

## Port checklist
- [ ] Recover readable Java source from the JAR and review behavior
- [ ] Initialize independent Forge 47.x / Minecraft 1.20.1 Gradle project under this folder
- [ ] Adapt sign block entity logic and client renderer to 1.20.1 mappings
- [ ] Update Forge metadata, mixin configuration and Java target (17)
- [ ] Build with Forge toolchain and verify startup and adjacent-wall-sign behavior

## Isolation
Do not edit root Gradle/build files, NetworkStorage source, CI workflows, or existing branches. Keep all port files in `connected-wall-signs-forge-1.20.1/`. A build is **not yet verified**.
