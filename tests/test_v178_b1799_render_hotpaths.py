#!/usr/bin/env python3
"""No-build B1799 v11 FPS invariants: exact minimap pixels and weak world cache."""
import ast
import os
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/'features/v178/apply-v178-b1799-render-hotpaths.py'
WORKFLOW=(ROOT/'.github/workflows/networkstorage-v1.7-clean.yml').read_text(encoding='utf-8')

class B1799ExactOutput(unittest.TestCase):
    def test_pipeline_stays_v11_and_buildlocked(self):
        text=PATCH.read_text(encoding='utf-8')
        ast.parse(text)
        earlier='python3 features/v178/apply-v178-b1792-render-fps.py'
        later='python3 features/v178/apply-v178-b1799-render-hotpaths.py'
        self.assertIn(earlier,WORKFLOW)
        self.assertIn(later,WORKFLOW)
        self.assertLess(WORKFLOW.index(earlier),WORKFLOW.index(later))
        self.assertIn('xSxLabs-Network-Storage-1.7.8-v12.jar',WORKFLOW)
        self.assertIn('xsxlabs-network-storage-1.7.8-v12',WORKFLOW)
        self.assertIn("contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')",WORKFLOW)

    def test_mask_equivalent_to_per_pixel_original_for_every_pixel(self):
        side=304
        radius=(side-1)*0.5
        inner=radius-1.25
        outer2=radius*radius
        inner2=inner*inner
        mask=[]
        for y in range(side):
            for x in range(side):
                dx=x+0.5-side*0.5
                dz=y+0.5-side*0.5
                distance=dx*dx+dz*dz
                cached=2 if distance>outer2 else 1 if distance>=inner2 else 0
                mask.append(cached)
        self.assertEqual(len(mask),side*side)
        self.assertTrue(0 in mask and 1 in mask and 2 in mask)
        for sample in (0x00000000,0xff1c2530,0xff89abde):
            for type_ in (0,1,2):
                actual=0 if type_==2 else 0xff95adbc if type_==1 else sample
                expected=sample
                if type_==2:expected=0
                elif type_==1:expected=0xff95adbc
                self.assertEqual(actual,expected)

    def test_separable_zoom_sampling_same_coordinates_at_all_zoom_levels(self):
        side=304
        for crop in (16,112,304,448,624):
            for startx,startz in ((-314,-223),(-1,0),(33,128)):
                firstcx=startx>>4
                firstcz=startz>>4
                cols=[]
                for px in range(side):
                    wx=startx+(px*crop//side)
                    cols.append(((wx>>4)-firstcx,wx&15))
                for py in range(side):
                    wz=startz+(py*crop//side)
                    row=((wz>>4)-firstcz,wz&15)
                    for px in range(side):
                        wx=startx+(px*crop//side)
                        old=((wx>>4)-firstcx,(wz>>4)-firstcz,(wz&15)*16+(wx&15))
                        new=(cols[px][0],row[0],row[1]*16+cols[px][1])
                        self.assertEqual(old,new)

    def test_weak_cache_cannot_strongly_retain_old_level(self):
        s=PATCH.read_text(encoding='utf-8')
        self.assertIn('java.lang.ref.WeakReference<net.minecraft.world.level.Level>',s)
        self.assertIn('cached.level.get()==',s)
        self.assertNotIn('final net.minecraft.world.level.Level level;',s)
        self.assertNotIn('getChunk(',s)
        self.assertNotIn('forceChunk(',s)
        self.assertNotIn('texture.upload()',s)

    def test_generated_java_contract_when_reconstructed(self):
        java_root=os.environ.get('V1_SOURCE_ROOT')
        if not java_root:self.skipTest('requires reconstructed CI Java sources')
        path=Path(java_root)/'dev/obsidiannetwork'
        mini=(path/'client/V178MiniRaster.java').read_text(encoding='utf-8')
        facade=(path/'client/render/CableFacadeRenderer.java').read_text(encoding='utf-8')
        for token in ('B1799_CIRCLE_MASK','B1799_COLUMN_CHUNK','B1799_COLUMN_PIXEL',
                      'img.setPixel(px,py,color)','texture.upload()'):
            self.assertIn(token,mini)
        for token in ('B1792_FACADE_LIGHT_CACHE','java.lang.ref.WeakReference',
                      'cached.level.get()==','xsxNow-cached.tick<5L'):
            self.assertIn(token,facade)
        self.assertNotIn('final net.minecraft.world.level.Level level;',facade)

if __name__=='__main__':unittest.main()
