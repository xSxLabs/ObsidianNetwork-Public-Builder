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
 private static void command(String command){''')

# B891 removed the old arrow buttons and introduced its own mouseScrolled.
# Replace only the live scroll action, NOT the deleted arrow callbacks.
# The final B902/B957 (and other intervening render tweaks) can rewrite the
# wheel loop. Replace the entire existing mouseScrolled override by METHOD
# BOUNDARIES instead of matching a fragile historical for-loop fragment.
# Retain the user-visible 9-item row/page offset and vanilla tooltip code.
screen_path=J/screen
source=screen_path.read_text(encoding="utf-8")
a=source.find(" @Override public boolean mouseScrolled(")
b=source.find(" @Override protected void extractTooltip(",a)
assert a>=0 and b>a and source.count(" @Override public boolean mouseScrolled(")==1, "B1228_WHEEL_METHOD_DRIFT"
wheel=''' @Override public boolean mouseScrolled(double mx,double my,double scrollX,double scrollY){
  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  if(x>=8&&x<170&&y>=38&&y<128&&scrollY!=0.0D){
   if(wheelCooldown>0)return true;
   button(scrollY>0?0:1);
   wheelCooldown=5;
   if(filterEditor)filterPage=Math.max(0,Math.min(1,filterPage+(scrollY<0?1:-1)));
   else scrollRow=Math.max(0,scrollRow+(scrollY<0?1:-1));
   return true;
  }
  return super.mouseScrolled(mx,my,scrollX,scrollY);
 }
'''
source=source[:a]+wheel+source[b:]
# Preserve B910's later module click routing! Only replace the five-command
# for-loop inside the original scrollbar click, not the surrounding method.
# Find the actual command inside B902's final scrollbar handler, regardless
# of preceding B910/B957 screen transforms and whitespace/hitbox rewrites.
# Only one invocation must exist, otherwise fail closed.
token='command(delta>0?"networkbackpack next":"networkbackpack previous");'
assert source.count(token)==1,("B1230_SCROLLBAR_COMMAND_DRIFT",source.count(token))
call=source.index(token)
loop=source.rfind("for(int i=0;i<5;i++)",max(0,call-480),call)
assert loop>=0,("B1230_SCROLLBAR_LOOP_MISSING",source[call-220:call+120])
brace=source.find("{",loop,call)
assert brace>=0,("B1230_SCROLLBAR_BRACE_MISSING",loop,call)
depth=1
end=brace+1
while end<len(source) and depth:
 if source[end]=="{":depth+=1
 elif source[end]=="}":depth-=1
 end+=1
assert depth==0 and call<end and end-loop<500,"B1230_SCROLLBAR_LOOP_UNSAFE"
replacement='''if(wheelCooldown>0)return true;
    button(delta>0?1:0);
    wheelCooldown=5;
    if(filterEditor)filterPage=Math.max(0,Math.min(1,filterPage+delta));
    else scrollRow=Math.max(0,scrollRow+delta);'''
source=source[:loop]+replacement+source[end:]
assert 'command(scrollY>0?"networkbackpack previous":"networkbackpack next")' not in source
assert 'command(delta>0?"networkbackpack next":"networkbackpack previous")' not in source
screen_path.write_text(source,encoding="utf-8")

fix(screen,'command("networkbackpack sort");','button(2);')
fix(screen,'command("networkbackpack filters");','button(3);')
fix(screen,'command("networkbackpack clearfilter "+selectedFilter);','button(64);')
fix(screen,'command("networkbackpack setfilter "+selectedFilter+" "+slot);','button(65+slot);')
# B857 already routes real list clicks through container input (not commands),
# including empty slots. Keep that lossless player cursor/deposit behavior.
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
