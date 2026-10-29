#!/usr/bin/env python3
"""B404 (v1.7.3): AE2-style cosmetic JEI missing-slot highlights with partial transfer.

The old B368 client preview intentionally returned null to keep the JEI +
clickable, but this also removed red missing-ingredient highlights.
Keep the existing server-authoritative B368 partial extraction/rollback intact.
A JEI COSMETIC error displays red missing slots WITHOUT disabling the + button.
"""
import json
import os
import re
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
resources=Path(os.environ["V1_RESOURCE_ROOT"])
handler=root/"compat/jei/NetworkStorageRecipeTransferHandler.java"
screen=root/"client/StorageTerminalScreen.java"

src=handler.read_text(encoding="utf-8")
assert "B368_JEI_PARTIAL_PREVIEW" in src, "B404_EXPECTS_GREEN_B398_B368"
assert src.count("public IRecipeTransferError transferRecipe(")==1
assert src.count("private static List<IRecipeSlotView> findMissingSlots(")==1
assert src.count("private static StorageTerminalScreen findParentTerminalScreen()")==1
assert "B404_JEI_COSMETIC_MISSING" not in src

preview=re.compile(
 r'if\s*\(!doTransfer\)\s*\{\s*'
 r'// B368_JEI_PARTIAL_PREVIEW:[\s\S]*?'
 r'return null;\s*\}\s*else\s*\{')
replacement='''if (!doTransfer) {
         // B404_JEI_COSMETIC_MISSING: red slots, but PLUS remains CLICKABLE.
         java.util.List<IRecipeSlotView> missing = findMissingSlots(recipeSlots, player, container);
         return missing.isEmpty() ? null : new PartialTransferPreviewError(missing);
      } else {'''
src,n=preview.subn(lambda _:replacement,src,count=1)
assert n==1,("B404_JEI_PREVIEW_DRIFT",n)
assert src.count("ClientPacketDistributor.sendToServer(new JeiCraftTransferPayload(")==1
start=src.index("   private static List<IRecipeSlotView> findMissingSlots(")
end=src.index("   private static StorageTerminalScreen findParentTerminalScreen()",start)
new=r'''   private static final class SourceStock {
      final ItemStack stack;
      long remaining;
      SourceStock(ItemStack stack, long amount) {
         this.stack = stack;
         this.remaining = Math.max(0L, amount);
      }
   }

   // B404_JEI_STOCK_MATCH: recipe identity and stored stack identity differ.
   // A generic JEI ingredient accepts charged, renamed and damaged versions.
   // Explicit component requirements still match the normalised component set.
   private static boolean matchesForPreview(ItemStack recipe, ItemStack actual) {
      if (recipe.isEmpty() || actual.isEmpty() || !actual.is(recipe.getItem())) return false;
      if (ItemStack.isSameItemSameComponents(recipe, actual)) return true;
      if (recipe.getComponentsPatch().isEmpty()) return true;
      ItemStack simplified = actual.copyWithCount(1);
      simplified.remove(net.minecraft.core.component.DataComponents.CUSTOM_NAME);
      simplified.remove(net.minecraft.core.component.DataComponents.DAMAGE);
      simplified.remove(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get());
      return ItemStack.isSameItemSameComponents(recipe, simplified);
   }

   // B404_JEI_RED_MISSING: never mutate inventory during JEI's hover preview.
   // Source stocks are separately accounted for, avoiding false "available"
   // when the same ingredient is required in two or more recipe positions.
   private static List<IRecipeSlotView> findMissingSlots(
         IRecipeSlotsView recipeSlots, Player player, StorageTerminalMenu container) {
      StorageTerminalScreen terminal=findParentTerminalScreen();
      List<IRecipeSlotView> inputs=new ArrayList<>(
          recipeSlots.getSlotViews(RecipeIngredientRole.INPUT));
      inputs.removeIf(IRecipeSlotView::isEmpty);
      if (inputs.isEmpty()) return List.of();
      java.util.Set<String> relevant=new java.util.HashSet<>();
      for (IRecipeSlotView slot : inputs) {
         for (ItemStack possible : slot.getItemStacks().toList()) {
            if (!possible.isEmpty())
               relevant.add(net.minecraft.core.registries.BuiltInRegistries.ITEM
                   .getKey(possible.getItem()).toString());
         }
      }
      List<SourceStock> stock=new ArrayList<>();
      if (terminal != null) {
         for (Map.Entry<ItemKey,Long> entry : terminal.jeiNetworkSnapshot().entrySet()) {
            ItemKey key=entry.getKey();
            if (entry.getValue()<=0L || !relevant.contains(key.itemId())) continue;
            ItemStack stored=terminal.jeiStoredVariant(key);
            if (!stored.isEmpty()) stock.add(new SourceStock(stored,entry.getValue()));
         }
      }
      for (int i=0; i<player.getInventory().getContainerSize(); i++) {
         ItemStack item=player.getInventory().getItem(i);
         if (!item.isEmpty()) stock.add(new SourceStock(item,item.getCount()));
      }
      // Current crafting inputs count, never the output (menu slot 0).
      for (int i=StorageTerminalMenu.CRAFT_START;i<StorageTerminalMenu.CRAFT_END;i++) {
         ItemStack item=container.getSlot(i).getItem();
         if (!item.isEmpty()) stock.add(new SourceStock(item,item.getCount()));
      }
      // Prefer slots with few alternatives so an "any plank" slot cannot
      // steal the only exact oak plank needed by a constrained slot.
      inputs.sort(java.util.Comparator.comparingLong(
         slot -> slot.getItemStacks().filter(item -> !item.isEmpty()).count()));
      List<IRecipeSlotView> missing=new ArrayList<>();
      for (IRecipeSlotView slot : inputs) {
         boolean found=false;
         for (ItemStack choice : slot.getItemStacks().toList()) {
            if (choice.isEmpty()) continue;
            long amount=Math.max(1L,(long)choice.getCount());
            for (SourceStock candidate : stock) {
               if (candidate.remaining>=amount && matchesForPreview(choice,candidate.stack)) {
                  candidate.remaining-=amount;
                  found=true;
                  break;
               }
            }
            if (found) break;
         }
         if (!found) missing.add(slot);
      }
      return missing;
   }

   // B404_JEI_COSMETIC_MISSING: JEI's COSMETIC error is clickable, unlike a
   // USER_FACING transfer-blocking error. Only the actual missing recipe
   // slots are red when hovering PLUS, like an AE2 crafting terminal.
   private record PartialTransferPreviewError(
         List<IRecipeSlotView> missing) implements IRecipeTransferError {
      @Override public Type getType() { return Type.COSMETIC; }
      @Override public int getButtonHighlightColor() { return 0xFFFFAC35; }
      @Override public int getMissingCountHint() { return missing.size(); }
      @Override public void getTooltip(mezz.jei.api.gui.builder.ITooltipBuilder tooltip) {
         tooltip.add(Component.translatable("gui.obsidiannetwork.jei_missing_partial",missing.size()));
      }
      @Override public void showError(net.minecraft.client.gui.GuiGraphicsExtractor graphics,
           int mouseX,int mouseY,IRecipeSlotsView slots,int recipeX,int recipeY) {
         graphics.pose().pushMatrix();
         graphics.pose().translate(recipeX,recipeY);
         for (IRecipeSlotView slot : missing) {
            slot.drawHighlight(graphics,0x99FF3030);
         }
         graphics.pose().popMatrix();
      }
   }

'''
src=src[:start]+new+src[end:]
assert "Type.COSMETIC" in src and "getMissingCountHint()" in src
handler.write_text(src,encoding="utf-8")

ss=screen.read_text(encoding="utf-8")
needle="   public long jeiStoredAmount(ItemStack stack) {"
assert ss.count(needle)==1,("B404_SCREEN_ANCHOR_DRIFT",ss.count(needle))
addition=r'''   // B404_JEI_EXACT_STOCK_VIEW: read-only client snapshot for accurate
   // network + inventory + crafting-grid JEI missing slot previews.
   public java.util.Map<ItemKey,Long> jeiNetworkSnapshot() {
      return java.util.Collections.unmodifiableMap(this.clientState.snapshot());
   }

   public ItemStack jeiStoredVariant(ItemKey key) {
      if (this.minecraft == null || this.minecraft.level == null) return ItemStack.EMPTY;
      byte[] payload=this.stackVisualPayloads.get(key);
      if (payload!=null) {
         try {
            return new MinecraftItemStackCodec(this.minecraft.level.registryAccess())
               .recreate(new ExactStackDescriptor(key.itemId(),payload),1);
         } catch (RuntimeException badData) {
            return ItemStack.EMPTY;
         }
      }
      var id=Identifier.tryParse(key.itemId());
      if (id==null) return ItemStack.EMPTY;
      Item item=(Item)BuiltInRegistries.ITEM.getValue(id);
      return item==null ? ItemStack.EMPTY : new ItemStack(item);
   }

'''
ss=ss.replace(needle,addition+needle,1)
screen.write_text(ss,encoding="utf-8")

for loc,label in [
  ("de_de","Fehlende Zutaten: %s (rot markiert). Klicken zum Einfügen verfügbarer Zutaten."),
  ("en_us","Missing ingredients: %s (highlighted red). Click to move available ingredients.")]:
    f=resources/f"assets/obsidiannetwork/lang/{loc}.json"
    data=json.loads(f.read_text(encoding="utf-8"))
    key="gui.obsidiannetwork.jei_missing_partial"
    assert key not in data,(loc,key)
    data[key]=label
    f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Verify that the original B368 server partial-transfer mechanism stays intact.
server=(root/"menu/StorageTerminalMenu.java").read_text(encoding="utf-8")
assert "B368_PARTIAL_INGREDIENTS" in server
assert "xsxRecipeIngredientAccepts" in server
assert "JEI rollback incomplete" in server
assert "if(found<0)" in server.replace(" ","") or "if (found < 0)" in server
print("B404_JEI_COSMETIC_MISSING_PASS: red ingredient slots + partial click + component-compatible stock")
