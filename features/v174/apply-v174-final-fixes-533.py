#!/usr/bin/env python3
"""B533: complete user-tested HUD, tank helmet refill, paste fluid and cable cap."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(rel,old,new):
 p=J/rel;s=p.read_text()
 assert s.count(old)==1,("B533_SOURCE_DRIFT",rel,old[:90],s.count(old))
 p.write_text(s.replace(old,new,1))
def make(rel,source):
 p=J/rel;assert not p.exists(),("B533_JAVA_COLLISION",rel)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
# Tiny HUD directly ABOVE vanilla armor icons. The Armor FE HUD is untouched.
p=J/"client/PowerArmorBuild98Client.java";s=p.read_text()
pattern=r'   // B530_NUTRIPASTE_SECOND_HUD:[\s\S]*?py\+10,pasteColor\);'
new=r'''   // B533_NUTRIPASTE_ARMOR_ROW: slim, transparent, above vanilla armor bar.
   var pasteHelmet=p.getItemBySlot(EquipmentSlot.HEAD);
   long pasteMb=dev.obsidiannetwork.nutrition.NutriPaste.stored(pasteHelmet);
   long pasteCap=dev.obsidiannetwork.nutrition.NutriPaste.HELMET_CAPACITY;
   double pasteFraction=Math.max(0D,Math.min(1D,pasteMb/(double)pasteCap));
   int pastePct=(int)Math.round(pasteFraction*100D);
   int pasteWidth=70,px=mc.getWindow().getGuiScaledWidth()/2-91;
   int py=mc.getWindow().getGuiScaledHeight()-66;
   int pasteColor=pasteFraction<0.15?0xffe5a880:0xff85e7b4;
   String pasteLabel="PASTE "+pastePct+"%";
   g.text(mc.font,pasteLabel,px,py,pasteColor);
   g.fill(px,py+10,px+pasteWidth,py+12,0x88435855);
   g.fill(px,py+10,px+(int)Math.round(pasteWidth*pasteFraction),
       py+12,pasteColor);'''
s,n=re.subn(pattern,lambda m:new,s,count=1)
assert n==1,("B533_NUTRI_HUD_ANCHOR",n)
p.write_text(s)
# Add persistent tooltip to every xSxLabs power helmet, including in menus.
make("nutrition/NutriPasteTooltip.java",r'''package dev.obsidiannetwork.nutrition;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import net.minecraft.network.chat.Component;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;
/** B533_HELMET_PASTE_TOOLTIP: current capacity and percentage on item hover. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class NutriPasteTooltip {
 private NutriPasteTooltip(){}
 @SubscribeEvent public static void itemTooltip(ItemTooltipEvent event){
  var stack=event.getItemStack();
  if(stack.isEmpty()||PowerArmorRuntime.tier(stack,0)<1)return;
  long stored=NutriPaste.stored(stack),max=NutriPaste.HELMET_CAPACITY;
  int pct=(int)Math.round(100D*stored/max);
  event.getToolTip().add(Component.literal(
    "NutriPaste: "+stored+" / "+max+" mB ("+pct+"%)").withStyle(style->style.withColor(0xff8dd1a7)));
 }
}
''')
# Draw an actual level meter at bottom of Nutrinator, including a 1-pixel
# min when there is paste but fill is <1/148th of a billion mB.
p=J/"client/V174NutrinatorScreen.java";s=p.read_text()
start=s.index(" private static int bar(")
end=s.index(" private static String compact(",start)
s=s[:start]+''' private static int bar(long amount,long maximum){
  if(maximum<=0L||amount<=0L)return 0;
  return Math.max(1,(int)Math.min(146L,Math.round(146D*Math.min(1D,(double)amount/maximum))));
 }
'''+s[end:]
assert "meter(g,x+12,y+130,be.guiPaste(),be.guiPasteCapacity(),0xff51dda9);" in s
s=s.replace("   meter(g,x+12,y+130,be.guiPaste(),be.guiPasteCapacity(),0xff51dda9);",
'''   // B533_NUTRINATOR_TANK_LIVE_FILL: actual current/total long ratio.
   long amt=be.guiPaste(),cap=Math.max(1L,be.guiPasteCapacity());
   int pct=(int)Math.round(100D*amt/cap);
   g.text(font,"NUTRIPASTE TANK  "+pct+"%",x+12,y+118,0xff87e4ae);
   meter(g,x+12,y+130,amt,cap,0xffaa825a);''',1)
p.write_text(s)
# All four Network Tank sizes share this one BE type. Persist the helmet stack.
change("blockentity/NetworkTankBlockEntity.java",
 " private final int capacity;private final FluidStacksResourceHandler tank;",
 ''' // B533_NETWORK_TANK_HELMET: saved slot; never exposed to fluid or item pipes.
 private final net.minecraft.world.SimpleContainer helmet=new net.minecraft.world.SimpleContainer(1){
  @Override public void setChanged(){super.setChanged();NetworkTankBlockEntity.this.setChanged();}
 };
 public net.minecraft.world.SimpleContainer helmetSlot(){return helmet;}
 private final int capacity;private final FluidStacksResourceHandler tank;''')
change("blockentity/NetworkTankBlockEntity.java",
 " public FluidStacksResourceHandler tank(){return tank;}public int capacity(){return capacity;}",
 ''' public FluidStacksResourceHandler tank(){return tank;}public int capacity(){return capacity;}
 // B533_NETWORK_TANK_HELMET_FILL: server only, actual tank drain, no paste duplication.
 public static void tick(net.minecraft.world.level.Level level,net.minecraft.core.BlockPos pos,
       net.minecraft.world.level.block.state.BlockState state,NetworkTankBlockEntity be){
  if(level.isClientSide()||level.getGameTime()%20L!=0L)return;
  var stack=be.helmet.getItem(0);
  if(stack.isEmpty()||dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(stack,0)<1)return;
  long room=dev.obsidiannetwork.nutrition.NutriPaste.HELMET_CAPACITY-
       dev.obsidiannetwork.nutrition.NutriPaste.stored(stack);
  if(room<=0)return;
  var fluid=net.neoforged.neoforge.fluids.capability.IFluidHandler.of(be.tank);
  var held=fluid.getFluidInTank(0);
  if(held.isEmpty()||held.getFluid()!=dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get())return;
  int offer=(int)Math.min(10_000L,Math.min(room,(long)held.getAmount()));
  if(offer<=0)return;
  var drained=fluid.drain(offer,net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
  if(drained.isEmpty()||drained.getFluid()!=dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get())return;
  long inserted=dev.obsidiannetwork.nutrition.NutriPaste.add(stack,drained.getAmount());
  if(inserted<drained.getAmount()){
   fluid.fill(new net.neoforged.neoforge.fluids.FluidStack(
       dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get(),
       drained.getAmount()-(int)inserted),
       net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
  }
  be.helmet.setChanged();
 }''')
change("blockentity/NetworkTankBlockEntity.java",
 'tank.serialize(out.child("tank"));}',
 '''tank.serialize(out.child("tank"));if(!helmet.getItem(0).isEmpty())out.store("xsxTankHelmet",net.minecraft.world.item.ItemStack.CODEC,helmet.getItem(0));}''')
change("blockentity/NetworkTankBlockEntity.java",
 'tank.deserialize(in.childOrEmpty("tank"));}',
 '''tank.deserialize(in.childOrEmpty("tank"));helmet.setItem(0,in.read("xsxTankHelmet",net.minecraft.world.item.ItemStack.CODEC).orElse(net.minecraft.world.item.ItemStack.EMPTY));}''')
change("block/NetworkTankBlock.java",
 "@Override protected RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}",
 '''@Override protected RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 // B533_NETWORK_TANK_AUTOFILL_TICK: shared by 64K,256K,1024K,4096K tiers.
 @Override public <T extends BlockEntity> net.minecraft.world.level.block.entity.BlockEntityTicker<T>
 getTicker(Level l,BlockState s,net.minecraft.world.level.block.entity.BlockEntityType<T> t){
  return !l.isClientSide()&&t==dev.obsidiannetwork.registry.ModBlockEntities.NETWORK_TANK.get()
   ?(world,pos,state,be)->NetworkTankBlockEntity.tick(world,pos,state,(NetworkTankBlockEntity)be):null;
 }''')
# Actual single armor slot preceding all 36 vanilla slots. Keep original grid.
change("menu/NetworkTankMenu.java",
 'addDataSlots(data);for(int r=0;r<3;r++)',
 '''addDataSlots(data);
 // B533_NETWORK_TANK_HELMET_SLOT: index zero; player indices 1..36.
 addSlot(new Slot(be.helmetSlot(),0,8,27){
  @Override public boolean mayPlace(ItemStack stack){
   return dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(stack,0)>0;
  }
  @Override public int getMaxStackSize(){return 1;}
 });
 for(int r=0;r<3;r++)''')
p=J/"menu/NetworkTankMenu.java";s=p.read_text()
m=re.search(r' @Override public ItemStack quickMoveStack\(Player p,int i\)\{[^\n]*\}',s)
assert m,("B533_TANK_QUICKMOVE_MISSING",s[-1200:])
s=s[:m.start()]+''' // B533_NETWORK_TANK_SLOT_QUICKMOVE: helmet in/out; no inventory duplication.
 @Override public ItemStack quickMoveStack(Player p,int i){
  if(i<0||i>=slots.size())return ItemStack.EMPTY;
  Slot slot=slots.get(i);if(!slot.hasItem())return ItemStack.EMPTY;
  ItemStack src=slot.getItem(),copy=src.copy();
  if(i==0){if(!moveItemStackTo(src,1,37,true))return ItemStack.EMPTY;}
  else if(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(src,0)>0){
   if(!moveItemStackTo(src,0,1,false))return ItemStack.EMPTY;
  }else if(i<=27){
   if(!moveItemStackTo(src,28,37,false))return ItemStack.EMPTY;
  }else if(!moveItemStackTo(src,1,28,false))return ItemStack.EMPTY;
  if(src.isEmpty())slot.set(ItemStack.EMPTY);else slot.setChanged();
  return copy;
 }'''+s[m.end():]
p.write_text(s)
# GUI visual slot frame with label; preserves full tank meter and inventory.
change("client/NetworkTankScreen.java",
 'g.outline(leftPos+31,topPos+27,114,16,0xFF6A6A6A);',
 '''// B533_NETWORK_TANK_HELMET_GUI: real menu slot at x8,y27.
 g.outline(leftPos+7,topPos+26,20,20,0xff568ca2);
 g.outline(leftPos+31,topPos+27,114,16,0xFF6A6A6A);''')
change("client/NetworkTankScreen.java",
 'g.text(font,title,leftPos+8,topPos+6,0xFFE0E0E0,false);',
 '''g.text(font,title,leftPos+8,topPos+6,0xFFE0E0E0,false);
 g.text(font,"H",leftPos+10,topPos+17,0xff92ddd1,false);''')
# Use identical actual cable model rather than a vanilla concrete block
# that is always the wrong color at the end of teal energy cables.
change("client/EnergyCableInputRenderer.java",
 'resolver.update(out.cap,Blocks.CYAN_CONCRETE.defaultBlockState(),DISPLAY);',
 '''resolver.update(out.cap,be.getBlockState(),DISPLAY); // B533_ACTUAL_ENERGY_CABLE_CAP_TEXTURE''')
print("B533_HUD_TOOLTIP_NUTRINATOR_TANK_HELMET_AND_CABLE_PASS")
