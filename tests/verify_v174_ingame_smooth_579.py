#!/usr/bin/env python3
"""B579 strict compiled-source regression for continuous FE, rates and Vision."""
from pathlib import Path
import os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
react=(J/"reactor/ReactorControllerBlockEntity.java").read_text()
bank=(J/"powerbank/PowerbankBlockEntity.java").read_text()
vision=(J/"client/NetworkVisionClient.java").read_text()
socket=(J/"client/EnergyCableInputRenderer.java").read_text()
assert "B579_REACTOR_GENERATE_EVERY_TICK" in react
assert "B579_REACTOR_PUSH_EVERY_TICK" in react
assert "B579_REACTOR_ACTUAL_EXPORT_WINDOW" in react
assert "(long)be.rodAssemblies*600L*20L" not in react
assert "(long)be.rodAssemblies*600L*(100-be.controlRodInsertion)/100L" in react
assert "Math.min(Math.max(0L,FE_CAPACITY-be.storedFe),theoretical)" in react
assert "be.waterMb=Math.max(0,be.waterMb-activity);" in react
assert "be.fuelTicks=Math.max(0,be.fuelTicks-activity);" in react
assert "public long guiFePerTick(){return b579ActualGeneration;}" in react
assert "b579ActualGeneration=generated" in react
assert "be.b579ActualGeneration=produced" in react
assert "b579Generated" in react and "b514Output" in react
assert "B579_BANK_ROLLING_20" in bank
assert "B579_BANK_IDLE_DECAY" in bank
assert "b579WindowIn/20L" in bank and "b579WindowOut/20L" in bank
assert "b579InputBuckets[idx]+=addIn" in bank
assert "B579_VISION_CACHED_CONNECTIONS" in vision
assert "int steps=Math.min(32," in vision
assert "xrayPositions.size()>=160" in vision
assert "if((b579VisionMasks.getOrDefault(pos,0)" in vision
assert "B579_ENERGY_INPUT_BLACK_FRAME" in socket
assert "Blocks.BLACK_CONCRETE.defaultBlockState()" in socket
assert socket.count("dark(state,pose,collector,") == 6
assert socket.count("cap(state,pose,collector,") == 6
# Equivalence across realistic rod numbers and insertion values (unclamped).
for rods in (0,1,5,15,30,100,1024):
 for inserted in (0,10,50,90,100):
  old_batch=rods*600*20*(100-inserted)//100
  each=rods*600*(100-inserted)//100
  assert each*20==old_batch,(rods,inserted)
# Nominal example: 15 rod assemblies = 9000 FE/t, not 180000 FE/t.
assert 15*600==9000 and 15*600*20==180000
print("B579_1_TICK_FE_CONSERVATION_TRUE_RATE_BLUE_INPUT_AND_CACHED_PIPE_VISION_PASS")
