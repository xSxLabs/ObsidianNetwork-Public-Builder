#!/usr/bin/env python3
"""B1662 lightweight RFTools-inspired xSxLabs Mining Builder: baked multi-part model.
Only resource JSONs, static PNGs, and placement-facing state; no renderer/tick changes.
"""
import json, os, struct, zlib
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
block=J/"mining/V178MiningBuilderBlock.java"
source=block.read_text(encoding="utf-8")
def once(before,after):
 global source
 count=source.count(before)
 assert count==1,("B1662_MINING_BLOCK_SOURCE_DRIFT",count,before[:80])
 source=source.replace(before,after,1)

once('''import net.minecraft.core.BlockPos;''',
'''import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;''')
once(''' private static final MapCodec<V178MiningBuilderBlock> CODEC=simpleCodec(V178MiningBuilderBlock::new);
 public V178MiningBuilderBlock(Properties p){super(p);}''',
''' private static final MapCodec<V178MiningBuilderBlock> CODEC=simpleCodec(V178MiningBuilderBlock::new);
 public static final EnumProperty<Direction> FACING=BlockStateProperties.HORIZONTAL_FACING;
 public V178MiningBuilderBlock(Properties p){
  super(p);
  registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));
 }
 @Override public BlockState getStateForPlacement(BlockPlaceContext context){
  return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite());
 }
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> builder){
  builder.add(FACING);
 }''')
block.write_text(source,encoding="utf-8")

statefile=R/"assets/obsidiannetwork/blockstates/mining_builder.json"
modelfile=R/"assets/obsidiannetwork/models/block/mining_builder.json"
original=json.loads(modelfile.read_text(encoding="utf-8"))
existing=json.loads(statefile.read_text(encoding="utf-8"))
assert original.get("parent")=="minecraft:block/cube_all", "B1662_MINING_BASE_MODEL_DRIFT"
assert existing=={"variants":{"":{"model":"obsidiannetwork:block/mining_builder"}}}, "B1662_MINING_BASE_STATE_DRIFT"
statefile.write_text(json.dumps({"variants":{
  f"facing={direction}":{"model":"obsidiannetwork:block/mining_builder","y":angle}
  for direction,angle in (("north",0),("east",90),("south",180),("west",270))
}},indent=2)+"\n",encoding="utf-8")

# Every box remains in vanilla's 0..16 model geometry. No per-frame renderer.
parts=[]
def box(lo,hi,material,front=None):
 assert all(0<=v<=16 for v in (*lo,*hi)) and all(l<h for l,h in zip(lo,hi))
 faces={face:{"texture":"#"+(front if front and face=="north" else material)}
        for face in ("north","south","west","east","up","down")}
 parts.append({"from":list(lo),"to":list(hi),"faces":faces})
box((0,0,0),(16,2,16),"shell")
box((2,2,2),(14,13,14),"panel")
box((1,2,1),(15,4,15),"shell")
box((1,12,1),(15,14,15),"shell")
for x in (0,13):
 for z in (0,13):
  box((x,2,z),(x+3,15,z+3),"shell")
box((4,5,1),(12,11,3),"trim","front")
box((5,6,0),(11,10,1),"core")
box((0,5,4),(2,11,12),"trim")
box((14,5,4),(16,11,12),"trim")
for lo,hi in [
 ((2,14,2),(14,16,4)),((2,14,12),(14,16,14)),
 ((2,14,4),(4,16,12)),((12,14,4),(14,16,12))
]:
 box(lo,hi,"shell")
box((5,14,5),(11,15,11),"core")
box((5,5,14),(11,11,16),"vent")
box((1,7,5),(3,10,11),"vent")
box((13,7,5),(15,10,11),"vent")
assert len(parts)==20,("B1662_EXPECTED_BAKED_PART_COUNT",len(parts))
texture_names=("shell","panel","trim","core","front","vent")
modelfile.write_text(json.dumps({
 "textures":{"particle":"obsidiannetwork:block/mining_builder_shell",
             **{name:"obsidiannetwork:block/mining_builder_"+name for name in texture_names}},
 "elements":parts
},indent=2)+"\n",encoding="utf-8")

# Small authored pixel-art patterns. A source-controlled generator avoids
# third-party PNG libraries and avoids shipping any external copyrighted textures.
N=32
def rgba(rgb):
 return ((rgb>>16)&255,(rgb>>8)&255,rgb&255,255)
def pixel(kind,x,y):
 edge=x<3 or y<3 or x>=29 or y>=29
 border=x in (2,3,28,29) or y in (2,3,28,29)
 rivet=(x in (5,26) and y in (5,26))
 noise=((x*11+y*17+(x^y)*3)%17)-8
 if kind=="shell":
  rgb=0x111b27 if edge else (0x243547 if border else 0x1b2937)
  if 7<x<25 and y in (7,24):rgb=0x41576a
  if rivet:rgb=0x8297a3
 elif kind=="panel":
  rgb=0x141f2b if edge else 0x273a4a
  if (x+y)%13 in (0,1):rgb=0x314a5c
  if x in (7,24) or y in (7,24):rgb=0x192736
  if rivet:rgb=0x637e91
 elif kind=="trim":
  rgb=0x0e1b29 if edge else 0x1a4b5b
  if border:rgb=0x45c8d7
  if x in (7,8,23,24) or y in (7,8,23,24):rgb=0x256c80
 elif kind=="core":
  dx=x-15.5;dy=y-15.5;r=dx*dx+dy*dy
  rgb=0x101d30
  if r<151:rgb=0x165b80
  if 80<r<151:rgb=0x3bc5e0
  if r<75:rgb=0x209cce
  if r<24:rgb=0xa2f5ff
  if border:rgb=0x203d53
 elif kind=="front":
  rgb=0x0b1625 if edge else 0x223b4f
  if border:rgb=0x69d7eb
  if 8<=x<=23 and 7<=y<=24:
   rgb=0x2a627f if (x+y)//5%2 else 0x19506c
  if 11<=x<=20 and 11<=y<=20:rgb=0x4de4f4
  if rivet:rgb=0xc5eefa
 else:
  rgb=0x101a25 if edge else 0x253745
  if (x//4)%2==0 and 5<y<27:rgb=0x09141e
  if y in (7,24):rgb=0x4ebaca
 if kind in ("shell","panel") and not edge:
  c=((rgb>>16)&255,(rgb>>8)&255,rgb&255)
  rgb=sum((max(0,min(255,v+noise)) << (16-i*8)) for i,v in enumerate(c))
 return rgba(rgb)

def chunk(kind,data):
 return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
def png(name):
 rows=bytearray()
 for y in range(N):
  rows.append(0)
  for x in range(N):rows.extend(pixel(name,x,y))
 return (b"\x89PNG\r\n\x1a\n"+
         chunk(b"IHDR",struct.pack(">IIBBBBB",N,N,8,6,0,0,0))+
         chunk(b"IDAT",zlib.compress(bytes(rows),9))+
         chunk(b"IEND",b""))
folder=R/"assets/obsidiannetwork/textures/block"
folder.mkdir(parents=True,exist_ok=True)
for name in texture_names:
 path=folder/("mining_builder_"+name+".png")
 assert not path.exists(),("B1662_TEXTURE_COLLISION",path.name)
 path.write_bytes(png(name))
assert set(json.loads(modelfile.read_text())["textures"])-{"particle"}==set(texture_names)
assert len(parts)>=16 and all(len(v["faces"])==6 for v in parts)
print("B1662_MINING_BUILDER_DIRECTIONAL_BAKED_3D_SIX_CUSTOM_PNG_TEXTURES_PASS")
