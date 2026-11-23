# Forge 1.20.1 backport verification

## What has been checked
- Original uploaded JAR is present in the local working session and has been inspected with `unzip` and `javap`.
- Original SignBlockEntityMixin targets `getText(boolean)`, `setText(SignText,boolean)` and `getMaxTextLineWidth()`.
- Original renderer targets `render`, `renderSignModel`, `renderSignText`, `translateSignText`; Forge 1.20.1 signatures **not yet verified**.
- Source-level validation script is included at `scripts/verify-source.sh`.

## Blocking issues
1. This workspace does not yet contain a Gradle wrapper or Forge 1.20.1 development dependencies. No successful compile is claimed.
2. The sign mixin signatures must be checked against the 1.20.1 mappings before use. Mixin method names or return types may differ.
3. The client renderer is not wired up. The current text layout helper is not sufficient to render a connected sign canvas.
4. The horizontal-only resolver is not necessarily feature-parity with the original grouping algorithm.
5. No Minecraft client or dedicated server smoke test has been run.

## Build instructions once the toolchain is available
Use a Java 17 JDK and Gradle 8-compatible wrapper with ForgeGradle 6.
Run from **this subdirectory only**, not the repository root:

```bash
bash scripts/verify-source.sh
./gradlew --no-daemon build
```

Do not publish a release until a full compile and in-game render test passes. All changes are isolated to this subdirectory on the `port/connected-wall-signs-forge-1.20.1` branch.
