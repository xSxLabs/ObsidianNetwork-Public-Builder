#!/usr/bin/env python3
"""v1.7.4 recovery: recheck multiblocks after server restart and reject orphan ports."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(rel,old,new):
 p=J/rel
 text=p.read_text(encoding="utf-8")
 assert text.count(old)==1,("V174_RECOVERY_SOURCE_DRIFT",rel,old[:90],text.count(old))
 p.write_text(text.replace(old,new,1),encoding="utf-8")

# Restarts must not create FE from a stale persisted formed flag. Instead,
# recover only those reactors explicitly formed before the save, at a staggered
# 200-tick retry, and only when enough world chunks are loaded to validate.
change("reactor/ReactorControllerBlockEntity.java",
 ' private boolean formed=false;\n private String status="UNFORMED";',
 ''' private boolean formed=false;
 private boolean restorePending=false;
 private String status="UNFORMED";''')
change("reactor/ReactorControllerBlockEntity.java",
 '''  if(!(level instanceof ServerLevel sl)||sl.getGameTime()%20L!=0L)return;
  // Full revalidation is deliberately infrequent, NOT on every block/entity tick.''',
 '''  if(!(level instanceof ServerLevel sl)||sl.getGameTime()%20L!=0L)return;
  // V174_REACTOR_AUTO_RECOVERY_431: stagger retries; never trust a saved
  // formed flag without rechecking all shell blocks in loaded chunks.
  long phase=Math.floorMod(pos.asLong(),200L);
  if(be.restorePending&&(sl.getGameTime()+phase)%200L==0L){
   var checked=be.revalidate(sl);
   String reason=checked.reason().toLowerCase(java.util.Locale.ROOT);
   if(checked.valid()||(!reason.contains("unload")&&!reason.contains("not loaded")))
    be.restorePending=false;
  }
  // Full revalidation is deliberately infrequent, NOT on every block/entity tick.''')
# The tick code executes only every 20 ticks. Use a phase aligned to its
# 20-tick cadence rather than arbitrary hash bits, otherwise it may never fire.
change("reactor/ReactorControllerBlockEntity.java",
 '  long phase=Math.floorMod(pos.asLong(),200L);',
 '  long phase=Math.floorMod(pos.asLong(),10L)*20L;')
change("reactor/ReactorControllerBlockEntity.java",
 '''  formed=false;status="REVALIDATE (SHIFT + RIGHT CLICK)";''',
 '''  restorePending=in.getBooleanOr("reactorFormed",false);
  formed=false;status=restorePending?"RESTORING":"UNFORMED";''')

# The 3x3x(3..12) Powerbank can be cheaply checked every 20 seconds, including
# after a restart, without a chunk load or permanent polling of the full world.
change("powerbank/PowerbankBlock.java",
 ''' @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){return new PowerbankBlockEntity(p,s);}
 private InteractionResult access''',
 ''' @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){return new PowerbankBlockEntity(p,s);}
 @Override public <T extends BlockEntity> net.minecraft.world.level.block.entity.BlockEntityTicker<T> getTicker(
      Level level,BlockState state,net.minecraft.world.level.block.entity.BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,ModBlockEntities.POWERBANK.get(),
      PowerbankBlockEntity::tick);
 }
 private InteractionResult access''')

# Link membership is recalculated on each real shell validation. A previously
# linked port does not retain access after it leaves a valid multiblock.
change("powerbank/PowerbankBlockEntity.java",
 ''' private long linked=NONE,amount=0L,capacity=0L;
 private boolean formed=false;''',
 ''' private long linked=NONE,amount=0L,capacity=0L;
 // V174_POWERBANK_AUTHORIZED_PORTS_431: runtime-only, reconstructed per shell.
 private final java.util.Set<Long> activePorts=new java.util.HashSet<>();
 private boolean formed=false;''')
change("powerbank/PowerbankBlockEntity.java",
 '''      &&be.mode()==PowerbankBlock.Mode.CONTROLLER&&be.formed)return be;''',
 '''      &&be.mode()==PowerbankBlock.Mode.CONTROLLER&&be.formed
      &&be.activePorts.contains(worldPosition.asLong()))return be;''')
change("powerbank/PowerbankBlockEntity.java",
 '''  formed=result.valid();
  if(formed){
   capacity=result.capacity();
   for(BlockPos p:result.ports()){''',
 '''  formed=result.valid();
  activePorts.clear();
  if(formed){
   capacity=result.capacity();
   for(BlockPos p:result.ports()){
    activePorts.add(p.asLong());''')
change("powerbank/PowerbankBlockEntity.java",
 ''' private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> journal=''', 
 ''' // V174_POWERBANK_AUTO_RECOVERY_431: bounded validation on the main server
 // thread. 400 ticks interval, coordinates stagger checks across controllers.
 public static void tick(net.minecraft.world.level.Level world,BlockPos at,BlockState state,
                         PowerbankBlockEntity be){
  if(!(world instanceof ServerLevel sl)||be.mode()!=PowerbankBlock.Mode.CONTROLLER)return;
  long phase=Math.floorMod(at.asLong(),400L);
  if((sl.getGameTime()+phase)%400L!=0L)return;
  be.revalidate(sl);
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> journal=''')
# Important: one ticker invocation per tick, no overrun of 3x3x12 scan;
# no FE mutation in validation, and no target chunk force-load.
generated=(J/"powerbank/PowerbankBlockEntity.java").read_text()
assert "activePorts.contains(worldPosition.asLong())" in generated
assert "bankAmount" in generated and "formed=false" in generated
assert "getChunkAt(" not in generated
reactor=(J/"reactor/ReactorControllerBlockEntity.java").read_text()
assert "V174_REACTOR_AUTO_RECOVERY_431" in reactor
assert "restorePending=in.getBooleanOr" in reactor
assert "storedFe=Math.max" in reactor
print("V174_MULTIBLOCK_RECOVERY_431_PASS")
