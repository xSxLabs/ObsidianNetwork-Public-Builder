#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Checking isolated Forge 1.20.1 source tree"
test -f build.gradle
test -f settings.gradle
test -f src/main/resources/META-INF/mods.toml
test -f src/main/resources/connected_wall_signs.mixins.json
python3 - <<'PY'
import json, pathlib, re
root=pathlib.Path('src/main')
cfg=json.loads((root/'resources/connected_wall_signs.mixins.json').read_text())
assert cfg['compatibilityLevel']=='JAVA_17'
assert cfg['required']
for entry in cfg.get('mixins',[])+cfg.get('client',[]):
    source=root/'java'/pathlib.Path(*cfg['package'].split('.'))/(entry.replace('.','/')+'.java')
    assert source.is_file(), f'Missing mixin: {source}'
props=pathlib.Path('gradle.properties').read_text()
assert re.search(r'^minecraft_version=1\.20\.1$',props,re.M)
assert re.search(r'^forge_version=47\.',props,re.M)
print('PASS: project metadata, mixin references and Forge target')
PY
if [[ -x ./gradlew ]]; then
  echo "Gradle wrapper found. Run ./gradlew --no-daemon build to compile."
else
  echo "NOTICE: No Gradle wrapper committed. Compilation has not been performed."
fi
