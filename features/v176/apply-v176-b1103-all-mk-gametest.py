#!/usr/bin/env python3
"""B1103: extend original real server GameTest (not user runtime) MK1 through MK24."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
assert s.count("                for(int tier=0;tier<2;tier++){")==1
s=s.replace("                for(int tier=0;tier<2;tier++){","                for(int tier=0;tier<24;tier++){",1)
assert s.count("Real MK1/MK2 Power Armor conservation roundtrip")==1
s=s.replace("Real MK1/MK2 Power Armor conservation roundtrip",
            "Real MK1-MK24 Power Armor conservation roundtrip",1)
start="                  var parts=tier==0?new net.minecraft.world.item.Item[]{"
end='                  check(owned(level,base,player).isEmpty(),"old world stand remains before tier "+tier);'
assert s.count(start)==1 and s.count(end)==1
a,b=s.index(start),s.index(end,s.index(start))
assert "ObsidianNetwork.POWER_ARMOR_MK2_BOOTS.get()" in s[a:b]
parts=("HELMET","CHESTPLATE","LEGGINGS","BOOTS")
cases=[]
for mk in range(1,25):
 names=["                      ObsidianNetwork.POWER_ARMOR_"+(f"MK{mk}_" if mk>1 else "")+part+".get()" for part in parts]
 cases.append("                    case "+str(mk)+" -> new net.minecraft.world.item.Item[]{\n"+",\n".join(names)+"\n                    };")
replacement="""                  // B1103 96 real registered MK1..MK24 items; never dummy tiers.
                  net.minecraft.world.item.Item[] parts=switch(tier+1){
"""+"\n".join(cases)+"""
                    default -> throw new IllegalStateException("Invalid MK "+(tier+1));
                  };
                  for(int slot=0;slot<4;slot++)
                    check(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.tier(
                         new net.minecraft.world.item.ItemStack(parts[slot]),slot)==tier+1,
                         "Wrong item tier for MK"+(tier+1)+" slot "+slot);
"""
s=s[:a]+replacement+s[b:]
assert 'B1102_REAL_TRANSFER_NOT_STARTED' in s
assert 'B1102_REAL_SUIT_MUST_REMAIN_VISIBLE' in s
assert 'check(stand.isRemoved(),"entered world suit still exists, tier "+tier);' in s
assert 'protection5_roundtrip=true' in s
assert s.count('POWER_ARMOR_REAL_ROUNDTRIP_V69')==2
for mk in range(1,25):
 for part in parts:
  assert "ObsidianNetwork.POWER_ARMOR_"+(f"MK{mk}_" if mk>1 else "")+part+".get()" in s
p.write_text(s,encoding="utf-8")
print("B1103_REAL_MK1_TO_MK24_FULL_ENTRY_EXIT_ITEM_CONSERVATION_PATCH_PASS")
