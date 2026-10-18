#!/usr/bin/env python3
"""Harden persistent named wireless networks, and add owner-only rename/delete.

Network IDs are immutable identities; deletion deliberately leaves old block
entities with their private buffers untouched until their owner rebinds them.
Production transfer already fails closed for deleted network IDs.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def replace(path,needle,updated):
 p=root/path
 src=p.read_text()
 assert src.count(needle)==1, f"anchor mismatch: {path}: {needle[:70]}"
 p.write_text(src.replace(needle,updated,1))

network="wireless/WirelessNetworkData.java"
replace(network,
 '  for(Entry e:entries)if(e.id()!=null&&e.name()!=null&&e.id().length()<=80&&e.name().length()<=40&&e.chargingMask()>=0)',
 '  for(Entry e:entries)if(e.id()!=null&&e.name()!=null&&e.owner()!=null&&e.id().length()<=80&&e.name().length()<=40&&e.owner().length()<=64&&e.chargingMask()>=0&&(e.chargingMask()&~ALL_CATEGORIES)==0)')
replace(network,
 '  if(!canAccess(p,id)||mask<0||(mask&~ALL_CATEGORIES)!=0)return false;',
 '  if(DEFAULT_ID.equals(id)||!canAccess(p,id)||mask<0||(mask&~ALL_CATEGORIES)!=0)return false;')
replace(network,
 '  if(old.chargingMask()==mask)return true;',
 '  if(old.chargingMask()==mask)return true;')
replace(network,
 """  setDirty();return true;
 }
}
""",
 """  setDirty();return true;
 }
 /** Rename a private network without changing its stable ID. Main is shared/read-only. */
 public boolean rename(ServerPlayer player,String id,String name){
  if(player==null||name==null||id==null||DEFAULT_ID.equals(id))return false;
  name=name.strip();
  if(name.isEmpty()||name.length()>32)return false;
  Entry old=networks.get(id);
  if(old==null||!old.owner().equals(player.getUUID().toString()))return false;
  for(Entry e:networks.values())if(!e.id().equals(id)&&e.owner().equals(old.owner())
    &&e.name().equalsIgnoreCase(name))return false;
  if(old.name().equals(name))return true;
  networks.put(id,new Entry(id,name,old.owner(),old.chargingMask()));
  setDirty();return true;
 }
 /** Deleting a network revokes transfer immediately; stored FE is still on its antennas. */
 public boolean delete(ServerPlayer player,String id){
  if(player==null||id==null||DEFAULT_ID.equals(id))return false;
  Entry old=networks.get(id);
  if(old==null||!old.owner().equals(player.getUUID().toString()))return false;
  networks.remove(id);setDirty();return true;
 }
}
""")
commands="wireless/WirelessNetworkCommands.java"
replace(commands,
 """     return available.size();
    }))
  );
""",
 """     return available.size();
    }))
    .then(Commands.literal("rename")
     .then(Commands.argument("id",StringArgumentType.word())
      .then(Commands.argument("name",StringArgumentType.greedyString())
       .executes(ctx->{
        var player=ctx.getSource().getPlayerOrException();
        var id=StringArgumentType.getString(ctx,"id");
        var name=StringArgumentType.getString(ctx,"name");
        boolean ok=WirelessNetworkData.get(player.level().getServer()).rename(player,id,name);
        player.sendSystemMessage(Component.literal(ok?"Wireless network renamed":"Cannot rename network: check ownership, name and ID"));
        return ok?1:0;
       }))))
    .then(Commands.literal("delete")
     .then(Commands.argument("id",StringArgumentType.word())
      .executes(ctx->{
       var player=ctx.getSource().getPlayerOrException();
       var id=StringArgumentType.getString(ctx,"id");
       boolean ok=WirelessNetworkData.get(player.level().getServer()).delete(player,id);
       player.sendSystemMessage(Component.literal(ok?
        "Wireless network deleted; reconnect any devices holding stored FE":
        "Cannot delete network: check ownership and ID"));
       return ok?1:0;
      })))
  );
""")
menu="menu/WirelessNetworkMenu.java"
replace(menu,
 '''   var created=storage.create(p,"Network "+(storage.entries().size()+1));
   if(created==null)return false;''',
 '''   WirelessNetworkData.Entry created=null;
   // Deleting an earlier name must not make the GUI create action unusable.
   for(int n=1;n<=128&&created==null;n++)created=storage.create(p,"Network "+n);
   if(created==null)return false;''')
print("WIRELESS_NAMED_NETWORK_MANAGEMENT_V1 PASS")
