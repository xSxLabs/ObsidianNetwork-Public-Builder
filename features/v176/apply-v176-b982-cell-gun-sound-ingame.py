#!/usr/bin/env python3
"""B982: approved Build 998 in-game findings. Applied strictly AFTER B980.

Real-drive cell insertion (shift-click and carried-cell drop slot), a distinct
Cell Terminal front only, right-arm world muzzle with no floating hatch, turret
stand activation, 20 rounds/second and a punchier positional shot mix.
The first-person gun, other five block faces, cell NBT and FE debit stay intact.
"""
import json
import os
import re
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def replace(rel,old,new):
    p=J/rel
    source=p.read_text(encoding="utf-8")
    assert source.count(old)==1,("B982_SOURCE_DRIFT",rel,source.count(old),old[:100])
    p.write_text(source.replace(old,new,1),encoding="utf-8")

# 1. Keep the complete original Crafting Terminal casing, change FRONT ONLY.
# A separate violet cell-bank overlay draws solely on the north/front face.
from PIL import Image,ImageDraw
model_path=A/"models/block/cell_terminal.json"
model=json.loads(model_path.read_text(encoding="utf-8"))
assert model.get("elements") and model["textures"].get("ns_violet")
original_faces=json.dumps(model["elements"],sort_keys=True)
model["textures"]["xsx_cell_front"]="obsidiannetwork:block/cell_terminal_b982_front"
model["elements"].append({
 "from":[2.0,2.0,-0.16],"to":[14.0,14.0,-0.06],
 "faces":{"north":{"uv":[0,0,16,16],"texture":"#xsx_cell_front"}}
})
assert all("south" not in element["faces"] and "east" not in element["faces"]
           and "west" not in element["faces"] and "up" not in element["faces"]
           and "down" not in element["faces"] for element in model["elements"][-1:])
assert original_faces==json.dumps(model["elements"][:-1],sort_keys=True)
model_path.write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
front=Image.new("RGBA",(32,32),(19,14,36,255))
d=ImageDraw.Draw(front)
d.rectangle((1,1,30,30),fill=(35,25,64),outline=(117,66,170))
d.rectangle((3,3,28,28),fill=(13,13,31),outline=(172,91,221))
d.rectangle((5,6,26,11),fill=(56,30,91),outline=(123,77,176))
for x in (7,14,21):
 d.rectangle((x,14,x+4,24),fill=(28,42,70),outline=(128,76,199))
 d.rectangle((x+1,16,x+3,21),fill=(125,76,216))
 d.point((x+2,23),fill=(87,236,211))
d.line((6,27,25,27),fill=(83,203,205),width=2)
front.save(A/"textures/block/cell_terminal_b982_front.png")

# 2. Graph-first adjacency fails when a terminal touches a passive network
# cable: discover a powered graph node through the same NETWORK-only cable
# component. Search only already loaded blocks and stop at 16384 cables.
bridge="network/WorldTopologyBridge.java"
p=J/bridge
s=p.read_text(encoding="utf-8")
a=s.index("   public static NetworkRuntime xsxCellTerminalNetwork(")
b=s.index("   // Use existing authoritative drive registry",a)
method=r"""   public static NetworkRuntime xsxCellTerminalNetwork(ServerLevel level,BlockPos pos) {
      if(level==null||pos==null||!level.hasChunkAt(pos))return null;
      java.util.ArrayDeque<BlockPos> pending=new java.util.ArrayDeque<>();
      java.util.HashSet<Long> seen=new java.util.HashSet<>();
      // Directly connected controllers, terminals and drives take precedence.
      for(Direction face:Direction.values()){
         BlockPos neighbor=pos.relative(face);
         if(!level.hasChunkAt(neighbor))continue;
         NetworkRuntime network=runtimeForTerminal(level,neighbor);
         if(network==null)network=runtimeForDrive(level,neighbor);
         if(network==null)network=runtimeForController(level,neighbor);
         if(network==null)network=runtimeForAccessory(level,neighbor);
         if(network!=null&&network.powered())return network;
         if(NetworkSignalRelayBridge.networkWire(level,neighbor)
              &&seen.add(neighbor.asLong()))pending.addLast(neighbor);
      }
      // A terminal connected solely via cables must also resolve the actual
      // controller/drive graph, not be declared offline.
      while(!pending.isEmpty()&&seen.size()<=16384){
         BlockPos cable=pending.removeFirst();
         if(!level.hasChunkAt(cable)
             ||!NetworkSignalRelayBridge.networkWire(level,cable))continue;
         NetworkRuntime own=runtimeForAccessory(level,cable);
         if(own!=null&&own.powered())return own;
         for(Direction face:Direction.values()){
            BlockPos neighbor=cable.relative(face);
            if(!level.hasChunkAt(neighbor)||neighbor.equals(pos))continue;
            NetworkRuntime network=runtimeForDrive(level,neighbor);
            if(network==null)network=runtimeForTerminal(level,neighbor);
            if(network==null)network=runtimeForController(level,neighbor);
            if(network!=null&&network.powered())return network;
            if(seen.size()<16384
                &&NetworkSignalRelayBridge.networkWire(level,neighbor)
                &&seen.add(neighbor.asLong()))pending.addLast(neighbor);
         }
      }
      return null;
   }
"""
assert "xsxCellTerminalDrives(" in s
assert "xsxCellTerminalDrives(" in s[b:]
s=s[:a]+method+s[b:]
p.write_text(s,encoding="utf-8")

# 3. Manual click: a visible drop slot in the otherwise virtual ChestMenu.
# It NEVER stores cells in the phantom menu container. Only real DriveMenu BE
# backing containers are written, and the carried item is consumed after readback.
menu="cellterminal/V176CellTerminalMenu.java"
replace(menu,
'''   });
  }
 }
 @Override public boolean stillValid(Player player){''',
'''   });
  }
  Slot oldDrop=slots.get(0);
  slots.set(0,new Slot(oldDrop.container,oldDrop.getContainerSlot(),80,56){
   @Override public boolean isActive(){return true;}
   @Override public boolean mayPlace(ItemStack item){
    return item.getItem() instanceof StorageCellItem;
   }
   @Override public boolean mayPickup(Player player){return false;}
  });
 }
 @Override public boolean stillValid(Player player){''')
replace(menu,
''' @Override public void clicked(int slotId,int button,ContainerInput action,Player player){
  // No spoofed slot insertion into a non-existent cell holding inventory.
  if(slotId>=0&&slotId<54)return;
  super.clicked(slotId,button,action,player);
 }''',
''' @Override public void clicked(int slotId,int button,ContainerInput action,Player player){
  // The first visible slot is an INPUT ACTION, never an inventory.
  if(slotId==0){
   if(!(player instanceof ServerPlayer server)
       ||!(server.level() instanceof ServerLevel world)
       ||button<0||button>1||!stillValid(player))return;
   ItemStack carried=getCarried();
   if(carried.isEmpty()||!(carried.getItem() instanceof StorageCellItem))return;
   var scan=V176CellTerminalTopology.scan(world,terminal.getBlockPos());
   if(!scan.online()||scan.freeSlots()<1)return;
   var drives=new ArrayList<>(scan.drives());
   drives.sort(Comparator.comparingInt(StorageDriveBlockEntity::occupiedSlots)
        .thenComparingLong(d->d.getBlockPos().asLong()));
   for(StorageDriveBlockEntity drive:drives){
    if(drive.isRemoved()||drive.getLevel()!=world
       ||!world.hasChunkAt(drive.getBlockPos()))continue;
    int target=drive.xsxCellTerminalFirstEmptySlot();
    if(target<0)continue;
    Container backing=DriveMenu.xsxCellTerminalBacking(drive);
    if(!backing.getItem(target).isEmpty())continue;
    ItemStack one=carried.copyWithCount(1);
    backing.setItem(target,one);
    if(!ItemStack.matches(backing.getItem(target),one)){
     ItemStack rollback=backing.removeItemNoUpdate(target);
     if(!ItemStack.matches(rollback,one))
      throw new IllegalStateException("Cell Terminal drop slot insert mismatch");
     return;
    }
    carried.shrink(1); // after the real drive confirms the exact cell
    setCarried(carried);
    broadcastChanges();
    return;
   }
   return;
  }
  // All other 53 virtual preview slots remain disabled.
  if(slotId>0&&slotId<54)return;
  super.clicked(slotId,button,action,player);
 }''')
screen="client/V176CellTerminalScreen.java"
replace(screen,
'''   });
  }
 }
 private V176CellTerminalBlockEntity live(){''',
'''   });
  }
  Slot oldDrop=this.menu.slots.get(0);
  this.menu.slots.set(0,new Slot(oldDrop.container,oldDrop.getContainerSlot(),80,56){
   @Override public boolean isActive(){return true;}
   @Override public boolean mayPlace(ItemStack item){
    return item.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem;
   }
   @Override public boolean mayPickup(net.minecraft.world.entity.player.Player p){return false;}
  });
 }
 private V176CellTerminalBlockEntity live(){''')
replace(screen,
'''  g.text(font,"SHIFT-CLICK Storage Cells to distribute",8,111,0xff90f4ff);''',
'''  g.text(font,"Drop Cell above or SHIFT-CLICK inventory",8,111,0xffb899ff);''')
replace(screen,
'''  g.fill(x+8,y+100,x+168,y+103,0xff31677b);''',
'''  g.fill(x+8,y+100,x+168,y+103,0xff735397);
  g.fill(x+78,y+54,x+98,y+74,0xff7e56b9);
  g.fill(x+79,y+55,x+97,y+73,0xff271438);''')

# 4. Keep only one slim barrel in the third-person right arm draw.
# First-person BARREL and elbow/crosshair quaternion are NOT touched.
visual="client/V176MicroMgVisualClient.java"
replace(visual,
 '''        .addBox(-0.62F,5.0F,-3.15F,1.24F,8.5F,1.25F),PartPose.ZERO);''',
 '''        .addBox(-0.52F,3.8F,-2.95F,1.04F,9.5F,1.05F),PartPose.ZERO);''')
replace(visual,
 '''   pose.translate(0.0F,0.0F,-0.075F);''',
 '''   pose.translate(0.0F,0.0F,0.04F);''')
p=J/visual
s=p.read_text(encoding="utf-8")
a=s.index(" public static void drawArm(")
b=s.index("\n }",a)+3
arm=s[a:b]
arm,removed=re.subn(r"(?m)^\s*nodes\.submitModelPart\(HATCH,pose,RenderTypes\.entitySolid\(texture\(tier\)\),\s*\n\s*light,OverlayTexture\.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0\);",
                   "\n   // B982: no floating plate; the world gun is barrel-only.",arm)
assert removed==1,("B982_WORLD_HATCH_NOT_FOUND",removed)
assert "nodes.submitModelPart(XSX_WORLD_BARREL,pose" in arm
s=s[:a]+arm+s[b:]
# ArmorStand muzzle is active on the authoritative turret tag, or the
# already-synced arm pose as before; no arbitrary free armor-stand guns.
old='''   boolean armed=has(chest,"micro_mg")&&
       (has(chest,"micro_mg_turret_on")||stand.getRightArmPose().x()<-45F);'''
assert s.count(old)==1,("B982_STAND_ARMED_DRIFT",s.count(old))
new='''   boolean armed=stand.entityTags().contains("xsxlabs_v176_turret")||
       (has(chest,"micro_mg")&&
        (has(chest,"micro_mg_turret_on")||stand.getRightArmPose().x()<-45F));'''
s=s.replace(old,new,1)
assert "drawRight(xsxTurretPose,event.getSubmitNodeCollector()," in s
assert 'xsxLogTurretPose(stand.getId(),tier,amount,"EXIT")' in s
p.write_text(s,encoding="utf-8")

# 5. 16 -> 20 physically spawned rounds per second, preserving 3000FE/round,
# module checks, friendly-fire protection and per-tick server authority.
rules="powerarmor/V176MicroMgRules.java"
replace(rules,
'''  return tick>=lastShotTick && tick-lastShotTick>=COOLDOWN_TICKS
      &&tick%5L!=4L; // 0,1,2,3,5,6,7,8,... 16 shots per second''',
'''  return tick>=lastShotTick && tick-lastShotTick>=COOLDOWN_TICKS;
  // 20 server-authorized rounds per 20 ticks; still at most one per tick.''')
# 6. More percussive positional burst: short blast transient + mechanical click;
# no synthetic noise played on clients independent of real server shots.
replace("powerarmor/V176MicroMgFire.java",
'''   world.playSound(null,p.blockPosition(),SoundEvents.CROSSBOW_SHOOT,
      SoundSource.PLAYERS,0.45F,1.75F);''',
'''   float pitch=1.20F+0.04F*(now%3L);
   world.playSound(null,p.blockPosition(),SoundEvents.FIREWORK_ROCKET_BLAST,
      SoundSource.PLAYERS,0.32F,pitch);
   world.playSound(null,p.blockPosition(),SoundEvents.CROSSBOW_SHOOT,
      SoundSource.PLAYERS,0.16F,1.95F);''')
replace("powerarmor/V176CompanionMode.java",
'''    world.playSound(null,suit.blockPosition(),SoundEvents.CROSSBOW_SHOOT,
      SoundSource.PLAYERS,0.45F,1.7F);''',
'''    float pitch=1.20F+0.04F*(now%3L);
    world.playSound(null,suit.blockPosition(),SoundEvents.FIREWORK_ROCKET_BLAST,
      SoundSource.PLAYERS,0.32F,pitch);
    world.playSound(null,suit.blockPosition(),SoundEvents.CROSSBOW_SHOOT,
      SoundSource.PLAYERS,0.16F,1.95F);''')

# Regression contracts: 1P gun untouched, real backing, unchanged non-front
# terminal geometry, single world barrel and both live sound origins.
m=(J/menu).read_text(encoding="utf-8")
v=(J/visual).read_text(encoding="utf-8")
assert "backing.setItem(target,one);" in m
assert "carried.shrink(1); // after the real drive confirms" in m
assert "if(slotId>0&&slotId<54)return;" in m
assert v.count("nodes.submitModelPart(XSX_WORLD_BARREL,pose")==1
assert "nodes.submitModelPart(BARREL,pose" in v
assert "nodes.submitModelPart(HATCH,pose" not in v[v.index(" public static void drawArm("):v.index("\n }",v.index(" public static void drawArm("))+3]
assert "XSXLABS_TEMP_B980_TURRET_RENDER" in v
assert "NetworkSignalRelayBridge.networkWire(level,cable)" in (J/bridge).read_text()
assert "world.playSound" in (J/"powerarmor/V176CompanionMode.java").read_text()
assert "tick%5L!=4L" not in (J/rules).read_text()
print("B982_CELL_CLICK_AND_GRAPH_FRONT_ONLY_BARREL_ONLY_TURRET_20RPS_SHOT_MIX_PASS")
