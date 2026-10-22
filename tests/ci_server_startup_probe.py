#!/usr/bin/env python3
"""Start the REAL dedicated server, verify it reaches Done, then stop promptly.

Unlike a fixed 90-second 'timeout' that always waits even after startup, this
supervisor waits up to the SAME 90 seconds for the actual Minecraft readiness
signal, verifies 5 seconds of continued healthy running, and then terminates
the full spawned process group. No GameTests are removed or shortened.
"""
import argparse
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

READY = re.compile(r'Done \([0-9.]+s\)!|For help, type "help"')
FATAL = re.compile(
    r'Failed to start|Exception in server tick loop|ModLoadingException|LoadingFailedException'
)


def run(command, workdir, logfile, timeout_seconds=90.0, stability_seconds=5.0):
    workdir = Path(workdir)
    logfile = Path(logfile)
    assert workdir.is_dir(), "Missing build project: " + str(workdir)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    ready_at = None
    process = None
    error = None
    try:
        with logfile.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                command, cwd=workdir, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True
            )
            while True:
                # Log file is ordinary UTF-8 with occasional Gradle ANSI.
                content = logfile.read_text(encoding="utf-8", errors="replace")
                if FATAL.search(content):
                    error = "Fatal Minecraft startup/runtime log entry"
                    break
                if process.poll() is not None:
                    error = "Server exited before controlled shutdown (rc=%s)" % process.returncode
                    break
                now = time.monotonic()
                if ready_at is None and READY.search(content):
                    ready_at = now
                    print("CI_SERVER_READY: Minecraft reported Done; stability window starts",
                          flush=True)
                if ready_at is not None and now - ready_at >= stability_seconds:
                    print("CI_SERVER_READY_STABLE: Minecraft still running after %.1fs" %
                          stability_seconds, flush=True)
                    break
                if now - started > timeout_seconds:
                    error = "Server not ready/stable before %.1fs timeout" % timeout_seconds
                    break
                time.sleep(0.25)
    finally:
        # Like the former 'timeout' kill, but ONLY after a verified ready server.
        # Linux GitHub runner: new process session contains Gradle and Java child.
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
        if logfile.exists():
            print("===== REAL DEDICATED SERVER STARTUP LOG =====", flush=True)
            print(logfile.read_text(encoding="utf-8", errors="replace"), flush=True)
    if error:
        raise RuntimeError(error)
    final_log = logfile.read_text(encoding="utf-8", errors="replace")
    if ready_at is None or not READY.search(final_log) or FATAL.search(final_log):
        raise RuntimeError("Server startup validation failed")
    print("CI_SERVER_STARTUP_PASS elapsed=%.2fs (old gate: fixed 90s)" %
          (time.monotonic()-started), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", default="work")
    p.add_argument("--log", default="/tmp/build101-server.log")
    p.add_argument("--timeout", type=float, default=90.0)
    p.add_argument("--stability", type=float, default=5.0)
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()
    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        cmd = ["gradle", "--no-daemon", "--no-configuration-cache",
               "runServer", "--stacktrace"]
    run(cmd, args.workdir, args.log, args.timeout, args.stability)


if __name__ == "__main__":
    main()
