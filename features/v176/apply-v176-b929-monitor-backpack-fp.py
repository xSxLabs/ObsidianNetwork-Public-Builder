#!/usr/bin/env python3
"""B929: four-way Power Monitor + white computer back, restore visible inventory,
reject hidden phantom slots, output-only reactor readout, black 24-color backpacks,
and first-person right-arm correction. Apply after B917; NEVER modify 3P pose.
"""
import os, json
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B929_SOURCE_DRIFT",rel,s.count(old),old[:105])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

menu="power/V176PowerTerminalMenu.java"
# The machine's 54 phantom ChestMenu slots stay permanently inert and
# offscreen. The 36 REAL player slots must remain interactive.
edit(menu,
 "  for(int slot=0;slot<slots.size();slot++){",
 "  for(int slot=0;slot<54;slot++){")
edit(menu,
 """  // Monitor contains no inventory: block PICKUP, QUICK_MOVE, SWAP, THROW,
  // CLONE, PICKUP_ALL and drag actions. Never mutate the carried item.
  return;
 }""",
 """  // Only the invisible machine grid is forbidden. Normal player inventory
  // PICKUP/SWAP/THROW must retain vanilla semantics; shift transfer to the
  // nonexistent machine inventory is still blocked by quickMoveStack().
  if(slotId>=0&&slotId<54)return;
  super.clicked(slotId,button,input,player);
 }""")

screen="client/V176PowerMonitorScreen.java"
edit(screen,
 "  int x=getLeftPos(),y=getTopPos(),h=124;",
 "  int x=getLeftPos(),y=getTopPos(),h=getImageHeight();")
edit(screen,
 "  // No player-inventory raster. All 90 slots are inert and invisible.",
 """  // The real 3x9 player inventory and 1x9 hotbar, aligned with the
  // original ChestMenu player slots 54..89. NEVER paint phantom top slots.
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?139+(i/9)*18:197);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff345869);
   g.fill(sx,sy,sx+17,sy+17,0xff203746);
  }""")
edit(screen,
 """   g.text(font,"IN "+compact(d.inputFePerTick())+" OUT "+compact(d.outputFePerTick())+
       " FE/t",8,y+9,0xffd4dfe5);""",
 """   String rate=d.type()==V176PowerMonitorRules.DeviceType.REACTOR
      ?"OUT "+compact(d.outputFePerTick())+" FE/t"
      :"IN "+compact(d.inputFePerTick())+" OUT "+compact(d.outputFePerTick())+" FE/t";
   g.text(font,rate,8,y+9,0xffd4dfe5);""")

block="power/V176PowerTerminalBlock.java"
edit(block,
 "import net.minecraft.core.BlockPos;",
 """import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Block;""")
edit(block,
 """ private static final MapCodec<V176PowerTerminalBlock> CODEC=simpleCodec(V176PowerTerminalBlock::new);
 public V176PowerTerminalBlock(Properties props){super(props);}""",
 """ private static final MapCodec<V176PowerTerminalBlock> CODEC=simpleCodec(V176PowerTerminalBlock::new);
 public static final EnumProperty<Direction> FACING=BlockStateProperties.HORIZONTAL_FACING;
 public V176PowerTerminalBlock(Properties props){
  super(props);
  registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));
 }
 @Override public BlockState getStateForPlacement(BlockPlaceContext ctx){
  return defaultBlockState().setValue(FACING,ctx.getHorizontalDirection().getOpposite());
 }
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> b){
  b.add(FACING);
 }
 @Override public BlockState rotate(BlockState state,Rotation rotation){
  return state.setValue(FACING,rotation.rotate(state.getValue(FACING)));
 }
 @Override public BlockState mirror(BlockState state,Mirror mirror){
  return state.rotate(mirror.getRotation(state.getValue(FACING)));
 }""")

state=A/"blockstates/power_terminal.json"
present=json.loads(state.read_text(encoding="utf-8"))
assert present.get("variants")=={"":{"model":"obsidiannetwork:block/power_terminal"}},("B929_MONITOR_STATE_DRIFT",present)
state.write_text(json.dumps({"variants":{
 "facing=north":{"model":"obsidiannetwork:block/power_terminal","y":0},
 "facing=east":{"model":"obsidiannetwork:block/power_terminal","y":90},
 "facing=south":{"model":"obsidiannetwork:block/power_terminal","y":180},
 "facing=west":{"model":"obsidiannetwork:block/power_terminal","y":270}
}},indent=2)+"\n",encoding="utf-8")

# Preserve B915 front exactly (north). The opposite computer face gets the
# same shape/readout layout but a white/grey color scheme, not a new symbol.
front=A/"textures/block/power_terminal_computer_front.png"
back=A/"textures/block/power_terminal_computer_back_white.png"
assert front.is_file()
with Image.open(front) as im:
 rgba=im.convert("RGBA")
 white=Image.new("RGBA",rgba.size)
 src=rgba.load(); out=white.load()
 for y in range(rgba.height):
  for x in range(rgba.width):
   r,g,b,a=src[x,y]
   lum=(r*0.3+g*0.59+b*0.11)
   t=int(max(120,min(247,242-0.52*lum)))
   out[x,y]=(t,t,min(255,t+2),a)
 white.save(back,optimize=True)
model=A/"models/block/power_terminal.json"
data=json.loads(model.read_text(encoding="utf-8"))
assert data["textures"]["north"]=="obsidiannetwork:block/power_terminal_computer_front"
data["textures"]["south"]="obsidiannetwork:block/power_terminal_computer_back_white"
model.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")

# B932: Restore the ORIGINAL 24 Backpack armor-matched palettes exactly
# as generated by generate-v176-backpack-24-models.py. No recoloring here.
# All item models, block models, recipes, storage and GUI remain unchanged.

# 1P is independent of 3P. The real arm rendering callback, rather than
# the maybe-skipped empty-hand render callback, must advance the MG extension.
gun="client/V176MicroMgVisualClient.java"
edit(gun,
 "  float progress=deploymentProgress(player.getId());",
 "  float progress=extension(player.getId(),armedForAttack(player));")
edit(gun,
 "  pose.translate(-0.05F,0.10F,-0.18F);",
 "  pose.translate(-0.25F,0.10F,-0.18F);")

m=(J/menu).read_text()
s=(J/screen).read_text()
b=(J/block).read_text()
assert "for(int slot=0;slot<54;slot++)" in m
assert "if(slotId>=0&&slotId<54)return;" in m
assert "super.clicked(slotId,button,input,player);" in m
assert "return ItemStack.EMPTY;" in m
assert "int x=getLeftPos(),y=getTopPos(),h=getImageHeight();" in s
assert "String rate=d.type()==V176PowerMonitorRules.DeviceType.REACTOR" in s
assert "for(int i=0;i<36;i++)" in s
assert "ctx.getHorizontalDirection().getOpposite()" in b
assert all((A/"models/block"/f"network_backpack_mk{i}.json").is_file() for i in range(1,25))
print("B932_MONITOR_AND_FP_ORIGINAL_24_BACKPACK_PALETTES_RESTORED_PASS")
