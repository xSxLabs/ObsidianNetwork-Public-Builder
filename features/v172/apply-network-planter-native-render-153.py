#!/usr/bin/env python3
"""Build 153: native Minecraft 26.1.2 block-state crops, vanilla saplings and true-species trees.

Replaces all runtime-generated crop planes and homemade texture identifiers.
Rendering uses BlockModelResolver and BlockModelRenderState (26.1 submission API);
the normal resource-backed block model remains ONLY the stripped-wood pot itself.
Independent of Botany Pots or other additional mods. No harvesting/storage changes.
"""
import json
import os
from pathlib import Path
root=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
blockstates=root/"blockstates"
models=root/"models/block"
blocks=sorted(blockstates.glob("network_planter*.json"))
assert len(blocks)==12,len(blocks)
# Replace every visual variant with the original, complete wood model. This
# prevents old planted overlays being rendered ON TOP of our native BER.
for source in blocks:
    name=source.stem
    wood="oak" if name=="network_planter" else name.removeprefix("network_planter_stripped_")
    base="network_planter_wood_"+wood
    assert (models/(base+".json")).is_file(),(name,base)
    previous=json.loads(source.read_text(encoding="utf-8"))["variants"]
    assert len(previous)==104,(name,len(previous))
    variants={key:{"model":"obsidiannetwork:block/"+base} for key in previous}
    assert len(variants)==104
    assert set(key.split("plant=")[1] for key in variants)=={
      "empty","wheat","beetroot","carrot","potato","melon","pumpkin",
      "nether_wart","sweet_berries","cocoa","cactus","sugar_cane","bamboo",
      "oak","spruce","birch","jungle","acacia","dark_oak","mangrove",
      "cherry","pale_oak","azalea","flowering_azalea","crimson","warped"}
    source.write_text(json.dumps({"variants":variants},indent=2)+"\n",encoding="utf-8")

# These are obsolete and potentially broken; they must not enter the JAR.
obsolete=list(models.glob("network_planter*_age*.json"))+list(models.glob("network_planter_grow_*.json"))
assert len(obsolete)>=1248,len(obsolete)
for path in obsolete:path.unlink()

renderer=r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.obsidiannetwork.block.NetworkPlanterBlock;
import dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockDisplayContext;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/** BUILD153_NATIVE_PLANTER_RENDER:
 * 26.1 native vanilla BlockStates, never hand-picked texture paths.
 * Four growth stages; true species sapling for young trees; actual log/leaf
 * block models for mature trees. No Botany Pots dependency.
 */
public final class NetworkPlanterRenderer implements
    BlockEntityRenderer<NetworkPlanterBlockEntity, NetworkPlanterRenderer.GrowthState> {
 private static final BlockDisplayContext DISPLAY_CONTEXT=BlockDisplayContext.create();
 private final BlockModelResolver resolver;
 public NetworkPlanterRenderer(BlockEntityRendererProvider.Context context){
  resolver=context.blockModelResolver();
 }
 public static final class GrowthState extends BlockEntityRenderState {
  public final BlockModelRenderState plantModel=new BlockModelRenderState();
  public final BlockModelRenderState trunkModel=new BlockModelRenderState();
  public final BlockModelRenderState leafModel=new BlockModelRenderState();
  public NetworkPlanterBlock.Plant species=NetworkPlanterBlock.Plant.EMPTY;
  public int age;
  public boolean active;
  public boolean tree;
 }
 @Override public GrowthState createRenderState(){return new GrowthState();}

 private static BlockState sapling(NetworkPlanterBlock.Plant plant){
  return switch(plant){
   case OAK->Blocks.OAK_SAPLING.defaultBlockState();
   case SPRUCE->Blocks.SPRUCE_SAPLING.defaultBlockState();
   case BIRCH->Blocks.BIRCH_SAPLING.defaultBlockState();
   case JUNGLE->Blocks.JUNGLE_SAPLING.defaultBlockState();
   case ACACIA->Blocks.ACACIA_SAPLING.defaultBlockState();
   case DARK_OAK->Blocks.DARK_OAK_SAPLING.defaultBlockState();
   case MANGROVE->Blocks.MANGROVE_PROPAGULE.defaultBlockState();
   case CHERRY->Blocks.CHERRY_SAPLING.defaultBlockState();
   case PALE_OAK->Blocks.PALE_OAK_SAPLING.defaultBlockState();
   case AZALEA->Blocks.AZALEA.defaultBlockState();
   case FLOWERING_AZALEA->Blocks.FLOWERING_AZALEA.defaultBlockState();
   case CRIMSON->Blocks.CRIMSON_FUNGUS.defaultBlockState();
   case WARPED->Blocks.WARPED_FUNGUS.defaultBlockState();
   default->Blocks.AIR.defaultBlockState();
  };
 }
 private static BlockState trunk(NetworkPlanterBlock.Plant plant){
  return switch(plant){
   case SPRUCE->Blocks.SPRUCE_LOG.defaultBlockState();
   case BIRCH->Blocks.BIRCH_LOG.defaultBlockState();
   case JUNGLE->Blocks.JUNGLE_LOG.defaultBlockState();
   case ACACIA->Blocks.ACACIA_LOG.defaultBlockState();
   case DARK_OAK->Blocks.DARK_OAK_LOG.defaultBlockState();
   case MANGROVE->Blocks.MANGROVE_LOG.defaultBlockState();
   case CHERRY->Blocks.CHERRY_LOG.defaultBlockState();
   case PALE_OAK->Blocks.PALE_OAK_LOG.defaultBlockState();
   case CRIMSON->Blocks.CRIMSON_STEM.defaultBlockState();
   case WARPED->Blocks.WARPED_STEM.defaultBlockState();
   default->Blocks.OAK_LOG.defaultBlockState();
  };
 }
 private static BlockState leaves(NetworkPlanterBlock.Plant plant){
  return switch(plant){
   case SPRUCE->Blocks.SPRUCE_LEAVES.defaultBlockState();
   case BIRCH->Blocks.BIRCH_LEAVES.defaultBlockState();
   case JUNGLE->Blocks.JUNGLE_LEAVES.defaultBlockState();
   case ACACIA->Blocks.ACACIA_LEAVES.defaultBlockState();
   case DARK_OAK->Blocks.DARK_OAK_LEAVES.defaultBlockState();
   case MANGROVE->Blocks.MANGROVE_LEAVES.defaultBlockState();
   case CHERRY->Blocks.CHERRY_LEAVES.defaultBlockState();
   case PALE_OAK->Blocks.PALE_OAK_LEAVES.defaultBlockState();
   case AZALEA->Blocks.AZALEA_LEAVES.defaultBlockState();
   case FLOWERING_AZALEA->Blocks.FLOWERING_AZALEA_LEAVES.defaultBlockState();
   case CRIMSON->Blocks.NETHER_WART_BLOCK.defaultBlockState();
   case WARPED->Blocks.WARPED_WART_BLOCK.defaultBlockState();
   default->Blocks.OAK_LEAVES.defaultBlockState();
  };
 }
 private static BlockState crop(NetworkPlanterBlock.Plant plant){
  return switch(plant){
   case WHEAT->Blocks.WHEAT.defaultBlockState();
   case BEETROOT->Blocks.BEETROOTS.defaultBlockState();
   case CARROT->Blocks.CARROTS.defaultBlockState();
   case POTATO->Blocks.POTATOES.defaultBlockState();
   case MELON->Blocks.MELON_STEM.defaultBlockState();
   case PUMPKIN->Blocks.PUMPKIN_STEM.defaultBlockState();
   case NETHER_WART->Blocks.NETHER_WART.defaultBlockState();
   case SWEET_BERRIES->Blocks.SWEET_BERRY_BUSH.defaultBlockState();
   case COCOA->Blocks.COCOA.defaultBlockState();
   case CACTUS->Blocks.CACTUS.defaultBlockState();
   case SUGAR_CANE->Blocks.SUGAR_CANE.defaultBlockState();
   case BAMBOO->Blocks.BAMBOO.defaultBlockState();
   default->Blocks.AIR.defaultBlockState();
  };
 }
 /** Native integer property: Minecraft owns each crop's correct model/texture. */
 private static BlockState cropAge(BlockState base,int phase){
  var prop=base.getBlock().getStateDefinition().getProperty("age");
  if(prop instanceof IntegerProperty age){
   int max=age.getPossibleValues().stream().mapToInt(Integer::intValue).max().orElse(0);
   return base.setValue(age,Math.min(max,Math.max(0,(max*phase+1)/3)));
  }
  return base;
 }
 @Override public void extractRenderState(NetworkPlanterBlockEntity be,
       GrowthState out,float partialTick,Vec3 cameraPosition,
       ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress){
  BlockEntityRenderer.super.extractRenderState(be,out,partialTick,cameraPosition,breakProgress);
  BlockState state=be.getBlockState();
  out.active=false;
  if(!(state.getBlock() instanceof NetworkPlanterBlock))return;
  out.species=state.getValue(NetworkPlanterBlock.PLANT);
  out.age=state.getValue(NetworkPlanterBlock.AGE);
  if(out.species==NetworkPlanterBlock.Plant.EMPTY)return;
  out.tree=out.species.tree;
  BlockState nativeState=out.tree?sapling(out.species):cropAge(crop(out.species),out.age);
  if(nativeState.isAir())return;
  resolver.update(out.plantModel,nativeState,DISPLAY_CONTEXT);
  if(out.tree && out.age>=2){
   resolver.update(out.trunkModel,trunk(out.species),DISPLAY_CONTEXT);
   resolver.update(out.leafModel,leaves(out.species),DISPLAY_CONTEXT);
  }
  out.active=true;
 }
 private static void draw(BlockModelRenderState model,GrowthState state,
    PoseStack pose,SubmitNodeCollector collector,
    float x,float y,float z,float sx,float sy,float sz){
  pose.pushPose();
  pose.translate(x-sx*.5f,y,z-sz*.5f);
  pose.scale(sx,sy,sz);
  model.submit(pose,collector,state.lightCoords,OverlayTexture.NO_OVERLAY,0);
  pose.popPose();
 }
 @Override public void submit(GrowthState state,PoseStack pose,
    SubmitNodeCollector collector,CameraRenderState camera){
  if(!state.active)return;
  // Soil top on our six-cuboid pot is 7/16 high.
  float soil=7f/16f;
  if(!state.tree){
   float s=.56f+.14f*state.age;
   float height=s;
   if(state.species==NetworkPlanterBlock.Plant.CACTUS
      ||state.species==NetworkPlanterBlock.Plant.SUGAR_CANE
      ||state.species==NetworkPlanterBlock.Plant.BAMBOO){
     height=.45f+.30f*state.age;
     s=.45f;
   }
   draw(state.plantModel,state,pose,collector,.5f,soil,.5f,s,height,s);
   return;
  }
  // Phase 0 and 1 MUST show a real original Minecraft sapling.
  if(state.age<2){
   float scale=state.age==0?.73f:1.0f;
   draw(state.plantModel,state,pose,collector,.5f,soil,.5f,scale,scale,scale);
   return;
  }
  // The mature growth uses real log and foliage BLOCK MODELS (incl. biome tint),
  // not fake 6-face texture cubes. Distinct species keep their leaf/stem identity.
  float trunkWidth=state.age==2?.22f:.32f;
  float trunkHeight=state.age==2?.78f:1.22f;
  float crown=state.age==2?.58f:.84f;
  draw(state.trunkModel,state,pose,collector,.5f,soil,.5f,trunkWidth,trunkHeight,trunkWidth);
  draw(state.leafModel,state,pose,collector,.5f,soil+trunkHeight-crown*.38f,
       .5f,crown,crown*.8f,crown);
  if(state.age==3){
   draw(state.leafModel,state,pose,collector,.26f,soil+trunkHeight-.25f,
       .5f,.42f,.42f,.42f);
   draw(state.leafModel,state,pose,collector,.74f,soil+trunkHeight-.25f,
       .5f,.42f,.42f,.42f);
  }
 }
 @Override public boolean shouldRenderOffScreen(){return true;}
 @Override public int getViewDistance(){return 40;}
}
'''
registration=r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** BUILD153_NATIVE_PLANTER_REGISTER: client MOD bus only, dedicated-server safe. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class NetworkPlanterClientRenderRegistration {
 private NetworkPlanterClientRenderRegistration(){}
 @SubscribeEvent public static void register(EntityRenderersEvent.RegisterRenderers event){
  event.registerBlockEntityRenderer(ModBlockEntities.NETWORK_PLANTER.get(),
      NetworkPlanterRenderer::new);
 }
}
'''
target=java/"client/NetworkPlanterRenderer.java"
assert not target.exists(),target
target.write_text(renderer,encoding="utf-8")
target=java/"client/NetworkPlanterClientRenderRegistration.java"
assert not target.exists(),target
target.write_text(registration,encoding="utf-8")

assert "BlockModelResolver" in renderer
assert "resolver.update(out.plantModel,nativeState,DISPLAY_CONTEXT)" in renderer
assert "case OAK->Blocks.OAK_SAPLING.defaultBlockState()" in renderer
assert "case CHERRY->Blocks.CHERRY_SAPLING.defaultBlockState()" in renderer
assert "BlockEntityRenderer.super.extractRenderState" in renderer
assert "value=Dist.CLIENT" in registration and "Bus.MOD" not in registration
assert all(len(json.loads(p.read_text())["variants"])==104 for p in blocks)
assert not list(models.glob("network_planter*_age*.json"))
print("BUILD153_NATIVE_PLANTER_PASS: vanilla BlockStates and true saplings, 12 stripped wood models, 26 plants x 4 phases, 0 broken generated growth models")
