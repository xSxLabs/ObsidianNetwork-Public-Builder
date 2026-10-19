#!/usr/bin/env python3
"""Add real 3x3 compression recipe shift-click conservation stress to GameTests.

Runs with a real StorageTerminalMenu on the existing 50-drive fixture.
No production behavior is altered. Fail closed on fixture drift.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='final int[] xsxCraftTicks={0};'
marker="XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1"
assert s.count(anchor)==1 and marker not in s
assert "xsxCraftMenu.clicked(0,0," in s
assert "xsxlabsBurstTerminalPos" in s
code=r'''
                  // XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1
                  // One 3x3 compression craft of each type via the same
                  // production result-slot QUICK_MOVE as normal player input.
                  // This catches a regression not covered by log -> planks.
                  for(var xsxNineCase : new net.minecraft.world.item.Item[][]{
                      {net.minecraft.world.item.Items.COAL,net.minecraft.world.item.Items.COAL_BLOCK},
                      {net.minecraft.world.item.Items.REDSTONE,net.minecraft.world.item.Items.REDSTONE_BLOCK},
                      {net.minecraft.world.item.Items.BONE_MEAL,net.minecraft.world.item.Items.BONE_BLOCK}
                  }){
                    for(int i=1;i<=9;i++)
                      xsxCraftMenu.slots.get(i).set(
                          new net.minecraft.world.item.ItemStack(xsxNineCase[0],1));
                    var xsxNinePreview=xsxCraftMenu.slots.get(0).getItem();
                    if(xsxNinePreview.isEmpty()||xsxNinePreview.getItem()!=xsxNineCase[1])
                      throw new IllegalStateException("3x3 compression recipe missing: "+xsxNineCase[0]);
                    xsxCraftMenu.clicked(0,0,
                        net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,xsxCraftPlayer);
                    for(int i=1;i<=9;i++)
                      if(!xsxCraftMenu.slots.get(i).getItem().isEmpty())
                        throw new IllegalStateException("9-input shift craft did not consume slot "+i);
                    int xsxNineProduced=0;
                    for(int i=0;i<36;i++){
                      var item=xsxCraftInv.getItem(i);
                      if(!item.isEmpty()){
                        if(item.getItem()!=xsxNineCase[1])
                          throw new IllegalStateException("Unexpected 9-input result "+item);
                        xsxNineProduced+=item.getCount();
                        xsxCraftInv.setItem(i,net.minecraft.world.item.ItemStack.EMPTY);
                      }
                    }
                    if(xsxNineProduced!=1)
                      throw new IllegalStateException("9-input craft conservation: "+xsxNineProduced);
                  }
                  System.out.println("XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1 PASS cases=3 ingredients=27 results=3");
'''
# Insert after player and inventory initialization, before 15-tick fixture setup.
needle='final int[] xsxCraftTicks={0};'
assert s.count('var xsxCraftInv=xsxCraftPlayer.getInventory();')==1
s=s.replace(needle,code+"\n                  "+needle,1)
assert s.count(marker)==2
p.write_text(s,encoding="utf-8")
print("NINE_INGREDIENT_SHIFT_CRAFT_TEST_INJECTION_V1 PASS")
