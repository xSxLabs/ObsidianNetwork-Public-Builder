#!/usr/bin/env python3
"""B445: scalable actual layer-diagram preview for the 5..64 reactor and 3..12 powerbank.

Client-only visualization; no packets, world mutation, saved-data migration, or
changes to validated reactor/powerbank structure rules.
Runs strictly AFTER apply-guidebook-442.py.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V174GuidebookScreen.java"
s=p.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,("V174_B445_GUIDE_DRIFT",s.count(old),old[:90])
 s=s.replace(old,new,1)

change(" private int page=0;",''' // B445_SCALED_LAYERS: independent client-side controls, no fake menu slots.
 private int page=0;
 private boolean showReactor=true;
 private int reactorSize=5,reactorLayer=0,powerbankHeight=3,powerbankLayer=0;''')

change('''  g.text(font,TITLE[page],8,15,0xfff5d68c);''',
'''  if(page!=7)g.text(font,TITLE[page],8,15,0xfff5d68c);''')

change('''  String[] rows=PLAN[page];
  for(int i=0;i<rows.length;i++)
   g.text(font,rows[i],12,27+i*9,0xffd7f8e3);''','''  if(page==7){
   int edge=showReactor?reactorSize:3;
   int height=showReactor?reactorSize:powerbankHeight;
   int layer=showReactor?reactorLayer:powerbankLayer;
   g.text(font,(showReactor?"R ":"P ")+edge,8,27,0xfff6e1a6);
   g.text(font,edge+"x"+height+"x"+edge,116,16,0xfff6e1a6);
   g.text(font,"TYPE",8,35,0xffa1f7ff);
   g.text(font,"- SIZE +",8,49,0xffa1f7ff);
   g.text(font,"- Y +",8,64,0xffa1f7ff);
   g.text(font,"Y "+(layer+1)+"/"+height,116,75,0xffb9effa);
  }else{
   String[] rows=PLAN[page];
   for(int i=0;i<rows.length;i++)
    g.text(font,rows[i],12,27+i*9,0xffd7f8e3);
   g.text(font,NOTE[page],8,73,0xffb2d1dc);
  }''')
change('''  g.text(font,NOTE[page],8,73,0xffb2d1dc);
  g.text(font,"PAGE "+(page+1)+"/"+PLAN.length,121,4,0xffffffff);''',
'''  g.text(font,"PAGE "+(page+1)+"/"+PLAN.length,121,4,0xffffffff);''')

# Keep page navigation separate from the 64-pixel grid; no controls over inventory.
change('''  g.text(font,"< PREV",113,37,0xffa1f7ff);
  g.text(font,"NEXT >",113,54,0xffa1f7ff);''','''  g.text(font,"< PREV",120,37,0xffa1f7ff);
  g.text(font,"NEXT >",120,54,0xffa1f7ff);''')
change('''  g.fill(x+105,y+34,x+170,y+49,0xff1d4153);
  g.fill(x+105,y+51,x+170,y+67,0xff1d4153);''','''  g.fill(x+117,y+34,x+170,y+49,0xff1d4153);
  g.fill(x+117,y+51,x+170,y+67,0xff1d4153);
  if(page==7){
   g.fill(x+5,y+31,x+46,y+45,0xff1d4153);
   g.fill(x+5,y+47,x+46,y+60,0xff1d4153);
   g.fill(x+5,y+62,x+46,y+75,0xff1d4153);
   // Diagram is a true XZ slice. Each square is one voxel, uniformly scaled.
   // 64x64 is capped at 4096 draws per frame; no world scanning.
   int size=showReactor?reactorSize:3;
   int height=showReactor?reactorSize:powerbankHeight;
   int layer=showReactor?reactorLayer:powerbankLayer;
   int step=Math.max(1,64/size),startX=x+49,startY=y+17;
   for(int z=0;z<size;z++)for(int xx=0;xx<size;xx++){
    boolean outer=layer==0||layer==height-1||xx==0||z==0||xx==size-1||z==size-1;
    int color=outer?0xff548ba4:0xff0d2330;
    if(showReactor&&!outer&&xx==size/2&&z==size/2)color=0xffedb257;
    // All service interfaces are on the shell on the first middle layer.
    if(layer==1){
     if(xx==size/2&&z==0)color=0xff55d8ed; // controller
     if(xx==0&&z==size/2)color=0xff90ec9e; // item / FE input
     if(xx==size-1&&z==size/2)color=0xffa4a9ff; // water / FE output
     if(showReactor&&xx==size/2&&z==size-1)color=0xffedb257; // reactor FE output
    }
    g.fill(startX+xx*step,startY+z*step,
           startX+(xx+1)*step,startY+(z+1)*step,color);
   }
  }''')
change('''   if(x>=105D&&x<=170D){''','''   if(page==7&&x>=5D&&x<=46D){
    if(y>=31D&&y<=45D){showReactor=!showReactor;return true;}
    if(y>=47D&&y<=60D){
     if(showReactor){
      reactorSize=Math.max(5,Math.min(64,reactorSize+(x<25D?-1:1)));
      reactorLayer=Math.min(reactorLayer,reactorSize-1);
     }else{
      powerbankHeight=Math.max(3,Math.min(12,powerbankHeight+(x<25D?-1:1)));
      powerbankLayer=Math.min(powerbankLayer,powerbankHeight-1);
     }
     return true;
    }
    if(y>=62D&&y<=75D){
     if(showReactor)reactorLayer=Math.max(0,Math.min(reactorSize-1,reactorLayer+(x<25D?-1:1)));
     else powerbankLayer=Math.max(0,Math.min(powerbankHeight-1,powerbankLayer+(x<25D?-1:1)));
     return true;
    }
   }
   if(x>=117D&&x<=170D){''')
assert "B445_SCALED_LAYERS" in s
assert "new SimpleContainer(27)" not in s  # real container implementation is elsewhere
p.write_text(s,encoding="utf-8")
print("V174_GUIDEBOOK_SIZE_445_PASS: reactor 5..64, powerbank 3..12, every Y slice")
