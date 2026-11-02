#!/usr/bin/env python3
"""B891: real wearer's forward-arm pose, smaller mounted MG, first-person mount,
and backpack mouse-focus / precise quantity / row scrolling fixes.
Applied AFTER B879. Source reconstruction is fail-closed on drift.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B891_DRIFT",rel,s.count(old),old[:160])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# Physical arm-axis weapon model is shared by world-suit and worn armor:
# shrink the unwieldy 13px gun to a compact 8.5px top-arm barrel.
gun="client/V176MicroMgVisualClient.java"
edit(gun,
 ".texOffs(0,0).addBox(-0.9F,5.0F,-3.5F,1.8F,13.0F,1.8F)",
 ".texOffs(0,0).addBox(-0.62F,5.0F,-3.15F,1.24F,8.5F,1.25F)")
edit(gun,
 ".texOffs(0,15).addBox(-1.6F,2.5F,-3.25F,3.2F,6.0F,0.8F)",
 ".texOffs(0,15).addBox(-1.12F,3.5F,-3.05F,2.24F,4.2F,0.65F)")
# Model and hand share the same arm length direction; correct sideways drift
# from the vanilla camera hand's right edge and keep the gun ON the upper arm.
edit(gun,
 "  pose.translate(0.39F,-0.34F,-0.45F);",
 "  pose.translate(0.58F,-0.30F,-0.53F);")
# Tilt slightly more horizontally to track the forward pointing right fist.
edit(gun,
 "  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-90.0F));",
 "  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-96.0F));")

# Force the real PlayerModel arm and its sleeve to the same orientation as the
# gun and the armor. Keep this only in attack mode and never pose the left arm.
# PlayerModel setupAnim TAIL is the visible body, not just a render-layer prop.
for rel,old,new in (
 ("mixin/V176AttackPlayerModelMixin.java",
  "  this.rightArm.xRot=-1.535F;",
  "  this.rightArm.xRot=-1.43F;"),
 ("mixin/V176AttackRightArmMixin.java",
  "  rightArm.xRot=-1.535F;",
  "  rightArm.xRot=-1.43F;"),
 ("client/V176MicroMgLayer.java",
  "  arm.xRot=-1.535F;arm.yRot=0F;arm.zRot=0F;",
  "  arm.xRot=-1.43F;arm.yRot=0F;arm.zRot=0F;"),
 ("client/V176MicroMgVisualClient.java",
  "  arm.xRot=-1.535F;arm.yRot=0F;arm.zRot=0F;",
  "  arm.xRot=-1.43F;arm.yRot=0F;arm.zRot=0F;"),
):
 edit(rel,old,new)

# Re-apply the pose to the player's sleeve in the actual registered weapon
# layer, so follow-on humanoid/armor animations don't detach the gun.
edit("client/V176MicroMgLayer.java",
 "  arm.xRot=-1.43F;arm.yRot=0F;arm.zRot=0F;",
 """  arm.xRot=-1.43F;arm.yRot=0F;arm.zRot=0F;
  // Last model-layer guard. The right sleeve uses the same shoulder pivot.
  var sleeve=getParentModel().rightSleeve;
  sleeve.xRot=arm.xRot;sleeve.yRot=arm.yRot;sleeve.zRot=arm.zRot;""")

screen="client/V176BackpackScreen.java"
# B816 painted the number in extractLabels, BEFORE item icons. Remove that
# old overlay; draw count text in renderSlotContents AFTER the item instead.
p=J/screen
s=p.read_text(encoding="utf-8")
begin="  for(int index=0;index<45;index++){"
end='  g.text(font,"MODULES",'
assert s.count(end)==1,("B893_LABELS_TARGET_DRIFT",s.count(end))
if s.count(begin)==1 and s.index(begin)<s.index(end):
 s=s[:s.index(begin)]+s[s.index(end):]
else:
 # B857 and subsequent patches can restructure the label loop. The new
 # foreground slot overlay supersedes any early labels in either layout.
 print("B893_EARLY_COUNT_LABEL_BLOCK_ALREADY_RESTRUCTURED")
p.write_text(s,encoding="utf-8")
edit(screen,
 '''   g.pose().popMatrix();
   return;''',
 '''   g.pose().popMatrix();
   // Item is already submitted: draw the compact stored count in FRONT.
   var countData=stack.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
   long amount=countData.getLongOr("xsx_v176_preview_total",0L);
   if(amount>1L){
    String label=amount>=1000000?amount/1000000+"M":
      amount>=1000?amount/1000+"k":Long.toString(amount);
    g.nextStratum();
    g.text(font,label,slot.x+16-font.width(label),slot.y+9,0xffeffaff);
   }
   return;''')

# Replace page-by-45 jumping with a 9-slot/row offset, preserving 45 preview
# slots and server validation. The mouse wheel scrolls a single row at a time.
# Both the preview access and transaction cursor index must scroll together.
p=J/"backpack/V176BackpackMenu.java"
source=p.read_text(encoding="utf-8")
old_position="   int position=page*45+slot-4;"
assert source.count(old_position)==2,("B894_ROW_INDEX_DRIFT",source.count(old_position))
p.write_text(source.replace(old_position,"   int position=page*9+slot-4;"),encoding="utf-8")
edit("backpack/V176BackpackMenu.java",
 "   int last=Math.max(0,(resultEntries().size()-1)/45);",
 "   int last=Math.max(0,(resultEntries().size()-45+8)/9);")

# Delete only the two paging arrows, preserve all controls/search/sort.
edit(screen,
 '''  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal("<"),b->command("networkbackpack previous"))
       .bounds(leftPos+123,topPos+127,22,13).build());
  addRenderableWidget(net.minecraft.client.gui.components.Button.builder(
      Component.literal(">"),b->command("networkbackpack next"))
       .bounds(leftPos+147,topPos+127,22,13).build());
''',
 "")

edit(screen,
 '''  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  if((button==0||button==1)&&x>=8&&x<170&&y>=38&&y<128){''',
 '''  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  boolean onSearch=searchBox!=null&&searchBox.isMouseOver(mx,my);
  // Right-click the SEARCH field to clear, without disturbing modules/items.
  if(onSearch&&button==1){
   searchBox.setValue("");
   setFocused(searchBox);
   return true;
  }
  // Any click outside search relinquishes the keyboard focus. AutoFocus
  // still works on screen opening or when toggled back on.
  if(!onSearch&&searchBox!=null){
   searchBox.setFocused(false);
   if(getFocused()==searchBox)setFocused(null);
  }
  if((button==0||button==1)&&x>=8&&x<170&&y>=38&&y<128){''')

edit(screen,
 '''  return super.mouseClicked(event,doubleClick);
 }''',
 '''  return super.mouseClicked(event,doubleClick);
 }
 @Override public boolean mouseScrolled(double mx,double my,double scrollX,double scrollY){
  int x=(int)mx-getLeftPos(),y=(int)my-getTopPos();
  if(x>=8&&x<170&&y>=38&&y<128&&scrollY!=0.0D){
   // One 9-item row per wheel step; commands retain the server-owned index.
   int steps=Math.max(1,Math.min(4,(int)Math.ceil(Math.abs(scrollY))));
   for(int i=0;i<steps;i++)
    command(scrollY>0?"networkbackpack previous":"networkbackpack next");
   return true;
  }
  return super.mouseScrolled(mx,my,scrollX,scrollY);
 }
 @Override protected void extractTooltip(
     net.minecraft.client.gui.GuiGraphicsExtractor g,int mx,int my){
  super.extractTooltip(g,mx,my);
  // Full 64-bit amount as part of the hover tooltip, NOT below the grid.
  var slot=getHoveredSlot();
  if(slot==null)return;
  int index=this.menu.slots.indexOf(slot);
  if(index<4||index>=49)return;
  var stack=slot.getItem();
  if(stack.isEmpty())return;
  var tag=stack.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA,
      net.minecraft.world.item.component.CustomData.EMPTY).copyTag();
  long amount=tag.getLongOr("xsx_v176_preview_total",0L);
  if(amount<1)return;
  var lines=new java.util.ArrayList<>(getTooltipFromContainerItem(stack));
  lines.add(Component.literal("Menge: "+
      String.format(java.util.Locale.GERMANY,"%,d",amount)));
  g.setTooltipForNextFrame(font,lines,mx,my);
 }''')
# A fresh click outside search must stay unfocused, not snap back.
assert 'if(getFocused()==searchBox)setFocused(null)' in (J/screen).read_text()
assert 'mouseScrolled(double mx,double my,double scrollX,double scrollY)' in (J/screen).read_text()
assert 'g.nextStratum()' in (J/screen).read_text()
assert 'setTooltipForNextFrame(font,lines,mx,my)' in (J/screen).read_text()
print("B891_THIRDPERSON_COMPACT_ARM_FIRSTPERSON_ALIGNED_BACKPACK_SCROLL_HOVER_COUNTS_FOCUS_READY")
