#!/usr/bin/env python3
"""Add real 3x3 compression recipe shift-click conservation stress to GameTests.

Runs with a real StorageTerminalMenu on the existing 50-drive fixture.
No production behavior is altered. Fail closed on fixture drift.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
anchor='if(!rt.powered())throw new IllegalStateException("Shift crafting test network unpowered");'
marker="XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1"
assert s.count(anchor)==1 and marker not in s
assert "xsxCraftMenu.clicked(0,0," in s
assert "xsxlabsBurstTerminalPos" in s
code=r'''
                  // XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1
                  // Sixteen consecutive 3x3 compression crafts per case via
                  // the production result-slot QUICK_MOVE as normal player input.
                  // This catches a regression not covered by log -> planks.
                  long xsxNineTotalNs=0L;
                  long xsxNineWorstNs=0L;
                  for(var xsxNineCase : new net.minecraft.world.item.Item[][]{
                      {net.minecraft.world.item.Items.COAL,net.minecraft.world.item.Items.COAL_BLOCK},
                      {net.minecraft.world.item.Items.REDSTONE,net.minecraft.world.item.Items.REDSTONE_BLOCK},
                      {net.minecraft.world.item.Items.BONE_MEAL,net.minecraft.world.item.Items.BONE_BLOCK},
                      {net.minecraft.world.item.Items.IRON_INGOT,net.minecraft.world.item.Items.IRON_BLOCK}
                  }){
                    for(int i=1;i<=9;i++)
                      xsxCraftMenu.slots.get(i).set(
                          new net.minecraft.world.item.ItemStack(xsxNineCase[0],16));
                    // Existing player inventory may contain unrelated fixture items.
                    // Track only the recipe output, without deleting other stacks.
                    int xsxNineBefore=0;
                    for(int i=0;i<36;i++){
                      var stack=xsxCraftInv.getItem(i);
                      if(stack.getItem()==xsxNineCase[1]) xsxNineBefore+=stack.getCount();
                    }
                    var xsxNinePreview=xsxCraftMenu.slots.get(0).getItem();
                    if(xsxNinePreview.isEmpty()||xsxNinePreview.getItem()!=xsxNineCase[1])
                      throw new IllegalStateException("3x3 compression recipe missing: "+xsxNineCase[0]);
                    long xsxNineStartNs=System.nanoTime();
                    xsxCraftMenu.clicked(0,0,
                        net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,xsxCraftPlayer);
                    long xsxNineElapsedNs=System.nanoTime()-xsxNineStartNs;
                    xsxNineTotalNs+=xsxNineElapsedNs;
                    xsxNineWorstNs=Math.max(xsxNineWorstNs,xsxNineElapsedNs);
                    for(int i=1;i<=9;i++)
                      if(!xsxCraftMenu.slots.get(i).getItem().isEmpty())
                        throw new IllegalStateException("9-input shift craft did not consume slot "+i);
                    int xsxNineProduced=0;
                    for(int i=0;i<36;i++){
                      var item=xsxCraftInv.getItem(i);
                      if(!item.isEmpty()&&item.getItem()==xsxNineCase[1])
                        xsxNineProduced+=item.getCount();
                    }
                    xsxNineProduced-=xsxNineBefore;
                    if(xsxNineProduced!=16)
                      throw new IllegalStateException("9-input craft conservation: "+xsxNineProduced);
                  }
                  System.out.println("XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1 PASS cases=4 ingredients=576 results=64 total_click_ns="+xsxNineTotalNs+" worst_click_ns="+xsxNineWorstNs+" not_server_MSPT=true");
'''

eight=r'''
                  // XSXLABS_REAL_EIGHT_INGREDIENT_SHIFT_CRAFT_V1
                  // 8-slot chest recipe, deliberately leaving the centre empty.
                  // Exercise the real QUICK_MOVE result path with sixteen crafts.
                  for(int xsxEightSlot=1; xsxEightSlot<=9; xsxEightSlot++) {
                    xsxCraftMenu.slots.get(xsxEightSlot).set(
                      xsxEightSlot==5 ? net.minecraft.world.item.ItemStack.EMPTY :
                      new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.OAK_PLANKS,16));
                  }
                  int xsxEightBefore=0;
                  for(int xsxEightSlot=0; xsxEightSlot<36; xsxEightSlot++) {
                    var xsxEightStack=xsxCraftInv.getItem(xsxEightSlot);
                    if(xsxEightStack.getItem()==net.minecraft.world.item.Items.CHEST)
                      xsxEightBefore+=xsxEightStack.getCount();
                  }
                  var xsxEightPreview=xsxCraftMenu.slots.get(0).getItem();
                  if(xsxEightPreview.isEmpty() || xsxEightPreview.getItem()!=net.minecraft.world.item.Items.CHEST)
                    throw new IllegalStateException("8-slot chest recipe missing from real terminal");
                  long xsxEightStarted=System.nanoTime();
                  xsxCraftMenu.clicked(0,0,
                      net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,xsxCraftPlayer);
                  long xsxEightElapsed=System.nanoTime()-xsxEightStarted;
                  for(int xsxEightSlot=1; xsxEightSlot<=9; xsxEightSlot++)
                    if(!xsxCraftMenu.slots.get(xsxEightSlot).getItem().isEmpty())
                      throw new IllegalStateException("8-slot chest shift craft left input at "+xsxEightSlot);
                  int xsxEightAfter=0;
                  for(int xsxEightSlot=0; xsxEightSlot<36; xsxEightSlot++) {
                    var xsxEightStack=xsxCraftInv.getItem(xsxEightSlot);
                    if(xsxEightStack.getItem()==net.minecraft.world.item.Items.CHEST)
                      xsxEightAfter+=xsxEightStack.getCount();
                  }
                  if(xsxEightAfter-xsxEightBefore!=16)
                    throw new IllegalStateException("8-slot chest craft conservation: "+(xsxEightAfter-xsxEightBefore));
                  System.out.println("XSXLABS_REAL_EIGHT_INGREDIENT_SHIFT_CRAFT_V1 PASS ingredients=128 results=16 total_click_ns="+xsxEightElapsed+" not_server_MSPT=true");
'''
# Four 9-slot output batches already hit the legitimate 64-result per-tick
# safety cap. The 8-slot test MUST run on the next real server tick.
# Never weaken the cap or the full sixteen-craft conservation assertions.
needle=anchor
assert s.count('var xsxCraftInv=xsxCraftPlayer.getInventory();')==1
sequence_anchor="xsxCraftSequence.thenExecute(()->{"
assert s.count(sequence_anchor)==1, "Shift craft tick sequence completion moved"
s=s.replace(needle,needle+"\n"+code,1)
s=s.replace(sequence_anchor,
    "// XSXLABS_EIGHT_SLOT_NEXT_TICK_V2: 9-slot suite exhausted this tick's 64-item cap.\n"
    "                  xsxCraftSequence.thenExecuteAfter(1,()->{\n"+eight+"\n                  });\n"
    "                  "+sequence_anchor,1)
assert s.count(marker)==2
assert s.count("XSXLABS_REAL_EIGHT_INGREDIENT_SHIFT_CRAFT_V1")==2
assert s.count("XSXLABS_EIGHT_SLOT_NEXT_TICK_V2")==1
assert s.count("xsxCraftSequence.thenExecuteAfter(1,()->{")>=1
assert s.index(anchor)<s.index(marker, s.index(anchor))
assert s.count("xsxNineProduced!=16")==1
p.write_text(s,encoding="utf-8")
print("NINE_INGREDIENT_SHIFT_CRAFT_TEST_INJECTION_V1 PASS")
