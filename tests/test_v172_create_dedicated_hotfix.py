#!/usr/bin/env python3
"""Emergency dedicated-server Create compatibility and piston carry regression.

Compile fake Create methods referencing PoseStack, DELETE PoseStack.class before
running, then resolve only the server-side handles and exercise vertical
platform support and movement in both directions. Real Create still needs
in-game validation after a green release build.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PL=(ROOT/"features/v172/apply-power-armor-create-platform-136.py").read_text()
CAR=(ROOT/"features/v172/apply-power-armor-create-carrier-138.py").read_text()

JAVA={
"com/mojang/blaze3d/vertex/PoseStack.java": """
package com.mojang.blaze3d.vertex;
public final class PoseStack {}
""",
"net/minecraft/world/phys/Vec3.java": """
package net.minecraft.world.phys;
public record Vec3(double x,double y,double z) {
 public Vec3 add(double dx,double dy,double dz) {
  return new Vec3(x+dx,y+dy,z+dz);
 }
}
""",
"net/minecraft/core/BlockPos.java": """
package net.minecraft.core;
import net.minecraft.world.phys.Vec3;
public record BlockPos(int x,int y,int z) {
 public static BlockPos containing(Vec3 p) {
  return new BlockPos((int)Math.floor(p.x()),(int)Math.floor(p.y()),
                      (int)Math.floor(p.z()));
 }
}
""",
"com/simibubi/create/content/contraptions/Contraption.java": """
package com.simibubi.create.content.contraptions;
import java.util.Map;
import net.minecraft.core.BlockPos;
public final class Contraption {
 public Map<BlockPos,String> getBlocks(){return Map.of(new BlockPos(0,0,0),"floor");}
}
""",
"com/simibubi/create/content/contraptions/AbstractContraptionEntity.java": """
package com.simibubi.create.content.contraptions;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.world.phys.Vec3;
public class AbstractContraptionEntity {
 private Vec3 offset=new Vec3(10,0,20);
 private final Contraption contraption=new Contraption();
 public void setOffset(Vec3 v){offset=v;}
 public Contraption getContraption(){return contraption;}
 public Vec3 toLocalVector(Vec3 v,float partialTicks){
  return new Vec3(v.x()-offset.x(),v.y()-offset.y(),v.z()-offset.z());
 }
 public Vec3 toGlobalVector(Vec3 v,float partialTicks){
  return new Vec3(v.x()+offset.x(),v.y()+offset.y(),v.z()+offset.z());
 }
 public void applyLocalTransforms(PoseStack CLIENT_ONLY,float partialTicks){}
}
""",
"Launcher.java": """
import java.lang.invoke.*;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.Vec3;
public final class Launcher {
 static void require(boolean value,String message){
  if(!value)throw new AssertionError(message);
 }
 public static void main(String[] args) throws Throwable {
  ClassLoader loader=Launcher.class.getClassLoader();
  Class<?> base=Class.forName(
    "com.simibubi.create.content.contraptions.AbstractContraptionEntity",false,loader);
  Class<?> type=Class.forName(
    "com.simibubi.create.content.contraptions.Contraption",false,loader);
  MethodHandles.Lookup lookup=MethodHandles.publicLookup();
  MethodType transform=MethodType.methodType(Vec3.class,Vec3.class,float.class);
  MethodHandle local=lookup.findVirtual(base,"toLocalVector",transform);
  MethodHandle global=lookup.findVirtual(base,"toGlobalVector",transform);
  MethodHandle get=lookup.findVirtual(base,"getContraption",
      MethodType.methodType(type));
  MethodHandle blocksHandle=lookup.findVirtual(type,"getBlocks",
      MethodType.methodType(Map.class));
  Object entity=base.getConstructor().newInstance();
  Vec3 foot=new Vec3(10.5,1,20.5);
  Vec3 point=(Vec3)local.invoke(entity,foot,1F);
  Map<?,?> blocks=(Map<?,?>)blocksHandle.invoke(get.invoke(entity));
  BlockPos underneath=BlockPos.containing(point.add(0,-.125,0));
  require(blocks.containsKey(underneath),"real support block must be below feet");
  require(Math.abs(point.y()-(underneath.y()+1))<.5,"feet must rest on actual floor");
  MethodHandle set=lookup.findVirtual(base,"setOffset",
      MethodType.methodType(void.class,Vec3.class));
  set.invoke(entity,new Vec3(10,3.25,20));
  Vec3 raised=(Vec3)global.invoke(entity,point,1F);
  require(Math.abs(raised.y()-4.25)<1e-8,"mechanical piston UP");
  set.invoke(entity,new Vec3(10,-4.5,20));
  Vec3 lowered=(Vec3)global.invoke(entity,point,1F);
  require(Math.abs(lowered.y()+3.5)<1e-8,"mechanical piston DOWN");
  require(Math.abs(raised.x()-foot.x())<1e-8,"retain local X");
  require(Math.abs(lowered.z()-foot.z())<1e-8,"retain local Z");
  System.out.println("DEDICATED_CREATE_NO_POSESTACK_UP_DOWN_PASS");
 }
}
"""
}

class CreateDedicatedHotfix(unittest.TestCase):
 def test_one_owner_of_real_armor_stand(self):
  self.assertNotIn("@EventBusSubscriber",PL)
  self.assertIn("@EventBusSubscriber",CAR)
  self.assertIn("stand.setPos(dest.x,dest.y,dest.z)",CAR)
  self.assertIn("world.noCollision(stand,stand.getBoundingBox().move(delta))",CAR)
  self.assertIn("PowerArmorRecallIndex.get(level.getServer()).index",CAR)
  self.assertNotIn("setItemSlot(",CAR)
  self.assertNotIn("addFreshEntity(",CAR)
 def test_no_reflective_client_class_enumeration(self):
  for source in (PL,CAR):
   self.assertNotIn(".getMethod(",source)
   self.assertNotIn(".getMethods(",source)
   self.assertNotIn("import net.minecraft.client",source)
   self.assertNotIn("import com.mojang.blaze3d",source)
  self.assertIn("lookup.findVirtual(base",CAR)
  self.assertIn("MethodType.methodType(Map.class)",CAR)
 def test_actual_jvm_missing_pose_stack_and_both_piston_directions(self):
  if not shutil.which("javac") or not shutil.which("java"):
   self.skipTest("JDK missing")
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   sources=[]
   for rel,body in JAVA.items():
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(body);sources.append(str(p))
   classes=root/"classes";classes.mkdir()
   subprocess.run(["javac","-d",str(classes),*sources],check=True,
                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   missing=classes/"com/mojang/blaze3d/vertex/PoseStack.class"
   self.assertTrue(missing.is_file())
   missing.unlink()
   result=subprocess.run(["java","-cp",str(classes),"Launcher"],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertIn("DEDICATED_CREATE_NO_POSESTACK_UP_DOWN_PASS",result.stdout)

if __name__=="__main__":unittest.main()
