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
# IDs are transmitted only for the caller's accessible networks. Visible names
# may change; identity always remains the stable UUID.
menu_path="menu/WirelessNetworkMenu.java"
replace(menu_path,
 ' private final List<String> names=new ArrayList<>();',
 ' private final List<String> names=new ArrayList<>();\n private final List<String> ids=new ArrayList<>();')
replace(menu_path,
 '  for(int k=0;k<count;k++)names.add(buf.readUtf(40));',
 '  for(int k=0;k<count;k++){ids.add(buf.readUtf(80));names.add(buf.readUtf(40));}')
replace(menu_path,
 '   for(var e:WirelessNetworkData.get(p2.level().getServer()).available(p2))names.add(e.name());',
 '   for(var e:WirelessNetworkData.get(p2.level().getServer()).available(p2)){ids.add(e.id());names.add(e.name());}')
replace(menu_path,
 ' public String displayName(){',
 ''' public String selectedId(){
  int i=selection();
  return i>=0&&i<ids.size()?ids.get(i):"";
 }
 public String displayName(){''')

block="block/WirelessNetworkBlock.java"
replace(block,
 '     for(var network:available)b.writeUtf(network.name(),40);',
 '     for(var network:available){b.writeUtf(network.id(),80);b.writeUtf(network.name(),40);}')

screen="client/WirelessNetworkScreen.java"
replace(screen,
 ' private static final String[] CATEGORIES={"Inventory","Curios","Armor","Offhand","Hotbar"};',
 ''' private static final String[] CATEGORIES={"Inventory","Curios","Armor","Offhand","Hotbar"};
 private net.minecraft.client.gui.components.EditBox networkName;''')
replace(screen,
 '  super(menu,inventory,title,224,175);titleLabelX=-10000;inventoryLabelX=-10000;',
 '  super(menu,inventory,title,224,240);titleLabelX=-10000;inventoryLabelX=-10000;')
replace(screen,
 '''  addRenderableWidget(Button.builder(Component.literal("Create network"),button->click(1)).bounds(leftPos+128,topPos+39,85,20).build());
  for(int i=0;i<5;i++){''',
 '''  addRenderableWidget(Button.builder(Component.literal("Auto create"),button->click(1)).bounds(leftPos+128,topPos+39,85,20).build());
  networkName=new net.minecraft.client.gui.components.EditBox(font,leftPos+12,topPos+65,201,18,Component.literal("Wireless network name"));
  networkName.setMaxLength(32);
  addRenderableWidget(networkName);
  addRenderableWidget(Button.builder(Component.literal("Create named"),button->sendNamed("create")).bounds(leftPos+12,topPos+91,100,20).build());
  addRenderableWidget(Button.builder(Component.literal("Rename"),button->sendNamed("rename")).bounds(leftPos+116,topPos+91,47,20).build());
  addRenderableWidget(Button.builder(Component.literal("Delete"),button->sendNamed("delete")).bounds(leftPos+166,topPos+91,47,20).build());
  for(int i=0;i<5;i++){''')
replace(screen,
 '     .bounds(leftPos+12,topPos+70+i*19,117,18).build());',
 '     .bounds(leftPos+12,topPos+125+i*19,117,18).build());')
replace(screen,
 ''' private void click(int id){''',
 ''' /** Built-in client command transport; Brigadier/server permissions are authoritative. */
 private void sendNamed(String operation){
  if(minecraft==null||minecraft.getConnection()==null)return;
  String id=menu.selectedId(),name=networkName==null?"":networkName.getValue().strip();
  String command;
  if("create".equals(operation)){
   if(name.isEmpty()||name.length()>32)return;
   command="wirelessnet create "+name;
  }else{
   if(id.isEmpty()||dev.obsidiannetwork.wireless.WirelessNetworkData.DEFAULT_ID.equals(id))return;
   if("rename".equals(operation)){
    if(name.isEmpty()||name.length()>32)return;
    command="wirelessnet rename "+id+" "+name;
   }else if("delete".equals(operation)){
    command="wirelessnet delete "+id;
   }else return;
  }
  minecraft.getConnection().sendCommand(command);
  onClose();
 }
 private void click(int id){''')
replace(screen,
 'topPos+75+i*19',
 'topPos+130+i*19')
replace(screen,
 'topPos+163',
 'topPos+229')
# A network deletion invalidates its identity (although antenna FE remains
# buffered). Require two clicks on the exact same selected ID.
replace(screen,
 ' private net.minecraft.client.gui.components.EditBox networkName;',
 ' private net.minecraft.client.gui.components.EditBox networkName;\n private String deletionConfirmation="";')
replace(screen,
 '''   }else if("delete".equals(operation)){
    command="wirelessnet delete "+id;''',
 '''   }else if("delete".equals(operation)){
    if(!id.equals(deletionConfirmation)){deletionConfirmation=id;return;}
    command="wirelessnet delete "+id;''')
replace(screen,
 ''' private void click(int id){
  if(minecraft''',
 ''' private void click(int id){
  deletionConfirmation="";
  if(minecraft''')
replace(screen,
 '  g.text(font,"Sender buffer: "+menu.energyInThousands()+"k FE",leftPos+12,topPos+229,-1,false);',
 '''  if(!deletionConfirmation.isEmpty())
   g.text(font,"Click Delete again to confirm",leftPos+12,topPos+214,0xffff7a78,false);
  g.text(font,"Sender buffer: "+menu.energyInThousands()+"k FE",leftPos+12,topPos+229,-1,false);''')
print("WIRELESS_NAMED_NETWORK_MANAGEMENT_V3 PASS: commands + owner-only GUI with deletion confirmation")

