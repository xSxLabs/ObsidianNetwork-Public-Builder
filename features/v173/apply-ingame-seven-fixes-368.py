#!/usr/bin/env python3
"""B368: one integrated v1.7.3 ingame fix set.

- JEI/TMI ingredient variants: matching-only normalization of custom name, FE,
  and damage, preserving the exact descriptor and transactional rollback.
- Missing ingredient: leave its crafting slot empty rather than aborting the
  entire JEI transfer; present ingredients still move.
- MAP uses a fixed configurable world Start-Y and Depth for all columns,
  deterministic bounded XYZ LOD, and tabletop-aligned whole-volume projection.
- NETWORK shows only its 3D blocks (discard stale TextDisplay status).
- Wheel labels share sector angular geometry with selection and highlighting.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(path,old,new):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B368_SOURCE_DRIFT",path,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def file(path):return J/path

# ---- AE2-style JEI recipe transfer: recipe identity != storage identity ----
menu=file("menu/StorageTerminalMenu.java")
s=menu.read_text(encoding="utf-8")
start="public void applyJeiRecipeGrid("
end="private static Ingredient[] recipeIngredients3x3("
assert s.count(start)==s.count(end)==1,("B368_JEI_BOUNDARY_DRIFT",s.count(start),s.count(end))
a=s.index(start);b=s.index(end,a)
section=s[a:b]
# Bytecode of green B367 verifies two Ingredient.test calls: one for exact
# reconstructed NETWORK candidates, one for player inventory fallback.
tests=list(re.finditer(r'(?P<receiver>\b[A-Za-z_]\w*)\.test\s*\((?P<arg>[A-Za-z_]\w*)\)',section))
assert len(tests)==2,("B368_JEI_INGREDIENT_TEST_DRIFT",[(m.group(0)) for m in tests])
for m in reversed(tests):
 section=section[:m.start()]+f'xsxRecipeIngredientAccepts({m.group("receiver")},{m.group("arg")})'+section[m.end():]
# Bytecode of green B367 verifies EXACTLY one best-inventory-slot <0 early
# return inside the 9-ingredient planning loop. Continue means empty slot;
# commit phase already skips ItemStack.EMPTY and preserves exact extraction.
missing=re.compile(r'if\s*\(\s*[A-Za-z_]\w*\s*<\s*0\s*\)\s*(?:\{\s*)?return\s*;\s*(?:\})?')
all_missing=list(missing.finditer(section))
assert len(all_missing)==1,("B368_JEI_MISSING_SLOT_DRIFT",[m.group(0) for m in all_missing])
m=all_missing[0]
section=section[:m.start()]+'''// B368_PARTIAL_INGREDIENTS: do not abort for one unavailable ingredient.
                     // The planned ItemStack.EMPTY remains untouched for this slot.
                     continue;'''+section[m.end():]
assert "reservedNet.merge(bestKey, 1L, Math::addExact);" in section
assert "runtime.storage().extract(desc[ixx].key(), 1L)" in section
assert "runtime.storage().insertExact(desc[ixxx].key(), desc[ixxx].canonicalPayload(), 1L)" in section
helper=''' // B368_AE_RECIPE_VARIANTS: never mutate the real item or its descriptor.
 // First ask the actual recipe ingredient (including modded data predicates).
 // Only if that rejects, try a TEMPORARY copy without mutable presentation,
 // stored FE or wear. Exact network extraction still uses the full ItemKey.
 private static boolean xsxRecipeIngredientAccepts(Ingredient ingredient,ItemStack candidate){
  if(candidate==null||candidate.isEmpty())return false;
  if(ingredient.test(candidate))return true;
  ItemStack simple=candidate.copy();
  simple.remove(net.minecraft.core.component.DataComponents.CUSTOM_NAME);
  simple.remove(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get());
  simple.remove(net.minecraft.core.component.DataComponents.DAMAGE);
  return ingredient.test(simple);
 }
 '''
s=s[:a]+helper+section+s[b:]
menu.write_text(s,encoding="utf-8")

# ---- JEI's CLIENT preview must not reject partially available recipes ----
# The original preview compares exact ItemKey and sends a missing-slot error
# BEFORE the user can click. The server's safe transactional planner must be
# the sole authority: allow click even when some components/slots are absent.
jei=file("compat/jei/NetworkStorageRecipeTransferHandler.java")
client_code=jei.read_text(encoding="utf-8")
a=client_code.index("public IRecipeTransferError transferRecipe(")
b=client_code.index("private static List<IRecipeSlotView> findMissingSlots(",a)
section=client_code[a:b]
pattern=re.compile(r'if\s*\(!doTransfer\)\s*\{\s*List<IRecipeSlotView>\s+missing\s*=\s*findMissingSlots\(recipeSlots,\s*player\);\s*return\s+!missing\.isEmpty\(\)\s*\?\s*this\.helper\.createUserErrorForMissingSlots\(.*?\)\s*:\s*null\s*;',re.S)
match=pattern.search(section)
assert match is not None,("B368_JEI_CLIENT_PREVIEW_DRIFT",section[:1000])
replacement='''if (!doTransfer) {
          // B368_JEI_PARTIAL_PREVIEW: never block an intentionally partial
          // craft transfer; the server checks recipes and available inventory.
          return null;'''
section=section[:match.start()]+replacement+section[match.end():]
assert "ClientPacketDistributor.sendToServer(new JeiCraftTransferPayload(" in section
client_code=client_code[:a]+section+client_code[b:]
jei.write_text(client_code,encoding="utf-8")

# ---- Persist and synchronize the MAP world Y start independently of height ----
be="blockentity/NetworkDeviceBlockEntity.java"
change(be,
 ' public String holoMode(){return holoMode;}',
 ''' // B368_MAP_START_WORLD_Y: default above local terminal; persisted thereafter.
 private int holoMapStartY=Integer.MIN_VALUE;
 public int holoMapStartY(){return holoMapStartY==Integer.MIN_VALUE?
                         worldPosition.getY()+16:holoMapStartY;}
 public String holoMode(){return holoMode;}''')
change(be,
 'int depth,int radius){',
 'int depth,int radius,int startY){')
change(be,
 'holoDepth=Math.max(1,Math.min(32,depth));holoRadius=Math.max(1,Math.min(12,radius));',
 '''holoDepth=Math.max(1,Math.min(128,depth));holoRadius=Math.max(1,Math.min(12,radius));
  holoMapStartY=Math.max(level.getMinY(),Math.min(level.getMaxY()-1,startY));''')
change(be,
 'out.putInt("holo_radius",holoRadius);',
 'out.putInt("holo_radius",holoRadius);out.putInt("holo_start_y",holoMapStartY);')
change(be,
 'holoDepth=Math.max(1,Math.min(32,in.getIntOr("holo_depth",5)));',
 'holoDepth=Math.max(1,Math.min(128,in.getIntOr("holo_depth",5)));')
change(be,
 'holoRadius=Math.max(1,Math.min(12,in.getIntOr("holo_radius",1)));',
 '''holoRadius=Math.max(1,Math.min(12,in.getIntOr("holo_radius",1)));
  holoMapStartY=in.getIntOr("holo_start_y",Integer.MIN_VALUE);''')
# Previously restored server status TextDisplay entities overlay the NETWORK
# geometry. MAP and NETWORK are both block-only modes; CUSTOM alone owns text.
change(be,'if("map".equals(holoMode)){',
          'if("map".equals(holoMode)||"network".equals(holoMode)){')

payload="network/HologramConfigPayload.java"
change(payload,'int width,int height,int depth,int radius)',
                'int width,int height,int depth,int radius,int startY)')
change(payload,'buf.writeInt(p.depth());buf.writeInt(p.radius());',
               'buf.writeInt(p.depth());buf.writeInt(p.radius());buf.writeInt(p.startY());')
change(payload,'buf.readInt(),buf.readInt()));',
               'buf.readInt(),buf.readInt(),buf.readInt()));')
change(payload,
 'be.configure(player,p.mode(),p.text(),p.color(),p.width(),p.height(),p.depth(),p.radius());',
 'be.configure(player,p.mode(),p.text(),p.color(),p.width(),p.height(),p.depth(),p.radius(),p.startY());')

screen="client/HologramConfigScreen.java"
change(screen,'private EditBox content,color,size,heightInput,radius;',
              'private EditBox content,color,size,heightInput,radius,startY,depthInput;')
change(screen,
 '  heightInput=make(bx+160,by+85,85,"Height above table",be==null?"1":""+be.holoHeight(),3);',
 '''  heightInput=make(bx+160,by+85,85,"Height above table",be==null?"1":""+be.holoHeight(),3);
  // B368_MAP_GUI_Y_DEPTH: only MAP exposes a fixed world vertical slice.
  startY=make(bx+12,by+127,85,"Start world Y",be==null?"80":""+be.holoMapStartY(),4);
  depthInput=make(bx+108,by+127,85,"Depth blocks",be==null?"32":""+be.holoDepth(),3);''')
change(screen,
 '  radius.visible=map;radius.active=map;',
 '''  radius.visible=map;radius.active=map;
  startY.visible=map;startY.active=map;
  depthInput.visible=map;depthInput.active=map;''')
change(screen,
 's,val(heightInput,1,1,32),s,r));',
 's,val(heightInput,1,1,32),val(depthInput,32,1,128),r,val(startY,80,-64,512)));')
change(screen,
 '   g.text(font,"3D terrain map - automatic size and proportions",bx+12,by+126,0xffd3e4f1);',
 '   g.text(font,"START WORLD Y     DEPTH (BLOCKS)",bx+12,by+112,0xffd3e4f1);')
change(screen,
 '   g.text(font,"Only already loaded chunks will be sampled.",bx+12,by+144,0xffa9c6d5);',
 '   g.text(font,"Fixed Y slice; loaded chunks only.",bx+12,by+163,0xffa9c6d5);')

renderer="client/V173WorldGhostRenderer.java"
# Render real 3D network ONLY, no fallback floating text; CUSTOM retains text.
change(renderer,
 '   if("network".equals(be.holoMode()))networkProjection(mc,ev,cam,mapTerminal,be);',
 '''   if("network".equals(be.holoMode())){
    // B368_NETWORK_NO_STATUS_TEXT: 3D cables/importers/exporters only.
    networkProjection(mc,ev,cam,mapTerminal,be);
    return;
   }''')
p=file(renderer);s=p.read_text(encoding="utf-8")
a=s.index(" // V173_VOLUME_MAP_327: genuine exposed blocks")
b=s.index(" private static net.minecraft.client.multiplayer.ClientLevel portalWorld;",a)
# A fixed Y interval is used for EVERY column, not a variable
# surfaceHeight[ix][iz]-depth that produces broken hanging fragments.
volume=r''' // B368_MAP_FIXED_VOLUME: true blockstates from a uniform world Y slice.
 // Project the entire volume ABOVE the table at HEIGHT 1; do not use
 // independent depth limits per column, fake stone skirts, or surface-only LOD.
 private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,
                                                   NetworkDeviceBlockEntity be){
  java.util.ArrayList<MapVoxel> out=new java.util.ArrayList<>();
  if(t==null||mc.level==null)return out;
  final int radiusChunks=Math.max(1,Math.min(12,be.holoRadius()));
  final int radius=16*radiusChunks, side=2*radius+1;
  final int fromY=Math.max(mc.level.getMinY(),
       Math.min(mc.level.getMaxY()-1,be.holoMapStartY()));
  final int depth=Math.max(1,Math.min(128,be.holoDepth()));
  final int bottomY=Math.max(mc.level.getMinY(),fromY-depth+1);
  final int xzStep=Math.max(1,(side+27)/28);
  final int columns=(side+xzStep-1)/xzStep;
  // <=4096 sampled cells, evenly budgeted ACROSS the complete XYZ volume.
  final int layers=Math.max(1,Math.min(12,4096/(columns*columns)));
  final int yStep=Math.max(1,(fromY-bottomY+layers)/layers);
  final double footprint=2.5D+radiusChunks*1.25D;
  final double perBlock=footprint/side;
  final double xzSize=xzStep*perBlock;
  final double originX=t.getX()+.5D-footprint/2D;
  final double originZ=t.getZ()+.5D-footprint/2D;
  // Position once, after sampling: the bottommost real model rests exactly
  // on the tabletop at HEIGHT=1; height steps translate by +1 whole block.
  final double tabletop=t.getY()+be.holoHeight();
  for(int ix=0;ix<columns;ix++)for(int iz=0;iz<columns;iz++){
   int wx=t.getX()-radius+ix*xzStep,wz=t.getZ()-radius+iz*xzStep;
   if(!mc.level.hasChunkAt(new BlockPos(wx,fromY,wz)))continue;
   for(int layer=0;layer<layers;layer++){
    int high=fromY-layer*yStep;
    if(high<bottomY)break;
    int low=Math.max(bottomY,high-yStep+1);
    BlockPos sample=new BlockPos(wx,high,wz);
    if(!mc.level.hasChunkAt(sample))continue;
    BlockState real=mc.level.getBlockState(sample);
    if(real.isAir())continue;
    BlockState state=real.getFluidState().isEmpty()?real:
       Blocks.BLUE_STAINED_GLASS.defaultBlockState();
    out.add(new MapVoxel(state,originX+ix*xzSize,
       (low-bottomY)*perBlock,originZ+iz*xzSize,
       xzSize,(high-low+1)*perBlock,xzSize));
   }
  }
  if(out.isEmpty())return out;
  // B368_MAP_TABLETOP_CALIBRATION: shift the lowest drawn model, not the
  // sampled terrain reference, avoiding the reported 2-block floating offset.
  double lowest=Double.POSITIVE_INFINITY;
  for(MapVoxel voxel:out)lowest=Math.min(lowest,voxel.y());
  double shift=tabletop-lowest;
  java.util.ArrayList<MapVoxel> aligned=new java.util.ArrayList<>(out.size());
  for(MapVoxel voxel:out)
   aligned.add(new MapVoxel(voxel.state(),voxel.x(),voxel.y()+shift,
      voxel.z(),voxel.sx(),voxel.sy(),voxel.sz()));
  return aligned;
 }

'''
s=s[:a]+volume+s[b:]
p.write_text(s,encoding="utf-8")

# ---- Wheel: labels at EXACT centers of the same 4/5 angular sectors ----
wheel="client/NetworkActionWheelClient.java"
p=file(wheel);s=p.read_text(encoding="utf-8")
old='''  for(int i=0;i<4;i++){
   int cx=x+(i==1?76:i==3?-76:0);
   int cy=y+(i==0?-76:i==2?76:0);
   String name=ACTIONS[i];
   int color=i==selected?0xffffffff:0xffbde8ee;
   g.text(mc.font,name,cx-mc.font.width(name)/2,cy-4,color);
  }'''
new='''  // B368_WHEEL_ALIGNED_LABELS: SAME angular centers as wheelSector().
  // Five slices are ordered 0 EXIT, 1 PORTAL B, 4 VISION, 2 RECALL, 3 PORTAL A.
  // Four slices preserve the original 0/1/2/3 top/right/bottom/left order.
  int[] order=hasVision?new int[]{0,1,4,2,3}:new int[]{0,1,2,3};
  for(int slot=0;slot<order.length;slot++){
   int i=order[slot];
   double angle=(2D*Math.PI*slot)/order.length;
   int cx=x+(int)Math.round(76D*Math.sin(angle));
   int cy=y-(int)Math.round(76D*Math.cos(angle));
   String name=i==4?"VISION":ACTIONS[i];
   int color=i==selected?0xffffffff:0xffbde8ee;
   g.text(mc.font,name,cx-mc.font.width(name)/2,cy-4,color);
  }'''
assert s.count(old)==1,("B368_WHEEL_LABEL_DRIFT",s.count(old))
s=s.replace(old,new,1)
# Remove the *old* Vision fixed bottom-right text (it does not match
# the 72-degree center); the new sector loop draws exactly one label.
old='''  if(hasVision){
   int ink=selected==4?0xffffffff:0xffbde8ee;
   // Both words are INSIDE the bottom-right radial wedge.
   g.text(mc.font,"VISION",x+58-mc.font.width("VISION")/2,y+48,ink);
   String state=NetworkVisionClient.active()?"ON":"OFF";
   g.text(mc.font,state,x+58-mc.font.width(state)/2,y+62,
          NetworkVisionClient.active()?0xff62ffbe:ink);
  }'''
assert s.count(old)==1,("B368_OLD_VISION_LABEL_DRIFT",s.count(old))
s=s.replace(old,"  // VISION now has one angle-matched label inside its real sector.",1)
p.write_text(s,encoding="utf-8")
for path,marker in ((menu,"B368_PARTIAL_INGREDIENTS"),(file(renderer),"B368_MAP_FIXED_VOLUME"),
                    (file(renderer),"B368_NETWORK_NO_STATUS_TEXT"),(file(wheel),"B368_WHEEL_ALIGNED_LABELS")):
 assert marker in path.read_text(encoding="utf-8")
print("V173_B368_INTEGRATED_SEVEN_FIXES_PASS")
