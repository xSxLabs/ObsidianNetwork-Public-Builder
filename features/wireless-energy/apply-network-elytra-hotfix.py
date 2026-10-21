#!/usr/bin/env python3
"""Build 368 Network Elytra follow-up: optional Curios, client boost, custom assets."""
from pathlib import Path
import os, json, zlib, struct, math

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])
item=java/"item/NetworkElytraItem.java"
source=item.read_text(encoding="utf-8")
marker="XSXLABS_NETWORK_ELYTRA_CURIOS_BOOST_V2"
assert marker not in source

old='''        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        if (!(chest.getItem() instanceof NetworkElytraItem)) return;
        long energy = EnergyTool.energy(chest);'''
new='''        // XSXLABS_NETWORK_ELYTRA_CURIOS_BOOST_V2: no Curios classes resolve without Curios.
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        if (!(chest.getItem() instanceof NetworkElytraItem)
            && net.neoforged.fml.ModList.get().isLoaded("curios"))
            chest = dev.obsidiannetwork.wireless.NetworkElytraCurios.find(player);
        if (!(chest.getItem() instanceof NetworkElytraItem)) return;
        long energy = EnergyTool.energy(chest);'''
assert source.count(old)==1
source=source.replace(old,new,1)
old='''            player.setDeltaMovement(next);
        }'''
new='''            player.setDeltaMovement(next);
            player.hasImpulse = true; // Send motion updates; client mirrors movement.
        }'''
assert source.count(old)==1
source=source.replace(old,new,1)
item.write_text(source,encoding="utf-8")

# Optional bridge is invoked ONLY when Curios is actually loaded.
bridge=java/"wireless/NetworkElytraCurios.java"
assert not bridge.exists()
bridge.write_text(r'''package dev.obsidiannetwork.wireless;
import dev.obsidiannetwork.item.NetworkElytraItem;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import top.theillusivec4.curios.api.CuriosApi;

/** Optional 26.1 Curios API linkage. Never called without the mod installed. */
public final class NetworkElytraCurios {
 private NetworkElytraCurios(){}
 public static ItemStack find(Player player) {
  var inv = CuriosApi.getCuriosInventory(player);
  if(inv.isEmpty())return ItemStack.EMPTY;
  // Prefer back/elytra slots; never let a random vanity/other slot grant flight.
  for(String slot : new String[]{"back","elytra"}) {
   var handler=inv.get().getCurios().get(slot);
   if(handler==null)continue;
   var stacks=handler.getStacks();
   for(int i=0;i<stacks.getSlots();i++) {
    ItemStack stack=stacks.getStackInSlot(i);
    if(stack.getItem() instanceof NetworkElytraItem)return stack;
   }
  }
  return ItemStack.EMPTY;
 }
}
''',encoding="utf-8")

# Both vanilla and optional Curios wings share the same server-authoritative FE.
# Player input is client-authoritative; velocity MUST also be applied locally.
client=java/"client/NetworkElytraBoostClient.java"
assert not client.exists()
client.write_text(r'''package dev.obsidiannetwork.client;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.item.NetworkElytraItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** Client movement prediction for Shift boost. Never loads on dedicated server. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class NetworkElytraBoostClient {
 private NetworkElytraBoostClient(){}
 @SubscribeEvent public static void onTick(ClientTickEvent.Post event) {
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null || !mc.player.isFallFlying() || !mc.options.keyShift.isDown())return;
  ItemStack wing=mc.player.getItemBySlot(EquipmentSlot.CHEST);
  if(!(wing.getItem() instanceof NetworkElytraItem)
      && net.neoforged.fml.ModList.get().isLoaded("curios"))
   wing=dev.obsidiannetwork.wireless.NetworkElytraCurios.find(mc.player);
  if(!(wing.getItem() instanceof NetworkElytraItem)
      || EnergyTool.energy(wing)<NetworkElytraItem.SHIFT_COST_PER_5_TICKS)return;
  Vec3 v=mc.player.getDeltaMovement().add(mc.player.getLookAngle().normalize().scale(0.09D));
  if(v.lengthSqr()>2.4D*2.4D)v=v.normalize().scale(2.4D);
  mc.player.setDeltaMovement(v);
 }
}
''',encoding="utf-8")

mod=java/"ObsidianNetwork.java"
t=mod.read_text(encoding="utf-8")
old="net.minecraft.world.item.equipment.EquipmentAssets.ELYTRA"
new='''net.minecraft.resources.ResourceKey.create(
                  net.minecraft.world.item.equipment.EquipmentAssets.ROOT_ID,
                  net.minecraft.resources.Identifier.fromNamespaceAndPath("obsidiannetwork","network_elytra"))'''
assert t.count(old)==1
mod.write_text(t.replace(old,new,1),encoding="utf-8")

def put(path,content):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(content,indent=2)+"\\n",encoding="utf-8")

# Modern Curios uses vanilla item tags; both optional slots are supported.
for slot in ("back","elytra"):
 put(res/("data/curios/tags/item/"+slot+".json"),{"replace":False,"values":["obsidiannetwork:network_elytra"]})
 put(res/("data/curios/tags/items/"+slot+".json"),{"replace":False,"values":["obsidiannetwork:network_elytra"]})

# Provision one dedicated back slot when Curios alone is installed. Merges by slot ID.
put(res/"data/obsidiannetwork/curios/slots/back.json",
    {"size":1,"order":100,"icon":"curios:slot/empty_back_slot"})
put(res/"data/obsidiannetwork/curios/entities/players.json",
    {"entities":["minecraft:player"],"slots":["back"]})

put(res/"assets/obsidiannetwork/equipment/network_elytra.json",
    {"layers":{"wings":[{"texture":"obsidiannetwork:network_elytra","use_player_texture":False}]}})
put(res/"assets/obsidiannetwork/models/item/network_elytra.json",
    {"parent":"minecraft:item/generated","textures":{"layer0":"obsidiannetwork:item/network_elytra"}})

# Bundled 2D item icon and 3D Elytra-model wing atlas: shaded titanium/purple
# with readable wing silhouette, luminous cyan-violet circuitry, edge plating.
# Pure stdlib PNG to avoid new Gradle/Python build dependencies.
def png(path,w,h,pixel):
 rows=[]
 for y in range(h):
  row=bytearray([0])
  for x in range(w):
   row.extend(pixel(x,y))
  rows.append(bytes(row))
 raw=zlib.compress(b"".join(rows),9)
 def chunk(name,data):
  return struct.pack(">I",len(data))+name+data+struct.pack(">I",zlib.crc32(name+data)&0xffffffff)
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(b"\\x89PNG\\r\\n\\x1a\\n"+chunk(b"IHDR",struct.pack(">2I5B",w,h,8,6,0,0,0))+chunk(b"IDAT",raw)+chunk(b"IEND",b""))

def icon(x,y):
 # Symmetric articulated panels; turquoise conduits contrast the graphite shell.
 X=x/2;Y=y/2
 wing=abs(X-16)
 if wing>14 or Y<5 or Y>26:return (0,0,0,0)
 inner=5.5+0.37*(Y-5)
 outer=13.8-0.20*(Y-5)
 if not(inner<=wing<=outer):return (0,0,0,0)
 edge=min(wing-inner,outer-wing)
 if edge<0.9:return (117,102,147,255)
 vein=abs(Y-(6.2+1.05*(wing-6)))
 if vein<0.7:return (53,210,234,255)
 if abs(Y-(20-0.37*wing))<0.6:return (162,78,234,255)
 shade=int(27+25*(1-(Y-5)/22)+12*(1-edge/max(1,outer-inner)))
 return (shade,shade-2,shade+21,255)

def wings(x,y):
 # Vanilla wing UVs occupy the central span. Paint every face consistently.
 X=x/2;Y=y/2
 if not(0<=X<64 and 0<=Y<32):return (0,0,0,0)
 in_panel=(22<=X<=45 and 0<=Y<=23) or (0<=X<22 and 0<=Y<=22)
 if not in_panel:return (0,0,0,0)
 u=(X-22 if X>=22 else X)
 v=Y
 edge=(u<2 or u>20 or v<2 or v>20)
 if edge:return (114,93,151,255)
 grid=(int(u*2)%8==0 or int(v*2)%9==0)
 if abs(v-(4+0.56*u))<0.65 or abs(v-(18-0.23*u))<0.65:
  return (58,209,242,255)
 if abs(u-12)<0.55 or abs(u-16)<0.45:return (168,70,218,255)
 shade=int(39+12*math.sin(u*0.27)+9*math.cos(v*0.19))
 return (shade,33,shade+31,255) if not grid else (58,51,86,255)

png(res/"assets/obsidiannetwork/textures/item/network_elytra.png",64,64,icon)
png(res/"assets/obsidiannetwork/textures/entity/equipment/wings/network_elytra.png",128,64,wings)
assert "NETWORK_ELYTRA_CURIOS_BOOST_V2" in item.read_text()
print("NETWORK_ELYTRA_CURIOS_BOOST_V2 PASS: Curios back/elytra + client boost + bundled sci-fi wings and icon")
