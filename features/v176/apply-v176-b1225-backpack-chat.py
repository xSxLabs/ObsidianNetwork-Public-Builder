#!/usr/bin/env python3
"""B1225: bidirectional placed Backpack cable transfer, no GUI command-spam,
and persistent scoped xSxLabs chat mute. Apply AFTER all B1189/B1224 stages."""
from pathlib import Path
import os

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def fix(path,old,new):
 p=J/path
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B1225_SOURCE_DRIFT",path,old[:90],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# Real NeoForge ResourceHandler, not an external/parallel hidden inventory:
# one empty ingress index after the deterministic live stored-item list.
# Existing extraction indices 0..n-1 are preserved exactly.
be="backpack/NetworkBackpackBlockEntity.java"
fix(be,
 '    @Override public int size(){return list().size();}',
 '    @Override public int size(){return backpack.isEmpty()?0:list().size()+1;} // B1225_LIVE_EMPTY_INGRESS')

fix(be,
 '''    @Override public long getCapacityAsLong(int i,
      net.neoforged.neoforge.transfer.item.ItemResource resource){return 0L;}
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.item.ItemResource resource){
     return false; // extract-only, never fill hidden upgrade/cell/filter slots.
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.item.ItemResource item,
      int amount,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}''',
 '''    @Override public long getCapacityAsLong(int i,
      net.neoforged.neoforge.transfer.item.ItemResource resource){
     if(level==null||backpack.isEmpty())return 0L;
     var entries=list();
     if(i<0||i>entries.size())return 0L;
     long stored=i<entries.size()?entries.get(i).count():0L;
     if(resource.isEmpty())
      return Math.min(Integer.MAX_VALUE,Math.max(stored,V176BackpackCells.capacity(backpack)));
     if(!isValid(i,resource))return 0L;
     long free=Math.max(0L,V176BackpackCells.capacity(backpack)-V176BackpackCells.used(backpack));
     return Math.min((long)Integer.MAX_VALUE,stored+free);
    }
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.item.ItemResource resource){
     if(level==null||backpack.isEmpty()||resource.isEmpty()
        ||resource.getItem() instanceof NetworkBackpackItem)return false;
     var entries=list();
     if(i<0||i>entries.size()||V176BackpackCells.capacity(backpack)<=0L)return false;
     // Occupied indices may accept only the exact existing item and components.
     // The final empty virtual index admits new types into installed real cells.
     if(i==entries.size())return true;
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
     return resource.equals(net.neoforged.neoforge.transfer.item.ItemResource.of(
       codec.recreate(entries.get(i).descriptor(),1)));
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.item.ItemResource item,
      int amount,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     if(amount<=0||level==null||level.isClientSide()||!isValid(i,item))return 0;
     // Prepare a DETACHED candidate first: failing insertion never snapshots or
     // changes the placed bag. Rollback restores exactly the prior item/components.
     int requested=Math.min(amount,item.getMaxStackSize());
     if(requested<=0)return 0;
     ItemStack updated=backpack.copy();
     var result=V176BackpackCells.insert(level,updated,item.toStack(),requested);
     int accepted=(int)result.accepted();
     if(accepted<=0)return 0; // full / disallowed / no installed storage
     cableJournal.updateSnapshots(tx);
     backpack=updated;
     return accepted; // B1225_REAL_CELLS_TRANSACTIONAL_INGRESS
    }''')

# Keep the original extract method intact; it retains complete rollback
# and must continue working from Backpack -> chest.

menu="backpack/V176BackpackMenu.java"
fix(menu,' private final Storage storage;',
''' private final Storage storage;
 private int selectedCableFilter=-1;
 // B1225: inventory-button packets avoid vanilla chat-command spam handling.
 @Override public boolean clickMenuButton(Player player,int action){
  if(!(player instanceof ServerPlayer server)||server.containerMenu!=this
       ||!storage.source.valid())return false;
  if(action==0)return page(server,-1);
  if(action==1)return page(server,1);
  if(action==2)return sort(server);
  if(action==3){selectedCableFilter=-1;return toggleFilterEditor(server);}
  if(action==4){
   ItemStack bag=storage.source.current();
   return storage.magnet(!V176BackpackCells.magnetEnabled(bag),
                          V176BackpackCells.magnetWhitelist(bag));
  }
  if(action==5){
   ItemStack bag=storage.source.current();
   return storage.magnet(V176BackpackCells.magnetEnabled(bag),
                         !V176BackpackCells.magnetWhitelist(bag));
  }
  if(action>=10&&action<64){
   if(!storage.filterEditor||action-10>=V176BackpackCells.FILTER_SLOTS)return false;
   selectedCableFilter=action-10;return true;
  }
  if(action==64)return selectedCableFilter>=0
     &&editFilter(server,selectedCableFilter,-1);
  if(action>=65&&action<101)return selectedCableFilter>=0
     &&editFilter(server,selectedCableFilter,action-65);
  if(action>=101&&action<146)return withdraw(server,action-101,64);
  if(action>=146&&action<191)return withdraw(server,action-146,1);
  return false;
 }
''')

screen="client/V176BackpackScreen.java"
fix(screen,' private static final int SIDE_X=183;',
''' private String pendingSearch="";
 private int searchDelay=-1;
 private int wheelCooldown=0;
 private static final int SIDE_X=183;''')
fix(screen,
 '''  searchBox.setResponder(value->command(
      value.isBlank()?"networkbackpack search clear":"networkbackpack search "+value));''',
 '''  // No per-keystroke commands! One debounced update after typing stops.
  searchBox.setResponder(value->{pendingSearch=value;searchDelay=25;});''')
fix(screen,
 ''' private static void command(String command){''',
 ''' @Override protected void containerTick(){
  super.containerTick();
  if(wheelCooldown>0)wheelCooldown--;
  if(searchDelay>0&&--searchDelay==0&&!filterEditor){
   // Server-side validation remains in V176BackpackMenu.search().
   String query=pendingSearch.replace("\\r","").replace("\\n","").trim();
   command(query.isBlank()?"networkbackpack search clear":"networkbackpack search "+query);
  }
 }
 private void button(int action){
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.gameMode!=null&&mc.player!=null&&mc.player.containerMenu==menu)
   mc.gameMode.handleInventoryButtonClick(menu.containerId,action);
 }
 @Override public boolean mouseScrolled(double mx,double my,double dx,double dy){
  // Exactly one inventory action per 5 client ticks, never a chat command.
  if(dy!=0&&wheelCooldown==0
     &&mx>=getLeftPos()+7&&mx<getLeftPos()+170
     &&my>=getTopPos()+36&&my<getTopPos()+129){
   button(dy<0?1:0);
   wheelCooldown=5;
   if(filterEditor)filterPage=Math.max(0,Math.min(1,filterPage+(dy<0?1:-1)));
   return true;
  }
  return super.mouseScrolled(mx,my,dx,dy);
 }
 private static void command(String command){''')

fix(screen,'command("networkbackpack previous");','button(0);')
fix(screen,'command("networkbackpack next");','button(1);')
fix(screen,'command("networkbackpack sort");','button(2);')
fix(screen,'command("networkbackpack filters");','button(3);')
fix(screen,'command("networkbackpack clearfilter "+selectedFilter);','button(64);')
fix(screen,'command("networkbackpack setfilter "+selectedFilter+" "+slot);','button(65+slot);')
fix(screen,'command("networkbackpack take "+entry+" "+(button==1?1:64));',
    'button((button==1?146:101)+entry);')
fix(screen,'''     if(button==1)button(64);
     return true;''',
'''     button(10+selectedFilter);
     if(button==1)button(64);
     return true;''')
fix(screen,
 '''       command(tag.getBooleanOr("xsx_v176_magnet_on",false)
         ?"networkbackpack magnet off":"networkbackpack magnet on");''',
 '''       button(4); // B1225_NO_CHAT_COMMAND_FOR_MAGNET''')
fix(screen,
 '''       command(tag.getBooleanOr("xsx_v176_magnet_whitelist",false)
         ?"networkbackpack magnet blacklist":"networkbackpack magnet whitelist");''',
 '''       button(5); // B1225_NO_CHAT_COMMAND_FOR_FILTER_MODE''')

# The stored-chat mute works per world/player already. Its stack-only
# heuristic misses mod feedback that is marshalled through vanilla dispatch.
# Recognize the mod's explicit message labels as well (never user chat).
chat="powerarmor/V176ChatControl.java"
fix(chat,
 '''  // Check the emitting Java call stack, not message wording or packet text.
  // The calling chain must include OUR mod (not this filter itself).
  return WALKER.walk(stream->stream.limit(60).anyMatch(f->{''',
 '''  // Direct xSxLabs-labelled system/actionbar feedback may be emitted on a
  // later vanilla dispatch frame with no originating mod code on the stack.
  // Keep vanilla player chat and other mods' unlabelled packets untouched.
  String message=packet instanceof ClientboundSystemChatPacket chat
      ?chat.content().getString()
      :((ClientboundSetActionBarTextPacket)packet).text().getString();
  if(message.startsWith("[xSxLabs]")||message.startsWith("[XSXLABS]")
      ||message.startsWith("[ObsidianNetwork]")
      ||message.startsWith("[Network Storage]"))return true;
  // Also catch unlabelled messages emitted directly by our own mod code.
  return WALKER.walk(stream->stream.limit(60).anyMatch(f->{''')

fix(chat,
 '''      .then(Commands.literal("status").executes(c->status(c.getSource().getPlayerOrException())))));
 }''',
 '''      .then(Commands.literal("status").executes(c->status(c.getSource().getPlayerOrException())))));
  // Also expose a conflict-free short alias on servers with an /xsxlabs root.
  e.getDispatcher().register(Commands.literal("modchat")
    .then(Commands.literal("off").executes(c->set(c.getSource().getPlayerOrException(),false)))
    .then(Commands.literal("on").executes(c->set(c.getSource().getPlayerOrException(),true)))
    .then(Commands.literal("status").executes(c->status(c.getSource().getPlayerOrException()))));
 }''')
print("B1225_BIDIRECTIONAL_BACKPACK_CABLE_TRANSACTION_NO_SPAM_GUI_AND_MODCHAT_PASS")
