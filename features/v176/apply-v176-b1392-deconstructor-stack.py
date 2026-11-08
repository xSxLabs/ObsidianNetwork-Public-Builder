#!/usr/bin/env python3
"""B1392: Shift+DECONSTRUCT handles the complete machine input stack.

Normal clicks continue to use the original single-operation server code.
The Shift action is a separate vanilla inventory-button ID (2), verified and
executed only on the server. Never grant items on the client.
"""
import os
import re
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
menu = root / "menu/DeconstructionTerminalMenu.java"
screen = root / "client/DeconstructionTerminalScreen.java"
m = menu.read_text("utf-8")
s = screen.read_text("utf-8")

assert "B1392_DECONSTRUCT_STACK" not in m, "B1392 patch applied twice"
assert "DECONSTRUCT success outputs=" in m, "B1392 original single-action diagnostics absent"
assert "serverPlan(" in m and "syncPreview(" in m, "B1392 plan/preview API drift"
assert "handleInventoryButtonClick" in s, "B1392 client button API drift"

# Do not replace the original click handler: a normal click must remain
# precisely the same single recipe operation.
sig = re.search(
    r"\bboolean\s+clickMenuButton\s*\(\s*(?:[\w.]+\.)?Player\s+(\w+)\s*,\s*int\s+(\w+)\s*\)\s*\{",
    m,
)
assert sig is not None, "B1392 server click handler signature drift"
player_name, button_name = sig.group(1), sig.group(2)
assert len(re.findall(r"\bboolean\s+clickMenuButton\s*\(", m)) == 1
injected = (
    "\n      // B1392_DECONSTRUCT_STACK: button 1 stays single, button 2 is Shift+click.\n"
    f"      if ({button_name} == 2) return b1392DeconstructStack({player_name});\n"
)
m = m[:sig.end()] + injected + m[sig.end():]

# The existing Plan is an immutable per-recipe snapshot with 'consume' and
# 3x3 'out'. Calculate operations once (not one expensive recipe search per
# input) and split every resulting ItemStack at its legal maximum stack size.
# Deliver through the same server inventory/drop path as the single action,
# then refresh the menu once rather than per item.
helper = """
  // B1392_DECONSTRUCT_STACK: server-only, one batch per real Shift+click.
  private boolean b1392DeconstructStack(net.minecraft.world.entity.player.Player player) {
    if (!(player instanceof net.minecraft.server.level.ServerPlayer serverPlayer)
        || !this.stillValid(serverPlayer)) return false;
    java.util.Optional<Plan> found = this.serverPlan(serverPlayer);
    if (found.isEmpty()) return false;
    Plan recipe = found.get();
    net.minecraft.world.item.ItemStack input = this.machine.getItem(0);
    if (input.isEmpty() || recipe.consume <= 0) return false;

    // A normal Minecraft stack fits in one batch. Bound hacked oversized
    // inputs so malicious packets cannot create unbounded work in one tick.
    int operations = Math.min(input.getCount() / recipe.consume, 4096);
    if (operations <= 0) return false;

    // Capture output templates before mutating the input slot. All quantities
    // come from the server-selected reverse recipe (including Smithing).
    net.minecraft.world.item.ItemStack[] outputs = recipe.out;
    if (outputs == null) return false;
    int inputConsumed = operations * recipe.consume;
    input.shrink(inputConsumed);
    this.machine.setItem(0, input);

    net.minecraft.world.entity.player.Inventory inventory = serverPlayer.getInventory();
    int overflowDropped = 0;
    for (net.minecraft.world.item.ItemStack template : outputs) {
      if (template == null || template.isEmpty()) continue;
      long amount = (long) template.getCount() * operations;
      int stackMax = Math.max(1, template.getMaxStackSize());
      while (amount > 0L) {
        int portion = (int) Math.min(amount, (long) stackMax);
        net.minecraft.world.item.ItemStack result = template.copyWithCount(portion);
        inventory.add(result);
        if (!result.isEmpty()) {
          int left = result.getCount();
          if (serverPlayer.drop(result, false) != null) {
            overflowDropped += left;
          } else {
            XSX_LOG.error("[xSxDiag] B1392 overflow drop failed stack={}", result);
          }
        }
        amount -= portion;
      }
    }
    this.syncPreview(this.serverPlan(serverPlayer));
    this.broadcastChanges();
    XSX_LOG.info("[xSxDiag] B1392 DECONSTRUCT_STACK operations={} consumed={} overflowDropped={}",
        operations, inputConsumed, overflowDropped);
    return true;
  }

"""
xp = re.search(r"\bpublic\s+int\s+xpCost\s*\(", m)
assert xp is not None and len(re.findall(r"\bpublic\s+int\s+xpCost\s*\(", m)) == 1, "B1392 XP method drift"
m = m[:xp.start()] + helper + m[xp.start():]

# Vanilla container button traffic is already server-authoritative and does
# not spam chat/commands. Shift state is sampled only when the GUI button is
# actually clicked. ID 1 stays the existing behavior; ID 2 requests batch.
client_call = re.compile(r"handleInventoryButtonClick\s*\(\s*([^;,]+?)\s*,\s*1\s*\)")
matches = list(client_call.finditer(s))
assert len(matches) == 1, ("B1392 client click anchor drift", len(matches))
s, changed = client_call.subn(
    lambda hit: "handleInventoryButtonClick("
    + hit.group(1) + ", (net.minecraft.client.gui.screens.Screen.hasShiftDown() ? 2 : 1))",
    s, count=1,
)
assert changed == 1
assert "B1392_DECONSTRUCT_STACK" in m
assert "b1392DeconstructStack(" in m
assert "hasShiftDown() ? 2 : 1" in s
menu.write_text(m, "utf-8")
screen.write_text(s, "utf-8")
print("B1392_DECONSTRUCT_STACK_SERVER_CLIENT_PATCH_PASS")
