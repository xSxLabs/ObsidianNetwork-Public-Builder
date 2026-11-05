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
# B1166: sculpted Netherite weapon: asymmetric axe face, hooked rear pick,
# recessed violet inlays, faceted handle and per-face metallic highlights.
palette=Image.new("RGBA",(64,64),(0,0,0,255))
colors=[(17,16,25),(34,32,43),(52,49,63),(73,70,84),
 (106,101,119),(145,140,155),(187,181,194),(218,211,222),
 (48,22,73),(90,32,139),(149,48,219),(205,103,255),
 (33,29,47),(62,51,79),(102,65,135),(239,182,255)]
for idx,color in enumerate(colors):
 x=(idx%4)*16;y=(idx//4)*16
 for yy in range(16):
  for xx in range(16):
   light=((xx*3+yy*5+idx*7)%9)-4
   bevel=10 if xx==0 or yy==0 else (-10 if xx==15 or yy==15 else 0)
   palette.putpixel((x+xx,y+yy),tuple(max(0,min(255,c+light+bevel)) for c in color)+(255,))
palette.save(A/"textures/item/multitool_3d.png")
parts=[]
def cuboid(lo,hi,tile,edge=None):
 def uv(t):return [(t%4)*16,(t//4)*16,(t%4+1)*16,(t//4+1)*16]
 faces={}
 for f in ("north","south","east","west","up","down"):
  material=(edge if edge is not None and f in ("up","east") else tile)
  faces[f]={"uv":uv(material),"texture":"#palette"}
 parts.append({"from":lo,"to":hi,"faces":faces})
# Octagonal-looking grip built from narrower inset longitudinal facets.
cuboid([6.7,0.5,6.7],[9.3,11.9,9.3],1,3)
cuboid([7.05,0.4,6.35],[8.95,11.5,6.75],2,4)
cuboid([7.05,0.4,9.25],[8.95,11.5,9.65],0,2)
cuboid([6.35,0.4,7.05],[6.75,11.5,8.95],0,2)
cuboid([9.25,0.4,7.05],[9.65,11.5,8.95],2,4)
# Wrapped leather rings, purple light channels, forged butt pommel.
for y in (1.7,4.5,7.3,10.1):
 cuboid([6.45,y,6.45],[9.55,y+0.36,9.55],8,10)
 cuboid([7.1,y+0.1,6.2],[8.9,y+0.25,6.5],11)
cuboid([6.2,0.0,6.2],[9.8,0.75,9.8],2,5)
cuboid([6.7,0.0,6.05],[9.3,0.65,6.25],10,11)
# Narrow violet vein running from pommel to weapon collar.
cuboid([7.65,2.2,6.12],[8.35,10.6,6.38],9,11)
# Forged core with stepped collar and inset gem.
cuboid([5.1,11.0,5.75],[10.9,13.9,10.25],1,4)
cuboid([5.65,11.45,5.45],[10.35,13.45,5.8],3,5)
cuboid([5.65,11.45,10.2],[10.35,13.45,10.55],3,5)
cuboid([7.0,11.75,5.16],[9.0,13.15,5.48],9,11)
cuboid([7.0,11.75,10.52],[9.0,13.15,10.84],9,11)
# AXE toward +X: curved silhouette from a series of offset beveled facets.
# Upper and lower corners flare; the middle cuts back to a concave waist.
cuboid([10.5,11.0,6.0],[12.1,14.6,10.0],2,4)
cuboid([11.7,12.2,6.25],[13.2,15.2,9.75],3,5)
cuboid([12.9,13.1,6.55],[14.35,15.8,9.45],4,6)
cuboid([14.0,14.0,6.95],[15.0,15.9,9.05],5,7)
cuboid([14.85,14.8,7.3],[15.65,15.95,8.7],6,7)
cuboid([11.7,9.3,6.4],[13.3,12.1,9.6],2,4)
cuboid([12.9,8.5,6.7],[14.25,10.4,9.3],3,5)
cuboid([13.95,8.15,7.1],[14.95,9.4,8.9],5,6)
cuboid([14.7,8.0,7.4],[15.45,8.8,8.6],6,7)
# Thin, razor bright edge, deliberately recessed at the center.
cuboid([14.3,12.2,7.25],[14.8,13.0,8.75],5,6)
# Violet ornamental channels on BOTH broad axe surfaces.
for z0,z1 in ((5.95,6.2),(9.8,10.05)):
 cuboid([11.2,12.7,z0],[12.8,13.05,z1],9,11)
 cuboid([12.15,13.35,z0],[13.6,13.65,z1],10,11)
# PICK toward -X: rear spear tapers outward, with a hooked lower point.
cuboid([3.8,12.0,6.3],[5.5,14.45,9.7],2,4)
cuboid([2.4,12.7,6.6],[4.0,14.0,9.4],3,5)
cuboid([1.1,13.1,6.95],[2.65,13.85,9.05],4,6)
cuboid([0.2,13.4,7.4],[1.25,13.75,8.6],6,7)
cuboid([2.65,11.1,7.0],[3.55,12.9,9.0],2,4)
cuboid([3.05,9.8,7.2],[3.85,11.25,8.8],3,5)
cuboid([3.45,8.5,7.5],[4.0,9.95,8.5],5,6)
cuboid([3.65,7.75,7.75],[4.05,8.65,8.25],6,7)
for z0,z1 in ((6.2,6.45),(9.55,9.8)):
 cuboid([2.4,13.1,z0],[4.75,13.4,z1],9,11)
# Dark faceted weapon body, never a flat item/handheld sprite.
model.write_text(json.dumps({"textures":{"palette":"obsidiannetwork:item/multitool_3d","particle":"obsidiannetwork:item/multitool_3d"},"gui_light":"front","elements":parts,"display":{"thirdperson_righthand":{"rotation":[0,-90,55],"translation":[0,2,0],"scale":[0.7,0.7,0.7]},"thirdperson_lefthand":{"rotation":[0,90,-55],"translation":[0,2,0],"scale":[0.7,0.7,0.7]},"firstperson_righthand":{"rotation":[0,-90,55],"translation":[0.0,1.0,0.0],"scale":[0.55,0.55,0.55]},"firstperson_lefthand":{"rotation":[0,90,-55],"translation":[0.0,1.0,0.0],"scale":[0.55,0.55,0.55]},"gui":{"rotation":[30,225,0],"translation":[0,0,0],"scale":[0.82,0.82,0.82]},"ground":{"translation":[0,2,0],"scale":[0.55,0.55,0.55]},"fixed":{"rotation":[0,180,0],"scale":[0.85,0.85,0.85]}}},indent=2)+chr(10))
definition=A/"items/multitool.json";definition.parent.mkdir(parents=True,exist_ok=True)
definition.write_text(json.dumps({"model":{"type":"minecraft:model","model":"obsidiannetwork:item/multitool"}},indent=2)+"\n")
print("B1154_MULTITOOL_REGISTERED_RECIPE_TEXTURE_AND_CHAIN_MINING_PASS")
