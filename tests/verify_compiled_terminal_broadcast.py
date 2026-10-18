#!/usr/bin/env python3
"""Ensure the final mod JAR syncs the menu once per grid mutation, not twice."""
from pathlib import Path
import subprocess
import sys

def verify(jar):
    assert Path(jar).is_file()
    s=subprocess.run(["javap","-c","-p","-classpath",str(jar),
                      "dev.obsidiannetwork.menu.StorageTerminalMenu"],
                     text=True,capture_output=True,check=True).stdout
    start="public void slotsChanged(net.minecraft.world.Container);"
    stop="public int recipeChoiceCount();"
    rebuild="private void rebuildRecipeChoice(net.minecraft.server.level.ServerPlayer, net.minecraft.server.level.ServerLevel);"
    after="public boolean clickMenuButton(net.minecraft.world.entity.player.Player, int);"
    assert s.count(start)==s.count(stop)==s.count(rebuild)==s.count(after)==1
    slots=s.split(start,1)[1].split(stop,1)[0]
    choice=s.split(rebuild,1)[1].split(after,1)[0]
    assert slots.count("Method rebuildRecipeChoice:")==1
    assert slots.count("Method broadcastChanges:")==0, "Duplicate terminal broadcast survived"
    assert choice.count("Method broadcastChanges:")==2, "Recipe-choice branch sync was removed"
    assert slots.count("Method dev/obsidiannetwork/blockentity/TerminalInventoryBlockEntity.setCraftItem:")==1, (
        "Terminal persisted craft slots disappeared")
    print("COMPILED_TERMINAL_SINGLE_GRID_BROADCAST_V1 PASS both_recipe_branches_synced=true")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: verify_compiled_terminal_broadcast.py file.jar")
    verify(Path(sys.argv[1]))
