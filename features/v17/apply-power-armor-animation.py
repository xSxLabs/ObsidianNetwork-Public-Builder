#!/usr/bin/env python3
"""Clean v1.7: vanilla model-driven 4-step world animation, two-block suit height."""
import json,os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def edit(rel,old,new):
 p=j/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,f"ANIMATION SOURCE DRIFT {rel} {s.count(old)}"
 p.write_text(s.replace(old,new,1),encoding="utf-8")
edit("powerarmor/ArmorStationBlock.java",
 ''' private static final MapCodec<ArmorStationBlock> CODEC=simpleCodec(ArmorStationBlock::new);
 public ArmorStationBlock(Properties p){super(p);}''',
 ''' // Four visual stages (0 closed, 3 fully open).
 public static final net.minecraft.world.level.block.state.properties.IntegerProperty FRAME =
   net.minecraft.world.level.block.state.properties.IntegerProperty.create("frame",0,3);
 public static final net.minecraft.world.level.block.state.properties.BooleanProperty FILLED =
   net.minecraft.world.level.block.state.properties.BooleanProperty.create("filled");
 private static final MapCodec<ArmorStationBlock> CODEC=simpleCodec(ArmorStationBlock::new);
 public ArmorStationBlock(Properties p){
  super(p);registerDefaultState(stateDefinition.any().setValue(FRAME,0).setValue(FILLED,false));
 }
 @Override protected void createBlockStateDefinition(
   net.minecraft.world.level.block.state.StateDefinition.Builder<net.minecraft.world.level.block.Block,BlockState> b){
  b.add(FRAME,FILLED);
 }''')
edit("powerarmor/ArmorStationBlock.java",
 ''' @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new ArmorStationBlockEntity(pos,state);
 }''',
 ''' @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new ArmorStationBlockEntity(pos,state);
 }
 @Nullable @Override public <T extends BlockEntity>
 net.minecraft.world.level.block.entity.BlockEntityTicker<T> getTicker(Level level,BlockState state,
   net.minecraft.world.level.block.entity.BlockEntityType<T> type){
  if(level.isClientSide())return null;
  return createTickerHelper(type,dev.obsidiannetwork.registry.ModBlockEntities.ARMOR_STATION.get(),
    ArmorStationBlockEntity::serverTick);
 }''')
edit("powerarmor/ArmorStationBlock.java",
 '''  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;''',
 '''  if(!(level.getBlockEntity(pos) instanceof ArmorStationBlockEntity station))return InteractionResult.PASS;
  if(station.isAnimating())return InteractionResult.FAIL;''')
edit("powerarmor/ArmorStationBlock.java",
 '''  station.clear();
  for(int i=0;i<4;i++)p.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i).copy());''',
 '''  station.clear();
  station.startOpen();
  for(int i=0;i<4;i++)p.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i).copy());''')
edit("powerarmor/PowerArmorCommands.java",
 '''  for(int i=0;i<4;i++)stand.put(i,worn.get(i));
  for(int i=0;i<4;i++)p.setItemSlot''',
 '''  for(int i=0;i<4;i++)stand.put(i,worn.get(i));
  stand.startClose();
  for(int i=0;i<4;i++)p.setItemSlot''')
edit("powerarmor/ArmorStationBlockEntity.java",
 ''' private final ItemStack[] suit={ItemStack.EMPTY,ItemStack.EMPTY,ItemStack.EMPTY,ItemStack.EMPTY};''',
 ''' private final ItemStack[] suit={ItemStack.EMPTY,ItemStack.EMPTY,ItemStack.EMPTY,ItemStack.EMPTY};
 private int animationTicks=0;
 private boolean opening=false;
 public boolean isAnimating(){return animationTicks>0;}
 public void startOpen(){animationTicks=20;opening=true;draw(true,1);setChanged();}
 public void startClose(){animationTicks=20;opening=false;draw(true,3);setChanged();}
 private void draw(boolean filled,int frame){
  if(level==null||level.isClientSide())return;
  var old=level.getBlockState(worldPosition);
  if(!(old.getBlock() instanceof ArmorStationBlock))return;
  var next=old.setValue(ArmorStationBlock.FILLED,filled)
    .setValue(ArmorStationBlock.FRAME,Math.max(0,Math.min(3,frame)));
  if(!old.equals(next))level.setBlock(worldPosition,next,3);
 }
 public static void serverTick(net.minecraft.world.level.Level level,BlockPos pos,BlockState state,ArmorStationBlockEntity be){
  if(be.animationTicks<=0)return;
  int progress=20-be.animationTicks;
  int frame=be.opening?Math.min(3,1+progress/6):Math.max(0,3-progress/6);
  be.draw(true,frame);
  be.animationTicks--;
  if(be.animationTicks==0)be.draw(be.occupied(),0);
  be.setChanged();
 }''')
edit("powerarmor/ArmorStationBlockEntity.java",
 '''  suit[i]=stack.copy();setChanged();''',
 '''  suit[i]=stack.copy();setChanged();
  if(!isAnimating())draw(occupied(),0);''')
edit("powerarmor/ArmorStationBlockEntity.java",
 '''  suit[i]=ItemStack.EMPTY;
  setChanged();
  return current;''',
 '''  suit[i]=ItemStack.EMPTY;
  setChanged();
  if(!isAnimating())draw(occupied(),0);
  return current;''')
edit("powerarmor/ArmorStationBlockEntity.java",
 '''  for(int i=0;i<4;i++)suit[i]=ItemStack.EMPTY;
  setChanged();''',
 '''  for(int i=0;i<4;i++)suit[i]=ItemStack.EMPTY;
  setChanged();
  if(!isAnimating())draw(false,0);''')
edit("powerarmor/ArmorStationBlockEntity.java",
 '''  out.store("armor_suit",ItemStack.OPTIONAL_CODEC.listOf(),snapshot());''',
 '''  out.store("armor_suit",ItemStack.OPTIONAL_CODEC.listOf(),snapshot());
  out.putInt("power_armor_anim",animationTicks);
  out.putBoolean("power_armor_opening",opening);''')
edit("powerarmor/ArmorStationBlockEntity.java",
 '''  for(int i=0;i<4;i++)suit[i]=i<list.size()?list.get(i).copy():ItemStack.EMPTY;''',
 '''  for(int i=0;i<4;i++)suit[i]=i<list.size()?list.get(i).copy():ItemStack.EMPTY;
  animationTicks=Math.max(0,Math.min(20,in.getIntOr("power_armor_anim",0)));
  opening=in.getBooleanOr("power_armor_opening",false);''')

# Build a model as a full humanoid suit rising two Minecraft blocks
# above its base, not a one-block iron cube. Arm panels swing out in frames.
# No special client renderer: vanilla blockstates synchronize to all players.
def cuboid(x1,y1,z1,x2,y2,z2,texture):
 face={"texture":"#"+texture}
 return {"from":[x1,y1,z1],"to":[x2,y2,z2],"faces":{
   side:dict(face) for side in ("north","south","east","west","up","down")}}
def model(filled,frame):
 cubes=[cuboid(1,0,1,15,2,15,"metal"),
        cuboid(2,2,7,3,31,9,"metal"),cuboid(13,2,7,14,31,9,"metal")]
 if filled:
  out=(0,1,3,5)[frame]
  lift=(0,0,2,4)[frame]
  cubes.extend([
   cuboid(4,2,5,7,13,11,"red"),cuboid(9,2,5,12,13,11,"red"),
   cuboid(4,13,5,12,25,12,"red"),
   cuboid(5,24+lift,5,11,28+lift,11,"red"),
   cuboid(6,25+lift,4,10,28+lift,5,"gold"),
   cuboid(7,18,3,9,20,5,"reactor"),
   cuboid(1-out,15,6,4-out,25,12,"red"),
   cuboid(12+out,15,6,15+out,25,12,"red"),
   cuboid(1-out,24,5,4-out,26,12,"gold"),
   cuboid(12+out,24,5,15+out,26,12,"gold")])
 return {"parent":"minecraft:block/block",
         "textures":{"metal":"minecraft:block/netherite_block",
                     "red":"minecraft:block/redstone_block",
                     "gold":"minecraft:block/gold_block",
                     "reactor":"minecraft:block/sea_lantern",
                     "particle":"minecraft:block/netherite_block"},
         "elements":cubes}
def put(path,d):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
states={}
for filled in (False,True):
 for frame in range(4):
  name=f"armor_station_{'suit' if filled else 'empty'}_{frame}"
  states[f"filled={str(filled).lower()},frame={frame}"]={"model":"obsidiannetwork:block/"+name}
  put(res/"models/block"/(name+".json"),model(filled,frame))
put(res/"blockstates/armor_station.json",{"variants":states})
put(res/"models/item/armor_station.json",{"parent":"obsidiannetwork:block/armor_station_empty_0"})
print("CLEAN_V17_ANIMATION_PASS: original 4-frame animated 2-block suit; backup/exit stable")
