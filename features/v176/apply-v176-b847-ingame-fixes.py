#!/usr/bin/env python3
"""B847: fix real 26.1 player arm rendering, backpack slots, icons, unique backpacks.
Runs after B843 and the B839 API compatibility patch. Fail closed on drift.
Do not affect armor entry/exit/recall or unrelated inventory systems.
"""
import os,json,colorsys,math
from pathlib import Path
from PIL import Image,ImageDraw
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"

def edit(rel,old,new,n=1):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==n,("B847_SOURCE_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,n),encoding="utf-8")

def write(rel,text):
 p=J/rel
 assert not p.exists(),("B847_ALREADY_PRESENT",str(p))
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(text,encoding="utf-8")

# PlayerModel overrides setupAnim(AvatarRenderState), AFTER HumanoidModel setupAnim.
# The previous superclass Mixin is not the final model mutation. Preserve it
# for worn armor layers and add a PlayerModel TAIL hook for the visible player.
write("mixin/V176AttackPlayerModelMixin.java",'''package dev.obsidiannetwork.mixin;

import dev.obsidiannetwork.client.V176MicroMgVisualClient;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The actual last animation pass for the player, not the overwritten
 * HumanoidModel pre-render pose. Runs on remote players, too.
 */
@Mixin(PlayerModel.class)
public abstract class V176AttackPlayerModelMixin extends HumanoidModel<AvatarRenderState> {
 public V176AttackPlayerModelMixin(ModelPart root){super(root);}
 @Inject(method="setupAnim(Lnet/minecraft/client/renderer/entity/state/AvatarRenderState;)V",at=@At("TAIL"))
 private void xsxlabs$aimRightArmLast(AvatarRenderState state,CallbackInfo callback){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var entity=mc.level.getEntity(state.id);
  if(!(entity instanceof Player player) || !V176MicroMgVisualClient.armedForAttack(player))return;
  // Raise only RIGHT upper arm, almost horizontal forward. Mirror for right sleeve.
  this.rightArm.xRot=-1.535F;
  this.rightArm.yRot=0.0F;
  this.rightArm.zRot=0.0F;
  ((PlayerModel)(Object)this).rightSleeve.copyFrom(this.rightArm);
 }
}
''')
mx=R/"obsidiannetwork.mixins.json"
m=json.loads(mx.read_text(encoding="utf-8"))
assert "V176AttackRightArmMixin" in m.get("client",[])
assert "V176AttackPlayerModelMixin" not in m["client"]
m["client"].append("V176AttackPlayerModelMixin")
mx.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")

# The old Post hook drew a gun from untransformed player feet, applying an
# arbitrary 1.35-block lift. Instead submit inside a real player RenderLayer,
# whose PoseStack is already the renderer's root transform, and transform by
# the *same rightArm ModelPart* used by the visible armored player.
visual=J/"client/V176MicroMgVisualClient.java"
s=visual.read_text(encoding="utf-8")
start=s.index(" @SubscribeEvent public static void worn(RenderPlayerEvent.Post<?> event){")
end=s.index(" @SubscribeEvent public static void firstPerson(",start)
s=s[:start]+s[end:]
s=s.replace(" private static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,",
            " public static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,")
s=s.replace(" private static float extension(int key,boolean armed){",
            " public static float extension(int key,boolean armed){")
s=s.replace(" private static int tier(LivingEntity entity){",
            " public static int tier(LivingEntity entity){")
assert "RenderPlayerEvent.Post<?> event" not in s and "public static void drawArm" in s
visual.write_text(s,encoding="utf-8")
write("client/V176MicroMgLayer.java",'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.world.entity.player.Player;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** One arm-attached weapon layer, no world-coordinate gun or second whole arm.
 * Attachment follows the parent model's actual rightArm pivot and x/y/z rotation.
 */
public final class V176MicroMgLayer extends RenderLayer<AvatarRenderState,PlayerModel> {
 public V176MicroMgLayer(RenderLayerParent<AvatarRenderState,PlayerModel> parent){super(parent);}
 @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,
       AvatarRenderState state,float yaw,float pitch){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var e=mc.level.getEntity(state.id);
  if(!(e instanceof Player player))return;
  int tier=V176MicroMgVisualClient.tier(player);
  if(tier==0)return;
  boolean armed=V176MicroMgVisualClient.armedForAttack(player);
  float deployment=V176MicroMgVisualClient.extension(e.getId(),armed);
  if(deployment<=0.001F)return;
  // PoseStack is already in the player model coordinate frame.
  // drawArm delegates to rightArm.translateAndRotate(pose); no foot offsets.
  V176MicroMgVisualClient.drawArm(pose,nodes,light,
      getParentModel().rightArm,tier,deployment);
 }
 @EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
 public static final class Register {
  private Register(){}
  @SubscribeEvent public static void layers(EntityRenderersEvent.AddLayers event){
   for(var skin : event.getSkins()){
    var renderer=event.getPlayerRenderer(skin);
    if(renderer!=null)renderer.addLayer(new V176MicroMgLayer(renderer));
   }
  }
 }
}
''')

# GUI BUG: the slot accepted only stacks of EXACTLY one, while a click from a
# stacked StorageCellItem tried to insert the whole carried count. Limit actual
# slot transfer to one, and handle Shift-click installation before cell storage.
edit("backpack/V176BackpackMenu.java",
 '''if(slot<0||slot>=4||stack.isEmpty()||stack.getCount()!=1
      ||stack.getItem() instanceof NetworkBackpackItem)return false;''',
 '''if(slot<0||slot>=4||stack.isEmpty()
      ||stack.getItem() instanceof NetworkBackpackItem)return false;''')
edit("backpack/V176BackpackMenu.java",
 '''     @Override public boolean mayPickup(Player player){
      return slot<4&&storage.removable(slot);
     }''',
 '''     @Override public boolean mayPickup(Player player){
      return slot<4&&storage.removable(slot);
     }
     @Override public int getMaxStackSize(ItemStack stack){
      return slot<4?1:super.getMaxStackSize(stack);
     }''')
edit("backpack/V176BackpackMenu.java",
 '''  ItemStack updated=storage.source.current().copy();
  V176BackpackCells.Transfer result=V176BackpackCells.insert(''',
 '''  // Module installation is NOT ordinary item deposit. Never consume the
  // upgrade unless its exact backpack component write has committed.
  int moduleSlot=-1;
  if(current.is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get()))
   moduleSlot=0;
  else if(current.getItem() instanceof StorageCellItem){
   var installed=V176BackpackCells.slots(storage.source.current());
   for(int i=1;i<=3;i++)if(installed.get(i).isEmpty()){moduleSlot=i;break;}
  }
  if(moduleSlot>=0){
   ItemStack single=current.copy();single.setCount(1);
   ItemStack bag=storage.source.current().copy();
   if(!V176BackpackCells.putUpgrade(bag,moduleSlot,single)
       ||!storage.source.save(bag))return ItemStack.EMPTY;
   current.shrink(1);
   slot.setChanged();
   broadcastChanges();
   return single;
  }
  ItemStack updated=storage.source.current().copy();
  V176BackpackCells.Transfer result=V176BackpackCells.insert(''')
# Client displays a ChestMenu rather than server-specific V176BackpackMenu;
# this wrapper needs identical limits for click/drag transaction predictions.
edit("client/V176BackpackScreen.java",
 '''     @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return slotIndex<4;}
   });''',
 '''     @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return slotIndex<4;}
     @Override public int getMaxStackSize(net.minecraft.world.item.ItemStack stack){
      return slotIndex<4?1:super.getMaxStackSize(stack);
     }
   });''')

# Fixed asset paths: never use dynamically generated item texture layer refs
# to the vanilla BLOCK atlas for an item. Provide real RGBA item PNGs in mod.
def stone(name,obsidian=False):
 im=Image.new("RGBA",(32,32),(0,0,0,0));d=ImageDraw.Draw(im)
 # Crisp original block-like pixel geometry, with cracks and dark grout.
 for y in range(32):
  for x in range(32):
   grid=((x*17+y*13+(x//5)*11+(y//7)*19)%19)-9
   if obsidian:
    v=(31+grid//3,19+grid//2,53+grid)
    if (x*7+y*11)%41<3:v=(62,40,101)
   else:
    k=117+grid*3+(15 if (x//9+y//8)%3==0 else -9)
    v=(k,min(255,k+3),min(255,k+5))
   im.putpixel((x,y),(*[max(0,min(255,int(c))) for c in v],255))
 for x,y in [(0,8),(11,8),(11,17),(23,17),(23,4),(5,24),(19,28)]:
  points=[(x%32,y),(min(31,x+5),min(31,y+2)),(min(31,x+3),min(31,y+7))]
  d.line(points,fill=(13,9,25,255) if obsidian else (60,62,65,255),width=2)
 out=A/"textures/item"/(name+"_base.png");out.parent.mkdir(parents=True,exist_ok=True)
 im.save(out,optimize=True)
 with Image.open(out) as check:assert check.size==(32,32) and check.mode=="RGBA"
 model=A/"models/item"/(name+".json")
 obj=json.loads(model.read_text(encoding="utf-8"))
 assert obj["parent"]=="minecraft:item/generated"
 obj["textures"]["layer0"]="obsidiannetwork:item/"+name+"_base"
 model.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
for item in ("compressed_cobblestone_1x","compressed_cobblestone_3x"):
 stone(item)
stone("compressed_obsidian_1x",True)

# Same framed electronic upgrade style as existing Power Armor modules.
def circuit(kind):
 im=Image.new("RGBA",(32,32),(0,0,0,0));d=ImageDraw.Draw(im)
 d.rounded_rectangle((2,2,29,29),radius=3,fill=(13,23,36,255),outline=(74,106,131,255),width=2)
 d.rectangle((5,5,26,26),fill=(13,53,83,255),outline=(52,169,206,255),width=1)
 d.rectangle((7,7,24,24),fill=(12,44,72,255))
 for x in (8,23):
  for y in (8,23):d.rectangle((x,y,x+1,y+1),fill=(128,210,238,255))
 if kind=="magnet":
  d.arc((10,8,23,23),0,180,fill=(98,240,255,255),width=4)
  d.rectangle((10,14,13,22),fill=(94,230,247,255))
  d.rectangle((20,14,23,22),fill=(94,230,247,255))
  d.rectangle((11,21,13,24),fill=(240,101,114,255))
  d.rectangle((20,21,22,24),fill=(240,101,114,255))
 else:
  d.rectangle((9,13,20,17),fill=(143,204,224,255))
  d.rectangle((13,10,17,21),fill=(58,179,212,255))
  d.rectangle((20,12,25,18),fill=(177,211,227,255))
  d.rectangle((24,13,27,17),fill=(32,55,69,255))
  d.rectangle((8,21,19,22),fill=(46,215,241,255))
 name="network_backpack_magnet_upgrade" if kind=="magnet" else "power_card_micro_mg"
 png=A/"textures/item"/(name+".png")
 im.save(png,optimize=True)
 model=A/"models/item"/(name+".json")
 data=json.loads(model.read_text(encoding="utf-8"))
 data["textures"]={"layer0":"obsidiannetwork:item/"+name}
 model.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
circuit("magnet");circuit("micro_mg")

# Twenty-four EXPLICIT contrasting palettes. Do not sample dominant atlas
# pixels: near-identical armor atlases were yielding repeated backpack colors.
palettes=[
 ((28,105,194),(236,179,49)),((186,44,47),(32,192,210)),
 ((70,166,60),(244,206,65)),((118,61,192),(67,217,205)),
 ((220,102,29),(58,106,208)),((44,172,180),(230,73,125)),
 ((206,54,153),(91,211,62)),((67,85,104),(244,138,44)),
 ((230,196,61),(78,42,164)),((95,181,228),(218,61,68)),
 ((49,121,81),(225,107,178)),((166,70,37),(55,216,233)),
 ((138,198,54),(55,85,186)),((165,64,215),(245,125,40)),
 ((217,76,87),(173,224,58)),((53,163,144),(204,92,225)),
 ((238,142,53),(68,205,129)),((79,118,209),(243,87,176)),
 ((201,197,178),(68,125,205)),((43,49,67),(200,185,54)),
 ((101,198,198),(188,50,81)),((143,94,187),(221,200,105)),
 ((211,114,159),(52,145,120)),((69,166,112),(247,99,47))]
assert len(palettes)==24 and len(set(palettes))==24
def faces(tex,uv):return {k:{"texture":tex,"uv":uv} for k in ("north","south","east","west","up","down")}
def el(f,t,tex,uv=None):
 if uv is None:uv={"#body":[0,0,8,8],"#accent":[8,0,16,8],"#dark":[0,8,8,16],"#glow":[8,8,16,16]}[tex]
 return {"from":f,"to":t,"faces":faces(tex,uv)}
# Distinct rounded-looking STEP silhouette in Minecraft cubes: tapered crown,
# side pockets, lid, two exposed shoulder straps, front cargo pocket & handle.
shape=[
 el([3.8,2,5],[12.2,12.9,12],"#body"),
 el([4.4,12.9,5.6],[11.6,14.2,11.5],"#body"),
 el([5.2,14.2,7.5],[10.8,15.4,10],"#accent"),
 el([3.7,10.8,4.5],[12.3,13.2,12.1],"#accent"),
 el([4.2,2.4,4.3],[11.8,10.3,5.2],"#body"),
 el([4.9,3.3,3.5],[11.1,7.4,4.5],"#dark"),
 el([5.2,3.8,3.2],[10.8,6.9,3.8],"#accent"),
 el([5.8,5.9,3.1],[10.2,6.6,3.8],"#accent"),
 el([7.1,6.7,3.1],[8.9,7.5,3.8],"#glow"),
 el([5.5,10.3,3.8],[10.5,11.4,5],"#dark"),
 el([5.4,11.4,4.1],[10.6,12.8,5.2],"#accent"),
 el([2.5,4.0,6.1],[4.0,9.9,11.1],"#body"),
 el([12,4.0,6.1],[13.5,9.9,11.1],"#body"),
 el([2.2,8.9,6.2],[4.1,10.1,11],"#accent"),
 el([11.9,8.9,6.2],[13.8,10.1,11],"#accent"),
 el([2.4,4.4,5.8],[4.1,5.1,11.2],"#dark"),
 el([11.9,4.4,5.8],[13.6,5.1,11.2],"#dark"),
 el([4.0,2.2,11.9],[5.2,12.9,13.1],"#dark"),
 el([10.8,2.2,11.9],[12.0,12.9,13.1],"#dark"),
 el([4.0,9.7,12.6],[5.3,12.0,13.5],"#accent"),
 el([10.7,9.7,12.6],[12.0,12.0,13.5],"#accent"),
 el([5.2,13.4,10.3],[6.3,15.8,12],"#dark"),
 el([9.7,13.4,10.3],[10.8,15.8,12],"#dark"),
 el([6,15.0,10.8],[10,15.9,12.2],"#accent"),
 el([3.4,2.0,5.7],[4.2,11.1,6.3],"#accent"),
 el([11.8,2.0,5.7],[12.6,11.1,6.3],"#accent"),
 el([4.9,3.0,4.0],[11.1,3.9,5.3],"#dark"),
 el([5.8,3.5,3.1],[10.2,4.0,4.0],"#body"),
 el([7.0,9.6,4.0],[9.0,10.9,4.7],"#glow")
]
for i,(body,accent) in enumerate(palettes,1):
 name=f"network_backpack_mk{i}"
 png=A/"textures/block"/(name+".png")
 # Four highly contrasted material quadrants with small texture noise.
 dark=tuple(max(8,int(v*.43)) for v in body)
 light=tuple(min(255,int(v*.35+accent[k]*.80)) for k,v in enumerate(accent))
 swatches=[body,accent,dark,light]
 im=Image.new("RGBA",(32,32))
 for y in range(32):
  for x in range(32):
   idx=(y//16)*2+(x//16)
   base=swatches[idx]
   delta=(((x//3)*5+(y//4)*7)%11)-5
   im.putpixel((x,y),tuple(max(0,min(255,v+delta)) for v in base)+(255,))
 im.save(png,optimize=True)
 model=A/"models/block"/(name+".json")
 data=json.loads(model.read_text(encoding="utf-8"))
 data["elements"]=shape
 data["textures"]={"particle":"#body","body":"obsidiannetwork:block/"+name,
 "accent":"obsidiannetwork:block/"+name,"dark":"obsidiannetwork:block/"+name,
 "glow":"obsidiannetwork:block/"+name}
 model.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
assert len(shape)>25

# Changes to IDs, inventory data or item behavior are forbidden by this patch.
assert "drawArm(pose,nodes,light" in (J/"client/V176MicroMgLayer.java").read_text()
print("V176_B847_PLAYERMODEL_FINAL_POSE_ARM_ATTACHED_LAYER_MODULE_SLOTS_REAL_ITEM_TEXTURES_24_PALETTES PASS")
