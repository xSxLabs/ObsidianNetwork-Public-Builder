#!/usr/bin/env python3
"""Bind a packaged mod to the exact runtime source/classes used by CI tests.

Capture after all runtime patches and compileJava, before starting any test JVM.
Verify after removing CI fixtures and rebuilding, before publishing the JAR.
Only the explicitly named CI fixture paths are excluded; other changes fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile


CI_PREFIXES = ("dev/obsidiannetwork/build103/", "dev/obsidiannetwork/restarttest/")
CI_RESOURCES = ("data/obsidiannetwork/structure/build103_empty.nbt",)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def excluded(name: str, resources: bool = False) -> bool:
    return any(name.startswith(prefix) for prefix in CI_PREFIXES) or (
        resources and name in CI_RESOURCES
    )


def file_map(root: Path, *, suffix: str | None = None, resources: bool = False) -> dict:
    if not root.is_dir():
        raise ValueError(f"Missing input directory: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if excluded(name, resources) or (suffix and not name.endswith(suffix)):
            continue
        result[name] = sha256(path.read_bytes())
    if not result:
        raise ValueError(f"No runtime inputs found in {root}")
    return result


def git_commit(repo: Path) -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError(f"Invalid Git commit in {repo}")
    return commit


def capture(args: argparse.Namespace) -> dict:
    result = {
        "schema_version": 1,
        "kind": "pre_execution_runtime_manifest",
        "public_commit": git_commit(args.public_repo),
        "private_source_commit": git_commit(args.private_repo),
        "excluded_ci_class_prefixes": list(CI_PREFIXES),
        "excluded_ci_resources": list(CI_RESOURCES),
        "sources": file_map(args.source_dir, suffix=".java"),
        "resources": file_map(args.resource_dir, resources=True),
        "classes": file_map(args.classes_dir, suffix=".class"),
    }
    if args.private_source_artifact:
        result["private_source_artifact"] = {
            "name": args.private_source_artifact.name,
            "sha256": sha256(args.private_source_artifact.read_bytes()),
        }
    return result


def require_same(label: str, expected: dict, actual: dict) -> None:
    if expected == actual:
        return
    missing = sorted(expected.keys() - actual.keys())
    added = sorted(actual.keys() - expected.keys())
    changed = sorted(k for k in expected.keys() & actual.keys() if expected[k] != actual[k])
    raise ValueError(f"{label} changed after tests were prepared: missing={missing}, added={added}, changed={changed}")


def verify(args: argparse.Namespace) -> dict:
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "pre_execution_runtime_manifest":
        raise ValueError("Unsupported pre-execution manifest")
    if manifest.get("excluded_ci_class_prefixes") != list(CI_PREFIXES) or manifest.get("excluded_ci_resources") != list(CI_RESOURCES):
        raise ValueError("CI exclusion policy changed")
    current = capture(args)
    for key in ("public_commit", "private_source_commit"):
        if current[key] != manifest[key]:
            raise ValueError(f"{key} changed after pre-execution capture")
    for key in ("sources", "resources", "classes"):
        require_same(key, manifest[key], current[key])
    if manifest.get("private_source_artifact") != current.get("private_source_artifact"):
        raise ValueError("Private source artifact changed")
    with ZipFile(args.jar) as jar:
        entries = jar.namelist()
        if len(entries) != len(set(entries)):
            raise ValueError("Duplicate entries in packaged JAR")
        leaked = [name for name in entries if excluded(name, resources=True)]
        if leaked:
            raise ValueError(f"CI fixtures leaked into user JAR: {leaked}")
        classes = {name: sha256(jar.read(name)) for name in entries if name.endswith(".class")}
        # Compare all classes, including unexpected classes from stale output/dependencies.
        require_same("packaged JAR classes", manifest["classes"], classes)
        for name, expected in manifest["resources"].items():
            if name not in entries or sha256(jar.read(name)) != expected:
                raise ValueError(f"Packaged runtime resource differs from tested input: {name}")
    return {
        "schema_version": 1,
        "kind": "verified_packaged_runtime",
        "status": "passed",
        "public_commit": manifest["public_commit"],
        "private_source_commit": manifest["private_source_commit"],
        "pre_execution_manifest_sha256": sha256(manifest_bytes),
        "jar": {"name": args.jar.name, "sha256": sha256(args.jar.read_bytes())},
        "runtime_sources": len(manifest["sources"]),
        "runtime_classes": len(manifest["classes"]),
        "source_unchanged_since_test_preparation": True,
        "classes_identical_to_test_preparation": True,
        "jar_classes_identical_to_test_preparation": True,
        "ci_fixtures_absent_from_jar": True,
        "note": "Execution success is recorded separately; this manifest proves byte identity, not test coverage.",
    }


def add_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--resource-dir", type=Path, required=True)
    parser.add_argument("--classes-dir", type=Path, required=True)
    parser.add_argument("--public-repo", type=Path, required=True)
    parser.add_argument("--private-repo", type=Path, required=True)
    parser.add_argument("--private-source-artifact", type=Path)
    parser.add_argument("--output", type=Path, required=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cap = commands.add_parser("capture", help="Capture runtime source and compiled class hashes before test execution")
    add_inputs(cap)
    check = commands.add_parser("verify", help="Verify unchanged runtime and byte-identical packaged JAR after tests")
    add_inputs(check)
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--jar", type=Path, required=True)
    commands.add_parser("selftest", help="Run offline parser and runtime identity regression tests")
    args = parser.parse_args()
    if args.command == "selftest":
        root = Path(__file__).resolve().parents[1]
        return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(root / "tests"), "-p", "test_*.py", "-v"], cwd=root).returncode
    try:
        result = capture(args) if args.command == "capture" else verify(args)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"BUILD_PROVENANCE FAIL: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"BUILD_PROVENANCE_{args.command.upper()} PASS {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
