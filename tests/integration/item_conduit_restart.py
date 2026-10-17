#!/usr/bin/env python3
"""Run two complete NeoForge dedicated-server JVMs against the same saved world.

The CI-only probe is injected for this test and always removed afterwards. No
runtime classes are mocked, no GameTest world reset occurs, and no NBT is copied
into replacement block entities. Each JVM exits via MinecraftServer.halt(false).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
PROBE = REPO / "tests/integration/ItemConduitRestartProbe.java"
GRADLE = """
// ON_ITEM_CONDUIT_RESTART_INTEGRATION_V1: a genuine dedicated server, not GameTestServer.
neoForge {
    runs {
        itemRestartServer {
            type = "server"
            programArgument "--nogui"
            gameDirectory = project.file('run-item-restart')
        }
    }
}
// Never ship the temporary integration subscriber, including stale class outputs.
tasks.named('jar', Jar) { exclude 'dev/obsidiannetwork/restarttest/**' }
"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def world_manifest(world):
    files = [world / "level.dat", *sorted((world / "region").glob("*.mca"))]
    require(files[0].is_file() and len(files) > 1, "Dedicated server did not save level.dat and region data")
    return {str(path.relative_to(world)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


def run_phase(project, output, phase, session, timeout):
    log = output.parent / f"item-conduit-restart-{phase}.log"
    result = output.parent / f"item-conduit-restart-{phase}.json"
    require(not result.exists(), f"Refusing stale phase result: {result}")
    env = os.environ.copy()
    env.update(ON_ITEM_RESTART_PHASE=phase, ON_ITEM_RESTART_REPORT=str(result), ON_ITEM_RESTART_SESSION=session)
    command = ["gradle", "--no-daemon", "--no-configuration-cache", "runItemRestartServer", "--stacktrace"]
    with log.open("w") as handle:
        process = subprocess.Popen(command, cwd=project, env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise AssertionError(f"Dedicated-server phase {phase} timed out; see {log}")
    text = log.read_text(errors="replace")
    require(code == 0, f"Dedicated-server phase {phase} failed rc={code}; see {log}")
    require(result.is_file(), f"Dedicated-server phase {phase} did not run its probe; see {log}")
    data = json.loads(result.read_text())
    require(data.get("session") == session and data.get("phase") == phase, "Probe report does not belong to this run")
    require(data.get("success") is True, f"ITEM {phase} test failed: {data.get('error')}; see {log}")
    require("Stopping server" in text, f"Missing normal server shutdown: {log}")
    require("Saving chunks for level" in text or "All dimensions are saved" in text, f"Missing world-save confirmation: {log}")
    require("Exception in server tick loop" not in text, f"Server crashed: {log}")
    data["gradle_exit_code"] = code
    data["normal_shutdown_verified"] = True
    data["log"] = log.name
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("work"))
    parser.add_argument("--output", type=Path, default=Path("dist/item-conduit-restart.json"))
    parser.add_argument("--phase-timeout", type=int, default=360)
    args = parser.parse_args()
    project = args.project.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), f"Refusing stale combined result: {output}")
    run = project / "run-item-restart"
    require(not (run / "world").exists(), "Restart integration requires a fresh test world; refusing to delete an existing world")
    run.mkdir(parents=True, exist_ok=True)
    (run / "eula.txt").write_text("eula=true\n")
    (run / "server.properties").write_text("online-mode=false\nserver-port=25569\nspawn-protection=0\nview-distance=2\nsimulation-distance=2\npause-when-empty-seconds=0\nsync-chunk-writes=true\nmax-tick-time=120000\nlevel-name=world\nmotd=CI ITEM conduit restart integration\n")
    target = project / "src/main/java/dev/obsidiannetwork/restarttest/ItemConduitRestartProbe.java"
    require(not target.exists(), "Restart probe already exists in source tree")
    build = project / "build.gradle"
    original_build = build.read_text()
    report = {"schema_version": 1, "status": "running", "session": str(uuid.uuid4()), "phases": {}}
    started = time.monotonic()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(PROBE.read_text())
        build.write_text(original_build + GRADLE)
        report["phases"]["before"] = run_phase(project, output, "before", report["session"], args.phase_timeout)
        report["world_after_stop_sha256"] = world_manifest(run / "world")
        # No file in the world is modified between the two independent JVMs.
        report["phases"]["after"] = run_phase(project, output, "after", report["session"], args.phase_timeout)
        before, after = report["phases"]["before"], report["phases"]["after"]
        require(before["server_jvm_pid"] != after["server_jvm_pid"], "Test reused the same server JVM")
        require(before["server_jvm_started"] != after["server_jvm_started"], "Test reused a JVM start time")
        require(after.get("configuration_preserved") is True and after.get("item_conservation") is True, "Missing restart integrity checks")
        report["world_after_restart_sha256"] = world_manifest(run / "world")
        report.update(status="passed", distinct_server_jvms=True, same_saved_world=True, source_probe_sha256=hashlib.sha256(PROBE.read_bytes()).hexdigest())
        print("ITEM_CONDUIT_PROCESS_RESTART_V1 PASS " + json.dumps({"before_pid": before["server_jvm_pid"], "after_pid": after["server_jvm_pid"], "topologies": after["topologies"]}))
    except BaseException as failure:
        report.update(status="failed", error=str(failure))
        raise
    finally:
        target.unlink(missing_ok=True)
        build.write_text(original_build)
        # Also delete generated probe classes, so no later packaging task can ship them.
        classes = project / "build/classes/java/main/dev/obsidiannetwork/restarttest"
        if classes.is_dir():
            for class_file in classes.glob("*.class"):
                class_file.unlink()
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
