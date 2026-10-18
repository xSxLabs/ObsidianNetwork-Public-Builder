#!/usr/bin/env python3
"""CI-only actual runtime linkage probe with Curios absent AND installed.

The owner GameTest runs on a bare NeoForge server first, and a separate CI run
relaunches the same post-patch GameTests with the Curios mod runtime jar.
Only reflectively touch the Curios adapter after checking ModList, to verify
that absence causes no classloader resolution and presence is actually usable.
Does not claim to prove a full inventory accessory charging scenario.
"""
import os
from pathlib import Path

f=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=f.read_text()
anchor='''                     System.out.println("WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 PASS");
                   })'''
assert s.count(anchor)==1,"wireless Curios post-owner anchor missing"
assert "WIRELESS_CURIOS_INSTALLED_LINKAGE_V1" not in s
extra=r'''
                   .thenExecuteAfter(2,()->{
                     boolean loaded=net.neoforged.fml.ModList.get().isLoaded("curios");
                     if(!loaded){
                      // The core loading path must never try resolving Curios API.
                      System.out.println("WIRELESS_CURIOS_ABSENT_START_V1 PASS");
                     }else{
                      try{
                       Class.forName("top.theillusivec4.curios.api.CuriosApi");
                       var bridge=Class.forName("dev.obsidiannetwork.wireless.WirelessCuriosCharging");
                       var method=bridge.getDeclaredMethod("charge",
                        net.minecraft.server.level.ServerPlayer.class,java.util.List.class,int.class);
                       method.setAccessible(true);
                       var probe=net.neoforged.neoforge.common.util.FakePlayerFactory.get(
                        helper.getLevel(),new com.mojang.authlib.GameProfile(
                         java.util.UUID.fromString("22130b0e-1c47-4bc4-822a-a78c5f61ea03"),"CuriosProbe"));
                       int charged=((Integer)method.invoke(null,probe,
                        java.util.List.of(),1024)).intValue();
                       check(charged==0,"WIRELESS Curios adapter charged with zero networks");
                       System.out.println("WIRELESS_CURIOS_INSTALLED_LINKAGE_V1 PASS");
                      }catch(ReflectiveOperationException error){
                       throw new IllegalStateException("WIRELESS installed Curios linkage failed",error);
                      }
                     }
                   })'''
f.write_text(s.replace(anchor,anchor+extra,1))
print("WIRELESS_CURIOS_DUAL_RUNTIME_GAMETEST_V1 INJECTED")
