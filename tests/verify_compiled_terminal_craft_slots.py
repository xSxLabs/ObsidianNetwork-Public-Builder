#!/usr/bin/env python3
"""Verify release JAR implements guarded exact craft-slot no-op fast path."""
import subprocess
import sys
from pathlib import Path

def verify(jar: Path):
    assert jar.is_file(), f"Missing release JAR: {jar}"
    cmd=["javap","-c","-p","-classpath",str(jar),
         "dev.obsidiannetwork.blockentity.TerminalInventoryBlockEntity"]
    out=subprocess.run(cmd,capture_output=True,text=True,check=True).stdout
    head="public void setCraftItem(int, net.minecraft.world.item.ItemStack);"
    end="public void copyFrom(net.minecraft.world.item.ItemStack[]);"
    assert out.count(head)==out.count(end)==1, "Compiled craft-slot method drift"
    body=out.split(head,1)[1].split(end,1)[0]
    # The newly added setCraftGrid method sits between these methods. Keep
    # verifying the original setter independently, not both method bodies.
    body=body.split("public void setCraftGrid(net.minecraft.world.item.ItemStack[]);",1)[0]
    for token in ("Method getCraftItem:(I)Lnet/minecraft/world/item/ItemStack;",
                  "Method net/minecraft/world/item/ItemStack.matches:",
                  "Method net/neoforged/neoforge/transfer/item/ItemStacksResourceHandler.extract:",
                  "Method net/neoforged/neoforge/transfer/item/ItemStacksResourceHandler.insert:",
                  "Method setChanged:()V"):
        assert body.count(token)==1,(token,body.count(token))
    assert body.count("Method net/neoforged/neoforge/transfer/transaction/Transaction.openRoot:")==2, (
        "Original 2 transaction blocks disappeared")
    assert body.index("Method getCraftItem:")<body.index("Method net/minecraft/world/item/ItemStack.matches:")
    assert body.index("Method net/minecraft/world/item/ItemStack.matches:") < body.index("Method net/neoforged/neoforge/transfer/transaction/Transaction.openRoot:")
    assert "bipush        9" in body or "bipush        9\n" in body, "9-slot bound gate missing"
    print("COMPILED_TERMINAL_UNCHANGED_CRAFT_SLOT_NOOP_V1 PASS two_original_transactions_preserved=true")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: verify_compiled_terminal_craft_slots.py mod.jar")
    verify(Path(sys.argv[1]))
