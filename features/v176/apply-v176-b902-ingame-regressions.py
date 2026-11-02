#!/usr/bin/env python3
"""B902: user-authorized B901 regression repairs, scoped to the v1.7.6 generated sources."""
from pathlib import Path
import os, re, json

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def read(rel):
 p=J/rel
 assert p.is_file(), ("B902_MISSING_JAVA",rel)
 return p, p.read_text(encoding="utf-8")

def exact(rel,old,new):
 p,s=read(rel)
 assert s.count(old)==1, ("B902_DRIFT",rel,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def bounded(rel,begin,end,new):
 p,s=read(rel)
 assert s.count(begin)==1 and s.count(end)==1 and s.index(begin)<s.index(end), ("B902_METHOD_DRIFT",rel,begin)
 p.write_text(s[:s.index(begin)]+new+s[s.index(end):],encoding="utf-8")

# A magnet updates the real backpack component between server menu ticks.
# Do not compare all nested Cell components to the opening-time snapshot.
# The physical item must still occupy the same equipped/hand location.
exact("backpack/V176BackpackMenu.java",
 "return player.isAlive()&&ItemStack.matches(live(),location.stack())\n       &&live().getItem() instanceof NetworkBackpackItem;",
 "return player.isAlive()&&live().getItem()==location.stack().getItem()\n       &&live().getCount()==1&&live().getItem() instanceof NetworkBackpackItem;")
# A filled Cell is portable. The CELL_CONTENTS component travels with it.
# Do not copy its stored contents into loose player inventory or empty it.
bounded("backpack/V176BackpackMenu.java",
 "  private boolean removable(int slot){",
 "  @Override public void setItem(int slot,ItemStack stack){",
 """  private boolean removable(int slot){
   if(slot<0||slot>=4)return false;
   ItemStack stack=getItem(slot);
   if(stack.isEmpty())return false;
   if(slot==0)return true;
   return stack.getItem() instanceof StorageCellItem
       ||stack.getItem() instanceof EquipmentCellItem;
  }
""")
# The filter editor has TWO pages of 45 templates (54 in total).
# Ordinary stored item list instead scrolls by 9 preview slots per row.
menu_p,menu_src=read("backpack/V176BackpackMenu.java")
old="""    int position=page*9+slot-4;
    return position>=0&&position<templates.getSlots()"""
assert menu_src.count(old)==1,("B902_FILTER_PAGE_DRIFT",menu_src.count(old))
menu_src=menu_src.replace(old,old.replace("page*9","page*45"))
assert menu_src.count("int last=Math.max(0,(resultEntries().size()-45+8)/9);")==1
menu_src=menu_src.replace("int last=Math.max(0,(resultEntries().size()-45+8)/9);",
                          "int last=filterEditor?1:Math.max(0,(resultEntries().size()-45+8)/9);")
menu_p.write_text(menu_src,encoding="utf-8")

# No artificial cap/slowdown: collect every eligible drop once per tick in
# a true 12-block spherical radius, using full entity stacks and actual cell
# capacity. Persist the bag BEFORE reducing each ground stack.
mag="backpack/V176BackpackMagnetEvents.java"
p,s=read(mag)
assert s.count("private static final int ITEM_BUDGET=128;")==1
assert s.count("private static final int ENTITY_BUDGET=16;")==1
s=s.replace(" private static final int ITEM_BUDGET=128;\n","")
s=s.replace(" private static final int ENTITY_BUDGET=16;\n","")
s=s.replace("private static final double RANGE=6.0D;","private static final double RANGE=12.0D;")
s=s.replace("       ||player.tickCount%5!=0||!player.isAlive())return;",
            "       ||!player.isAlive())return;")
s=s.replace("new AABB(player.blockPosition()).inflate(RANGE)",
            "player.getBoundingBox().inflate(RANGE)")
s=s.replace("  int entities=0,items=0;\n","")
s=s.replace("   if(++entities>ENTITY_BUDGET||items>=ITEM_BUDGET)break;\n","")
s=s.replace("   if(entity.hasPickUpDelay())continue;\n",
            "   if(entity.distanceToSqr(player)>RANGE*RANGE)continue;\n")
s=s.replace("   int tryItems=Math.min(ITEM_BUDGET-items,dropped.getCount());",
            "   int tryItems=dropped.getCount();")
s=s.replace("   items+=accepted;\n","")
for bad in ["ITEM_BUDGET","ENTITY_BUDGET","tickCount%5","hasPickUpDelay()"]:
 assert bad not in s, ("B902_MAGNET_STALE_CAP",bad)
assert "location.persist(player,updated)" in s and s.index("location.persist(player,updated)")<s.index("remainder.shrink(accepted)")
p.write_text(s,encoding="utf-8")

# The old B817 button handlers are multiline lambdas; B891's simple
# button regex deliberately did not match them. Remove both by semantic
# anchor and leave the 45-slot item view scrollable.
p,s=read("client/V176BackpackScreen.java")
for label,cmd in (("<","previous"),(">","next")):
 pattern=(r'(?s)\s*addRenderableWidget\(net\.minecraft\.client\.gui\.components\.Button\.builder\(\s*'
          +re.escape('Component.literal("'+label+'"),b->{')
          +r'.*?\.bounds\(leftPos\+\d+,topPos\+127,22,13\)\.build\(\);')
 s,num=re.subn(pattern,"\n",s,count=1)
 assert num==1,("B902_ARROW_NOT_REMOVED",label,num)
assert 'Component.literal("<")' not in s and 'Component.literal(">")' not in s
assert 'private int filterPage=0;' in s
s=s.replace(' private int filterPage=0;', ' private int filterPage=0;\n private int scrollRow=0;',1)
# Draw a visible narrow track outside the list (between x=170..183).
# Fully opaque inventory panel prevents the fake/underlying slot background.
needle="  g.fill(x+7,y+36,x+169,y+128,0xff091b2a);"
assert s.count(needle)==1,("B902_STORED_LIST_DRAW_DRIFT",s.count(needle))
s=s.replace(needle,
"""  g.fill(x+7,y+139,x+169,y+216,0xff183448);
"""+needle+"""
  g.fill(x+173,y+38,x+179,y+128,0xff163041);
  int thumbY=y+39+Math.min(73,scrollRow*3);
  g.fill(x+174,thumbY,x+178,thumbY+16,0xff80b9d2);
""",1)
old="""   for(int i=0;i<steps;i++)
    command(scrollY>0?"networkbackpack previous":"networkbackpack next");"""
new="""   for(int i=0;i<steps;i++){
    command(scrollY>0?"networkbackpack previous":"networkbackpack next");
    if(filterEditor)filterPage=Math.max(0,Math.min(1,filterPage+(scrollY<0?1:-1)));
    else scrollRow=Math.max(0,scrollRow+(scrollY<0?1:-1));
   }"""
assert s.count(old)==1,("B902_WHEEL_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
# Clicking the scrollbar moves by five rows. No navigation arrows are retained.
needle='  boolean onSearch=searchBox!=null&&searchBox.isMouseOver(mx,my);'
assert s.count(needle)==1
s=s.replace(needle,
"""  int scrollX=(int)mx-getLeftPos(),scrollY=(int)my-getTopPos();
  if(button==0&&scrollX>=173&&scrollX<180&&scrollY>=38&&scrollY<129){
   int delta=scrollY>38+Math.min(73,scrollRow*3)+8?1:-1;
   for(int i=0;i<5;i++){
    command(delta>0?"networkbackpack next":"networkbackpack previous");
    if(filterEditor)filterPage=Math.max(0,Math.min(1,filterPage+delta));
    else scrollRow=Math.max(0,scrollRow+delta);
   }
   return true;
  }
"""+needle,1)
assert "mouseScrolled(double mx,double my,double scrollX,double scrollY)" in s
p.write_text(s,encoding="utf-8")

# Real-world player and its equipment model must use one exactly horizontal
# right upper arm only while Attack Mode is active. The left arm is untouched.
for rel,anchor in (
 ("mixin/V176AttackPlayerModelMixin.java","this.rightArm.xRot=-1.43F;"),
 ("mixin/V176AttackRightArmMixin.java","rightArm.xRot=-1.43F;"),
 ("client/V176MicroMgLayer.java","arm.xRot=-1.43F;"),
 ("client/V176MicroMgVisualClient.java","arm.xRot=-1.43F;")
):
 p,s=read(rel)
 assert s.count(anchor)==1,("B902_ARM_TARGET_DRIFT",rel,s.count(anchor))
 p.write_text(s.replace(anchor,anchor.replace("-1.43F","-1.5707964F"),1),encoding="utf-8")
# RenderArmEvent is the physical first-person arm pass, while the barrel is
# already placed by RenderHandEvent. Adjust the rendered arm pose itself.
p,s=read("client/V176MicroMgVisualClient.java")
assert "import net.neoforged.neoforge.client.event.RenderHandEvent;" in s
s=s.replace("import net.neoforged.neoforge.client.event.RenderHandEvent;",
            "import net.neoforged.neoforge.client.event.RenderHandEvent;\nimport net.neoforged.neoforge.client.event.RenderArmEvent;",1)
armhook=""" @SubscribeEvent public static void xsxlabs$firstPersonStraightArm(RenderArmEvent event){
  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT
      ||!armedForAttack(event.getPlayer()))return;
  // Adjust VANILLA ARM, not the independently rendered gun. The renderer's
  // arm transform is already active when this event fires.
  event.getPoseStack().translate(0.11F,0.12F,-0.19F);
  event.getPoseStack().mulPose(com.mojang.math.Axis.XP.rotationDegrees(-24.0F));
 }
"""
marker=" @SubscribeEvent public static void worldSuit("
assert s.count(marker)==1
s=s.replace(marker,armhook+marker,1)
p.write_text(s,encoding="utf-8")

# Reuse the real multiblock material/models rather than Crying Obsidian on
# separately registered network ports. The monitor follows Powerbank styling
# and has an existing controller display face.
for name,reference in (
 ("reactor_network_port","reactor_power_port"),
 ("powerbank_network_port","powerbank_input"),
 ("power_terminal","powerbank_controller")
):
 src=R/"models/block"/(reference+".json")
 dst=R/"models/block"/(name+".json")
 assert src.is_file() and dst.is_file(),("B902_REFERENCE_MODEL_MISSING",reference)
 original=json.loads(src.read_text(encoding="utf-8"))
 assert "textures" in original or "parent" in original or "elements" in original
 dst.write_text(json.dumps({"parent":"obsidiannetwork:block/"+reference},
                            indent=2)+"\n",encoding="utf-8")

assert 'return stack.getItem() instanceof StorageCellItem\n       ||stack.getItem() instanceof EquipmentCellItem;' in (J/"backpack/V176BackpackMenu.java").read_text()
assert 'RANGE=12.0D' in (J/mag).read_text()
print("B902_FILLED_CELLS_GUI_STAYS_OPEN_INSTANT_RADIUS12_ALL_ENTITIES_SCROLLBAR_ARM_MATERIALS_READY")
