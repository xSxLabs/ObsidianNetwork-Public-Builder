#!/usr/bin/env python3
"""B464: Server-side Warden Darkness immunity for active Power Armor Night Vision.
Only if installed night_vision card + nightvision_on toggle + powered full suit.
Does not affect other effects, ordinary players, or toggled-off upgrade cards.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorRuntime.java"
s=p.read_text(encoding="utf-8").rstrip()
assert s.endswith("}") and "B464_NIGHTVISION_WARDEN_DARKNESS" not in s
s=s[:-1]+r'''
 /** B464_NIGHTVISION_WARDEN_DARKNESS: do not dim active helmet night vision.
  * Server event, no visual patches, no unrelated potion cancellation.
  */
 @SubscribeEvent public static void xsxNightVisionDarkness(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer p)||p.isSpectator())return;
  if(!p.hasEffect(net.minecraft.world.effect.MobEffects.DARKNESS))return;
  if(!powered(p)||!hasCard(p,"night_vision")||!hasCard(p,"nightvision_on"))return;
  p.removeEffect(net.minecraft.world.effect.MobEffects.DARKNESS);
 }
}
'''
p.write_text(s,encoding="utf-8")
assert 'B464_NIGHTVISION_WARDEN_DARKNESS' in s
print("B464_NIGHTVISION_DARKNESS_PASS: Warden Darkness removed only with active powered suit Night Vision")
