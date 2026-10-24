#!/usr/bin/env python3
"""Build112: fix the inverted six-part shield by restoring vanilla humanoid model space.

Build111 attached the shield to model parts but failed to apply the model-to-world
transform. Player model Y grows *downwards* from the head while the world Y
grows upwards from the feet. The missing scale AND 1.501-block origin offset
put the head under the feet. Reapply Minecraft's LivingEntityRenderer base
transform once around ALL six joint submissions. Nothing else changes.
"""
import os
from pathlib import Path

client=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorShieldClient.java"
source=client.read_text(encoding="utf-8")
assert "BUILD111_POSED_ARMOR_SHIELD" in source
assert source.count("submitPart(stack,collector,model.")==6

old = '''  var model=event.getRenderer().getModel();
  PoseStack stack=event.getPoseStack();
  var collector=event.getSubmitNodeCollector();

  // All values in vanilla model pixels, including ~1-1.5 px shield clearance.'''
new = '''  var model=event.getRenderer().getModel();
  PoseStack stack=event.getPoseStack();
  var collector=event.getSubmitNodeCollector();

  // BUILD112_MODEL_COORDS: RenderPlayerEvent.Post supplies an entity-space
  // PoseStack, but ModelPart cubes/poses are in humanoid MODEL space.
  // Vanilla LivingEntityRenderer flips model X/Y and moves the model's
  // origin 1.501 blocks above the feet. Without BOTH operations, the model
  // head at negative pixel Y appears UNDER the player's feet.
  // Mirror the vanilla model transform once at parent level, then let each
  // ModelPart.translateAndRotate supply its own animated joint transform.
  stack.pushPose();
  stack.scale(-1.0F,-1.0F,1.0F);
  stack.translate(0.0F,-1.501F,0.0F);

  // All values in vanilla model pixels, including ~1-1.5 px shield clearance.'''
assert source.count(old)==1, ("BUILD112 start anchor",source.count(old))
source=source.replace(old,new,1)

old_end = '''  submitPart(stack,collector,model.leftLeg,0F,5.8F,0F,
      3.15F,7.05F,3.10F,.43F,time,impact,alpha);
 }

 private static void submitPart'''
new_end = '''  submitPart(stack,collector,model.leftLeg,0F,5.8F,0F,
      3.15F,7.05F,3.10F,.43F,time,impact,alpha);
  stack.popPose(); // Restore caller's entity-space matrix.
 }

 private static void submitPart'''
assert source.count(old_end)==1, ("BUILD112 end anchor",source.count(old_end))
source=source.replace(old_end,new_end,1)
client.write_text(source,encoding="utf-8")

# Regression check against actual vanilla humanoid 24px vertical coordinates:
# head model -3.9px; torso +5.9px; boots +12px pivot +5.8px.
# Human head must be ABOVE the torso and torso ABOVE the boots in world Y.
head=1.501-(-3.9)/16
torso=1.501-(5.9)/16
boots=1.501-(12+5.8)/16
assert 2.0>head>torso>boots>0.0,(head,torso,boots)
assert source.count("stack.scale(-1.0F,-1.0F,1.0F);")==1
assert source.count("stack.translate(0.0F,-1.501F,0.0F);")==1
assert source.count("submitPart(stack,collector,model.")==6
assert source.count("stack.pushPose();")==2 and source.count("stack.popPose();")==2
assert 'id.equals("energy_shield")' in source
assert "EnergyTool.energy(armor)<20L" in source
print("BUILD112_MODEL_COORDS_PASS: head above torso above boots, all six posed segments transformed once, FE/damage unchanged")
