#!/usr/bin/env python3
"""B566 runtime patch-fixture, glass-seam and solar equivalence gates."""
import ast,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
GLASS=ROOT/'features/v174/apply-v174-seamless-formed-glass-566.py'
SOLAR=ROOT/'patches/apply-solar-sky-pos-reuse-566.py'
NAMES=['reactor_glass_formed','reactor_glass_formed_lit','powerbank_glass_formed']+[
 f'powerbank_glass_formed_lit_detail{i}' for i in range(3)]
class ConnectedGlass566(unittest.TestCase):
 def test_patches_compile(self):
  for p in (GLASS,SOLAR):ast.parse(p.read_text(encoding='utf8'))
 def test_glass_real_patch_and_no_casing_damage(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   j=root/'java/dev/obsidiannetwork/multiblock/MultiblockSkinBlock.java';j.parent.mkdir(parents=True)
   j.write_text('''public final class MultiblockSkinBlock extends Block {
 // B558_REACTOR_MIXED_PANELS
 void schema() { builder.add(FORMED,ACTIVE,LIT,RIM,CORNER,DETAIL); }
 @Override protected MapCodec<? extends Block> codec() {return CODEC;}
 }''')
   assets=root/'resources/assets/obsidiannetwork/textures/block';assets.mkdir(parents=True)
   for nm in NAMES:
    im=Image.new('RGBA',(32,32));pix=im.load()
    for y in range(32):
     for x in range(32):
      pix[x,y]=(25,40,60,190) if x in (0,31) or y in (0,31) else (50,160,230,99)
    im.save(assets/(nm+'.png'))
   casing=Image.new('RGBA',(32,32),(240,244,250,255))
   casing.save(assets/'reactor_casing_formed_design3_middle_detail0.png')
   original=(assets/'reactor_casing_formed_design3_middle_detail0.png').read_bytes()
   env=dict(os.environ,V1_SOURCE_ROOT=str(root/'java'),V1_RESOURCE_ROOT=str(root/'resources'))
   cmd=[sys.executable,str(GLASS)]
   subprocess.run(cmd,env=env,check=True,capture_output=True,text=True)
   self.assertEqual(original,(assets/'reactor_casing_formed_design3_middle_detail0.png').read_bytes())
   for name in NAMES:
    im=Image.open(assets/(name+'.png')).convert('RGBA')
    for i in range(32):
     self.assertEqual(im.getpixel((0,i)),im.getpixel((3,i)))
     self.assertEqual(im.getpixel((31,i)),im.getpixel((28,i)))
     self.assertEqual(im.getpixel((i,0)),im.getpixel((i,3)))
     self.assertEqual(im.getpixel((i,31)),im.getpixel((i,28)))
    self.assertEqual(im.getpixel((16,16)),(50,160,230,99))
   code=j.read_text()
   self.assertEqual(code.count('B566_CONNECTED_FORMED_GLASS_FACE_CULL'),1)
   self.assertIn('state.getValue(FORMED) && adjacentState.hasProperty(FORMED)',code)
   self.assertIn('return super.skipRendering(state,adjacentState,direction);',code)
   self.assertIn('POWERBANK_GLASS.get()',code)
   self.assertIn('REACTOR_GLASS.get()',code)
   again=subprocess.run(cmd,env=env,capture_output=True,text=True)
   self.assertNotEqual(again.returncode,0)
 def test_solar_live_sky_check_not_cached(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java';p.parent.mkdir(parents=True)
   p.write_text('''// B536_SOLAR_MSPT_FACE_MASK
// B547_SOLAR_SPARSE_FACE_WALK
// B565_SOLAR_FULL_BUFFER_SKY_FASTPATH
class SolarGeneratorBlockEntity {
 private ServerLevel energyCacheLevel;
 @Override public void onLoad() {}
 void tick() {
 if (be.energy.stored() < be.energy.capacity() && server.canSeeSky(pos.above())) {
 long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());
 }
 long budget = be.energy.stored();
 be.energyJournal.updateSnapshots(tx);
 tx.commit();
 budget -= accepted;
 }
}''')
   env=dict(os.environ,V1_SOURCE_ROOT=t)
   subprocess.run([sys.executable,str(SOLAR)],env=env,check=True,capture_output=True)
   code=p.read_text()
   self.assertIn('server.canSeeSky(be.xsxSolarAbove())',code)
   self.assertIn('private net.minecraft.core.BlockPos xsxSolarAbove;',code)
   self.assertEqual(code.count('server.canSeeSky('),1)
   self.assertNotIn('skyVisible =',code)
   self.assertEqual(code.count('tx.commit();'),1)
if __name__=='__main__':unittest.main()
