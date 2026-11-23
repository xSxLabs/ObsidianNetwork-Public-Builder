#!/usr/bin/env python3
"""B1861 / 1.7.8 v20: fluent water/lava removal and lossless chest/minecart mining.

The machine must have output space for ALL block loot and container contents
before it removes the source. This keeps conservation, loaded-chunk, ownership,
energy and global TPS budgets. Unrelated block entities and special minecarts
are left untouched.
"""
from pathlib import Path
import os

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=j/"mining/V178MiningBuilderBE.java"
s=p.read_text("utf-8")

def exactly(old,new):
    global s
    n=s.count(old)
    assert n==1,("B1861_SOURCE_DRIFT",old[:100],n)
    s=s.replace(old,new,1)

# Small, owner-checked minecart helper: no tick-world scans, only the target
# voxel already inside the region. Each cart occupies one budgeted mining op.
anchor=" public static void serverTick(Level level,BlockPos at,BlockState state,V178MiningBuilderBE machine){"
helper=""" // B1861: 0=no cart; 1=one safely collected; -1=pause at this voxel.
  private int b1861Minecart(ServerLevel world,BlockPos target){
   var carts=world.getEntitiesOfClass(
       net.minecraft.world.entity.vehicle.minecart.AbstractMinecart.class,
       new net.minecraft.world.phys.AABB(target));
   if(carts.isEmpty())return 0;
   for(var cart:carts){
    // Never disturb riders or special TNT/command/furnace/spawner minecarts.
    if(!cart.getPassengers().isEmpty()||!
        (cart instanceof net.minecraft.world.entity.vehicle.minecart.Minecart
        ||cart instanceof net.minecraft.world.entity.vehicle.minecart.MinecartChest
        ||cart instanceof net.minecraft.world.entity.vehicle.minecart.MinecartHopper))
     return -1;
    ItemStack vehicle=cart.getPickResult();
    if(vehicle.isEmpty())return -1;
    net.minecraft.world.Container cargo=
      cart instanceof net.minecraft.world.entity.vehicle.minecart.AbstractMinecartContainer c ? c : null;
    ItemStack[] saved=b1861Contents(cargo);
    try(Transaction tx=Transaction.openRoot()){
     if(!b1861Store(vehicle,tx)||!b1861StoreAll(saved,tx))return -1;
     if(!budget(world))return -1;
     if(cargo!=null)cargo.clearContent();
     // No entity drops: both the cart itself and its cargo are now in output.
     cart.discard();
     tx.commit();
     energy.set(Math.max(0,energy.getAmountAsInt()-ENERGY_PER_BLOCK));
     setChanged();
     return 1;
    }
   }
   return 0;
  }
  private static ItemStack[] b1861Contents(net.minecraft.world.Container inventory){
   if(inventory==null)return new ItemStack[0];
   ItemStack[] saved=new ItemStack[inventory.getContainerSize()];
   for(int slot=0;slot<saved.length;slot++)saved[slot]=inventory.getItem(slot).copy();
   return saved;
  }
  private boolean b1861Store(ItemStack stack,Transaction tx){
   return stack.isEmpty()||output.insert(ItemResource.of(stack),stack.getCount(),tx)==stack.getCount();
  }
  private boolean b1861StoreAll(ItemStack[] stacks,Transaction tx){
   for(ItemStack stack:stacks)if(!b1861Store(stack,tx))return false;
   return true;
  }
 """
exactly(anchor,helper+anchor)

old="""    if(current.isAir()||!current.getFluidState().isEmpty()
       ||current.getDestroySpeed(world,target)<0
       ||world.getBlockEntity(target)!=null
       ||target.equals(at)){
     ++machine.cursor;continue;
    }
    // Ownership enforced for every voxel, including cross-border selections.
    // Fail closed: target chunk must be owned by the builder operator.
    // No arbitrary wilderness or third-party-claimed mining.
    if(!V178Claims.mayMachineMine(world,target,machine.owner))return;
    if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;"""
assert s.count(old)==1,("B1861_BASE_MINE_GATE_MISMATCH",s.count(old))
new="""    if(target.equals(at)){++machine.cursor;continue;}
    // Authorization BEFORE entity/fluid/block handling, including empty cells.
    if(!V178Claims.mayMachineMine(world,target,machine.owner))return;
    if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;
    int cartResult=machine.b1861Minecart(world,target);
    if(cartResult!=0)return; // retry this voxel; other carts may be present
    if(current.isAir()||current.getDestroySpeed(world,target)<0){
     ++machine.cursor;continue;
    }
    // Avoid silently voiding arbitrary tile inventories in third-party mods.
    BlockEntity tile=world.getBlockEntity(target);
    if(tile!=null && !(tile instanceof net.minecraft.world.Container)
        && !(tile instanceof net.minecraft.world.level.block.entity.ShulkerBoxBlockEntity)){
     ++machine.cursor;continue;
    }
    // Vanilla water and lava (source or flowing) have no item loot.
    if(current.getBlock() instanceof net.minecraft.world.level.block.LiquidBlock){
     if(!canMineThisTick(world)||!budget(world))return;
     if(!world.setBlock(target,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3))return;
     machine.energy.set(Math.max(0,machine.energy.getAmountAsInt()-ENERGY_PER_BLOCK));
     ++machine.cursor;machine.setChanged();mined++;continue;
    }"""
exactly(old,new)

old2="""     var drops=Block.getDrops(current,world,target,null,null,machine.effectivePickaxe(world));
    try(Transaction tx=Transaction.openRoot()){
     boolean fits=true;
     for(ItemStack drop:drops)if(!drop.isEmpty()
        &&machine.output.insert(ItemResource.of(drop),drop.getCount(),tx)!=drop.getCount()){
       fits=false;break;
     }
     if(!fits)return; // full buffer means the mining machine PAUSES
     if(!budget(world))return; // global lag protection
     if(!world.destroyBlock(target,false))return;
     tx.commit(); // mined drops now owned by the machine, no item entities"""
# Current source may contain comment just before var drops; this is stable after
# B1692 and B1700 patches.
assert s.count(old2)==1,("B1861_DROP_TRANSACTION_ANCHOR",s.count(old2))
new2="""    // Supply the real tile to loot tables (important for shulker item contents).
    var drops=Block.getDrops(current,world,target,tile,null,machine.effectivePickaxe(world));
    // Shulkers preserve their inventory in the shulker item, not separately.
    net.minecraft.world.Container inventory=
      tile instanceof net.minecraft.world.Container c
       && !(tile instanceof net.minecraft.world.level.block.entity.ShulkerBoxBlockEntity)
       ? c : null;
    ItemStack[] contents=b1861Contents(inventory);
    try(Transaction tx=Transaction.openRoot()){
     boolean fits=true;
     for(ItemStack drop:drops)if(!machine.b1861Store(drop,tx)){fits=false;break;}
     if(fits)fits=machine.b1861StoreAll(contents,tx);
     if(!fits)return; // no break or chest mutation until ALL loot fits
     if(!budget(world))return; // global lag protection
     // Empty source before break so vanilla preRemove cannot drop contents
     // into world AND output. Restore it if the break was refused.
     if(inventory!=null)inventory.clearContent();
     if(!world.destroyBlock(target,false)){
      if(inventory!=null)for(int i=0;i<contents.length;i++)
       inventory.setItem(i,contents[i]);
      return;
     }
     tx.commit(); // container + block drops now owned exactly once"""
exactly(old2,new2)

# The existing v18 mining rate, FE budget, owner access and inventory output
# transaction must remain in place. Do not call block hooks during tests.
for token in ("b1861Minecart(world,target)","b1861Contents(inventory)",
    "b1861StoreAll(contents,tx)","world.destroyBlock(target,false)",
    "world.setBlock(target,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3)",
    "machine.effectivePickaxe(world)","V178Claims.mayMachineMine(world,target,machine.owner)",
    "machine.output(world)","machine.energy.set(","if(!world.hasChunkAt(target))return",
    "if(inventory!=null)inventory.clearContent()"):
    assert token in s,("B1861_LOSSLESS_GATE",token)
assert "machine.owner.equals(V178Claims.owner(world,target))" not in s
p.write_text(s,"utf-8")
print("B1861_V20_WATER_LAVA_CHEST_CONTAINER_MINECART_LOOT_BUFFER_NO_DUPES_PASS")
