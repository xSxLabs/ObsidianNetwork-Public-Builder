#!/usr/bin/env python3
"""B1154: self-contained netherite multitool, no PowerArmor/entry changes."""
import os,json,math
from pathlib import Path
from PIL import Image,ImageDraw
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
main=J/"ObsidianNetwork.java"
s=main.read_text()
anchor='   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_MICRO_MG ='
assert s.count(anchor)==1
s=s.replace(anchor,'''   public static final DeferredItem<dev.obsidiannetwork.multitool.MultitoolItem> MULTITOOL =
      ITEMS.registerItem("multitool",p -> new dev.obsidiannetwork.multitool.MultitoolItem(p.durability(6093)));
'''+anchor,1)
creative='            output.accept((ItemLike)POWER_CARD_MICRO_MG.get());'
assert s.count(creative)==1
s=s.replace(creative,creative+chr(10)+'            output.accept((ItemLike)MULTITOOL.get());',1)
main.write_text(s)
p=J/"multitool/MultitoolItem.java"
p.parent.mkdir(parents=True,exist_ok=True)
assert not p.exists()
p.write_text(r'''package dev.obsidiannetwork.multitool;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.Level;
import net.minecraft.world.item.component.Tool;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.entity.LivingEntity;

/** Pick, axe and shovel in one tool; only connected ores or leaf-bearing trees chain. */
public final class MultitoolItem extends Item {
 private static final int ORE_LIMIT=64, LOG_LIMIT=192, LEAF_LIMIT=256;
 private static final ThreadLocal<Boolean> CHAIN=ThreadLocal.withInitial(()->false);
 public MultitoolItem(Properties properties){
  super(ToolMaterial.NETHERITE.applyToolProperties(properties,BlockTags.MINEABLE_WITH_PICKAXE,8.0F,-3.0F,0.0F));
 }
 private static boolean ore(BlockState s){
  return s.is(net.minecraft.tags.BlockTags.create(net.minecraft.resources.Identifier.fromNamespaceAndPath("c","ores")))
    || s.is(net.minecraft.tags.BlockTags.create(net.minecraft.resources.Identifier.fromNamespaceAndPath("forge","ores")))
    || net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath().endsWith("_ore")
    || net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath().equals("ancient_debris");
 }
 private static boolean log(BlockState s){
  return s.is(BlockTags.LOGS)||s.is(BlockTags.LOGS_THAT_BURN);
 }
 private static boolean leaves(BlockState s){return s.is(BlockTags.LEAVES);}
 private static boolean mineable(BlockState s){
  return s.is(BlockTags.MINEABLE_WITH_PICKAXE)||s.is(BlockTags.MINEABLE_WITH_AXE)||s.is(BlockTags.MINEABLE_WITH_SHOVEL);
 }
 @Override public float getDestroySpeed(ItemStack stack,BlockState state){
  return mineable(state)?9.0F:super.getDestroySpeed(stack,state);
 }
 @Override public boolean isCorrectToolForDrops(ItemStack stack,BlockState state){
  return mineable(state)||super.isCorrectToolForDrops(stack,state);
 }
 @Override public InteractionResult useOn(UseOnContext ctx){
  Level world=ctx.getLevel();
  BlockPos pos=ctx.getClickedPos();
  BlockState state=world.getBlockState(pos);
  if(ctx.getPlayer()==null)return InteractionResult.PASS;
  BlockState target=null;
  if((state.is(Blocks.GRASS_BLOCK)||state.is(Blocks.DIRT)||state.is(Blocks.COARSE_DIRT)
       ||state.is(Blocks.PODZOL)||state.is(Blocks.MYCELIUM)||state.is(Blocks.ROOTED_DIRT))
      &&ctx.getClickedFace()!=Direction.DOWN
      &&world.getBlockState(pos.above()).isAir())
   target=Blocks.DIRT_PATH.defaultBlockState();
  else if(log(state)){
   Block stripped=net.minecraft.world.level.block.Blocks.STRIPPED_OAK_LOG;
   String name=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
   if(!name.startsWith("stripped_")&&(name.endsWith("_log")||name.endsWith("_wood")||name.endsWith("_stem")||name.endsWith("_hyphae"))){
    var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock());
    stripped=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getValue(net.minecraft.resources.Identifier.fromNamespaceAndPath(id.getNamespace(),"stripped_"+name));
   }else stripped=null;
   if(stripped==Blocks.AIR)stripped=null;
   if(stripped!=null){
    target=stripped.defaultBlockState();
    if(state.hasProperty(RotatedPillarBlock.AXIS)&&target.hasProperty(RotatedPillarBlock.AXIS))
     target=target.setValue(RotatedPillarBlock.AXIS,state.getValue(RotatedPillarBlock.AXIS));
   }
  }
  if(target==null)return InteractionResult.PASS;
  if(!world.isClientSide()){
   world.setBlock(pos,target,11);
   ctx.getItemInHand().hurtAndBreak(1,(ServerLevel)world,(ServerPlayer)ctx.getPlayer(),i->{});
  }
  return InteractionResult.SUCCESS;
 }
 @Override public boolean mineBlock(ItemStack stack,Level level,BlockState state,BlockPos pos,LivingEntity miner){
  boolean result=super.mineBlock(stack,level,state,pos,miner);
  if(level.isClientSide()||CHAIN.get()||!(miner instanceof ServerPlayer player)
      ||player.isShiftKeyDown()||player.isCreative()||stack.isEmpty())return result;
  boolean ores=ore(state),logs=log(state);
  if(!ores&&!logs)return result;
  ServerLevel server=(ServerLevel)level;
  if(logs&&!hasLeaves(server,pos))return result;
  CHAIN.set(true);
  try{
   Set<BlockPos> seen=new HashSet<>();
   ArrayDeque<BlockPos> queue=new ArrayDeque<>();
   queue.add(pos.immutable());seen.add(pos.immutable());
   int count=0,limit=ores?ORE_LIMIT:LOG_LIMIT;
   while(!queue.isEmpty()&&count<limit&&!stack.isEmpty()){
    BlockPos current=queue.removeFirst();
    for(int dx=-1;dx<=1;dx++)for(int dy=-1;dy<=1;dy++)for(int dz=-1;dz<=1;dz++){
     if(dx==0&&dy==0&&dz==0)continue;
     BlockPos next=current.offset(dx,dy,dz);
     if(Math.abs(next.getX()-pos.getX())>12||Math.abs(next.getY()-pos.getY())>32
         ||Math.abs(next.getZ()-pos.getZ())>12||!seen.add(next))continue;
     BlockState neighbor=server.getBlockState(next);
     if(!(ores?ore(neighbor):log(neighbor)))continue;
     queue.add(next);count++;
     if(!player.gameMode.destroyBlock(next))return result;
     if(count>=limit||stack.isEmpty())break;
    }
   }
   if(logs)clearLeaves(server,pos);
  }finally{CHAIN.remove();}
  return result;
 }
 private static boolean hasLeaves(ServerLevel level,BlockPos origin){
  for(int y=0;y<=12;y++)for(int x=-3;x<=3;x++)for(int z=-3;z<=3;z++)
   if(leaves(level.getBlockState(origin.offset(x,y,z))))return true;
  return false;
 }
 private static void clearLeaves(ServerLevel level,BlockPos origin){
  int removed=0;
  for(int y=-2;y<=24&&removed<LEAF_LIMIT;y++)
   for(int x=-8;x<=8&&removed<LEAF_LIMIT;x++)
    for(int z=-8;z<=8&&removed<LEAF_LIMIT;z++){
     BlockPos at=origin.offset(x,y,z);
     if(leaves(level.getBlockState(at))){
      level.destroyBlock(at,true);
      removed++;
     }
    }
 }
}
''')
recipe=R/"data/obsidiannetwork/recipe/multitool.json"
recipe.parent.mkdir(parents=True,exist_ok=True)
assert not recipe.exists()
recipe.write_text(json.dumps({"type":"minecraft:crafting_shaped","pattern":["SAP"," N "," N "],"key":{"S":"minecraft:netherite_shovel","A":"minecraft:netherite_pickaxe","P":"minecraft:netherite_axe","N":"minecraft:netherite_ingot"},"result":{"id":"obsidiannetwork:multitool","count":1}},indent=2)+"\n")
for lang in ("de_de","en_us"):
 f=A/f"lang/{lang}.json";d=json.loads(f.read_text());d["item.obsidiannetwork.multitool"]="Multitool";f.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
# Pixel-art 32x32 albedo, violet edge accents. Genuine item model with depth.
tex=A/"textures/item/multitool.png";tex.parent.mkdir(parents=True,exist_ok=True)
im=Image.new("RGBA",(32,32),(0,0,0,0));draw=ImageDraw.Draw(im)
dark="#201e2d";metal="#403d51";light="#666277";violet="#b12dff";glow="#e27aff"
draw.line([(6,29),(16,17)],fill=dark,width=6)
draw.line([(6,29),(16,17)],fill=metal,width=4)
draw.line([(7,27),(15,19)],fill=violet,width=1)
draw.polygon([(13,15),(19,11),(27,11),(30,14),(28,17),(20,16),(17,20)],fill=dark)
draw.polygon([(16,14),(20,12),(28,13),(27,15),(20,14),(18,18)],fill=metal)
draw.line([(20,12),(28,13)],fill=glow,width=2)
draw.polygon([(14,15),(10,12),(6,13),(3,18),(4,22),(8,18),(12,17)],fill=dark)
draw.polygon([(11,13),(7,14),(4,20),(8,17),(12,16)],fill=metal)
draw.line([(7,15),(4,20)],fill=violet,width=2)
draw.ellipse((13,14,19,20),fill=dark,outline=violet)
im.save(tex)
model=A/"models/item/multitool.json";model.parent.mkdir(parents=True,exist_ok=True)
model.write_text(json.dumps({"parent":"minecraft:item/handheld","textures":{"layer0":"obsidiannetwork:item/multitool"}},indent=2)+"\n")
# B1162: real volumetric Minecraft item model, not a flat handheld sprite.
# Palette texture: each 4x4 tile is a solid material, referenced on every cuboid face.
palette=Image.new("RGBA",(16,16),(0,0,0,255))
palette_colors=[(22,20,34,255),(54,51,69,255),(111,103,129,255),(174,57,246,255),
                (91,26,151,255),(222,143,255,255),(38,34,51,255),(75,69,89,255),
                (17,15,27,255),(129,52,189,255),(66,63,79,255),(194,187,211,255),
                (39,26,60,255),(144,70,215,255),(29,27,43,255),(85,82,102,255)]
for tile,c in enumerate(palette_colors):
 px=(tile%4)*4;py=(tile//4)*4
 for xx in range(px,px+4):
  for yy in range(py,py+4):palette.putpixel((xx,yy),c)
palette.save(A/"textures/item/multitool_3d.png")
parts=[]
def cuboid(lo,hi,tile):
 uv=[(tile%4)*4,(tile//4)*4,(tile%4)*4+4,(tile//4)*4+4]
 parts.append({"from":lo,"to":hi,"faces":{face:{"uv":uv,"texture":"#palette"} for face in ("north","south","east","west","up","down")}})
# Slender three-dimensional grip with a diagonal stair-stepped silhouette.
cuboid([6.8,0.2,6.8],[9.2,3.2,9.2],0)
cuboid([6.5,2.5,6.5],[9.5,5.8,9.5],1)
cuboid([6.5,5.2,6.5],[9.5,8.5,9.5],1)
cuboid([6.5,8.0,6.5],[9.5,11.5,9.5],1)
cuboid([6.5,10.5,6.5],[9.5,13.3,9.5],2)
# Violet grip bands and end cap.
cuboid([6.35,1.1,6.35],[9.65,1.65,9.65],4)
cuboid([6.35,3.6,6.35],[9.65,4.05,9.65],3)
cuboid([6.35,6.0,6.35],[9.65,6.45,9.65],4)
cuboid([6.35,8.6,6.35],[9.65,9.05,9.65],3)
# Forged central hub: full thickness, dark netherite with glowing purple core.
cuboid([5.4,11.0,5.1],[10.6,14.0,10.9],0)
cuboid([6.4,11.5,4.8],[9.6,13.6,5.15],3)
cuboid([6.4,11.5,10.85],[9.6,13.6,11.2],3)
# Axe blade FRONT (+X): wide, tall, beveled stepped cutting edge.
cuboid([10.1,10.5,5.8],[12.0,15.0,10.2],1)
cuboid([11.7,9.2,6.2],[13.6,15.7,9.8],2)
cuboid([13.3,8.5,6.7],[14.6,15.9,9.3],1)
cuboid([14.4,9.3,7.0],[15.25,15.6,9.0],2)
cuboid([14.95,10.3,7.35],[15.6,14.7,8.65],11)\n# Decorative violet inlaid spine along the handle.\ncuboid([7.55,2.1,6.22],[8.45,10.8,6.5],4)\ncuboid([7.65,2.6,6.15],[8.35,10.1,6.24],3)
# Blade inlays, visible from both broad faces.
cuboid([11.8,13.7,5.55],[14.0,14.2,5.9],3)
cuboid([11.8,13.7,10.1],[14.0,14.2,10.45],3)
cuboid([12.7,10.1,5.85],[13.3,13.7,6.15],4)
# Pickaxe BACK (-X): opposite head, hooked descending point.
cuboid([3.6,12.1,6.2],[5.8,14.5,9.8],1)
cuboid([1.9,12.9,6.7],[3.9,14.2,9.3],2)
cuboid([0.6,13.1,7.0],[2.1,13.9,9.0],11)
cuboid([2.4,10.8,7.0],[3.3,13.1,9.0],1)
cuboid([3.0,9.1,7.35],[3.8,11.0,8.65],2)
cuboid([3.4,8.1,7.65],[4.1,9.4,8.35],11)
cuboid([1.8,13.0,6.4],[4.9,13.4,6.75],3)
cuboid([1.8,13.0,9.25],[4.9,13.4,9.6],3)
# The shovel function is integrated into the reinforced lower grip, not a third head.
cuboid([6.25,0.0,6.25],[9.75,0.65,9.75],2)
model.write_text(json.dumps({"textures":{"palette":"obsidiannetwork:item/multitool_3d","particle":"obsidiannetwork:item/multitool_3d"},"gui_light":"front","elements":parts,"display":{"thirdperson_righthand":{"rotation":[0,-90,55],"translation":[0,2,0],"scale":[0.7,0.7,0.7]},"thirdperson_lefthand":{"rotation":[0,90,-55],"translation":[0,2,0],"scale":[0.7,0.7,0.7]},"firstperson_righthand":{"rotation":[0,-90,55],"translation":[0.0,1.0,0.0],"scale":[0.55,0.55,0.55]},"firstperson_lefthand":{"rotation":[0,90,-55],"translation":[0.0,1.0,0.0],"scale":[0.55,0.55,0.55]},"gui":{"rotation":[30,225,0],"translation":[0,0,0],"scale":[0.82,0.82,0.82]},"ground":{"translation":[0,2,0],"scale":[0.55,0.55,0.55]},"fixed":{"rotation":[0,180,0],"scale":[0.85,0.85,0.85]}}},indent=2)+chr(10))
definition=A/"items/multitool.json";definition.parent.mkdir(parents=True,exist_ok=True)
definition.write_text(json.dumps({"model":{"type":"minecraft:model","model":"obsidiannetwork:item/multitool"}},indent=2)+"\n")
print("B1154_MULTITOOL_REGISTERED_RECIPE_TEXTURE_AND_CHAIN_MINING_PASS")
