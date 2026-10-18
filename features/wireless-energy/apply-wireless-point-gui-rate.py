#!/usr/bin/env python3
"""User-requested Wireless #261: high-throughput FE and visible selectable roster.

Run only AFTER wireless-hardening, index hotpath, named network management,
menu cache, and roster-revision guard. Every source anchor must match exactly.
No new server/client packets; uses the existing inventory-button transport.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(relative,old,new):
    file=root/relative
    source=file.read_text(encoding="utf-8")
    assert source.count(old)==1,(relative,"missing/duplicate anchor",old[:100],source.count(old))
    file.write_text(source.replace(old,new,1),encoding="utf-8")

# One receiver offers up to 320,000 FE every FIVE game ticks = 64,000 FE/t
# sustained, subject to loaded sender buffers and accepting adjacent machines.
# Both receiver push and FE capability extraction use the same server-side cap.
# The charged-item budget stays separately limited to 16,000 FE per player/20t.
change("blockentity/WirelessNetworkBlockEntity.java",
       " private static final int MAX_TRANSFER=16000;",
       " // WIRELESS_HIGH_THROUGHPUT_V2: 320k FE/5t = 64k FE/t max per receiver.\n private static final int MAX_TRANSFER=320000;")

# The roster is copied once when the screen opens; the existing server
# roster-revision guard closes a stale menu when a rename/delete/create affects
# what this owner can see. The server always rechecks access and ID before
# accepting a direct selection. Never trust a client-sent network string.
change("menu/WirelessNetworkMenu.java",
       " public int selection(){return data.get(0);}",
       """ public int rosterSize(){return names.size();}
 public String rosterNameAt(int index){
  return index>=0&&index<names.size()?names.get(index):"";
 }
 public int selection(){return data.get(0);}""")
change("menu/WirelessNetworkMenu.java",
       "  if(button==0){",
       """  if(button>=32&&button<160){
   int choice=button-32;
   // The GUI's IDs must still correspond to the authoritative accessible
   // server roster. Edits in another open menu cannot silently remap a click.
   var current=storage.available(p);
   if(choice>=ids.size()||choice>=current.size())return false;
   if(!ids.get(choice).equals(current.get(choice).id())
      ||!names.get(choice).equals(current.get(choice).name()))return false;
   return device.selectNetworkFor(p,current.get(choice).id());
  }
  if(button==0){""")
# Keep left-hand controls untouched; add paginated entry buttons at right.
change("client/WirelessNetworkScreen.java",
       " private net.minecraft.client.gui.components.EditBox networkName;",
       """ private int rosterPage;
 private int lastRosterSelection=-1;
 private final Button[] rosterButtons=new Button[8];
 private net.minecraft.client.gui.components.EditBox networkName;""")
change("client/WirelessNetworkScreen.java",
       "  super(menu,inventory,title,224,240);titleLabelX=-10000;inventoryLabelX=-10000;",
       "  super(menu,inventory,title,380,258);titleLabelX=-10000;inventoryLabelX=-10000;")
change("client/WirelessNetworkScreen.java",
       """     .bounds(leftPos+12,topPos+125+i*19,117,18).build());
  }
 }""",
       """     .bounds(leftPos+12,topPos+125+i*19,117,18).build());
  }
  // WIRELESS_VISIBLE_ROSTER_V2: eight directly selectable network names.
  for(int row=0;row<8;row++){
   final int slot=row;
   Button entry=Button.builder(Component.literal(""),button->selectVisible(slot))
    .bounds(leftPos+229,topPos+50+row*20,140,18).build();
   rosterButtons[row]=entry;
   addRenderableWidget(entry);
  }
  addRenderableWidget(Button.builder(Component.literal("< Prev"),b->{
   if(rosterPage>0){rosterPage--;refreshRoster();}
  }).bounds(leftPos+229,topPos+218,67,18).build());
  addRenderableWidget(Button.builder(Component.literal("Next >"),b->{
   if((rosterPage+1)*8<menu.rosterSize()){rosterPage++;refreshRoster();}
  }).bounds(leftPos+302,topPos+218,67,18).build());
  refreshRoster();
 }""")
change("client/WirelessNetworkScreen.java",
       " private void click(int id){",
       """ private void selectVisible(int slot){
  int choice=rosterPage*8+slot;
  if(choice<0||choice>=menu.rosterSize())return;
  click(32+choice);
 }
 private void refreshRoster(){
  for(int row=0;row<rosterButtons.length;row++){
   Button entry=rosterButtons[row];
   if(entry==null)continue;
   int index=rosterPage*8+row;
   entry.visible=index<menu.rosterSize();
   if(entry.visible){
    String name=menu.rosterNameAt(index);
    if(name.length()>21)name=name.substring(0,20)+"…";
    entry.setMessage(Component.literal((index==menu.selection()?"> ":"  ")+name));
   }
  }
  lastRosterSelection=menu.selection();
 }
 private void click(int id){""")
change("client/WirelessNetworkScreen.java",
       """  g.outline(leftPos,topPos,imageWidth,imageHeight,-9681017);""",
       """  g.outline(leftPos,topPos,imageWidth,imageHeight,-9681017);
  g.fill(leftPos+225,topPos+42,leftPos+374,topPos+240,0xff242432);""")
change("client/WirelessNetworkScreen.java",
       """  g.text(font,"WIRELESS ENERGY NETWORK",leftPos+12,topPos+7,-1,false);""",
       """  if(lastRosterSelection!=menu.selection())refreshRoster();
  g.text(font,"WIRELESS ENERGY NETWORK",leftPos+12,topPos+7,-1,false);
  g.text(font,"AVAILABLE NETWORKS ("+menu.rosterSize()+")",leftPos+230,topPos+28,-1,false);""")
change("client/WirelessNetworkScreen.java",
       """  g.text(font,"Sender buffer: "+menu.energyInThousands()+"k FE",leftPos+12,topPos+229,-1,false);""",
       """  g.text(font,"Sender buffer: "+menu.energyInThousands()+"k FE",leftPos+12,topPos+229,-1,false);
  g.text(font,"Max transfer: 64,000 FE/t",leftPos+12,topPos+244,0xffbdc9f4,false);
  g.text(font,"Page "+(rosterPage+1)+"/"+Math.max(1,(menu.rosterSize()+7)/8),
    leftPos+272,topPos+243,0xffaabbcf,false);""")
print("WIRELESS_HIGH_THROUGHPUT_V2 PASS 320000 FE/5t; WIRELESS_VISIBLE_ROSTER_V2 PASS")
