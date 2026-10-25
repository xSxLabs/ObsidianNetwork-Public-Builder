#!/usr/bin/env python3
"""Build208: server-authoritative Portal A ID selector in a real Minecraft GUI.

No client-only payload required. Vanilla 9x3 menu transports entries to player;
clicks are interpreted server-side and never extract/duplicate display items.
Existing SavedData automatically migrates via an optional ID codec field.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,s):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 p.write_text(s,encoding="utf-8")

edit("portal/PortalIndex.java",
 'int x,int y,int z,boolean selected){',
 'int x,int y,int z,boolean selected,String id){')
edit("portal/PortalIndex.java",
 '''    Codec.BOOL.fieldOf("selected").forGetter(Anchor::selected)
  ).apply(i,Anchor::new));''',
 '''    Codec.BOOL.fieldOf("selected").forGetter(Anchor::selected),
    Codec.STRING.optionalFieldOf("id","").forGetter(Anchor::id)
  ).apply(i,Anchor::new));''')
edit("portal/PortalIndex.java",
 '''   public Anchor withSelected(boolean chosen){return new Anchor(owner,dimension,x,y,z,chosen);}''',
 '''   // Empty IDs belong to already-saved Build203 worlds; derive a stable alias.
   public String uid(){
    if(id!=null&&!id.isEmpty())return id;
    return UUID.nameUUIDFromBytes(key().getBytes(java.nio.charset.StandardCharsets.UTF_8)).toString();
   }
   public Anchor withSelected(boolean chosen){return new Anchor(owner,dimension,x,y,z,chosen,id);}''')
edit("portal/PortalIndex.java",
 'Anchor a=new Anchor(player.toString(),dim,pos.getX(),pos.getY(),pos.getZ(),true);',
 'Anchor a=new Anchor(player.toString(),dim,pos.getX(),pos.getY(),pos.getZ(),true,UUID.randomUUID().toString());')
edit("portal/PortalIndex.java",
 ''' public Anchor cycle(UUID owner){''',
 ''' /** V173_PORTAL_UID_SELECT: server validates ownership, stale IDs rejected. */
 public Anchor select(UUID owner,String uid){
  for(Anchor a:owned(owner))if(a.uid().equals(uid)){
   for(Anchor old:owned(owner))
    saved.put(old.key(),old.withSelected(old.key().equals(a.key())));
   setDirty();return a;
  }
  return null;
 }
 public Anchor cycle(UUID owner){''')

add("portal/PortalSelectMenu.java",r'''package dev.obsidiannetwork.portal;
import java.util.List;
import net.minecraft.network.chat.Component;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** V173_PORTAL_MENU: unique per-placed A IDs, selected via hotkey L + GUI. */
public final class PortalSelectMenu extends ChestMenu {
 private final ServerPlayer owner;
 private final List<PortalIndex.Anchor> anchors;
 private final SimpleContainer display;
 private int page=0;
 public PortalSelectMenu(int id,Inventory inventory,ServerPlayer player){
  this(id,inventory,player,new SimpleContainer(27));
 }
 private PortalSelectMenu(int id,Inventory inventory,ServerPlayer player,SimpleContainer slotsData){
  super(MenuType.GENERIC_9x3,id,inventory,slotsData,3);
  owner=player;display=slotsData;
  anchors=PortalIndex.get(player.level().getServer()).owned(player.getUUID());
  for(int n=0;n<27;n++){
   int at=n;
   slots.set(n,new Slot(display,at,8+(at%9)*18,18+(at/9)*18){
    @Override public boolean mayPlace(ItemStack stack){return false;}
    @Override public boolean mayPickup(Player player){return false;}
   });
  }
  redraw();
 }
 private void redraw(){
  for(int i=0;i<27;i++)display.setItem(i,ItemStack.EMPTY);
  int base=page*26;
  for(int i=0;i<26 && base+i<anchors.size();i++){
   var a=anchors.get(base+i);
   ItemStack stack=new ItemStack(a.selected()?Items.ENDER_EYE:Items.ENDER_PEARL);
   String label=(a.selected()?"[SELECTED] ":"")+"Portal A #"+a.uid().substring(0,8)+
      " / "+a.dimension()+" ["+a.x()+", "+a.y()+", "+a.z()+"]";
   stack.set(DataComponents.CUSTOM_NAME,Component.literal(label));
   display.setItem(i,stack);
  }
  if(anchors.size()>26){
   ItemStack next=new ItemStack(Items.ARROW);
   next.set(DataComponents.CUSTOM_NAME,Component.literal("Next page "+(page+1)+
      " / "+((anchors.size()+25)/26)));
   display.setItem(26,next);
  }
  broadcastChanges();
 }
 @Override public void clicked(int slotId,int button,ClickType clickType,Player p){
  if(p!=owner||!PortalActionPayload.hasUpgrade(owner)){owner.closeContainer();return;}
  if(slotId>=0&&slotId<27){
   if(slotId==26 && anchors.size()>26){
    page=(page+1)%((anchors.size()+25)/26);redraw();return;
   }
   int n=page*26+slotId;
   if(slotId<26 && n<anchors.size()){
    var found=PortalIndex.get(owner.level().getServer()).select(owner.getUUID(),anchors.get(n).uid());
    if(found!=null)owner.sendSystemMessage(Component.literal("Portal A #"+found.uid().substring(0,8)+
       " selected: "+found.dimension()+" ["+found.x()+", "+found.y()+", "+found.z()+"]"));
    owner.closeContainer();return;
   }
   return;
  }
  // No moving items into the fake destination slots.
  if(clickType==ClickType.QUICK_MOVE)return;
  super.clicked(slotId,button,clickType,p);
 }
 @Override public ItemStack quickMoveStack(Player player,int index){return ItemStack.EMPTY;}
 @Override public boolean stillValid(Player player){
  return player==owner&&PortalActionPayload.hasUpgrade(owner);
 }
}
''')

# The existing hotkey L previously auto-cycled. It now opens the owned A list.
edit("portal/PortalActionPayload.java",
 '''  var index=PortalIndex.get(player.level().getServer());
  var chosen=index.cycle(player.getUUID());
  if(chosen==null){tell(player,"No Portal A placed. Place a Network Portal A first.");return;}
  tell(player,"Portal A selected: "+chosen.dimension()+" ["+chosen.x()+", "+chosen.y()+", "+chosen.z()+"] ("+
     index.owned(player.getUUID()).size()+" saved)");''',
 '''  var index=PortalIndex.get(player.level().getServer());
  if(index.owned(player.getUUID()).isEmpty()){
   tell(player,"No Portal A placed. Place a Network Portal A first.");return;
  }
  player.openMenu(new net.minecraft.world.SimpleMenuProvider(
      (id,inv,p)->new PortalSelectMenu(id,inv,player),
      Component.literal("Select Portal A destination (click ID)")));''')
print("V173_PORTAL_UID_GUI_BUILD208_PASS")
