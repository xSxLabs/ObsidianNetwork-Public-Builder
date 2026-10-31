#!/usr/bin/env python3
"""B566 assert seamless assembled glass is actually shipped in the final JAR."""
import argparse,io,json
from pathlib import Path
from PIL import Image
from zipfile import ZipFile
BASE='assets/obsidiannetwork/'
NAMES=['reactor_glass_formed','reactor_glass_formed_lit','powerbank_glass_formed']+[
 f'powerbank_glass_formed_lit_detail{i}' for i in range(3)]
def verify(read):
 for name in NAMES:
  im=Image.open(io.BytesIO(read(BASE+'textures/block/'+name+'.png'))).convert('RGBA')
  assert im.size==(32,32),name
  for i in range(32):
   for a,b in [((0,i),(3,i)),((31,i),(28,i)),((i,0),(i,3)),((i,31),(i,28))]:
    assert im.getpixel(a)==im.getpixel(b),(name,a,b)
  assert im.getpixel((16,16))[3]<255,(name,'opaque interior')
 for name in ('reactor_glass','powerbank_glass'):
  variants=json.loads(read(BASE+'blockstates/'+name+'.json'))['variants']
  assert len(variants)==144,(name,len(variants))
  for k,v in variants.items():
   if 'formed=false' in k:assert v['model']=='obsidiannetwork:block/'+name,(name,k)
 print('B566_COMPILED_JOINED_GLASS_REACTOR_BANK_PASS')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--jar',type=Path);p.add_argument('--assets',type=Path);args=p.parse_args()
 assert bool(args.jar)!=bool(args.assets)
 if args.jar:
  with ZipFile(args.jar) as z:verify(z.read)
 else:
  root=args.assets.parent.parent
  verify(lambda name:(root/name).read_bytes())
