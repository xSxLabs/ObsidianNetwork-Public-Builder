The CI helpers keep runtime evidence separate from source checks and bind the
packaged JAR to the source and class files prepared for the actual test JVMs.

Run `python3 scripts/build_provenance.py selftest` for the offline regression
tests. Both helpers support `--help`.

Run all public and private runtime patchers before `compileJava`. Immediately
after that compilation, before the GameTest and dedicated-server processes:

```sh
python3 scripts/build_provenance.py capture \
  --source-dir work/src/main/java \
  --resource-dir work/src/main/resources \
  --classes-dir work/build/classes/java/main \
  --public-repo . --private-repo private \
  --private-source-artifact private/xSxLabs-Network-Storage-0.76.0-rc10.jar \
  --output dist/tested-build-manifest.json
```

After the tests, remove only CI fixtures, perform the final clean build, then
verify the actual candidate JAR (substitute its exact path):

```sh
python3 scripts/build_provenance.py verify \
  --source-dir work/src/main/java \
  --resource-dir work/src/main/resources \
  --classes-dir work/build/classes/java/main \
  --public-repo . --private-repo private \
  --private-source-artifact private/xSxLabs-Network-Storage-0.76.0-rc10.jar \
  --manifest dist/tested-build-manifest.json \
  --jar dist/xSxLabs-Network-Storage-1.1.1.jar \
  --output dist/build-provenance.json
```

This fails on source/resource changes after capture, changed compiled classes,
extra or changed JAR classes, or leaked `build103`/`restarttest` fixtures. The
manifest records both Git commits, the private input JAR hash, every runtime
source/resource/class hash, and the final JAR SHA256. Execution success remains
a separate gate: byte identity alone does not mean tests passed.

Generate the consolidated report from the actual runtime log. Add repeated
`--require-marker` arguments to replace the default three equipment/bulk
requirements with all the markers expected in that CI workload:

```sh
python3 scripts/diagnostic_report.py \
  --log /tmp/build103-gametest.log \
  --output dist/diagnostic-report.json \
  --require-gametest-pass \
  --restart-report dist/item-conduit-restart.json \
  --provenance-report dist/build-provenance.json \
  --server-ticks dist/server-ticks.json \
  --require-tick-workload equipment_offline \
  --require-tick-workload equipment_attached \
  --require-tick-workload equipment_registry_reference \
  --require-tick-workload rapid_crafting \
  --require-tick-workload rapid_bulk \
  --source-root work/src/main/java/dev/obsidiannetwork \
  --perf-output dist/perf-hotpaths.json
```

Each measurement retains its log filename, line number, and available runtime
clock/CI emission timestamp. Positional main durations and keys such as
`p95_ns` are retained. Malformed required fields, duplicate keys, bad percentile
ordering, absent required markers, invalid restart evidence, or inconsistent
tick summaries fail the command. Source snippets and shell commands do not
count as runtime measurements or successful GameTests.

`perf-hotpaths.json` is regenerated from the final source and explicitly marked
as a source audit, not a runtime profile. Server menu benchmarks cover the
server handlers; they do not cover a rendered Minecraft client. Tick durations
measure the interval between `ServerTickEvent.Pre` and `Post`, excluding
scheduling and tick-loop work outside those events. The report recomputes every
workload summary from the raw tick samples. Warning attribution uses explicit
benchmark wall-clock windows and actual server logger clocks only; buffered CI
timestamps and log line ordering never establish causal attribution.

The report's `status: passed` means extraction and its requested evidence gates
passed. `missing_release_gates` and measurement limits remain visible, including
unmeasured client rendering and complete tick-loop timing.
