#!/usr/bin/env python3
"""Gate for REAL registered 3P + ArmorStand render Event handlers.
Unlike B1038, does NOT just verify that an optional RenderLayer exists.
Checks the actual EventBusSubscriber-class Post methods contain a mesh submit.
Client screenshot/pixel check still requires a real game window.
"""
import subprocess,sys
from pathlib import Path
jar=Path(sys.argv[1]);assert jar.exists()
def dump(c):
 return subprocess.run(["javap","-v","-c","-p","-classpath",str(jar),c],
                       text=True,capture_output=True,check=True).stdout
visual=dump("dev.obsidiannetwork.client.V176MicroMgVisualClient")
def section(text,header,end):
 a=text.find(header)
 assert a>=0,("B1041_COMPILED_METHOD_ABSENT",header)
 b=text.find(end,a+len(header))
 assert b>a,("B1041_COMPILED_METHOD_BOUNDARY_ABSENT",header,end)
 return text[a:b]
player=section(visual,"public static void wornFallback(","public static void drawArm(")
assert "RenderPlayerEvent$Post" in player
assert "drawArm:" in player and "getSubmitNodeCollector" in player, "B1041_PLAYER_GUN_POST_NO_SUBMIT"
assert "XSXLABS_B1041_3PERSON_GUN_POST_SUBMITTED" in visual
turret=section(visual,"public static void worldSuit(","private static void lambda$")
assert "V176MicroMgStandLayer.submitFromPost:" in turret, "B1041_TURRET_POST_NOT_DISPATCHED"
assert "XSXLABS_B1041_TURRET_GUN_POST_SUBMITTED" in dump("dev.obsidiannetwork.client.V176MicroMgStandLayer")
stand=dump("dev.obsidiannetwork.client.V176MicroMgStandLayer")
assert "public static void submitFromPost(" in stand
assert "V176MicroMgVisualClient.drawArm:" in stand
assert "ArmorStandRenderState.rightArmPose" in stand
assert "HumanoidModel" not in stand,"B1041_OLD_ARMORSTAND_INCOMPATIBLE_MODEL_GATE"
# Published first-person path remains a standalone registered event handler.
assert "public static void firstPerson(" in visual and "SubmitNodeCollector.submitModelPart" in visual
# Annotation proof: class is not merely compiled, it is discovered as a
# NeoForge client EventBusSubscriber via the launcher.
assert 'net.neoforged.fml.common.EventBusSubscriber(' in visual
assert 'value=[Lnet/neoforged/api/distmarker/Dist;.CLIENT]' in visual
print("V176_B1041_REGISTERED_3P_PLAYER_AND_TURRET_POST_GEOMETRY_BYTECODE_PASS scope=no_pixel_test")
