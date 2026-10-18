#!/usr/bin/env python3
"""Controller GUI: compute its 21 read-only status fields once per game tick.

Old code performs runtime lookup, device-count lookup, autocrafting job count
and template scan for *each* of 21 ContainerData.get() calls. Preserve exact
21-field semantics, 20-tick device-summary refresh, generator menu and
authoritative runtime. Only per-GUI read-only status data is cached.
"""
import os
from pathlib import Path

f = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/menu/PowerStatusMenu.java"
src = f.read_text(encoding="utf-8")
old = """         public int get(int i) {
            if (be instanceof ControllerBlockEntity c) {
               long stored = c.energy().stored();
               long cap = c.energy().capacity();
               ServerLevel sl = c.getLevel() instanceof ServerLevel s ? s : null;
               NetworkRuntime r = sl == null ? null : WorldTopologyBridge.runtimeForController(sl, c.getBlockPos());
               int drives = r == null ? 0 : r.drives().size();
               int terms = r == null ? 0 : r.terminalCount();
               int use = 2 + drives + terms;
               int autocrafters = r == null ? 0 : WorldTopologyBridge.autocrafterCount(sl, r);
               int active = r == null ? 0 : WorldTopologyBridge.autocraftingActiveJobs(sl, r);
               int blocked = r == null ? 0 : WorldTopologyBridge.autocraftingBlockedJobs(sl, r);
               int templates = r == null ? 0 : WorldTopologyBridge.templatesForRuntime(sl, r).size();
               WorldTopologyBridge.DeviceCounts dc = r != null && sl != null ? this.summary(c, sl, r) : WorldTopologyBridge.DeviceCounts.EMPTY;

               return switch (i) {
                  case 0 -> (int)stored;
                  case 1 -> (int)cap;
                  case 2 -> use;
                  case 3 -> drives;
                  case 4 -> terms;
                  case 5 -> r != null && r.powered() ? 1 : 0;
                  case 6 -> autocrafters;
                  case 7 -> active;
                  case 8 -> blocked;
                  case 9 -> templates;
                  case 10 -> dc.cables();
                  case 11 -> dc.importers();
                  case 12 -> dc.exporters();
                  case 13 -> dc.templateCreators();
                  case 14 -> dc.templateManagers();
                  case 15 -> dc.craftingMonitors();
                  case 16 -> dc.wirelessAntennas();
                  case 17 -> dc.processingMachines();
                  case 18 -> dc.autocrafters();
                  case 19 -> dc.drives();
                  case 20 -> dc.terminals();
                  default -> 0;
               };
            } else if (be instanceof SolidFuelGeneratorBlockEntity g) {"""
new = """         // XSXLABS_CONTROLLER_STATUS_ONCE_PER_TICK_V1: no repeated topology,
         // templates or job scans for each of 21 status fields.
         private final int[] controllerSnapshot = new int[21];
         private long lastControllerTick = Long.MIN_VALUE;
         private ServerLevel lastControllerLevel;

         public int get(int i) {
            if (be instanceof ControllerBlockEntity c) {
               if (i < 0 || i >= controllerSnapshot.length) return 0;
               ServerLevel sl = c.getLevel() instanceof ServerLevel s ? s : null;
               if (sl == null) return 0;
               long now = sl.getGameTime();
               if (lastControllerTick != now || lastControllerLevel != sl) {
                  // Do not retain a NetworkRuntime or world references beyond
                  // this single menu's read-only status calculation.
                  NetworkRuntime r = WorldTopologyBridge.runtimeForController(sl, c.getBlockPos());
                  int drives = r == null ? 0 : r.drives().size();
                  int terms = r == null ? 0 : r.terminalCount();
                  int use = 2 + drives + terms;
                  int autocrafters = r == null ? 0 : WorldTopologyBridge.autocrafterCount(sl, r);
                  int active = r == null ? 0 : WorldTopologyBridge.autocraftingActiveJobs(sl, r);
                  int blocked = r == null ? 0 : WorldTopologyBridge.autocraftingBlockedJobs(sl, r);
                  int templates = r == null ? 0 : WorldTopologyBridge.templatesForRuntime(sl, r).size();
                  WorldTopologyBridge.DeviceCounts dc = r == null ?
                     WorldTopologyBridge.DeviceCounts.EMPTY : this.summary(c, sl, r);
                  controllerSnapshot[0] = (int)c.energy().stored();
                  controllerSnapshot[1] = (int)c.energy().capacity();
                  controllerSnapshot[2] = use;
                  controllerSnapshot[3] = drives;
                  controllerSnapshot[4] = terms;
                  controllerSnapshot[5] = r != null && r.powered() ? 1 : 0;
                  controllerSnapshot[6] = autocrafters;
                  controllerSnapshot[7] = active;
                  controllerSnapshot[8] = blocked;
                  controllerSnapshot[9] = templates;
                  controllerSnapshot[10] = dc.cables();
                  controllerSnapshot[11] = dc.importers();
                  controllerSnapshot[12] = dc.exporters();
                  controllerSnapshot[13] = dc.templateCreators();
                  controllerSnapshot[14] = dc.templateManagers();
                  controllerSnapshot[15] = dc.craftingMonitors();
                  controllerSnapshot[16] = dc.wirelessAntennas();
                  controllerSnapshot[17] = dc.processingMachines();
                  controllerSnapshot[18] = dc.autocrafters();
                  controllerSnapshot[19] = dc.drives();
                  controllerSnapshot[20] = dc.terminals();
                  lastControllerTick = now;
                  lastControllerLevel = sl;
               }
               return controllerSnapshot[i];
            } else if (be instanceof SolidFuelGeneratorBlockEntity g) {"""
if src.count(old) != 1:
    raise AssertionError(f"controller snapshot code drift: {src.count(old)}")
for token in ("lastSummaryTick", "now - this.lastSummaryTick >= 20L", "getCount()", "return 21;", "FuelContainer"):
    assert token in src, f"controller menu protected contract disappeared: {token}"
src = src.replace(old, new, 1)
assert "XSXLABS_CONTROLLER_STATUS_ONCE_PER_TICK_V1" in src
assert src.count("WorldTopologyBridge.runtimeForController(sl, c.getBlockPos())") == 1
f.write_text(src, encoding="utf-8")
print("CONTROLLER_STATUS_ONCE_PER_TICK_V1 PASS")
