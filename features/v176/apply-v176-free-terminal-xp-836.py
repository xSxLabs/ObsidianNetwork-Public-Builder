#!/usr/bin/env python3
"""v1.7.6: Deconstruction and Disenchanting Terminal operations cost zero XP levels.

Patch the actual reconstructed NeoForge menus, not just the client labels.
Strict one-match guards ensure upstream menu changes fail closed rather than
silently shipping an XP-charging terminal.
"""
from __future__ import annotations

import os
from pathlib import Path
import re


ROOT = Path(os.environ.get("V1_SOURCE_ROOT", "work/src/main/java"))
MENUS = ROOT / "dev/obsidiannetwork/menu"


def exactly_once(source: str, pattern: str, replacement: str, label: str) -> str:
    revised, matches = re.subn(pattern, replacement, source, flags=re.MULTILINE | re.DOTALL)
    if matches != 1:
        raise AssertionError(f"V176_FREE_TERMINAL_XP {label}: expected 1 source match, got {matches}")
    return revised


def patch_deconstruction(source: str) -> str:
    source = exactly_once(
        source,
        r"return q\.<Integer>map\(p -> p\.cost\)\.orElse\(0\);",
        "return 0;",
        "deconstruction server-synced displayed XP cost",
    )
    source = exactly_once(
        source,
        r"if \(!sp\.getAbilities\(\)\.instabuild && sp\.experienceLevel < p\.cost\)\s*\{\s*"
        r'XSX_LOG\.warn\("\[xSxDiag\] click rejected: xp need=\{\} have=\{\}", p\.cost, sp\.experienceLevel\);\s*'
        r"return false;\s*\}\s*else\s*\{",
        "{ // v1.7.6: deconstruction has no minimum XP level.",
        "deconstruction server-level rejection",
    )
    source = exactly_once(
        source,
        r"if \(!sp\.getAbilities\(\)\.instabuild\)\s*\{\s*"
        r"sp\.giveExperienceLevels\(-p\.cost\);\s*\}",
        "// v1.7.6: deconstruction does not deduct XP.",
        "deconstruction server XP deduction",
    )
    source = exactly_once(
        source,
        r"(public int xpCost\(\)\s*\{\s*)return this\.cost;(\s*\})",
        r"\g<1>return 0;\g<2>",
        "deconstruction GUI XP getter",
    )
    assert "sp.experienceLevel < p.cost" not in source
    assert "giveExperienceLevels(-p.cost)" not in source
    assert "this.syncPreview(q);" in source  # still syncs recipe preview
    assert "input.shrink(p.consume);" in source  # still consumes input items
    return source


def patch_disenchanting(source: str) -> str:
    source = exactly_once(
        source,
        r"return Math\.max\(1,\s*Math\.min\(5,\s*\(lvl \+ 1\) / 2\)\);",
        "return 0;",
        "disenchanting server-side XP price",
    )
    source = exactly_once(
        source,
        r"int xp = this\.serverCost\(p\);\s*"
        r"if \(!sp\.getAbilities\(\)\.instabuild && sp\.experienceLevel < xp\)\s*"
        r"\{\s*return false;\s*\}\s*else\s*\{",
        "{ // v1.7.6: disenchanting has no minimum XP level.",
        "disenchanting server-level rejection",
    )
    source = exactly_once(
        source,
        r"if \(!sp\.getAbilities\(\)\.instabuild\)\s*\{\s*"
        r"sp\.giveExperienceLevels\(-xp\);\s*\}",
        "// v1.7.6: disenchanting does not deduct XP.",
        "disenchanting server XP deduction",
    )
    assert "sp.experienceLevel < xp" not in source
    assert "giveExperienceLevels(-xp)" not in source
    assert "rt.storage().extract(plain.key(), 1L)" in source  # book still required
    assert "this.machine.setItem(1, out)" in source  # result still delivered
    return source


def main() -> None:
    for filename, patch in (
        ("DeconstructionTerminalMenu.java", patch_deconstruction),
        ("DisenchantingTerminalMenu.java", patch_disenchanting),
    ):
        path = MENUS / filename
        if not path.is_file():
            raise FileNotFoundError(f"V176_FREE_TERMINAL_XP missing reconstructed menu: {path}")
        old = path.read_text(encoding="utf-8")
        new = patch(old)
        if new == old:
            raise AssertionError(f"V176_FREE_TERMINAL_XP no changes applied to {filename}")
        path.write_text(new, encoding="utf-8")
        print(f"V176_FREE_TERMINAL_XP applied {filename} (server + GUI 0 levels)")
    print("V176_FREE_TERMINAL_XP_DECONSTRUCTION_DISENCHANTING PASS")


if __name__ == "__main__":
    main()
