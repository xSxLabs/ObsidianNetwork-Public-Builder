#!/usr/bin/env python3
"""B933 after B929: fix empty-hand MG, arm position and black hatch, eliminate monitor
ghost client targets, remove Powerbank toggle without affecting 3P arm or backpacks."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B933_SOURCE_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def between(rel,start,end,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(start)==1 and s.count(end)==1 and s.index(start)<s.index(end),("B933_SCOPE",rel)
 p.write_text(s[:s.index(start)]+new+s[s.index(end):],encoding="utf-8")
mg="client/V176MicroMgVisualClient.java"
# Root cause: B917 expressly skipped the gun for the player's EMPTY main hand.
edit(mg,
 "  if(progress<=0.001F||event.getItemStack().isEmpty())return;",
 "  if(progress<=0.001F)return;")
# RenderHandEvent draws ONE gun for both empty and held main hand.
# RenderArmEvent poses ONLY the real first-person arm, not a second gun.
between(mg,
 " @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){",
 " @SubscribeEvent public static void worldSuit(",
 """ @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  var player=event.getPlayer();
  int tier=tier(player);
  if(tier<1||tier>24)return;
  float progress=extension(player.getId(),armedForAttack(player));
  if(!armedForAttack(player)&&progress<=0.001F)return;
  // No proxy hand, no duplicate MG, no changes to the 3P PlayerModel.
  PoseStack pose=event.getPoseStack();
  pose.translate(-0.16F,0.10F,-0.18F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-50.0F));
 }
""")
edit(mg,
 "  pose.translate(0.58F,-0.30F,-0.53F);",
 "  pose.translate(0.43F,-0.27F,-0.58F);")
edit(mg,
 "  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-96.0F));",
 "  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-90.0F));")
# Shared vanilla main hand matrix: horizontal shift applies to visible arm,
# not only the barrel. No B907-style large parent rotation.
edit(mg,
 """  if(progress<=0.001F)return;
  // Only the held-item fallback uses the independent camera-space path.
  float gunOut=phase(progress,7.0F/12.0F,1.0F);""",
 """  if(progress<=0.001F)return;
  // Attack Mode: move the actual main hand toward the center, never offhand.
  if(armed)event.getPoseStack().translate(-0.21F,0.035F,0.0F);
  float gunOut=phase(progress,7.0F/12.0F,1.0F);""")
# The free dark hatch plate must not be drawn in STEADY Attack Mode; keep
# intermediate opening/closing phase so the animation still sequences.
p=J/mg;s=p.read_text(encoding="utf-8")
start=s.index(" public static void drawArm(")
stop=s.find(" private static void drawRight(",start)
if stop<0:stop=s.find(" @SubscribeEvent public static void",start)
assert stop>start,("B933_HATCH_BOUND",start,stop)
part=s[start:stop]
m=re.search(r"if\s*\(\s*hatchOpen\s*>\s*0\.001F\s*\)\s*\{",part)
assert m is not None,("B933_HATCH_DRIFT",part[:1200])
part=part[:m.start()]+"if(hatchOpen>0.001F&&hatchOpen<0.999F){"+part[m.end():]
p.write_text(s[:start]+part+s[stop:],encoding="utf-8")

# Server's 54 fake slots are already locked. But client ChestMenu still builds
# 54 slot hit targets on its own; hide them in the visible custom screen, too.
screen="client/V176PowerMonitorScreen.java"
edit(screen,"  super(menu,inv,title);",
 """  super(menu,inv,title);
  for(int i=0;i<54;i++){
   var slot=this.menu.getSlot(i);
   this.menu.slots.set(i,new net.minecraft.world.inventory.Slot(
        slot.container,slot.getContainerSlot(),-10000,-10000){
    @Override public boolean mayPlace(net.minecraft.world.item.ItemStack stack){return false;}
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return false;}
    @Override public boolean isActive(){return false;}
   });
  }""")
# POWERBANK is telemetry only. REACTOR continues to support ON/OFF.
edit(screen,
 "   g.text(font,state,153,y+3,d.enabled()?0xff7bffb0:0xffff9595);",
 """   if(d.type()==V176PowerMonitorRules.DeviceType.REACTOR)
    g.text(font,state,153,y+3,d.enabled()?0xff7bffb0:0xffff9595);""")
edit(screen,
 "   g.fill(x+148,ry+2,x+171,ry+16,0xff30566b);",
 """   var be=live();
   if(be!=null&&page*ROWS+i<be.devices().size()&&
       be.devices().get(page*ROWS+i).type()==V176PowerMonitorRules.DeviceType.REACTOR)
    g.fill(x+148,ry+2,x+171,ry+16,0xff30566b);""")
edit(screen,
 """      var d=list.get(idx);
      var mc=Minecraft.getInstance();""",
 """      var d=list.get(idx);
      if(d.type()!=V176PowerMonitorRules.DeviceType.REACTOR)return true;
      var mc=Minecraft.getInstance();""")
graph="power/V176PowerNetworkGraph.java"
edit(graph,
 """  if(world.getBlockEntity(target) instanceof PowerbankBlockEntity bank
     &&bank.mode()==PowerbankBlock.Mode.CONTROLLER){
   bank.xsxNetworkSetEnabled(!bank.xsxNetworkEnabled());
   return true;
  }""",
 """  // Powerbanks are status-only here; reject direct command toggles too.
""")
g=(J/mg).read_text();ui=(J/screen).read_text();net=(J/graph).read_text()
hand=g[g.index("public static void firstPerson(RenderHandEvent"):g.index("xsxlabs$aimVisibleFirstPersonArm")]
assert "event.getItemStack().isEmpty())return;" not in hand
assert "submitModelPart(BARREL" in hand
assert "pose.translate(0.43F,-0.27F,-0.58F)" in hand
assert "event.getPoseStack().translate(-0.21F,0.035F,0.0F)" in hand
assert "if(hatchOpen>0.001F&&hatchOpen<0.999F)" in g
assert "for(int i=0;i<54;i++)" in ui and "slot.getContainerSlot(),-10000,-10000" in ui
assert "for(int i=0;i<36;i++)" in ui
assert "d.type()!=V176PowerMonitorRules.DeviceType.REACTOR)return true;" in ui
assert "bank.xsxNetworkSetEnabled(!bank.xsxNetworkEnabled())" not in net
assert "V176FinalArmPose.java" not in open(__file__,encoding="utf-8").read()
print("B933_EMPTY_HAND_MG_ARM_LEFT_NO_STEADY_BLACK_HATCH_MONITOR_GHOSTS_BANK_READONLY_PASS")
