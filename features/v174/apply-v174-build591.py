#!/usr/bin/env python3
"""B591: targeted v1.7.4 features. Apply after B586 and before final regression/build."""
import os,re,json
from pathlib import Path
from PIL import Image
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def load(p):return p.read_text(encoding="utf-8")
def save(p,s):p.write_text(s,encoding="utf-8")
def once(s,a,b,where):
 n=s.count(a)
 assert n==1,("B591_ANCHOR",where,a[:120],n)
 return s.replace(a,b,1)
def method(s,signature):
 start=s.index(signature);begin=s.index("{",start);depth=0
 for i in range(begin,len(s)):
  if s[i]=="{":depth+=1
  elif s[i]=="}":
   depth-=1
   if depth==0:return start,i+1,s[start:i+1]
 raise AssertionError(("B591_METHOD_BRACES",signature))

# --- REACTOR: explicit auto-paused state; never confuse manual OFF with full-buffer pause.
p=J/"reactor/ReactorControllerBlockEntity.java";s=load(p)
assert "B579_REACTOR_GENERATE_EVERY_TICK" in s
s=once(s," private boolean enabled=true;"," private boolean enabled=true;\n // B591_REACTOR_AUTO_FULL: only the automatic full-buffer pause may resume.\n private boolean b591AutoFullPause=false;",str(p))
s=once(s," public boolean guiEnabled(){return enabled;}"," public boolean guiEnabled(){return enabled&&!b591AutoFullPause;}\n public boolean guiAutoPaused(){return b591AutoFullPause;}",str(p))
# Explicit buttons always own the mode. OFF never silently turns ON.
s=once(s,"  if(command==0)enabled=true;","  if(command==0){enabled=true;b591AutoFullPause=false;}",str(p))
s=once(s,"  else if(command==1||command==2)enabled=false; // shutdown/scram","  else if(command==1||command==2){enabled=false;b591AutoFullPause=false;} // shutdown/scram",str(p))
# Push existing FE first even while automatically paused; never prevent draining.
s=once(s,"  // B579_REACTOR_GENERATE_EVERY_TICK:",'''  // B591_REACTOR_AUTO_FULL_GATE: no structure scan, 1 constant-time check/tick.
  if(!be.enabled){be.b591AutoFullPause=false;}
  else if(be.formed&&be.storedFe>=FE_CAPACITY){
   if(!be.b591AutoFullPause){be.b591AutoFullPause=true;be.setChanged();}
   be.status="AUTO PAUSED: FULL";
  }else if(be.b591AutoFullPause && be.storedFe<FE_CAPACITY){
   be.b591AutoFullPause=false;be.status="RUNNING";be.setChanged();
  }
  // B579_REACTOR_GENERATE_EVERY_TICK:''',str(p))
s=once(s,"if(be.formed&&be.enabled&&be.fuelTicks>0&&be.waterMb>=20)",
         "if(be.formed&&be.enabled&&!be.b591AutoFullPause&&be.fuelTicks>0&&be.waterMb>=20)",str(p))
# The periodic fuel load and coolant usage must also stay off during auto-pause.
# Place the gate after periodic structure/recovery work, before fuel/water service.
s=once(s,'  if(!be.enabled){be.status="OFFLINE";return;}',
'''  if(!be.enabled){be.b591AutoFullPause=false;be.status="OFFLINE";return;}
  if(be.b591AutoFullPause){be.b579ActualGeneration=0L;be.status="AUTO PAUSED: FULL";return;}''',str(p))
# 5x actual rod usage, but production and coolant unchanged.
s=once(s,"be.fuelTicks=Math.max(0,be.fuelTicks-activity);",
         "be.fuelTicks=Math.max(0,be.fuelTicks-5*activity); // B591_FUEL_RODS_X5",str(p))
s=once(s,'out.putBoolean("reactorEnabled",enabled);',
         'out.putBoolean("reactorEnabled",enabled);out.putBoolean("b591AutoFullPause",b591AutoFullPause);',str(p))
s=once(s,'enabled=in.getBooleanOr("reactorEnabled",true);',
         'enabled=in.getBooleanOr("reactorEnabled",true);\n   b591AutoFullPause=enabled && in.getBooleanOr("b591AutoFullPause",false);',str(p))
save(p,s)

# --- POWERBANK: OUTPUT is an active server-tick producer, with atomic sink-first transfer.
p=J/"powerbank/PowerbankBlockEntity.java";s=load(p)
assert "B579_BANK_ROLLING_20" in s and "activePorts" in s
guard='  if(!(world instanceof ServerLevel sl)||be.mode()!=PowerbankBlock.Mode.CONTROLLER)return;'
assert s.count(guard)==1,("B592_CONTROLLER_TICK_GUARD",s.count(guard))
s=s.replace(guard,guard+"\n  // B592_POWERBANK_OUTPUT_TICK\n  be.b591PushOutput(sl);",1)
marker=" private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<long[]> journal="
helper=r'''
 // B591_POWERBANK_OUTPUT_PUSH: bounded by actual validated shell ports.
 // Ports are already tracked during normal revalidation, never new scans.
 // Sink first, port source second: both rollback on any rejected FE.
 private void b591PushOutput(ServerLevel server){
  if(mode()!=PowerbankBlock.Mode.CONTROLLER || !formed || amount<=0L)return;
  for(long encoded:activePorts){
   if(amount<=0L)return;
   BlockPos portPos=BlockPos.of(encoded);
   if(!server.hasChunkAt(portPos)
      ||!server.getBlockState(portPos).is(dev.obsidiannetwork.ObsidianNetwork.POWERBANK_OUTPUT.get()))continue;
   var entity=server.getBlockEntity(portPos);
   if(!(entity instanceof PowerbankBlockEntity output)
      ||output.mode()!=PowerbankBlock.Mode.OUTPUT
      ||output.controller()!=this)continue;
   var source=output.energyPort();
   for(net.minecraft.core.Direction face:net.minecraft.core.Direction.values()){
    if(amount<=0L)return;
    BlockPos neighbor=portPos.relative(face);
    if(neighbor.equals(worldPosition)||activePorts.contains(neighbor.asLong())
       ||!server.hasChunkAt(neighbor))continue;
    var target=server.getCapability(net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,
      neighbor,face.getOpposite());
    if(target==null||target==source)continue;
    int offer=(int)Math.min(1_000_000L,amount);
    if(offer<=0)return;
    try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
     int accepted=target.insert(offer,tx);
     if(accepted>0 && source.extract(accepted,tx)==accepted)tx.commit();
    }
   }
  }
 }
'''
assert s.count(marker)==1,("B591_BANK_JOURNAL_ANCHOR",s.count(marker))
s=s.replace(marker,helper+marker,1);save(p,s)

# --- ENERGY CABLE: real six-sided direction enforcement on EVERY BFS hop.
p=J/"blockentity/EnergyCableBlockEntity.java";s=load(p)
assert "B568_PER_TICK_LIVE_CABLE_BE_LOOKUP" in s and "B541_IMMUTABLE_ENERGY_CABLE_CUT_MASK" in s
gate=r'''
 // B591_ENERGY_DIRECTED_WALK: INPUT receives, OUTPUT emits, BOTH passes,
 // OFF completely disconnects. Uses live per-side mode; never caches modes.
 private static boolean b591FlowOpen(ServerLevel server,BlockPos cable,
                                     BlockState state,Direction side,boolean outward){
  if(!energyOpen(server,cable,state,side))return false;
  if(state.is(dev.obsidiannetwork.ObsidianNetwork.ENERGY_CABLE.get())){
   var obj=xsxLiveCable(server,cable);
   if(!(obj instanceof EnergyCableBlockEntity live))return false;
   int mode=live.energySideMode(side);
   return mode==3 || mode==(outward?2:1);
  }
  return true;
 }
'''
class_anchor="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert s.count(class_anchor)==1
s=s.replace(class_anchor,class_anchor+"\n"+gate,1)
# Each BFS uses the same forward cable/next direction, but extract walks
# BACKWARDS towards a source, whereas insert walks FORWARDS to a sink.
for signature,outward in (("public long getAmountAsLong()",False),
                          ("public int extract(",False),("public int insert(",True)):
 x,y,part=method(s,signature)
 # Locate the correct method: don't match another embedded energy provider.
 if "energyOpen(" not in part:
  matches=[m for m in re.finditer(re.escape(signature),s)]
  selected=None
  for m in matches:
   k,j,kpart=method(s[m.start():],signature);k+=m.start();j+=m.start()
   if "energyOpen(" in kpart:selected=(k,j,kpart);break
  assert selected,("B591_NO_BFS",signature)
  x,y,part=selected
 pat1=r'energyOpen\s*\(\s*server\s*,\s*cable\s*,\s*cableState\s*,\s*side\s*\)'
 pat2=r'energyOpen\s*\(\s*server\s*,\s*next\s*,\s*nextState\s*,\s*side\.getOpposite\(\)\s*\)'
 rep1="b591FlowOpen(server,cable,cableState,side,"+str(outward).lower()+")"
 rep2="b591FlowOpen(server,next,nextState,side.getOpposite(),"+str(not outward).lower()+")"
 part,n1=re.subn(pat1,rep1,part);part,n2=re.subn(pat2,rep2,part)
 assert n1==1 and n2==1,("B591_DIRECTIONAL_BFS_ANCHOR",signature,n1,n2)
 s=s[:x]+part+s[y:]
# Physical OFF: update only the current face's cut property on config change.
# Preserve original manual cut across an OFF->BOTH cycle and world reload.
s=once(s," private final byte[] energySideMode=new byte[]{3,3,3,3,3,3};",
''' private final byte[] energySideMode=new byte[]{3,3,3,3,3,3};
 // B591_OFF_REMEMBERS_MANUAL_CUT: OFF must not destroy a manual wrench cut.
 private final byte[] b591PriorCut=new byte[6];''',str(p))
old="""    energySideMode[id]=(byte)(mode==3?1:mode==1?2:mode==2?0:3);
    setChanged();"""
new="""    energySideMode[id]=(byte)(mode==3?1:mode==1?2:mode==2?0:3);
    // B591_ENERGY_OFF_PHYSICAL_GAP: actual existing CUT blockstate arm.
    if(level!=null&&!level.isClientSide()){
     var st=getBlockState();
     net.minecraft.world.level.block.state.properties.BooleanProperty cut=switch(side){
      case DOWN->dev.obsidiannetwork.block.EnergyCableBlock.CUT_DOWN;
      case UP->dev.obsidiannetwork.block.EnergyCableBlock.CUT_UP;
      case NORTH->dev.obsidiannetwork.block.EnergyCableBlock.CUT_NORTH;
      case SOUTH->dev.obsidiannetwork.block.EnergyCableBlock.CUT_SOUTH;
      case WEST->dev.obsidiannetwork.block.EnergyCableBlock.CUT_WEST;
      case EAST->dev.obsidiannetwork.block.EnergyCableBlock.CUT_EAST;
     };
     if(mode!=0 && (energySideMode[id]&255)==0)
      b591PriorCut[id]=(byte)(st.getValue(cut)?1:0);
     boolean closed=(energySideMode[id]&255)==0 || (mode==0 && b591PriorCut[id]!=0);
     if(st.getValue(cut)!=closed)level.setBlock(worldPosition,st.setValue(cut,closed),3);
    }
    setChanged();"""
s=once(s,old,new,str(p))
s=once(s,'out.putIntArray("energy_side_io",io);',
         'out.putIntArray("energy_side_io",io);\n      int[] prior=new int[6];for(int i=0;i<6;i++)prior[i]=b591PriorCut[i];\n      out.putIntArray("b591_prior_cut",prior);',str(p))
needle='int[] io=in.getIntArray("energy_side_io").orElse(new int[0]);'
s=once(s,needle,needle+'''
      int[] previous=in.getIntArray("b591_prior_cut").orElse(new int[0]);
      for(int i=0;i<6;i++)b591PriorCut[i]=(byte)(i<previous.length&&previous[i]!=0?1:0);''',str(p))
save(p,s)

# --- FORMED MULTIBLOCK GLASS: modify only six sprites; keep seamless equal pixels.
for name,alpha in (
 ("reactor_glass_formed",56),
 ("reactor_glass_formed_lit",74),
 ("powerbank_glass_formed",28),
 ("powerbank_glass_formed_lit_detail0",40),
 ("powerbank_glass_formed_lit_detail1",40),
 ("powerbank_glass_formed_lit_detail2",40)):
 p=A/"textures/block"/(name+".png")
 with Image.open(p) as original:
  im=original.convert("RGBA")
  assert im.size==(32,32),(name,im.size)
  data=list(im.getdata())
  assert len({pix[3] for pix in data})==1,(name,"expected uniform tint")
  assert data[0][3]>alpha,(name,data[0][3])
  im.putdata([(r,g,b,alpha) for r,g,b,a in data])
  im.save(p,optimize=True)
# B575's precise alpha gate is updated, NOT disabled; preserve all other checks.
p=Path(__file__).resolve().parent.parent.parent/"tests/verify_v174_ingame_regression_575.py"
# Script lives under features/v174; tests are two directory levels above.
assert p.is_file(),("B591_B575_GATE_PATH",p)
s=load(p);s=once(s,'("reactor_glass_formed",(43,104,148,81))',
                 '("reactor_glass_formed",(43,104,148,56))',str(p))
s=once(s,'("reactor_glass_formed_lit",(49,160,232,103))',
         '("reactor_glass_formed_lit",(49,160,232,74))',str(p))
save(p,s)

# Keep the legacy B579 FE regression strict while changing ONLY its fuel rate
# expectation: the earlier 1x assertion must now require 5x consumption.
p=Path(__file__).resolve().parent.parent.parent/"tests/verify_v174_ingame_smooth_579.py"
assert p.is_file(),("B591_B579_GATE_PATH",p)
check=load(p)
check=once(check,'assert "be.fuelTicks=Math.max(0,be.fuelTicks-activity);" in react',
                  'assert "be.fuelTicks=Math.max(0,be.fuelTicks-5*activity);" in react',str(p))
save(p,check)

# --- ULTRA SOLAR: new tier only; no change in 4 existing solar tick paths.
main=J/"ObsidianNetwork.java";s=load(main)
m=re.search(r'(?m)^([ \t]*public static final DeferredBlock<[^>]*SolarGeneratorBlock>\s+ELITE_SOLAR_GENERATOR\s*=)',s)
assert m,("B591_ULTRA_BLOCK_ANCHOR",s.find("ELITE_SOLAR_GENERATOR"))
anchor=m.group(1)
s=s.replace(anchor,'''    // B591_ULTRA_SOLAR: endgame production 9 * elite, same existing low-MSPT ticker.
    public static final DeferredBlock<dev.obsidiannetwork.block.SolarGeneratorBlock> ULTRA_SOLAR_GENERATOR =
       BLOCKS.registerBlock("ultra_solar_generator",dev.obsidiannetwork.block.SolarGeneratorBlock::new,
         p -> p.mapColor(MapColor.METAL).strength(3.0F,9.0F).requiresCorrectToolForDrops());
    public static final DeferredItem<BlockItem> ULTRA_SOLAR_GENERATOR_ITEM =
       ITEMS.registerSimpleBlockItem("ultra_solar_generator",ULTRA_SOLAR_GENERATOR);
    public static final DeferredItem<net.minecraft.world.item.Item> ULTRA_SOLAR_MATRIX =
       ITEMS.registerItem("ultra_solar_matrix",net.minecraft.world.item.Item::new);
    public static final DeferredItem<net.minecraft.world.item.Item> ULTRA_ENERGY_CORE =
       ITEMS.registerItem("ultra_energy_core",net.minecraft.world.item.Item::new);
'''+anchor,1)
m=re.search(r'(?m)^(\s*)output\.accept\(\(ItemLike\)ELITE_SOLAR_GENERATOR_ITEM\.get\(\)\);',s)
assert m,("B591_CREATIVE_TAB")
s=s[:m.end()]+"\n"+m.group(1)+'''output.accept((ItemLike)ULTRA_SOLAR_GENERATOR_ITEM.get());
'''+m.group(1)+'''output.accept((ItemLike)ULTRA_SOLAR_MATRIX.get());
'''+m.group(1)+'''output.accept((ItemLike)ULTRA_ENERGY_CORE.get());'''+s[m.end():]
save(main,s)
solar=J/"blockentity/SolarGeneratorBlockEntity.java";s=load(solar)
m=re.search(r'(?m)^(\s*public static final (?:SolarGeneratorBlockEntity\.)?Tier ELITE\s*=\s*new (?:SolarGeneratorBlockEntity\.)?Tier\s*\([^;]+\);)',s)
assert m,("B591_ELITE_TIER",s[s.find("ELITE")-100:s.find("ELITE")+400])
s=s[:m.end()]+"\n public static final Tier ULTRA = new Tier(5,46080L,32000000L,\"Ultra\");"+s[m.end():]
m=re.search(r'public static (?:SolarGeneratorBlockEntity\.)?Tier tierFor\s*\(\s*Block\s+\w+\s*\)\s*\{',s)
assert m,("B591_TIER_FOR",s.find("tierFor"))
param=re.search(r'\(\s*Block\s+(\w+)\s*\)',m.group()).group(1)
s=s[:m.end()]+"\n  if("+param+"==dev.obsidiannetwork.ObsidianNetwork.ULTRA_SOLAR_GENERATOR.get())return ULTRA; // B591_ULTRA_TIER\n"+s[m.end():]
save(solar,s)
be=J/"registry/ModBlockEntities.java";s=load(be)
anchor="(Block)ObsidianNetwork.ELITE_SOLAR_GENERATOR.get()"
if s.count(anchor)==1:s=s.replace(anchor,anchor+",\n         (Block)ObsidianNetwork.ULTRA_SOLAR_GENERATOR.get()",1)
else:
 anchor="ObsidianNetwork.ELITE_SOLAR_GENERATOR.get()"
 assert s.count(anchor)==1,("B591_SOLAR_BE_REG",s.count(anchor))
 s=s.replace(anchor,anchor+",\n         ObsidianNetwork.ULTRA_SOLAR_GENERATOR.get()",1)
save(be,s)

# The new block is pickaxe-minable and drops its item, like other panels.
tag=Path(os.environ["V1_RESOURCE_ROOT"])/"data/minecraft/tags/block/mineable/pickaxe.json"
assert tag.is_file(),("B591_PICKAXE_TAG_MISSING",tag)
tagdata=json.loads(load(tag));assert "obsidiannetwork:ultra_solar_generator" not in tagdata.get("values",[])
tagdata["values"].append("obsidiannetwork:ultra_solar_generator")
save(tag,json.dumps(tagdata,indent=2)+"\n")
# Three recipes enforce nine elite panels, eight cores, 64 netherite blocks,
# and eight nether stars per ultra solar panel.
recipes={
 "ultra_solar_matrix":(["EEE","EEE","EEE"],{"E":"obsidiannetwork:elite_solar_generator"}),
 "ultra_energy_core":(["NNN","NSN","NNN"],{"N":"minecraft:netherite_block","S":"minecraft:nether_star"}),
 "ultra_solar_generator":(["CCC","CMC","CCC"],{"C":"obsidiannetwork:ultra_energy_core","M":"obsidiannetwork:ultra_solar_matrix"})
}
for name,(pattern,key) in recipes.items():
 p=R/"recipe"/(name+".json")
 assert not p.exists(),("B591_RECIPE_COLLISION",str(p))
 p.write_text(json.dumps({"type":"minecraft:crafting_shaped","category":"misc",
   "pattern":pattern,"key":key,"result":{"id":"obsidiannetwork:"+name,"count":1}},indent=2)+"\n")
# New block's model inherits elite's mesh and preserves all existing sprites.
for root,folder in ((A/"blockstates","blockstates"),(A/"models/block","models/block"),
                    (A/"models/item","models/item"),(A/"items","items")):
 original=root/"elite_solar_generator.json";out=root/"ultra_solar_generator.json"
 assert original.exists() and not out.exists(),("B591_MODEL_PATH",original,out)
 data=load(original).replace("elite_solar_generator","ultra_solar_generator")
 if folder=="models/block":
  # Keep the full tested elite panel texture/model until custom artwork is approved.
  data=data.replace("obsidiannetwork:block/ultra_solar_generator","obsidiannetwork:block/elite_solar_generator")
 out.write_text(data)
for name,vanilla in (("ultra_solar_matrix","nether_star"),("ultra_energy_core","netherite_ingot")):
 (A/"models/item"/(name+".json")).write_text(json.dumps({"parent":"minecraft:item/generated",
   "textures":{"layer0":"minecraft:item/"+vanilla}},indent=2)+"\n")
 (A/"items"/(name+".json")).write_text(json.dumps({"model":{"type":"minecraft:model",
    "model":"obsidiannetwork:item/"+name}},indent=2)+"\n")
(A/"textures/block/ultra_solar_generator.png").write_bytes((A/"textures/block/elite_solar_generator.png").read_bytes())
loot=R/"loot_table/blocks/ultra_solar_generator.json";loot.parent.mkdir(parents=True,exist_ok=True)
loot.write_text(json.dumps({"type":"minecraft:block","pools":[{"rolls":1,"entries":[
 {"type":"minecraft:item","name":"obsidiannetwork:ultra_solar_generator"}]}]},indent=2)+"\n")
for lang,names in (("en_us",("Ultra Solar Panel","Ultra Solar Matrix","Ultra Energy Core")),
                   ("de_de",("Ultra-Solarpanel","Ultra-Solarmatrix","Ultra-Energiekern"))):
 p=A/"lang"/(lang+".json");d=json.loads(load(p))
 for key,value in zip(("block.obsidiannetwork.ultra_solar_generator",
                       "item.obsidiannetwork.ultra_solar_matrix",
                       "item.obsidiannetwork.ultra_energy_core"),names):
  assert key not in d,key
  d[key]=value
 save(p,json.dumps(d,indent=2,ensure_ascii=False)+"\n")
print("B591_REACTOR_FUEL_X5_AUTO_FULL_POWERBANK_OUTPUT_ENERGY_DIRECTION_GLASSES_ULTRA_SOLAR_PASS")
