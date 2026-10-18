#!/usr/bin/env python3
"""Fail closed if either Curios setup lacks the full 50-drive GUI timing breakdown."""
from pathlib import Path
import sys
from metric_parser import validated_gui_phase_breakdown

if len(sys.argv) != 3:
    raise SystemExit("Usage: verify-gui-phase-breakdown.py <no-curios-log> <curios-log>")
for name in sys.argv[1:]:
    p = Path(name)
    result = validated_gui_phase_breakdown(p.read_text(encoding="utf-8"))
    print("GUI_BREAKDOWN_VERIFIED", p.name, result)
