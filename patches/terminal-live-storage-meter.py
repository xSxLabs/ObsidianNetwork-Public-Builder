#!/usr/bin/env python3
"""Small, live, bounded Crafting Terminal used/total storage meter.

Reads the *attached runtime cells*, not block entities/world/chunks, and only
once per server menu every 10 ticks. Data is synced as 8 unsigned 16-bit
chunks to retain full 64-bit item counts through vanilla menu data slots.
"""
from pathlib import Path
import os,re

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
marker="XSXLABS_TERMINAL_STORAGE_METER_V1"

network=j/"core/StorageNetwork.java"
s=network.read_text(encoding="utf-8")
assert marker not in s
assert "private final ArrayList<StorageCellStore> cells = new ArrayList<>();" in s
assert "private final ArrayList<EquipmentCellStore> equipmentCells = new ArrayList<>();" in s
# The attached, in-memory StorageCellStore and EquipmentCellStore expose O(1)
# used/free counters; NEVER decode cell ItemStack/NBT or walk item type indexes.
normal=(j/"core/StorageCellStore.java").read_text(encoding="utf-8")
equipment=(j/"core/EquipmentCellStore.java").read_text(encoding="utf-8")
for name,source in [("normal",normal),("equipment",equipment)]:
    for field in ["used(","free("]:
        assert field in source, name+" storage missing constant-time "+field
method='''   // XSXLABS_TERMINAL_STORAGE_METER_V1: lightweight, attached-cell-only totals.
   // This includes the parallel equipment-cell lane; disconnected/removed
   // drives are not counted, and empty drive slots add no capacity.
   public long[] xsxStorageMeterTotals() {
      long occupied=0L, maximum=0L;
      for (StorageCellStore cell : this.cells) {
         if (cell==null) continue;
         long used=Math.max(0L,cell.used());
         long free=Math.max(0L,cell.free());
         occupied=xsxMeterAdd(occupied,used);
         maximum=xsxMeterAdd(maximum,xsxMeterAdd(used,free));
      }
      for (EquipmentCellStore cell : this.equipmentCells) {
         if (cell==null) continue;
         long used=Math.max(0L,cell.used());
         long free=Math.max(0L,cell.free());
         occupied=xsxMeterAdd(occupied,used);
         maximum=xsxMeterAdd(maximum,xsxMeterAdd(used,free));
      }
      return new long[]{occupied,maximum};
   }
   private static long xsxMeterAdd(long a,long b){
      return a>Long.MAX_VALUE-b ? Long.MAX_VALUE : a+b;
   }

'''
anchor="   public void addCell(StorageCellStore cell) {"
assert s.count(anchor)==1
network.write_text(s.replace(anchor,method+anchor,1),encoding="utf-8")

menu=j/"menu/StorageTerminalMenu.java"
s=menu.read_text(encoding="utf-8")
assert marker not in s
# The 3-arg/5-arg constructors delegate to the 7-arg primary constructor;
# bind data slots ONLY in the primary constructor (never twice).
ctor_matches=list(re.finditer(
    r'\bpublic\s+StorageTerminalMenu\s*\(\s*int\s+\w+\s*,\s*Inventory\s+(?P<inv>\w+)\s*,\s*BlockPos\s+(?P<pos>\w+)\s*,(?P<rest>[^)]*)\)\s*\{',s))
assert len(ctor_matches)>=1, "Crafting Terminal constructor shape drift"
ctor_matches=[m for m in ctor_matches if m.group("rest").count("long")>=2 and "String" in m.group("rest") and "boolean" in m.group("rest")]
assert len(ctor_matches)==1, "ambiguous primary 7-argument Crafting Terminal ctor"
m=ctor_matches[0]
# Data slots are small and per-open-menu. No network snapshot sent every tick.
fields='''
   // XSXLABS_TERMINAL_STORAGE_METER_V1: 8 unsigned 16-bit synchronized words.
   private final int[] xsxStorageMeterWords = new int[8];
   public long xsxStorageUsed() { return xsxStorageJoin(0); }
   public long xsxStorageCapacity() { return xsxStorageJoin(4); }
   private long xsxStorageJoin(int offset) {
      long result=0;
      for(int i=0;i<4;i++)
         result|=((long)(xsxStorageMeterWords[offset+i]&65535))<<(16*i);
      return result<0?Long.MAX_VALUE:result;
   }
   private void xsxInstallStorageMeter(Inventory inventory,BlockPos terminalPos) {
      this.addDataSlots(new net.minecraft.world.inventory.ContainerData() {
         private long lastSample=Long.MIN_VALUE;
         @Override public int get(int i) {
            if(i<0||i>=8)return 0;
            if(inventory.player.level() instanceof net.minecraft.server.level.ServerLevel sl) {
               long tick=sl.getGameTime();
               if(lastSample==Long.MIN_VALUE||tick<lastSample||tick-lastSample>=10L) {
                  lastSample=tick;
                  var runtime=dev.obsidiannetwork.network.WorldTopologyBridge.runtimeForTerminal(sl,terminalPos);
                  long[] totals=runtime==null?new long[]{0L,0L}:runtime.storage().xsxStorageMeterTotals();
                  for(int word=0;word<4;word++) {
                     xsxStorageMeterWords[word]=(int)((totals[0]>>>(16*word))&65535L);
                     xsxStorageMeterWords[word+4]=(int)((totals[1]>>>(16*word))&65535L);
                  }
               }
            }
            return xsxStorageMeterWords[i];
         }
         @Override public void set(int i,int value) {
            if(i>=0&&i<8)xsxStorageMeterWords[i]=value&65535;
         }
         @Override public int getCount(){return 8;}
      });
   }

'''
# Insert fields before first constructor (not into a client-dispatch delegated ctor).
first=re.search(r'\bpublic\s+StorageTerminalMenu\s*\(',s)
assert first
s=s[:first.start()]+fields+s[first.start():]
# Reparse since the insertion shifted the target constructor's positions.
m=re.search(re.escape(m.group(0)),s)
assert m
opening=s.find("{",m.start())
def closing(text,at):
    assert text[at]=="{"
    level=0
    for index in range(at,len(text)):
        if text[index]=="{":level+=1
        elif text[index]=="}":
            level-=1
            if level==0:return index
    raise AssertionError("unbalanced constructor")
end=closing(s,opening)
s=s[:end]+"\n      this.xsxInstallStorageMeter("+ctor_matches[0].group("inv")+","+ctor_matches[0].group("pos")+");\n   "+s[end:]
assert s.count("this.xsxInstallStorageMeter(")==1
menu.write_text(s,encoding="utf-8")

# The Crafting Terminal may have separate wired/wireless screens. Cover
# whichever GUI class actually renders this StorageTerminalMenu.
screens=[]
for file in (j/"client").glob("*Screen.java"):
    body=file.read_text(encoding="utf-8")
    if "StorageTerminalMenu" in body and "extends" in body and "this.leftPos" in body:
        screens.append(file)
assert screens, "No Crafting Terminal screen consuming StorageTerminalMenu found"
updated=0
for screen in screens:
    body=screen.read_text(encoding="utf-8")
    render=list(re.finditer(
        r'\b(?:public|protected)\s+void\s+extractContents\s*\(\s*(?:GuiGraphicsExtractor|net\.minecraft\.client\.gui\.GuiGraphicsExtractor)\s+(?P<g>\w+)\s*,[^)]*\)\s*\{',body))
    assert len(render)==1, "Crafting Terminal screen extractContents method drift: "+screen.name
    match=render[0]
    end=closing(body,match.end()-1)
    g=match.group("g")
    overlay=r'''
      // Low-cost client-only drawing: cached menu words, never network scans.
      long xsxOccupied=this.menu.xsxStorageUsed();
      long xsxMaximum=this.menu.xsxStorageCapacity();
      String xsxLabel="Storage "+xsxCompactItems(xsxOccupied)+" / "+xsxCompactItems(xsxMaximum);
      int xsxX=this.leftPos+this.imageWidth-this.font.width(xsxLabel)-7;
      int xsxY=this.topPos+8;
      '''+g+'''.text(this.font,xsxLabel,xsxX,xsxY,0xFFA5AFBC,false);
      int xsxBarX=this.leftPos+this.imageWidth-65, xsxBarY=this.topPos+19;
      '''+g+'''.fill(xsxBarX,xsxBarY,xsxBarX+58,xsxBarY+2,0xFF27323E);
      int xsxFill=xsxMaximum<=0L?0:(int)Math.min(58L,(xsxOccupied*58.0D)/xsxMaximum);
      if(xsxFill>0)'''+g+'''.fill(xsxBarX,xsxBarY,xsxBarX+xsxFill,xsxBarY+2,0xFF51B4CF);
'''
    helper='''
   // Tiny header readout; formatting is purely client-side, no String.format.
   private static String xsxCompactItems(long count) {
      if(count>=1000000000L)return Long.toString(count/1000000000L)+"G";
      if(count>=1000000L)return Long.toString(count/1000000L)+"M";
      if(count>=1000L)return Long.toString(count/1000L)+"k";
      return Long.toString(count);
   }
'''
    body=body[:end]+overlay+body[end:]
    # Inject in class before final closing brace.
    cend=body.rfind("}")
    assert cend>0
    body=body[:cend]+helper+body[cend:]
    screen.write_text(body,encoding="utf-8")
    updated+=1

assert updated>0
assert "xsxStorageMeterTotals()" in network.read_text()
assert "xsxStorageJoin(4)" in menu.read_text()
print("TERMINAL_STORAGE_METER_V1 PASS: synced used/total across "+str(updated)+" screens, 10-tick server cache")
