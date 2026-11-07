#!/usr/bin/env python3
"""B1324: ZERO internal FE buffering for Wireless Transmitter/Receiver.

Use direct transactional FE forwarding:
- transmitter.insert forwards to actual accepting receivers in the SAME
  transaction; idle networks return zero and cannot drain generators;
- receiver.extract / player wireless charging pulls live FE directly from
  loaded neighboring sources at an indexed transmitter;
- receiver auto-push performs sink preflight and commits only exact delivery.
No chunk loads, offline buffers, FE creation, or unbounded network traversal.
Legacy 'wireless_fe' NBT is retired; old saved transmitter balances are not
treated as available new energy. Run only after all existing wireless patches.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
runtime=root/"wireless/WirelessEnergyRuntime.java"
entity=root/"blockentity/WirelessNetworkBlockEntity.java"
files=[runtime,entity]
original={f:f.read_text("utf-8") for f in files}
r=original[runtime]; e=original[entity]

required_runtime=["NEXT_SENDER","WeakReference<WirelessNetworkBlockEntity>",
 "public static void register(WirelessNetworkBlockEntity sender)",
 "public static int pull(MinecraftServer server,String id,int wanted,TransactionContext tx)"]
required_entity=["public static final long CAPACITY=64000000L;",
 "private long stored;","public int withdraw(int requested,TransactionContext tx)",
 "private final class Handler implements EnergyHandler",
 "private final Journal journal=new Journal();",
 "public static void serverTick(Level level,BlockPos pos,BlockState state,WirelessNetworkBlockEntity be)",
 "int remainingBudget=Math.min(MAX_TRANSFER,64000);",
 "journal.updateSnapshots(tx);stored+=accepted;",
 'out.putLong("wireless_fe",stored);',
 "stored=transmitter?Math.max(0L,Math.min(CAPACITY,in.getLongOr(\"wireless_fe\",0L))):0L;"]
for token in required_runtime:
 assert token in r,("B1324_RUNTIME_DRIFT",token)
for token in required_entity:
 assert token in e,("B1324_ENTITY_DRIFT",token)

def one(text,old,new,label):
 n=text.count(old)
 assert n==1,("B1324_ANCHOR_DRIFT",label,n,old[:100])
 return text.replace(old,new,1)

def swap_method(src,signature,code):
 start=src.index(signature)
 opening=src.index("{",start)
 depth=0
 for i in range(opening,len(src)):
  if src[i]=="{":depth+=1
  elif src[i]=="}":
   depth-=1
   if depth==0:return src[:start]+code+src[i+1:]
 raise AssertionError(("B1324_METHOD_BOUNDS",signature))

# Retain network identifiers, ownership and all GUI access. Delete *all*
# power storage from the actual wireless blocks; cells/powerbank keep storage.
e=one(e," public static final long CAPACITY=64000000L;\n",
 "// B1324_DIRECT_FE_NO_TX_RX_BUFFER: antennas do not own energy.\n","remove_capacity")
e=one(e," private long stored;\n","","remove_stored_field")
e=one(e," public long stored(){return stored;}"," public long stored(){return 0L;}","legacy_status_no_storage")
e=one(e,"&&stored>0;",";","live_tx_not_buffer")
assert e.count("if(transmitter)WirelessEnergyRuntime.unregister(this);")==3
# Change all three lifecycle paths (selectNetwork, setRemoved, unload).
# There are three old sender-only unregister sites.
assert e.count("if(transmitter)WirelessEnergyRuntime.register(this);")==2
e=e.replace("if(transmitter)WirelessEnergyRuntime.register(this);","WirelessEnergyRuntime.register(this);")
assert e.count("if(transmitter)WirelessEnergyRuntime.unregister(this);")==3
e=e.replace("if(transmitter)WirelessEnergyRuntime.unregister(this);","WirelessEnergyRuntime.unregister(this);")
e=one(e,'  out.putLong("wireless_fe",stored);',
 """  // Legacy buffer NBT deliberately NOT emitted. Antennas now move FE only
  // between real machines; the saved network ID and owner remain persistent.""",
 "no_wireless_fe_save")
e=one(e,'  stored=transmitter?Math.max(0L,Math.min(CAPACITY,in.getLongOr("wireless_fe",0L))):0L;',
 """  // Legacy wireless_fe is ignored; never mint or silently re-expose it as
  // a new buffer. Drain older transmitter storage before installing this build.""",
 "no_wireless_fe_load")

e=swap_method(e," public int withdraw(int requested,TransactionContext tx)",r''' public int withdraw(int requested,TransactionContext tx){
  if(!isActive()||requested<=0||!(level instanceof ServerLevel world))return 0;
  int moved=0;
  // An antenna has zero FE. Pull only from actual neighboring generators/cells.
  for(Direction face:DIRECTIONS){
   if(moved>=requested)break;
   BlockPos neighbor=worldPosition.relative(face);
   if(!world.hasChunkAt(neighbor)||world.getBlockState(neighbor).getBlock()
       instanceof dev.obsidiannetwork.block.WirelessNetworkBlock)continue;
   EnergyHandler source=world.getCapability(Capabilities.Energy.BLOCK,
       neighbor,face.getOpposite());
   if(source==null||source==handler)continue;
   int extracted=source.extract(requested-moved,tx);
   if(extracted>0)moved+=Math.min(extracted,requested-moved);
  }
  return moved;
 }
 /** Advertise only real accessible neighboring source FE, NOT local storage.
  * This is advisory: the actual extracted amount is always transactional.
  */
 public long availableFromNeighbors(){
  if(!isActive()||!(level instanceof ServerLevel world))return 0L;
  long available=0L;
  for(Direction face:DIRECTIONS){
   BlockPos neighbor=worldPosition.relative(face);
   if(!world.hasChunkAt(neighbor)||world.getBlockState(neighbor).getBlock()
       instanceof dev.obsidiannetwork.block.WirelessNetworkBlock)continue;
   EnergyHandler source=world.getCapability(Capabilities.Energy.BLOCK,
       neighbor,face.getOpposite());
   if(source==null||source==handler)continue;
   available=Math.min((long)Integer.MAX_VALUE,
       available+Math.max(0L,source.getAmountAsLong()));
  }
  return available;
 }
 /** Direct transmitter push: put FE into real receiver-adjacent demand.
  * All inserts are part of the generator's parent TransactionContext.
  * No receiver stores energy, and no receiver advertises input capacity.
  */
 public int offerToNeighbors(int offered,TransactionContext tx){
  if(transmitter||offered<=0||isRemoved()
      ||!(level instanceof ServerLevel world)||!world.hasChunkAt(worldPosition))return 0;
  int moved=0;
  for(Direction face:DIRECTIONS){
   if(moved>=offered)break;
   BlockPos neighbor=worldPosition.relative(face);
   if(!world.hasChunkAt(neighbor)||world.getBlockState(neighbor).getBlock()
       instanceof dev.obsidiannetwork.block.WirelessNetworkBlock)continue;
   EnergyHandler sink=world.getCapability(Capabilities.Energy.BLOCK,
       neighbor,face.getOpposite());
   if(sink==null||sink==handler)continue;
   int accepted=sink.insert(offered-moved,tx);
   if(accepted>0)moved+=Math.min(accepted,offered-moved);
  }
  return moved;
 }''')

e=swap_method(e," private final class Handler implements EnergyHandler",r''' private final class Handler implements EnergyHandler {
  // A wireless endpoint is never a storage container. For receivers, expose
  // upstream live source availability as a proxy for machines that probe FE.
  public long getAmountAsLong(){
   if(transmitter||!(level instanceof ServerLevel server))return 0L;
   return WirelessEnergyRuntime.available(server.getServer(),networkId);
  }
  public long getCapacityAsLong(){
   // Receiver has a proxy extraction capability, not an FE tank.
   return transmitter?0L:Integer.MAX_VALUE;
  }
  public int insert(int amount,TransactionContext tx){
   if(!transmitter||amount<=0||!(level instanceof ServerLevel server)
       ||!isActive())return 0;
   return WirelessEnergyRuntime.offer(server.getServer(),networkId,amount,tx);
  }
  public int extract(int amount,TransactionContext tx){
   if(transmitter||amount<=0||!(level instanceof ServerLevel world))return 0;
   return WirelessEnergyRuntime.pull(world.getServer(),networkId,
       Math.min(amount,64000),tx);
  }
 }''')
assert "private long stored;" not in e
assert "journal.updateSnapshots(tx)" not in e
assert 'putLong("wireless_fe"' not in e
assert "stored+=" not in e and "stored-=" not in e

# Keep the proven weak loaded-transmitter registry, its round-robin sender
# selection, and the single reentry guard; add loaded receivers as sinks.
r=one(r," private static final ThreadLocal<Boolean> IN_TRANSFER=ThreadLocal.withInitial(()->false);",
 """ private static final ThreadLocal<Boolean> IN_TRANSFER=ThreadLocal.withInitial(()->false);
 private static final ThreadLocal<Boolean> IN_AVAILABLE=ThreadLocal.withInitial(()->false);
 private static final Map<MinecraftServer,Map<String,List<WeakReference<WirelessNetworkBlockEntity>>>> RECEIVERS =
  new WeakHashMap<>();""","receiver_registry")
r=swap_method(r," public static void register(WirelessNetworkBlockEntity sender)",r''' public static void register(WirelessNetworkBlockEntity sender){
  if(!(sender.getLevel() instanceof ServerLevel level))return;
  var registry=sender.isTransmitter()?LOADED:RECEIVERS;
  var bucket=registry.computeIfAbsent(level.getServer(),s->new HashMap<>())
    .computeIfAbsent(sender.networkId(),s->new ArrayList<>());
  bucket.removeIf(ref->ref.get()==null||ref.get()==sender);
  bucket.add(new WeakReference<>(sender));
 }''')
r=swap_method(r," public static void unregister(WirelessNetworkBlockEntity sender)",r''' public static void unregister(WirelessNetworkBlockEntity sender){
  if(!(sender.getLevel() instanceof ServerLevel level))return;
  var registry=sender.isTransmitter()?LOADED:RECEIVERS;
  var server=registry.get(level.getServer());
  if(server==null)return;
  var bucket=server.get(sender.networkId());
  if(bucket==null)return;
  bucket.removeIf(ref->ref.get()==null||ref.get()==sender);
  if(bucket.isEmpty())server.remove(sender.networkId());
  if(server.isEmpty())registry.remove(level.getServer());
 }''')
r=swap_method(r," public static long available(MinecraftServer server,String id)",r''' public static long available(MinecraftServer server,String id){
  if(IN_TRANSFER.get()||IN_AVAILABLE.get()
      ||WirelessNetworkData.get(server).find(id)==null)return 0L;
  var nets=LOADED.get(server);
  if(nets==null)return 0L;
  var group=nets.get(id);
  if(group==null)return 0L;
  IN_AVAILABLE.set(true);
  try{
   long total=0L;
   for(var ref:group){
    var be=ref.get();
    if(be!=null&&be.isActive()&&id.equals(be.networkId()))
     total=Math.min((long)Integer.MAX_VALUE,total+be.availableFromNeighbors());
   }
   return total;
  }finally{IN_AVAILABLE.set(false);}
 }''')
r=swap_method(r," public static int pull(MinecraftServer server,String id,int wanted,TransactionContext tx)",r''' public static int pull(MinecraftServer server,String id,int wanted,TransactionContext tx){
  if(wanted<=0||IN_TRANSFER.get()||WirelessNetworkData.get(server).find(id)==null)return 0;
  var nets=LOADED.get(server);
  if(nets==null)return 0;
  var group=nets.get(id);
  if(group==null||group.isEmpty())return 0;
  IN_TRANSFER.set(true);
  try{
   int remaining=wanted;
   int size=group.size();
   var cursors=NEXT_SENDER.computeIfAbsent(server,s->new HashMap<>());
   int start=Math.floorMod(cursors.getOrDefault(id,0),size);
   for(int offset=0;offset<size&&remaining>0;offset++){
    var be=group.get((start+offset)%size).get();
    if(be==null||!be.isActive()||!id.equals(be.networkId()))continue;
    remaining-=be.withdraw(remaining,tx);
   }
   cursors.put(id,(start+1)%size);
   return wanted-remaining;
  }finally{IN_TRANSFER.set(false);}
 }
 /** Accept generator push only to real, loaded receiver-side consumers.
  * Return zero when all consumers are full; the generator retains its FE.
  */
 public static int offer(MinecraftServer server,String id,int offered,TransactionContext tx){
  if(offered<=0||IN_TRANSFER.get()||WirelessNetworkData.get(server).find(id)==null)return 0;
  var groups=RECEIVERS.get(server);
  if(groups==null)return 0;
  var receivers=groups.get(id);
  if(receivers==null)return 0;
  IN_TRANSFER.set(true);
  try{
   int remaining=offered;
   for(var ref:receivers){
    if(remaining<=0)break;
    var device=ref.get();
    if(device==null||device.isRemoved()||device.isTransmitter()
        ||!id.equals(device.networkId()))continue;
    remaining-=device.offerToNeighbors(remaining,tx);
   }
   return offered-remaining;
  }finally{IN_TRANSFER.set(false);}
 }''')
assert "be.stored()" not in r
assert "be.withdraw(remaining,tx)" in r and "be.offerToNeighbors(remaining,tx)" in r
assert "IN_TRANSFER.set(false)" in r and "IN_AVAILABLE.set(false)" in r
assert "NEXT_SENDER" in r and "WeakReference<WirelessNetworkBlockEntity>" in r
# Both files checked before any write.
entity.write_text(e,encoding="utf-8")
runtime.write_text(r,encoding="utf-8")
print("B1324_ZERO_BUFFER_WIRELESS_DIRECT_FE_DEMAND_ONLY_ATOMIC_PASS")
