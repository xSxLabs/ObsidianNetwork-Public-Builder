#!/usr/bin/env python3
"""B1381: controller-wide, rollback-safe Powerbank output throttle and GUI slider.

Run LAST after B1351, never touch intake or unrelated reactor/energy-cell paths.
"""
import os
import re
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def modify(name,old,new,n=1):
    p=J/name
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==n,("B1381_DRIFT",name,old[:110],s.count(old),n)
    p.write_text(s.replace(old,new,n),encoding="utf-8")

p=J/"powerbank/PowerbankBlockEntity.java"
b=p.read_text(encoding="utf-8")
assert "B1351_RELINK_ON_LOAD" in b and "B1372BankOriginState" in b
assert "B1281_UNCAPPED_POWERBANK_AUTO_EXPORT" in b
assert "B1381_OUTPUT_LIMIT" not in b

def once(old,new,label):
    global b
    assert b.count(old)==1,("B1381_BANK_DRIFT",label,b.count(old))
    b=b.replace(old,new,1)

once(" public long guiEnergy(){return amount;}",''' // B1381_OUTPUT_LIMIT: one controller-wide FE budget for ALL output ports
  // and ALL external pullers. No limit is placed on INPUT.
  public static final long[] B1381_STEPS={
      0L,100_000L,500_000L,1_000_000L,2_000_000L,
      5_000_000L,10_000_000L,25_000_000L,50_000_000L,
      100_000_000L,250_000_000L,500_000_000L,
      1_000_000_000L,-1L};
  private long b1381OutputLimit=2_000_000L;
  private long b1381RateTick=Long.MIN_VALUE,b1381RateUsed=0L;
  public long b1381OutputLimit(){
   var bank=controller();return bank==null?2_000_000L:bank.b1381OutputLimit;
  }
  public void b1381SetOutputLimit(int index){
   if(mode()!=PowerbankBlock.Mode.CONTROLLER
      ||index<0||index>=B1381_STEPS.length)return;
   long chosen=B1381_STEPS[index];
   if(b1381OutputLimit==chosen)return;
   b1381OutputLimit=chosen;
   setChanged();
   if(level instanceof ServerLevel sl)
     sl.sendBlockUpdated(worldPosition,getBlockState(),getBlockState(),3);
  }
  private long b1381Remaining(){
   if(b1381OutputLimit<0)return Long.MAX_VALUE;
   if(level==null)return 0L;
   long consumed=b1381RateTick==level.getGameTime()?b1381RateUsed:0L;
   return Math.max(0L,b1381OutputLimit-consumed);
  }
  private void b1381Consume(int n){
   long now=level.getGameTime();
   if(b1381RateTick!=now){b1381RateTick=now;b1381RateUsed=0L;}
   b1381RateUsed+=n;
  }
  public long guiEnergy(){return amount;}''',"bank_fields")

# The existing bank energy journal contains amount and both pending
# ingress/egress counters. Extend THAT SAME journal to rollback provisional
# per-tick output tokens, including nested transfers and multi-port pulls.
once("return new long[]{amount,xsxPendingIn,xsxPendingOut};",
     "return new long[]{amount,xsxPendingIn,xsxPendingOut,b1381RateTick,b1381RateUsed};",
     "transaction_snapshot")
once("amount=before[0];xsxPendingIn=before[1];xsxPendingOut=before[2];",
     "amount=before[0];xsxPendingIn=before[1];xsxPendingOut=before[2];"
     "b1381RateTick=before[3];b1381RateUsed=before[4];",
     "transaction_rollback")

# Native cable and crossmod FE consumers must share the same one-tick
# allowance; never throttle the source/input pathway.
once("int taken=(int)Math.min((long)demand,b.amount);",
     "int taken=(int)Math.min(Math.min((long)demand,b.amount),b.b1381Remaining());",
     "extract_cap")
once("if(taken>0){b.journal.updateSnapshots(tx);b.amount-=taken;b.xsxPendingOut+=taken;b1300MarkSource(tx,b);}",
     "if(taken>0){b.journal.updateSnapshots(tx);b.b1381Consume(taken);"
     "b.amount-=taken;b.xsxPendingOut+=taken;b1300MarkSource(tx,b);}",
     "extract_budget")

# B591 sink-first transfer must offer <= the FE budget or source.extract()
# would accept less than target.insert() and force a rollback of everything.
once("int offer=(int)Math.min((long)Integer.MAX_VALUE,amount);",
     "int offer=(int)Math.min(Math.min((long)Integer.MAX_VALUE,amount),b1381Remaining());",
     "sink_first_offer")
once('out.putBoolean("xsxNetworkEnabled",xsxNetworkEnabled);',
     'out.putBoolean("xsxNetworkEnabled",xsxNetworkEnabled);\n'
     '    out.putLong("b1381OutputLimit",b1381OutputLimit);',
     "persist_save")
once('xsxNetworkEnabled=in.getBooleanOr("xsxNetworkEnabled",true);',
     '''xsxNetworkEnabled=in.getBooleanOr("xsxNetworkEnabled",true);
   long b1381Saved=in.getLongOr("b1381OutputLimit",2_000_000L);
   boolean b1381Valid=false;
   for(long v:B1381_STEPS)if(v==b1381Saved){b1381Valid=true;break;}
   b1381OutputLimit=b1381Valid?b1381Saved:2_000_000L;
   b1381RateTick=Long.MIN_VALUE;b1381RateUsed=0L;''',
     "persist_load")
assert b.count("b1381Consume(taken)") == 1
assert b.count("b1381Remaining()") == 3
p.write_text(b,encoding="utf-8")

# Server authority through the existing vanilla inventory-button packet,
# rather than chat commands (important for non-op/spam-kick protection).
menu=J/"powerbank/PowerbankMenu.java"
m=menu.read_text(encoding="utf-8")
needle=" @Override public boolean stillValid(Player player){"
assert m.count(needle)==1,("B1381_MENU_DRIFT",m.count(needle))
m=m.replace(needle,''' // B1381_SERVER_AUTHORIZED_BUTTONS: whitelist rate steps, local GUI only.
  @Override public boolean clickMenuButton(Player player,int button){
   if(player.isSpectator()||!stillValid(player)
       ||button<0||button>=PowerbankBlockEntity.B1381_STEPS.length)return false;
   var owner=bank.xsxNetworkController();
   if(owner==null||owner.mode()!=PowerbankBlock.Mode.CONTROLLER)return false;
   owner.b1381SetOutputLimit(button);
   return true;
  }
''' +needle,1)
menu.write_text(m,encoding="utf-8")

# Overlay only the Powerbank part of the pre-existing 250px-tall machine GUI,
# preserving real player inventory and all Reactor/Pump controls.
screen=J/"client/V174MachineScreen.java"
s=screen.read_text(encoding="utf-8")
assert "B503_MOUSE_INPUT_BOTTOM" in s and "B508_BANK_LIVE_IO" in s
assert "B1381_SLIDER" not in s

helpers=r'''
 // B1381_SLIDER: visual controls are client-only; the server owns the budget.
 private boolean b1381Dragging=false;
 private int b1381PreviewIndex=4;
 private static int b1381RateIndex(long limit){
  for(int i=0;i<PowerbankBlockEntity.B1381_STEPS.length;i++)
   if(PowerbankBlockEntity.B1381_STEPS[i]==limit)return i;
  return 4;
 }
 private PowerbankBlockEntity b1381Bank(){
  return live() instanceof PowerbankBlockEntity be?be:null;
 }
 private static String b1381Compact(long v){
  if(v<0)return "UNLIMITED";
  if(v>=1_000_000_000L)return (v/1_000_000_000L)+"B";
  if(v>=1_000_000L)return (v/1_000_000L)+"M";
  if(v>=1_000L)return (v/1_000L)+"K";
  return Long.toString(v);
 }
 private int b1381SliderIndex(double cursor){
  return Math.max(0,Math.min(12,(int)Math.round(
      (cursor-getLeftPos()-12D)*12D/154D)));
 }
 private void b1381DrawText(GuiGraphicsExtractor g){
  var bank=b1381Bank();
  if(bank==null)return;
  long limit=bank.b1381OutputLimit();
  int index=b1381Dragging?b1381PreviewIndex:b1381RateIndex(limit);
  String label=b1381Dragging
      ?b1381Compact(PowerbankBlockEntity.B1381_STEPS[index])
      :b1381Compact(limit);
  g.text(font,"INPUT: UNLIMITED",8,106,0xff83eeb8);
  g.text(font,"MAX OUTPUT: "+label+" FE/t",8,119,0xffe9e2f5);
  g.text(font,"0",12,144,0xffa9c0d8);
  g.text(font,"1B FE/t",127,144,0xffa9c0d8);
  g.text(font,"UNLIMITED",24,154,limit<0?0xff86ffe0:0xff9eb0c1);
 }
 private void b1381DrawBackground(GuiGraphicsExtractor g){
  var bank=b1381Bank();
  if(bank==null)return;
  int x=getLeftPos(),y=getTopPos();
  g.fill(x+5,y+102,x+171,y+167,0xff132837);
  g.fill(x+12,y+133,x+166,y+139,0xff37576e);
  int idx=b1381Dragging?b1381PreviewIndex:b1381RateIndex(bank.b1381OutputLimit());
  if(idx>12)idx=4;
  int thumb=x+12+(int)Math.round(154D*idx/12D);
  g.fill(thumb-4,y+129,thumb+4,y+142,0xff97e7ff);
  g.fill(x+9,y+151,x+20,y+162,0xff6b9eb5);
  if(bank.b1381OutputLimit()<0)
   g.fill(x+11,y+153,x+18,y+160,0xff64eed1);
 }
 private boolean b1381Click(double mx,double my,int button){
  if(button!=0||b1381Bank()==null)return false;
  int x=getLeftPos(),y=getTopPos();
  if(mx>=x+9&&mx<=x+167&&my>=y+150&&my<=y+164){
   long chosen=b1381Bank().b1381OutputLimit();
   b1381Send(chosen<0?4:13);
   return true;
  }
  if(mx>=x+7&&mx<=x+171&&my>=y+125&&my<=y+146){
   b1381Dragging=true;
   b1381PreviewIndex=b1381SliderIndex(mx);
   return true;
  }
  return false;
 }
 private void b1381Send(int id){
  var mc=Minecraft.getInstance();
  if(mc.gameMode!=null&&mc.player!=null)
   mc.gameMode.handleInventoryButtonClick(getMenu().containerId,id);
 }
 private boolean b1381Drag(double mx){
  if(!b1381Dragging)return false;
  b1381PreviewIndex=b1381SliderIndex(mx);
  return true;
 }
 private boolean b1381Release(int button){
  if(!b1381Dragging||button!=0)return false;
  b1381Dragging=false;
  b1381Send(b1381PreviewIndex);
  return true;
 }
'''
marker=" private final BlockPos devicePos;"
assert s.count(marker)==1,("B1381_SCREEN_FIELD_DRIFT",s.count(marker))
s=s.replace(marker,marker+"\n"+helpers,1)

def add_to_method(src,signature,code):
    starts=list(re.finditer(signature,src))
    assert len(starts)==1,("B1381_SCREEN_METHOD_DRIFT",signature,len(starts))
    start=starts[0].end()
    depth=1
    end=start
    while end<len(src) and depth:
        if src[end]=='{':depth+=1
        elif src[end]=='}':depth-=1
        end+=1
    assert depth==0,("B1381_SCREEN_UNBALANCED",signature)
    return src[:end-1]+"\n   "+code+"\n  "+src[end-1:]

s=add_to_method(s,
    r'@Override\s+protected\s+void\s+extractLabels\s*\(\s*GuiGraphicsExtractor\s+\w+\s*,\s*int\s+\w+\s*,\s*int\s+\w+\s*\)\s*\{',
    'if(machine==Machine.POWERBANK)b1381DrawText(g);')
s=add_to_method(s,
    r'@Override\s+public\s+void\s+extractBackground\s*\(\s*GuiGraphicsExtractor\s+\w+\s*,\s*int\s+\w+\s*,\s*int\s+\w+\s*,\s*float\s+\w+\s*\)\s*\{',
    'if(machine==Machine.POWERBANK)b1381DrawBackground(g);')

# Existing machine GUI has reactor click controls: retain them, put bank
# interaction first. Add overrides when they do not exist.
def inject_override(src,method,args,body,call):
    signature=r'public\s+boolean\s+'+method+r'\s*\('+args+r'\)\s*\{'
    matches=list(re.finditer(signature,src))
    assert len(matches)<=1,("B1381_"+method+"_DRIFT",len(matches))
    if matches:
        at=matches[0].end()
        return src[:at]+'\n   '+body+'\n'+src[at:]
    assert src.rstrip().endswith('}'),"B1381_CLASS_END"
    idx=src.rfind('}')
    return src[:idx]+' @Override public boolean '+method+'('+call[0]+'){\n   '+body+'\n   return super.'+method+'('+call[1]+');\n }\n'+src[idx:]

# Minecraft 26.1 uses the MouseButtonEvent object (not legacy doubles).
# Preserve vanilla/container behavior outside this Powerbank control.
assert "boolean mouseClicked(" not in s, "B1383_SCREEN_CLICK_API_CHANGED"
assert "boolean mouseDragged(" not in s, "B1383_SCREEN_DRAG_API_CHANGED"
assert "boolean mouseReleased(" not in s, "B1383_SCREEN_RELEASE_API_CHANGED"
idx=s.rfind('}')
assert idx>0 and s[idx+1:].strip()==""
s=s[:idx]+'''
 @Override public boolean mouseClicked(net.minecraft.client.input.MouseButtonEvent event,boolean doubleClick){
  if(machine==Machine.POWERBANK&&b1381Click(event.x(),event.y(),event.button()))return true;
  return super.mouseClicked(event,doubleClick);
 }
 @Override public boolean mouseDragged(net.minecraft.client.input.MouseButtonEvent event,double dx,double dy){
  if(machine==Machine.POWERBANK&&b1381Drag(event.x()))return true;
  return super.mouseDragged(event,dx,dy);
 }
 @Override public boolean mouseReleased(net.minecraft.client.input.MouseButtonEvent event){
  if(machine==Machine.POWERBANK&&b1381Release(event.button()))return true;
  return super.mouseReleased(event);
 }
'''+s[idx:]
assert "B1381_SLIDER" in s
screen.write_text(s,encoding="utf-8")
print("B1381_POWERBANK_OUTPUT_GUI_TRANSACTION_SAFE_GLOBAL_RATE_PASS")
