#!/usr/bin/env python3
"""Build174: positioned saved Blueprints, block states and real Printer controls."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(path,old,new):
 p=J/path;s=p.read_text(encoding="utf8")
 assert s.count(old)==1,(path,old[:100],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf8")

# Blueprint item no longer a dead storage token: place, rotate, mirror it.
path=J/"item/NetworkBlueprintItem.java"
s=path.read_text()
assert s.rstrip().endswith("}") and "V173_BLUEPRINT_POSITIONED" not in s
s=s.rstrip()[:-1]+r'''
 /** V173_BLUEPRINT_POSITIONED: right click = target, crouch+right = rotate.
  * Rotation positions 4-7 are mirrored. This metadata survives world reloads.
  */
 @Override public InteractionResult useOn(UseOnContext ctx){
  if(!(ctx.getLevel() instanceof ServerLevel server))return InteractionResult.SUCCESS;
  var player=ctx.getPlayer();if(player==null)return InteractionResult.PASS;
  var plan=ctx.getItemInHand();if(blocks(plan).isEmpty())return InteractionResult.PASS;
  if(player.isShiftKeyDown()){
   int rotation=0;
   try{rotation=Integer.parseInt(read(plan,"xsxlabs_rotation"));}catch(NumberFormatException ignored){}
   rotation=(rotation+1)%8;
   write(plan,"xsxlabs_rotation",Integer.toString(rotation));
   player.sendSystemMessage(Component.literal("Blueprint: "+((rotation%4)*90)+" degrees"+
     (rotation>=4?" MIRRORED":"")+". Right-click to set position."));
   return InteractionResult.SUCCESS;
  }
  BlockPos at=ctx.getClickedPos().relative(ctx.getClickedFace());
  write(plan,"xsxlabs_anchor",server.dimension().identifier()+"|"+
      at.getX()+"|"+at.getY()+"|"+at.getZ());
  player.sendSystemMessage(Component.literal("Blueprint target "+at.toShortString()+
    " stored. Insert into Network Printer; press START in GUI."));
  return InteractionResult.SUCCESS;
 }
 @SuppressWarnings({"unchecked","rawtypes"})
 private static String stateValue(net.minecraft.world.level.block.state.properties.Property property,
                                  Comparable value){return property.getName(value);}
 public static String describeState(net.minecraft.world.level.block.state.BlockState state){
  var result=new java.util.StringJoiner("&");
  for(var property:state.getProperties())
   result.add(property.getName()+"="+stateValue(property,state.getValue(property)));
  return result.toString();
 }
}
'''
path.write_text(s)
q=J/"item/NetworkSchematicQuillItem.java"
s=q.read_text()
for old,new in [
 ('ArrayList<String> out=new ArrayList<>(sx*sy*sz);','ArrayList<String> out=new ArrayList<>(sx*sy*sz);ArrayList<String> states=new ArrayList<>(sx*sy*sz);'),
 ('out.add("minecraft:air");continue;','out.add("minecraft:air");states.add("");continue;'),
 ('out.add(BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString());','out.add(BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString());states.add(NetworkBlueprintItem.describeState(state));'),
 ('write(finished,"xsxlabs_size",sx+","+sy+","+sz);','write(finished,"xsxlabs_size",sx+","+sy+","+sz);write(finished,"xsxlabs_states",String.join(";",states));')
]:
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
q.write_text(s)
edit("block/NetworkDeviceBlock.java",
 'Component.literal("xSxLabs Network Printer | "+be.status())',
 'Component.literal("xSxLabs Network Printer @"+pos.getX()+","+pos.getY()+","+pos.getZ())')
edit("menu/NetworkPrinterMenu.java",
 ' @Override public boolean stillValid(Player p){return printer.stillValid(p);}',
 ''' @Override public boolean clickMenuButton(Player player,int action){
  if(!(player instanceof net.minecraft.server.level.ServerPlayer)||!stillValid(player))return false;
  return printer.control(action);
 }
 @Override public boolean stillValid(Player p){return printer.stillValid(p);}''')
# Server and client must agree on the 9x3 vanilla ChestMenu hit boxes.
edit("menu/NetworkPrinterMenu.java",
 'new Slot(be,0,26,35){','new Slot(be,0,8,18){')
edit("menu/NetworkPrinterMenu.java",
 'new Slot(be,1,62,35){','new Slot(be,1,26,18){')
edit("menu/NetworkPrinterMenu.java",
 'new Slot(be,index,index==2?98:-100,index==2?35:-100){',
 'new Slot(be,index,index==2?44:-100,index==2?18:-100){')
e=J/"blockentity/NetworkDeviceBlockEntity.java"
s=e.read_text()
def rep(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new,1)
# Preserve Java package resolution even though printer(...) has a local
# NetworkRuntime variable named "net". Imports avoid interpreting
# net.minecraft as a dereference of that local variable.
rep('import net.minecraft.world.level.block.state.BlockState;',
    'import net.minecraft.world.level.block.Mirror;\nimport net.minecraft.world.level.block.Rotation;\nimport net.minecraft.world.level.block.state.BlockState;')
rep(' public String status(){return status;}',
''' public String status(){return status;}
 public int progress(){return completed;}
 public int planLength(){return NetworkBlueprintItem.blocks(blueprint).size();}
 public boolean running(){return running;}
 /** Server-authoritative GUI buttons: 0 start, 1 pause, 2 reset. */
 public boolean control(int button){
  if(mode()!=NetworkDeviceBlock.Mode.PRINTER||button<0||button>2)return false;
  if(button==0){
   if(planLength()==0){setStatus("INSERT SAVED BLUEPRINT");sync();return false;}
   if(NetworkBlueprintItem.read(blueprint,"xsxlabs_anchor").isBlank()){
    setStatus("POSITION BLUEPRINT FIRST");sync();return false;
   }
   running=true;setStatus("READY");
  }else if(button==1){running=false;setStatus("PAUSED BY PLAYER");}
  else{running=false;index=completed=0;missing=ItemStack.EMPTY;setStatus("STOPPED / RESET");}
  sync();return true;
 }''')
rep('  if(dims.length!=3||plan.size()!=dims[0]*dims[1]*dims[2]){',
'''  String target=NetworkBlueprintItem.read(blueprint,"xsxlabs_anchor");
  String prefix=world.dimension().identifier()+"|";
  if(target.isBlank()){setStatus("POSITION BLUEPRINT FIRST");return;}
  if(!target.startsWith(prefix)){setStatus("BLUEPRINT IN OTHER DIMENSION");return;}
  String[] coordinates=target.substring(prefix.length()).split("[|]");
  if(coordinates.length!=3){setStatus("INVALID TARGET");return;}
  int tx,ty,tz,turn=0;
  try{
   tx=Integer.parseInt(coordinates[0]);ty=Integer.parseInt(coordinates[1]);
   tz=Integer.parseInt(coordinates[2]);
   String angle=NetworkBlueprintItem.read(blueprint,"xsxlabs_rotation");
   if(!angle.isBlank())turn=Integer.parseInt(angle);
  }catch(NumberFormatException ex){setStatus("INVALID TARGET");return;}
  if(turn<0||turn>7){setStatus("INVALID ORIENTATION");return;}
  if(dims.length!=3||plan.size()!=dims[0]*dims[1]*dims[2]){''')
rep('  BlockPos dest=worldPosition.offset(dx-dims[0]/2,1+dy,dz+2);',
'''  int px=turn>=4?dims[0]-1-dx:dx,pz=dz;
  switch(turn%4){
   case 1->{int old=px;px=dims[2]-1-pz;pz=old;}
   case 2->{px=dims[0]-1-px;pz=dims[2]-1-pz;}
   case 3->{int old=px;px=pz;pz=dims[0]-1-old;}
  }
  BlockPos dest=new BlockPos(tx+px,ty+dy,tz+pz);''')
rep('  boolean placed=world.setBlock(dest,block.defaultBlockState(),3);',
'''  BlockState targetState=block.defaultBlockState();
  String properties=NetworkBlueprintItem.read(blueprint,"xsxlabs_states");
  if(!properties.isBlank()){
   String[] all=properties.split(";",-1);
   if(index<all.length)for(String pair:all[index].split("&")){
    int mid=pair.indexOf('=');
    if(mid<=0)continue;
    var property=block.getStateDefinition().getProperty(pair.substring(0,mid));
    if(property!=null)targetState=restoreProperty(targetState,property,pair.substring(mid+1));
   }
  }
  if(turn>=4)targetState=targetState.mirror(Mirror.FRONT_BACK);
  for(int n=0;n<turn%4;n++)targetState=targetState.rotate(Rotation.CLOCKWISE_90);
  boolean placed=world.setBlock(dest,targetState,3);''')
rep(' private void printer(ServerLevel world,NetworkRuntime net){',
''' @SuppressWarnings({"rawtypes","unchecked"})
 private static BlockState restoreProperty(BlockState state,
    net.minecraft.world.level.block.state.properties.Property property,String val){
  return (BlockState)property.getValue(val).map(value->state.setValue(property,(Comparable)value)).orElse(state);
 }
 private void printer(ServerLevel world,NetworkRuntime net){''')
rep('  if(fromBuffer>0L){energyBuffer-=fromBuffer;setChanged();}',
    '   if(fromBuffer>0L){energyBuffer-=fromBuffer;sync();}')
e.write_text(s)

# Vanilla button packets land in custom server ChestMenu. The client may
# use standard ChestMenu; no new fragile network payload is necessary.
p=J/"client/NetworkPrinterScreen.java"
s=p.read_text()
# Existing GUI visuals must exactly match vanilla client ChestMenu slot coords.
for old,new in (
 ('g.text(font,"BLUEPRINT",8,19,0xffe2dce6);',
  'g.text(font,"BLUEPRINT / FE CELL / MISSING",8,58,0xffe2dce6);'),
 ('g.text(font,"FE CELL",59,19,0xffe2dce6);',''),
 ('int sx=x+(i==0?26:i==1?62:98),sy=y+35;',
  'int sx=x+8+i*18,sy=y+18;')):
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
anchor=" @Override protected void extractLabels(GuiGraphicsExtractor g,int mouseX,int mouseY){"
assert s.count(anchor)==1
s=s.replace(anchor,r'''
 private void send(int button){
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.gameMode!=null)mc.gameMode.handleInventoryButtonClick(getMenu().containerId,button);
 }
 @Override protected void init(){
  super.init();
  int x=getLeftPos()+185,y=getTopPos();
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
    Component.literal("START"),b->send(0)).bounds(x,y+33,94,19).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
    Component.literal("PAUSE"),b->send(1)).bounds(x,y+55,94,19).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
    Component.literal("STOP / RESET"),b->send(2)).bounds(x,y+77,94,19).build());
 }
 private dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity device(){
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.level==null)return null;
  String title=getTitle().getString();int start=title.indexOf('@');
  if(start<0)return null;
  try{
   String[] pos=title.substring(start+1).split(",");
   if(pos.length!=3)return null;
   var be=mc.level.getBlockEntity(new net.minecraft.core.BlockPos(
      Integer.parseInt(pos[0]),Integer.parseInt(pos[1]),Integer.parseInt(pos[2])));
   return be instanceof dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity d?d:null;
  }catch(NumberFormatException ex){return null;}
 }
'''+anchor,1)
anchor='  int x=getLeftPos(),y=getTopPos();'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+r'''
  // Dedicated side console with actual FE and print progress.
  int x2=x+180;
  g.fill(x2,y,x2+107,y+167,0xff21cce2);
  g.fill(x2+2,y+2,x2+105,y+165,0xff142c3d);
  g.text(font,"PRINTER CONTROL",x2+5,y+11,0xffb1faff);
  var be=device();
  if(be!=null){
   long fe=be.availableFE(),capacity=be.ENERGY_CAPACITY;
   int fill=(int)Math.max(0L,Math.min(95L,fe*95L/Math.max(1L,capacity)));
   String status=be.status();
   g.text(font,status.length()>16?status.substring(0,16):status,x2+5,y+101,0xffd0f4ff);
   g.text(font,"ENERGY",x2+5,y+108,0xffaff4ff);
   g.fill(x2+5,y+120,x2+100,y+130,0xff244657);
   g.fill(x2+5,y+120,x2+5+fill,y+130,0xff27def4);
   g.text(font,fe+" FE",x2+5,y+134,0xffc1fbff);
   int total=be.planLength(),progress=be.progress();
   g.text(font,"BLOCKS "+progress+"/"+total,x2+5,y+147,0xffc5f8e8);
  }else g.text(font,"Syncing...",x2+5,y+119,0xffc1fbff);
''',1)
p.write_text(s)
print("V173_PRINTER_PLACEMENT_GUI174_PASS: Blueprint position/rotation/mirror, blockstates, START PAUSE STOP, FE/progress console")
