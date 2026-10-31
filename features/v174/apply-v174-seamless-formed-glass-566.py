#!/usr/bin/env python3
"""B566: join ONLY formed reactor/bank glass, retaining B558 interior glow.

No new block-state properties, ticking, scanning, or renderers. Culls only
internal faces of two joined formed glass blocks; preserves exterior faces.
Texture border removal is restricted to the six formed glass sprites.
"""
import os
from pathlib import Path
from PIL import Image

root=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork'
assets=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
p=root/'multiblock/MultiblockSkinBlock.java'
s=p.read_text(encoding='utf8')
marker='B566_CONNECTED_FORMED_GLASS_FACE_CULL'
assert marker not in s
assert s.count('public final class MultiblockSkinBlock extends Block {')==1
assert s.count('builder.add(FORMED,ACTIVE,LIT,RIM,CORNER,DETAIL);')==1
assert s.count(' @Override protected MapCodec<? extends Block> codec()')==1
assert s.count('B558_REACTOR_MIXED_PANELS')==1

method=''' // B566_CONNECTED_FORMED_GLASS_FACE_CULL: no per-block inner glass faces.
 // Vanilla chunk meshing invokes this when one glass block touches another.
 // Never hide the boundary against casing, air, the other glass family,
 // or any unformed/standalone glass.
 @Override protected boolean skipRendering(BlockState state,BlockState adjacentState,
                                           net.minecraft.core.Direction direction) {
  if(state.getValue(FORMED) && adjacentState.hasProperty(FORMED)
       && adjacentState.getValue(FORMED)) {
   boolean reactorGlass=state.is(dev.obsidiannetwork.ObsidianNetwork.REACTOR_GLASS.get());
   boolean bankGlass=state.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_GLASS.get());
   if((reactorGlass && adjacentState.is(dev.obsidiannetwork.ObsidianNetwork.REACTOR_GLASS.get()))
       ||(bankGlass && adjacentState.is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_GLASS.get())))
    return true;
  }
  return super.skipRendering(state,adjacentState,direction);
 }
'''
s=s.replace(' @Override protected MapCodec<? extends Block> codec()',method+' @Override protected MapCodec<? extends Block> codec()',1)
names=['reactor_glass_formed','reactor_glass_formed_lit','powerbank_glass_formed']+[f'powerbank_glass_formed_lit_detail{i}' for i in range(3)]
for name in names:
 q=assets/'textures/block'/(name+'.png')
 assert q.is_file(),('B566_MISSING_SPRITE',name)
 with Image.open(q) as im: assert im.size==(32,32) and im.mode=='RGBA',(name,im.size,im.mode)
for name in names:
 q=assets/'textures/block'/(name+'.png')
 with Image.open(q) as im: base=im.copy()
 px=base.load()
 out=Image.new('RGBA',(32,32))
 op=out.load()
 for y in range(32):
  for x in range(32):
   xx=max(3,min(28,x));yy=max(3,min(28,y))
   op[x,y]=px[xx,yy]
 for i in range(32):
  assert op[0,i]==op[3,i] and op[31,i]==op[28,i]
  assert op[i,0]==op[i,3] and op[i,31]==op[i,28]
 assert op[16,16]==px[16,16],name
 out.save(q,optimize=True)
p.write_text(s,encoding='utf8')
print('B566_CONNECTED_FORMED_GLASS_PASS: six seamless sprites, same core glow, culled internal faces, no added ticking')
