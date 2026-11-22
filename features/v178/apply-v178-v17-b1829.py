#!/usr/bin/env python3
"""v1.7.8 v17: 12-high Powerbank skin, reversible miner upgrades,
reference-style pickaxe, rotating skin-only map marker, smooth high-speed travel.

Applied after legacy v15 fixtures have checked their original snapshot.
No changed FE semantics, chunk tickets, mining budgets or worldmap persistence.
"""
import os
import re
import json
from pathlib import Path
from PIL import Image, ImageDraw

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def change(rel, before, after):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    assert s.count(before)==1, ("V17_ANCHOR",rel,before[:90],s.count(before))
    p.write_text(s.replace(before,after,1),encoding="utf-8")

def bounded_integer(rel, start, end, old, new):
    """Change only the named bounded BFS, never geometry/FE or reactor logic."""
    p=J/rel
    s=p.read_text("utf-8")
    a=s.index(start)
    b=s.index(end,a)
    method=s[a:b]
    matches=list(re.finditer(r"(?<![a-zA-Z_0-9])"+str(old)+r"(?![a-zA-Z_0-9])",method))
    assert len(matches)==1, ("V17_BOUNDED_BFS_DRIFT",rel,start,len(matches))
    method=method[:matches[0].start()]+str(new)+method[matches[0].end():]
    p.write_text(s[:a]+method+s[b:],"utf-8")

# B1829: the old 216-visited budget counts non-shell neighbor probes too.
# A complete 3x3x12 shell visits about 270 positions even though its shell
# itself has only 98 blocks. Both formation skin and charged-light pass were
# stopping before the final 3 rows. 512 is bounded and within loaded chunks.
bounded_integer("powerbank/PowerbankBlockEntity.java",
    "private static void skin(", "public long guiInputFePerTick",216,512)
bounded_integer("multiblock/MultiblockSkinBlock.java",
    "public static void illuminate(", "public static void applyAssemblyBands(",216,512)

# B1830: in addition to the vanilla slot, an owner-validated, server-side
# GUI retrieval path handles broken/mismatched click packets. No client-side
# inventory edits. The old -1 poll and 0..2 redstone controls are unchanged.
change("mining/V178MiningBuilderControl.java",
    """   if(!be.canOperate(player))return;
   if(msg.mode>=0&&!be.setRedstoneMode(player,msg.mode))return;
   V178MiningBuilderStatus.send(player,be,false);""",
    """   if(!be.canOperate(player))return;
   if(msg.mode==-2){
    // B1830_AUTHORITATIVE_UPGRADE_RECOVERY: one server-owned removal.
    var upgrades=be.removeSpeedUpgrades(player,16);
    if(!upgrades.isEmpty()){
     player.getInventory().add(upgrades);
     if(!upgrades.isEmpty())player.drop(upgrades,false);
    }
   }else if(msg.mode>=0&&!be.setRedstoneMode(player,msg.mode))return;
   V178MiningBuilderStatus.send(player,be,false);""")
change("client/V178MiningBuilderOperationsScreen.java",
    """addRenderableWidget(redstone);""",
    """addRenderableWidget(redstone);
   addRenderableWidget(Button.builder(Component.literal("SPEED-UPGRADES ENTNEHMEN"),b->{
     ClientPacketDistributor.sendToServer(new V178MiningBuilderControl(machine,-2));
   }).bounds(x+7,y+149,235,20).build());""")
change("client/V178MiningBuilderOperationsScreen.java",
    """V178UiTheme.panel(g,xx,y-4,252,h+8);""",
    """V178UiTheme.panel(g,xx,y-4,252,h+33);""")
change("client/V178MiningBuilderOperationsScreen.java",
    """xx+9,y+153,0xff8aabba);""",
    """xx+9,y+178,0xff8aabba);""")

# B1831: only the real player head, yaw-rotated 360 degrees. A single skin
# face extraction inside a 2D pose (no second compass pointer or world reads).
p=J/"client/V178MapMarkers.java"
s=p.read_text("utf-8")
start="  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){"
assert s.count(start)==1
a=s.index(start)
b=s.index("\n  }\n}",a)+len("\n  }")
old=s[a:b]
assert "PlayerFaceExtractor.extractRenderState" in old and "B1804_SMALL_POINTER" in old
new="""  public static void player(GuiGraphicsExtractor g,int x,int y,float yaw){
   // B1831_SKIN_ONLY_ROTATING_HEAD: north-up map, yaw=0 is south.
   var mc=net.minecraft.client.Minecraft.getInstance();
   g.pose().pushMatrix();
   g.pose().translate(x,y);
   g.pose().rotate((float)Math.toRadians(yaw+180.0f));
   g.fill(-3,-3,3,3,0xff071824);
   if(mc.player==null)g.fill(-2,-2,2,2,0xffffffff);
   else net.minecraft.client.gui.components.PlayerFaceExtractor.extractRenderState(
      g,mc.player.getSkin(),-2,-2,4);
   g.pose().popMatrix();
  }"""
p.write_text(s[:a]+new+s[b:],"utf-8")

# B1832: smooth movement during elytra/flight fast travel; the legacy 3-block
# gate disabled render-frame interpolation during high-speed movement.
# GPU scroll occurs every rendered frame; world chunks remain sampled on ticks.
change("client/V178MiniRaster.java",
    """if(Math.abs(interpX-lastX)<3.0D && Math.abs(interpZ-lastZ)<3.0D){""",
    """if(Math.abs(interpX-lastX)<Math.max(32.0D,lastCrop*0.50D)
       && Math.abs(interpZ-lastZ)<Math.max(32.0D,lastCrop*0.50D)){""")
change("client/V178MiniRaster.java",
    """float partial=mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);""",
    """float partial=Math.max(0.0f,Math.min(1.0f,
         mc.getDeltaTracker().getGameTimeDeltaPartialTick(false)));""")

# B1833: reference image inspired ice-blue curved pickaxe and wooden diagonal
# handle in the EXISTING 32px baked front atlas. Preserve housing and UVs.
front=A/"textures/block/mining_builder_front_v15.png"
with Image.open(front) as src:
    assert src.size==(32,32) and src.mode=="RGBA"
    img=src.copy()
d=ImageDraw.Draw(img)
# Clear just the monitor interior, not the purple casing/bezel.
d.rectangle((5,7,26,26),fill=(10,25,42,255))
# Wood handle from bottom-left to upper-right with dark outline and warm bevel.
d.line([(8,25),(21,12)],fill=(52,36,29,255),width=5)
d.line([(8,25),(21,12)],fill=(145,93,54,255),width=3)
d.line([(8,24),(20,12)],fill=(202,147,85,255),width=1)
# Broad, curved steel head. Right edge bends down to the pointed end.
d.polygon([(8,11),(11,9),(15,8),(19,8),(23,10),(25,13),
           (26,17),(26,22),(24,19),(23,15),(21,12),
           (18,11),(14,10),(11,10)],fill=(80,177,204,255))
d.line([(9,11),(12,9),(16,8),(19,9),(22,11)],fill=(192,240,243,255),width=1)
d.line([(23,12),(25,16),(25,20)],fill=(127,221,237,255),width=1)
d.point((20,10),fill=(231,253,250,255))
d.point((24,14),fill=(175,244,241,255))
img.save(front,optimize=True)

# Fail closed on the exact reconstructed sources and packaged resource model.
b=(J/"powerbank/PowerbankBlockEntity.java").read_text("utf-8")
m=(J/"multiblock/MultiblockSkinBlock.java").read_text("utf-8")
assert "512" in b[b.index("private static void skin("):b.index("public long guiInputFePerTick")]
assert "512" in m[m.index("public static void illuminate("):m.index("public static void applyAssemblyBands(")]
ctrl=(J/"mining/V178MiningBuilderControl.java").read_text("utf-8")
assert "B1830_AUTHORITATIVE_UPGRADE_RECOVERY" in ctrl
assert "player.getInventory().add(upgrades)" in ctrl
assert "be.removeSpeedUpgrades(player,16)" in ctrl
ops=(J/"client/V178MiningBuilderOperationsScreen.java").read_text("utf-8")
assert "SPEED-UPGRADES ENTNEHMEN" in ops
marker=(J/"client/V178MapMarkers.java").read_text("utf-8")
assert "B1831_SKIN_ONLY_ROTATING_HEAD" in marker and "rotate(" in marker
assert "for(int t=" not in marker[marker.index(start):]
mini=(J/"client/V178MiniRaster.java").read_text("utf-8")
assert "lastCrop*0.50D" in mini
with Image.open(front) as out:assert out.size==(32,32) and out.getpixel((19,9))[0]>100
print("V178_V17_12_ROW_POWERBANK_ALL_SKIN_SPEED_RECOVERY_CURVED_PICKAXE_ROTATING_HEAD_SMOOTH_FLIGHT_PASS")
