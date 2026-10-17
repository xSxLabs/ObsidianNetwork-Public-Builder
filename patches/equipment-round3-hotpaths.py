#!/usr/bin/env python3
"""Remove equipment registry scans and redundant post-commit work.

Run after equipment-dirty-serialization.py. Serialized formats, stack components,
transaction validation, descriptor validation and mutation listeners stay intact.
"""
import os
from pathlib import Path

root = Path(os.environ['V1_SOURCE_ROOT']) / 'dev/obsidiannetwork'

def replace_once(text, old, new):
    assert text.count(old) == 1, f'Equipment round3 source anchor changed: {old[:120]}'
    return text.replace(old, new, 1)

p = root / 'core/EquipmentEligibility.java'
s = p.read_text()
old = 'Item i=null;for(Item candidate:BuiltInRegistries.ITEM){if(BuiltInRegistries.ITEM.getKey(candidate).toString().equals(key.itemId())){i=candidate;break;}}'
new = '''// XSXLABS_EQUIPMENT_DIRECT_REGISTRY_LOOKUP_V1
net.minecraft.resources.Identifier id=net.minecraft.resources.Identifier.tryParse(key.itemId());
if(id==null)return false;
Item i=BuiltInRegistries.ITEM.getValue(id);
// Defaulted registries may return AIR for an unknown key. Preserve the original
// exact identifier comparison, including rejection of unqualified identifiers.
if(i==null||!BuiltInRegistries.ITEM.getKey(i).toString().equals(key.itemId()))return false;
'''
s = replace_once(s, old, new)
p.write_text(s)

p = root / 'blockentity/StorageDriveBlockEntity.java'
s = p.read_text()
assert 'private final boolean[] equipmentSerializationDirty' in s, 'Apply dirty serialization first'
# Transaction finalization calls onContentsChanged -> reconcileRuntimeSlot.
# Keep a fallback for callbacks that failed and leave normal cell behavior intact.
s = replace_once(s,
    '         this.reconcileRuntimeSlot(slot);\n         this.setChanged();\n         return !this.cellStack(slot).isEmpty();',
    '''         // XSXLABS_EQUIPMENT_COMMIT_RECONCILE_ONCE_V1
         if (!(one.getItem() instanceof EquipmentCellItem) || this.equipmentCells[slot] == null)
            this.reconcileRuntimeSlot(slot);
         this.setChanged();
         return !this.cellStack(slot).isEmpty();''')
# The source stack is already the committed encoded state of this newly decoded
# store. Neither attach nor replace mutates it. Future writes invalidate through
# the existing mutation listener; marking clean here avoids immediate re-encode.
s = replace_once(s,
    '            else this.drive.replaceDetached(slot,null);\n         } catch(RuntimeException ex)',
    '''            else this.drive.replaceDetached(slot,null);
            this.equipmentSerializationDirty[slot]=false; // XSXLABS_EQUIPMENT_DECODED_SNAPSHOT_CLEAN_V1
         } catch(RuntimeException ex)''')
# A loaded inventory likewise already owns the exact encoded snapshot.
s = replace_once(s,
    'this.equipmentSerializationDirty[dirtySlot]=true; this.setChanged(); }); } catch (RuntimeException ignored)',
    'this.equipmentSerializationDirty[dirtySlot]=true; this.setChanged(); }); this.equipmentSerializationDirty[slot]=false; } catch (RuntimeException ignored)')
p.write_text(s)

# Hashing an immutable component does not need to rescan its potentially large
# payload on every ItemResource/menu comparison. Equality still compares bytes.
p = root / 'component/EquipmentCellContents.java'
s = p.read_text()
s = replace_once(s, 'private final byte[]payload;private final long used;',
    'private final byte[]payload;private final long used;private final int payloadHash;')
s = replace_once(s, 'this.payload=Arrays.copyOf(p,p.length);this.used=s.used();',
    'this.payload=Arrays.copyOf(p,p.length);this.used=s.used();this.payloadHash=Arrays.hashCode(this.payload);')
s = replace_once(s, 'public int hashCode(){return Arrays.hashCode(payload);}',
    'public int hashCode(){return this.payloadHash;} // XSXLABS_EQUIPMENT_IMMUTABLE_HASH_V1')
p.write_text(s)
print('EQUIPMENT_ROUND3_HOTPATHS_V1 PASS registry=direct reconcile=once snapshot=clean hash=immutable')
