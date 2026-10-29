#!/usr/bin/env python3
"""B392: Printer speed slot, skip exactly one missing block, air free/instant."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
be=J/"blockentity/NetworkDeviceBlockEntity.java"
s=be.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,("B392_PRINTER_SOURCE_DRIFT",old[:90],s.count(old))
 s=s.replace(old,new,1)
change(' private boolean running=false;',
''' // B392_PRINTER_SPEED: one real inventory slot for installed upgrades.
 private ItemStack b392Speed=ItemStack.EMPTY;
 private static boolean b392IsSpeed(ItemStack stack){
  if(stack.isEmpty())return false;
  var id=BuiltInRegistries.ITEM.getKey(stack.getItem());
  return id!=null&&"obsidiannetwork".equals(id.getNamespace())&&
      id.getPath().contains("speed_upgrade");
 }
 private int b392SpeedCount(){return b392IsSpeed(b392Speed)?Math.min(16,b392Speed.getCount()):0;}
 private boolean running=false;''')
change(' public int progress(){return completed;}',
       ' public int progress(){return index;} // B392_AIR_PROGRESS: includes skipped air.')
change('if(mode()!=NetworkDeviceBlock.Mode.PRINTER||button<0||button>2)return false;',
       'if(mode()!=NetworkDeviceBlock.Mode.PRINTER||button<0||button>3)return false;')
change('''  if(button==0){
   if(planLength()==0)''',
'''  // B392_SKIP_ONCE: only a currently missing material can be skipped.
  // Remove the ghost FIRST, then advance ONE index; next missing pauses.
  if(button==3){
   if(!running||missing.isEmpty()||!status.startsWith("MISSING:")||
      index>=b378BlueprintBlocks().size())return false;
   missing=ItemStack.EMPTY;index++;
   setStatus("SKIPPED 1 MISSING BLOCK "+index+"/"+b378BlueprintBlocks().size());
   sync();return true;
  }
  if(button==0){
   if(planLength()==0)''')
change('''  if(net==null){setStatus("NETWORK OFFLINE");return;}''',
'''  // B392_AIR_ZERO_COST: skip ALL consecutive air voxels in one invocation,
  // even without power/network. Never charge energy or material for air.
  int beforeAir=index;
  while(index<plan.size()&&"minecraft:air".equals(plan.get(index)))index++;
  if(index!=beforeAir){missing=ItemStack.EMPTY;sync();}
  if(index>=plan.size()){
   running=false;setStatus("COMPLETE "+completed+"/"+plan.size());sync();return;
  }
  if(net==null){setStatus("NETWORK OFFLINE");return;}''')
change('''  if(!(level instanceof ServerLevel world)||world.getGameTime()%WORK_TICKS!=0)return;
  if(be.mode()==NetworkDeviceBlock.Mode.HOLOGRAM){
   if(world.getGameTime()%("map".equals(be.holoMode)?10:40)==0)be.hologram(world);
  }else if(be.mode()==NetworkDeviceBlock.Mode.PRINTER)be.printer(world,be.network(world));''',
'''  if(!(level instanceof ServerLevel world)||world.getGameTime()%WORK_TICKS!=0)return;
  if(be.mode()==NetworkDeviceBlock.Mode.HOLOGRAM){
   if(world.getGameTime()%("map".equals(be.holoMode)?10:40)==0)be.hologram(world);
  }else if(be.mode()==NetworkDeviceBlock.Mode.PRINTER){
   // B392_SPEED_BATCH: base 1 action/5 ticks, +1 per installed upgrade,
   // maximum 17 positions/5 ticks. Stop at first missing/block/error.
   int actions=1+be.b392SpeedCount();
   NetworkRuntime net=be.network(world);
   for(int i=0;i<actions;i++){
    int before=be.index;
    be.printer(world,net);
    if(!be.running||be.index==before)break;
   }
  }''')
change('  out.putBoolean("running",running);out.putString("status",status);',
'''  if(!b392Speed.isEmpty())out.store("speedUpgrades",ItemStack.CODEC,b392Speed);
  out.putBoolean("running",running);out.putString("status",status);''')
change('  running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");missing=ItemStack.EMPTY;',
'''  b392Speed=in.read("speedUpgrades",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  if(!b392IsSpeed(b392Speed))b392Speed=ItemStack.EMPTY;
  running=in.getBooleanOr("running",false);status=in.getStringOr("status","IDLE");missing=ItemStack.EMPTY;''')
change('for(ItemStack s:new ItemStack[]{blueprint,energy})',
       'for(ItemStack s:new ItemStack[]{blueprint,energy,b392Speed})')
change('return blueprint.isEmpty()&&energy.isEmpty();',
       'return blueprint.isEmpty()&&energy.isEmpty()&&b392Speed.isEmpty();')
change('return slot==0?blueprint:slot==1?energy:slot==2?missing:ItemStack.EMPTY;',
       'return slot==0?blueprint:slot==1?energy:slot==2?missing:slot==3?b392Speed:ItemStack.EMPTY;')
change('if(slot<0||slot>=2||count<=0)return ItemStack.EMPTY;',
       'if((slot!=0&&slot!=1&&slot!=3)||count<=0)return ItemStack.EMPTY;')
change('if(slot<0||slot>=2)return ItemStack.EMPTY;',
       'if(slot!=0&&slot!=1&&slot!=3)return ItemStack.EMPTY;')
change('''  }else if(slot==1&&(s.isEmpty()||EnergyTool.capacity(s)>0)){
   energy=s.copy();sync();
  }''',
'''  }else if(slot==1&&(s.isEmpty()||EnergyTool.capacity(s)>0)){
   energy=s.copy();sync();
  }else if(slot==3&&(s.isEmpty()||b392IsSpeed(s))){
   b392Speed=s.isEmpty()?ItemStack.EMPTY:s.copyWithCount(Math.min(16,s.getCount()));
   sync();
  }''')
change('return slot==0?s.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()):slot==1&&EnergyTool.capacity(s)>0;',
       'return slot==0?s.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()):slot==1?EnergyTool.capacity(s)>0:slot==3&&b392IsSpeed(s);')
change('blueprint=energy=missing=ItemStack.EMPTY;index=completed=0;sync();',
       'blueprint=energy=missing=b392Speed=ItemStack.EMPTY;index=completed=0;sync();')
assert "B391_PRINTER_STATE_CACHE" in s and "B392_AIR_ZERO_COST" in s
be.write_text(s,encoding="utf-8")

menu=J/"menu/NetworkPrinterMenu.java"
m=menu.read_text(encoding="utf-8")
assert m.count("if(slotId>=2&&slotId<27)return;")==1
assert m.count("if(slotId>=2&&slotId<27)return ItemStack.EMPTY;")==1
m=m.replace("if(slotId>=2&&slotId<27)return;",
            "if(slotId>=2&&slotId<27&&slotId!=3)return;",1)
m=m.replace("if(slotId>=2&&slotId<27)return ItemStack.EMPTY;",
            "if(slotId>=2&&slotId<27&&slotId!=3)return ItemStack.EMPTY;",1)
# B395 robust constructor insertion.
start=m.index(" public NetworkPrinterMenu(")
opening=m.index("{",start)
depth=0
closing=-1
for index in range(opening,len(m)):
 if m[index]=="{":depth+=1
 elif m[index]=="}":
  depth-=1
  if depth==0:
   closing=index
   break
assert closing>opening and m.count("slots.set(3,")==0
m=m[:closing]+'''  // B392 Speed Upgrade slot, never expose Missing slot.
  slots.set(3,new Slot(be,3,62,18){
   @Override public boolean mayPlace(ItemStack stack){return be.canPlaceItem(3,stack);}
  });
 '''+m[closing:]
menu.write_text(m,encoding="utf-8")

gui=J/"client/NetworkPrinterScreen.java"
g=gui.read_text(encoding="utf-8")
def guiChange(old,new):
 global g
 assert g.count(old)==1,("B392_PRINTER_GUI_DRIFT",old[:90],g.count(old))
 g=g.replace(old,new,1)
guiChange('public final class NetworkPrinterScreen extends ContainerScreen {',
'''public final class NetworkPrinterScreen extends ContainerScreen {
 private net.minecraft.client.gui.components.Button b392SkipButton;''')
guiChange('''    Component.literal("STOP / RESET"),b->send(2)).bounds(x,y+77,94,19).build());''',
'''    Component.literal("STOP / RESET"),b->send(2)).bounds(x,y+77,94,19).build());
  // B392_SKIP_BUTTON: shown only with a server-synced missing ghost item.
  b392SkipButton=addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
    Component.literal("SKIP BLOCK"),b->send(3)).bounds(x,y+99,94,19).build());''')
guiChange('''  var be=device();
  if(be!=null){''',
'''  var be=device();
  if(b392SkipButton!=null)
   b392SkipButton.visible=!getMenu().getSlot(2).getItem().isEmpty();
  if(be!=null){''')
for old,new in (
 ('g.fill(x2,y,x2+107,y+167,','g.fill(x2,y,x2+107,y+192,'),
 ('g.fill(x2+2,y+2,x2+105,y+165,','g.fill(x2+2,y+2,x2+105,y+190,'),
 ('x2+5,y+101,','x2+5,y+123,'),
 ('x2+5,y+108,','x2+5,y+130,'),
 ('x2+5,y+120,','x2+5,y+146,'),
 ('x2+100,y+130,','x2+100,y+156,'),
 ('x2+5+fill,y+130,','x2+5+fill,y+156,'),
 ('x2+5,y+134,','x2+5,y+160,'),
 ('x2+5,y+147,','x2+5,y+177,')
):
 assert old in g,("B392_GUI_STATUS_LAYOUT_DRIFT",old)
 g=g.replace(old,new)
gui.write_text(g,encoding="utf-8")
print("B392_PRINTER_SPEED_SKIP_AIR_PASS")
