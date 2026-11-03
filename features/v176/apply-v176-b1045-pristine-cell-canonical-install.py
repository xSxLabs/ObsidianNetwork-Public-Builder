#!/usr/bin/env python3
"""B1045: Fresh Storage/Equipment Cells are canonicalized after Drive install.

B1044's new pristine-cell GameTest demonstrated exact ItemStack.matches() is
not a valid post-install readback contract: the real Drive network attaches
CELL_CONTENTS payload to a freshly crafted Cell when first installed.
The input had no such component, but the actual installed cell is valid.

Normalize ONLY CELL_CONTENTS with StorageCellItem/EquipmentCellItem native
readStore and writeStore on COPIES, so every other data component (custom
name, etc.) must still be EXACTLY preserved and meaningful storage data
must match. Source buffer shrinks ONLY after a real Drive backing slot
reads back the same canonicalized Cell. Never remove or fake Drive inventory.
"""
from pathlib import Path
import os
P=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/cellterminal/V176CellTerminalBlockEntity.java"
s=P.read_text(encoding="utf-8")
old="""     ItemStack one=source.copyWithCount(1);
     try{
      backing.setItem(free,one);
      if(!ItemStack.matches(backing.getItem(free),one)){
       // No source was decremented; only undo our exact rejected write.
       if(ItemStack.matches(backing.getItem(free),one))
        backing.setItem(free,ItemStack.EMPTY);
       continue;
      }
     }catch(RuntimeException failure){"""
new="""     ItemStack one=source.copyWithCount(1);
     try{
      backing.setItem(free,one);
      ItemStack installed=backing.getItem(free);
      if(!xsxCanonicalSameCell(one,installed)){
       // Invalid/no installation: keep the real buffered Cell. Never
       // consume a source merely because a Drive write was attempted.
       System.err.println("XSXLABS_B1045_CELL_READBACK_REJECTED drive="+
           drive.getBlockPos()+" slot="+free+
           " expected="+one.getItem()+" actual="+installed.getItem());
       continue;
      }
     }catch(RuntimeException failure){"""
assert s.count(old)==1,("B1045_INSTALL_READBACK_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
needle=""" public int xsxAutoTransfer(ServerLevel server){"""
assert s.count(needle)==1
helper=r''' /** The Drive may add the authoritative empty CELL_CONTENTS to a newly
  * crafted Cell on initial attach. That is equivalent, not data loss. Other
  * components MUST be identical; stored items/types must serialize exactly.
  * Never mutate the original terminal source or installed Drive item here.
  */
 public static boolean xsxCanonicalSameCell(ItemStack before,ItemStack installed){
  if(ItemStack.matches(before,installed))return true;
  if(before.isEmpty()||installed.isEmpty()||
      before.getItem()!=installed.getItem()||
      before.getCount()!=installed.getCount())return false;
  try{
   ItemStack expected=before.copy();
   ItemStack actual=installed.copy();
   if(before.getItem() instanceof StorageCellItem cell){
    cell.writeStore(expected,cell.readStore(before));
    cell.writeStore(actual,cell.readStore(installed));
   }else if(before.getItem() instanceof EquipmentCellItem cell){
    cell.writeStore(expected,cell.readStore(before));
    cell.writeStore(actual,cell.readStore(installed));
   }else return false;
   return ItemStack.matches(expected,actual);
  }catch(RuntimeException corrupted){
   return false;
  }
 }
'''
s=s.replace(needle,helper+needle,1)
for required in ("if(!xsxCanonicalSameCell(one,installed))","source.shrink(1)","DriveMenu.xsxCellTerminalBacking"):
 assert required in s,("B1045_GUARD_MISSING",required)
P.write_text(s,encoding="utf-8")
print("B1045_PRISTINE_STORAGE_AND_EQUIPMENT_CELL_CANONICAL_INSTALL_SAFE_REAL_DRIVE_READBACK_PASS")
