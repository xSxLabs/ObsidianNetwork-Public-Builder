#!/usr/bin/env python3
"""Compiled NeoForge 26.1 checks for BOTH GUI slot endpoints and BOTH MG renderpaths.
Does NOT claim pixels were rendered: only a graphical client can prove that.
Companion mandatory real-server test: B1038 cable-connected 50-drive fixture.
"""
import subprocess,sys,zipfile
from pathlib import Path
jar=Path(sys.argv[1]);assert jar.is_file() and jar.stat().st_size>1000000,jar
def code(name):
 p=subprocess.run(["javap","-classpath",str(jar),"-c","-p",name],
                  text=True,capture_output=True,check=True)
 assert "Error:" not in p.stdout,name
 return p.stdout
def section(src,begin):
 assert begin in src,("B1038_MISSING_COMPILED_METHOD",begin)
 a=src.index(begin)
 b=src.find("\n  public ",a+len(begin))
 return src[a:b if b>=0 else len(src)]
with zipfile.ZipFile(jar) as z:
 files=set(z.namelist())
 required=[
 "client/V176MicroMgLayer.class","client/V176MicroMgLayer$Register.class",
 "client/V176MicroMgStandLayer.class","client/V176MicroMgStandLayer$Register.class",
 "cellterminal/V176CellTerminalMenu.class","cellterminal/V176CellTerminalMenu$2.class",
 "client/V176CellTerminalScreen$2.class"]
 for f in required:assert "dev/obsidiannetwork/"+f in files,("B1038_CLASS_ABSENT",f)
 tex="assets/obsidiannetwork/textures/entity/micro_mg_world_barrel.png"
 assert tex in files and z.read(tex).startswith(bytes.fromhex("89504e470d0a1a0a")),"B1038_BARREL_TEXTURE_BAD"
for cls in ("dev.obsidiannetwork.client.V176CellTerminalScreen$2",
            "dev.obsidiannetwork.cellterminal.V176CellTerminalMenu$2"):
 s=code(cls)
 active=section(s,"public boolean isActive();")
 place=section(s,"public boolean mayPlace(net.minecraft.world.item.ItemStack);")
 pickup=section(s,"public boolean mayPickup(net.minecraft.world.entity.player.Player);")
 assert "iconst_1" in active and "ireturn" in active,("B1038_CELL_PAD_INACTIVE",cls)
 assert "StorageCellItem" in place and "EquipmentCellItem" in place,("B1038_CELL_PAD_WRONG_FILTER",cls)
 assert "iconst_0" in pickup and "ireturn" in pickup,("B1038_PHANTOM_CELL_EXTRACT",cls)
menu=code("dev.obsidiannetwork.cellterminal.V176CellTerminalMenu")
clicked=section(menu,"public void clicked(int, int, net.minecraft.world.inventory.ContainerInput, net.minecraft.world.entity.player.Player);")
shift=section(menu,"public net.minecraft.world.item.ItemStack quickMoveStack(net.minecraft.world.entity.player.Player, int);")
for route in (clicked,shift):
 markers=("V176CellTerminalTopology.scan","DriveMenu.xsxCellTerminalBacking",
          "Container.setItem","ItemStack.matches","ItemStack.shrink")
 indexes=[route.find(m) for m in markers]
 assert all(i>=0 for i in indexes) and indexes==sorted(indexes),("B1038_CELL_NOT_ATOMIC_REAL_DRIVE",indexes)
player=code("dev.obsidiannetwork.client.V176MicroMgLayer")
render=section(player,"public void submit(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.client.renderer.SubmitNodeCollector, int, net.minecraft.client.renderer.entity.state.AvatarRenderState, float, float);")
for m in ("V176AttackRenderState.TIER","V176AttackRenderState.ACTIVE","PlayerModel.rightArm","V176MicroMgVisualClient.drawArm"):
 assert m in render,("B1038_PLAYER_BARREL_RENDER_PATH_MISSING",m)
assert "addLayer:" in code("dev.obsidiannetwork.client.V176MicroMgLayer$Register")
stand=code("dev.obsidiannetwork.client.V176MicroMgStandLayer")
render=section(stand,"public void submit(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.client.renderer.SubmitNodeCollector, int, net.minecraft.client.renderer.entity.state.ArmorStandRenderState, float, float);")
for m in ("TURRET_ACTIVE","TURRET_STAND_ID","rightArmPose","RIGHT_ARM_PIVOT","V176MicroMgVisualClient.drawArm"):
 assert m in render,("B1038_TURRET_BARREL_RENDER_PATH_MISSING",m)
reg=code("dev.obsidiannetwork.client.V176MicroMgStandLayer$Register")
for m in ("registerEntityModifier","ArmorStandRenderer.addLayer","xsxlabs_v176_turret"):
 assert m in reg,("B1038_TURRET_RENDER_REGISTRATION_MISSING",m)
visual=code("dev.obsidiannetwork.client.V176MicroMgVisualClient")
render=section(visual,"public static void drawArm(com.mojang.blaze3d.vertex.PoseStack, net.minecraft.client.renderer.SubmitNodeCollector, int, net.minecraft.client.model.geom.ModelPart, int, float);")
assert "XSX_WORLD_BARREL" in render and "SubmitNodeCollector.submitModelPart" in render,"B1038_NO_VISIBLE_BARREL_DRAW_IN_BYTECODE"
print("V176_B1038_COMPILED_CLIENT_GUI_PLAYER_TURRET_BARREL_AND_DRIVE_PATHS_PASS"+
 " scope=bytecode_no_pixels real_world_requires_separate_gametest")
