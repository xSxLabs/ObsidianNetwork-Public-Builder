#!/usr/bin/env python3
"""Verify the distributable MC26.1.2 JAR includes the narrowly scoped Elytra gate."""
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

def verify(jar):
    jar=Path(jar)
    assert jar.is_file(), "JAR missing: "+str(jar)
    cls="dev/obsidiannetwork/mixin/NetworkElytraSpeedCheckMixin.class"
    with ZipFile(jar) as z:
        entries=set(z.namelist())
        assert cls in entries,"Scoped Network Elytra speed-check mixin missing from JAR"
        mix=json.loads(z.read("obsidiannetwork.mixins.json"))
        assert "NetworkElytraSpeedCheckMixin" in mix.get("mixins",[]), "Mixin not registered in JAR"
        assert "NetworkElytraCuriosGlideMixin" in mix.get("mixins",[]), "Build 377 Curios gliding Mixin lost"
        binary=z.read(cls)
        assert b"shouldCheckPlayerMovement" in binary, "Target method annotation absent"
        assert b"xsxNetworkElytraSpeedCheck" in binary, "Scoped injection absent"
    proc=subprocess.run(["javap","-p","-c","-classpath",str(jar),
                         "dev.obsidiannetwork.mixin.NetworkElytraSpeedCheckMixin"],
                        capture_output=True,text=True,check=True)
    bc=proc.stdout
    for symbol in ("ServerPlayer.isFallFlying", "ServerPlayer.onGround",
                   "NetworkElytraCurios.find", "EnergyTool.energy",
                   "CallbackInfoReturnable.setReturnValue", "Double.isFinite"):
        assert symbol in bc, "Missing compiled gate: "+symbol
    for name in ("setGameRules", "setDeltaMovement"):
        assert name not in bc, "Movement/gamerule unexpectedly changed: "+name
    print("NETWORK_ELYTRA_COMPILED_SCOPED_SPEED_CHECK_V1 PASS")

if __name__=="__main__":
    assert len(sys.argv)==2,"Usage: verify_compiled_network_elytra_speedcheck.py JAR"
    verify(sys.argv[1])
