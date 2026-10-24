#!/usr/bin/env python3
"""Build146 final: Jade probe, 32-block recall and state preservation."""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(path,a,b):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(a)==1,(path,a[:150],s.count(a))
 p.write_text(s.replace(a,b,1),encoding="utf-8")
# 32 true 3-D blocks, not 32 horizontal blocks plus height.
edit("powerarmor/PowerArmorRecall.java",
     "Math.sqrt(256D-(double)height*height)",
     "Math.sqrt(1024D-(double)height*height)")
edit("powerarmor/PowerArmorRecall.java",
     "if(dest.distanceToSqr(p.position())>256D)continue;",
     "if(dest.distanceToSqr(p.position())>1024D)continue;")
edit("powerarmor/PowerArmorRecall.java",
     "for(int height:new int[]{2,5,9})",
     "for(int height:new int[]{2,5,9,16,24})")
edit("powerarmor/PowerArmorRecall.java",
     "signal acquired. Suit approaching from about 16 blocks.",
     "signal acquired. Suit approaching from about 32 blocks.")
edit("powerarmor/PowerArmorRecall.java",
     "no safe 16-block arrival location.",
     "no safe 32-block arrival location.")
# Ensure stalled status survives saves and is synced to Jade.
edit("blockentity/NetworkPlanterBlockEntity.java",
 'out.putInt("progress",progress);out.putInt("harvests",harvests);',
 'out.putInt("progress",progress);out.putInt("harvests",harvests);out.putBoolean("paused",stalled);')
edit("blockentity/NetworkPlanterBlockEntity.java",
 "  stalled=false;\n }\n @Override public void preRemoveSideEffects",
 '  stalled=in.getBooleanOr("paused",false);\n }\n @Override public void preRemoveSideEffects')
# Existing Jade plugin is already optional, installed only when Jade is present.
edit("compat/PowerArmorJadePlugin.java",
 "import snownee.jade.api.EntityAccessor;",
 "import snownee.jade.api.EntityAccessor;\nimport snownee.jade.api.BlockAccessor;\nimport snownee.jade.api.IBlockComponentProvider;")
edit("compat/PowerArmorJadePlugin.java",
 "registration.registerEntityComponent(SuitBonusProvider.INSTANCE, ArmorStand.class);",
 "registration.registerEntityComponent(SuitBonusProvider.INSTANCE, ArmorStand.class);\n"+
 "  registration.registerBlockComponent(PlanterProvider.INSTANCE,dev.obsidiannetwork.block.NetworkPlanterBlock.class);")
f=J/"compat/PowerArmorJadePlugin.java"
s=f.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
# append a client-only Jade block component. Values arrive through ordinary
# vanilla BlockEntity update packet (no extra network payload dependency).
s=s.rstrip()[:-1]+r'''
 /** BUILD146_JADE_PLANTER_STATUS: real synced inventory and growth state. */
 private enum PlanterProvider implements IBlockComponentProvider {
  INSTANCE;
  private static final Identifier UID=Identifier.fromNamespaceAndPath(
      "obsidiannetwork","network_planter_status");
  @Override public Identifier getUid(){return UID;}
  @Override public void appendTooltip(ITooltip tooltip,BlockAccessor accessor,IPluginConfig config){
   if(!(accessor.getBlockEntity() instanceof
        dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity p))return;
   tooltip.add(Component.literal("Soil: "+
       (p.soilStack().isEmpty()?"-":p.soilStack().getHoverName().getString())));
   tooltip.add(Component.literal("Seed/Sapling: "+
       (p.seedStack().isEmpty()?"-":p.seedStack().getHoverName().getString())));
   tooltip.add(Component.literal("Speed: "+p.upgrades()+"/16"));
   int progress=(int)(p.growth()*100L/Math.max(1,p.duration()));
   tooltip.add(Component.literal("Growth: "+Math.min(100,progress)+"%"));
   tooltip.add(Component.literal("Output: "+p.stored()+" items in "+
       p.slotsUsed()+"/9 slots"));
   tooltip.add(Component.literal(p.paused()?"PAUSED - buffer full":"Auto harvesting")
       .withStyle(p.paused()?ChatFormatting.RED:ChatFormatting.GREEN));
  }
 }
}
'''
f.write_text(s,encoding="utf-8")
for lang in ("en_us","de_de"):
 f=R/"assets/obsidiannetwork/lang"/(lang+".json")
 d=json.loads(f.read_text(encoding="utf-8"))
 d["config.jade.plugin_obsidiannetwork.network_planter_status"]=(
    "Network Planter status" if lang=="en_us" else "Network Planter Status")
 f.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("BUILD146_RECALL32_JADE_PASS: 32-block true-distance GeckoLib flight, synced Jade soil seed speed progress buffer paused")
