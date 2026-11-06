#!/usr/bin/env python3
"""B1230: Keep the PLACED Backpack GUI open during committed Item Cable IO.

A held/placed GUI should remain attached to the same block entity when its
three installed storage cells are changed by transactional cable extraction
or insertion. Only rebase a GUI snapshot after a COMMITTED cable transaction;
menu writes retain strict compare-and-swap against the last validated snapshot.
Never rebase inside save(), which would overwrite a concurrent cable update.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel, old, new):
 p=J/rel
 src=p.read_text(encoding="utf-8")
 count=src.count(old)
 assert count==1,("B1230_BACKPACK_SOURCE_DRIFT",rel,count,old[:130])
 p.write_text(src.replace(old,new,1),encoding="utf-8")

be="backpack/NetworkBackpackBlockEntity.java"
change(be,
 ''' private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''', 
 ''' // Only committed, not simulated or rolled-back, cable transfers advance
 // this generation. Menus can rebase their view without relinquishing CAS.
 private long xsxCableCommitRevision=0L;
 public long xsxCableCommitRevision(){return xsxCableCommitRevision;}
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=''')

change(be,
 '''    @Override protected void onRootCommit(ItemStack before){setChanged();}''',
 '''    @Override protected void onRootCommit(ItemStack before){
     // Both cable insert/extract are root-transaction committed here. Do not
     // count speculative simulations or rollbacks as external mutations.
     xsxCableCommitRevision++;
     setChanged();
    }''')

menu="backpack/V176BackpackMenu.java"
change(menu,
 '''  private ItemStack snapshot;
  public BlockSource(ServerPlayer player,NetworkBackpackBlockEntity be,BlockPos pos){
   this.player=player;this.be=be;this.pos=pos.immutable();
   snapshot=be.getBackpack().copy();
  }
  @Override public ItemStack current(){return be.getBackpack();}
  @Override public boolean valid(){
   return player.isAlive()&&player.level()==be.getLevel()
      &&player.level().getBlockEntity(pos)==be
      &&player.distanceToSqr(pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5)<=64
      &&ItemStack.matches(snapshot,be.getBackpack());
  }
  @Override public boolean save(ItemStack next){
   if(!valid()||!be.replaceBackpack(snapshot,next))return false;
   snapshot=next.copy();
   return true;
  }''',
 '''  private ItemStack snapshot;
  private long snapshotCableRevision;
  public BlockSource(ServerPlayer player,NetworkBackpackBlockEntity be,BlockPos pos){
   this.player=player;this.be=be;this.pos=pos.immutable();
   snapshot=be.getBackpack().copy();
   snapshotCableRevision=be.xsxCableCommitRevision();
  }
  @Override public ItemStack current(){return be.getBackpack();}
  private boolean samePlacedBackpack(){
   return player.isAlive()&&player.level()==be.getLevel()
      &&player.level().getBlockEntity(pos)==be
      &&player.distanceToSqr(pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5)<=64
      &&!be.getBackpack().isEmpty()
      &&be.getBackpack().getCount()==1
      &&be.getBackpack().getItem()==snapshot.getItem()
      &&be.getBackpack().getItem() instanceof NetworkBackpackItem;
  }
  @Override public boolean valid(){
   if(!samePlacedBackpack())return false;
   if(!ItemStack.matches(snapshot,be.getBackpack())){
    long revision=be.xsxCableCommitRevision();
    // A change from some OTHER cause is not an authorized cable rebase.
    if(revision==snapshotCableRevision)return false;
    snapshot=be.getBackpack().copy();
    snapshotCableRevision=revision;
   }
   return true;
  }
  @Override public boolean save(ItemStack next){
   // IMPORTANT: do NOT call valid() here; that would silently rebase a stale
   // mutation and could overwrite a cable transfer occurring after read.
   if(!samePlacedBackpack()
       ||!ItemStack.matches(snapshot,be.getBackpack())
       ||!be.replaceBackpack(snapshot,next))return false;
   snapshot=next.copy();
   snapshotCableRevision=be.xsxCableCommitRevision();
   return true;
  }''')

# Visible preview slots must also refresh when the same ItemStack instance
# was changed by an extract transaction inside the current game tick. Otherwise
# an open GUI can lag behind a cable even though the menu stays open.
change(menu,
 '''  private ItemStack cacheSource=ItemStack.EMPTY;
  private long cacheTick=Long.MIN_VALUE;''',
 '''  private ItemStack cacheSource=ItemStack.EMPTY;
  private long cacheCableRevision=Long.MIN_VALUE;
  private long cacheTick=Long.MIN_VALUE;''')
change(menu,
 '''   if(cacheTick==tick&&cacheSource==live
        &&cacheQuery.equals(query)&&cacheSort==countSort)return cacheEntries;''',
 '''   long liveCableRevision=source instanceof BlockSource bag
       ?bag.be.xsxCableCommitRevision():-1L;
   if(cacheTick==tick&&cacheSource==live
        &&cacheCableRevision==liveCableRevision
        &&cacheQuery.equals(query)&&cacheSort==countSort)return cacheEntries;''')
change(menu,
 '''   cacheTick=tick;
   cacheSource=live;''',
 '''   cacheTick=tick;
   cacheSource=live;
   cacheCableRevision=liveCableRevision;''')

src=(J/menu).read_text(encoding="utf-8")
be_src=(J/be).read_text(encoding="utf-8")
assert src.count("snapshotCableRevision=revision;")==1
assert src.count("!ItemStack.matches(snapshot,be.getBackpack())")==2
assert "||!be.replaceBackpack(snapshot,next)" in src
assert "xsxCableCommitRevision++;" in be_src
assert "cableJournal.updateSnapshots(tx)" in be_src
print("B1230_BACKPACK_GUI_STAYS_OPEN_ON_COMMITTED_CABLE_IO_AND_ATOMIC_CAS_PASS")
