#!/usr/bin/env python3
"""B378: remove fixed 16-block blueprint axes across all machines."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(file,old,new):
 p=J/file
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(file,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
item="item/NetworkBlueprintItem.java"
change(item,"public static final int MAX_SIZE=16;",
 """// B378_LARGE_BLUEPRINT: no 16-block axis restriction.
 public static final int MAX_SIZE=Integer.MAX_VALUE;
 public static final int MAX_BLOCKS=Math.max(4096,
     Math.min(16777216,Integer.getInteger("xsxlabs.blueprint.maxBlocks",1048576)));""")
quill="item/NetworkSchematicQuillItem.java"
change(quill,"if(sx>MAX_SIZE||sy>MAX_SIZE||sz>MAX_SIZE){",
       "long volume=(long)sx*sy*sz;\n  if(volume<=0L||volume>MAX_BLOCKS){")
change(quill,"Blueprint selection too large (max 16 x 16 x 16). Select the first corner again.",
       "Blueprint too large for available server memory (max \"+MAX_BLOCKS+\" blocks).")
change(quill,"ArrayList<String> out=new ArrayList<>(sx*sy*sz);ArrayList<String> states=new ArrayList<>(sx*sy*sz);",
       "ArrayList<String> out=new ArrayList<>((int)volume);ArrayList<String> states=new ArrayList<>((int)volume);")
change("item/BlueprintPlacementPayload.java","sx>16||sy>16||sz>16||rot<0||rot>7",
       "(long)sx*sy*sz>NetworkBlueprintItem.MAX_BLOCKS||rot<0||rot>7")
change("item/BlueprintPlacementPayload.java","NetworkBlueprintItem.blocks(stack).size()>4096",
       "NetworkBlueprintItem.blocks(stack).size()>NetworkBlueprintItem.MAX_BLOCKS")
change(item,"sx>16||sy>16||sz>16||rotation<0||rotation>7",
       "(long)sx*sy*sz>MAX_BLOCKS||rotation<0||rotation>7")
change("blockentity/NetworkDeviceBlockEntity.java",
       "d[0]<=16&&d[1]<=16&&d[2]<=16?d:new int[0]",
       "(long)d[0]*d[1]*d[2]<=NetworkBlueprintItem.MAX_BLOCKS?d:new int[0]")
change("blockentity/NetworkDeviceBlockEntity.java",
       "plan.size()!=dims[0]*dims[1]*dims[2]",
       "(long)plan.size()!=(long)dims[0]*dims[1]*dims[2]")
change("client/NetworkBlueprintPreviewClient.java",
       "volume<=0L||volume>4096L||sx>16||sy>16||sz>16",
       "volume<=0L||volume>NetworkBlueprintItem.MAX_BLOCKS")
print("B378_LARGE_BLUEPRINT_LIMITS_PASS")
