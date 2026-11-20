#!/usr/bin/env python3
"""B1692: three selectable mining shape-card modes plus 4x FE while actually flying.

Apply AFTER B1687 flight wheel and B1677 real card-slot patches. Never add
parallel manual drops: the standard enchanted-pickaxe Block.getDrops path is
still preflighted against the original transactional machine output.
"""
import json
import os
import struct
import zlib
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
R = Path(os.environ["V1_RESOURCE_ROOT"])
ASSETS = R / "assets/obsidiannetwork"
DATA = R / "data/obsidiannetwork"

def patch(rel, old, new):
    p = J / rel
    src = p.read_text(encoding="utf-8")
    assert src.count(old) == 1, ("B1692_SOURCE_DRIFT", rel, old[:90], src.count(old))
    p.write_text(src.replace(old, new, 1), encoding="utf-8")

def jsonfile(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), ("B1692_ASSET_COLLISION", str(path))
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Each is a genuinely different Item registry identity. All three share the
# existing item class and per-stack two-corner selection DataComponent, so
# every slot/interaction/dimension validation remains exactly unchanged.
patch("ObsidianNetwork.java",
'''   public static final DeferredItem<dev.obsidiannetwork.mining.V178MiningShapeCard> V178_SHAPE_CARD =
      ITEMS.registerItem("mining_shape_card",dev.obsidiannetwork.mining.V178MiningShapeCard::new);''',
'''   public static final DeferredItem<dev.obsidiannetwork.mining.V178MiningShapeCard> V178_SHAPE_CARD =
      ITEMS.registerItem("mining_shape_card",dev.obsidiannetwork.mining.V178MiningShapeCard::new);
    public static final DeferredItem<dev.obsidiannetwork.mining.V178MiningShapeCard> V178_SHAPE_CARD_FORTUNE_3 =
      ITEMS.registerItem("mining_shape_card_fortune_3",dev.obsidiannetwork.mining.V178MiningShapeCard::new);
    public static final DeferredItem<dev.obsidiannetwork.mining.V178MiningShapeCard> V178_SHAPE_CARD_SILK_TOUCH =
      ITEMS.registerItem("mining_shape_card_silk_touch",dev.obsidiannetwork.mining.V178MiningShapeCard::new);''')
patch("ObsidianNetwork.java",
'''             output.accept((ItemLike)V178_SHAPE_CARD.get());''',
'''             output.accept((ItemLike)V178_SHAPE_CARD.get());
             output.accept((ItemLike)V178_SHAPE_CARD_FORTUNE_3.get());
             output.accept((ItemLike)V178_SHAPE_CARD_SILK_TOUCH.get());''')

# Vanilla's block loot tables decide what each enchantment does. The two
# alternatives are mutually exclusive by *item identity*, not by a name/NBT
# string that a player could forge. The original normal card is unchanged.
patch("mining/V178MiningBuilderBE.java",
'''import dev.obsidiannetwork.registry.ModBlockEntities;''',
'''import dev.obsidiannetwork.registry.ModBlockEntities;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.enchantment.Enchantments;''')
patch("mining/V178MiningBuilderBE.java",
'''  public SimpleEnergyHandler energy(){return energy;}''',
'''  private ItemStack effectivePickaxe(ServerLevel world){
   ItemStack tool=new ItemStack(Items.NETHERITE_PICKAXE);
   if(card.is(ObsidianNetwork.V178_SHAPE_CARD_FORTUNE_3.get())){
    tool.enchant(world.registryAccess().lookupOrThrow(Registries.ENCHANTMENT)
       .getOrThrow(Enchantments.FORTUNE),3);
   }else if(card.is(ObsidianNetwork.V178_SHAPE_CARD_SILK_TOUCH.get())){
    tool.enchant(world.registryAccess().lookupOrThrow(Registries.ENCHANTMENT)
       .getOrThrow(Enchantments.SILK_TOUCH),1);
   }
   return tool;
  }
  public SimpleEnergyHandler energy(){return energy;}''')
patch("mining/V178MiningBuilderBE.java",
'''    // Read-only loot calculation. Ordinary drops, no silk/fortune duplication.
    var drops=Block.getDrops(current,world,target,null,null,new ItemStack(Items.NETHERITE_PICKAXE));''',
'''    // Vanilla loot calculations with the selected card's effective pickaxe.
    // Transactions still preflight the ENTIRE loot result before destroying
    // the block. No item entities, extra drops or Fortune/Silk combinations.
    var drops=Block.getDrops(current,world,target,null,null,machine.effectivePickaxe(world));''')

# 4x is charged ONLY for actual powered FlyModule flight. Standing, walking
# and Fly OFF keep the previous 20 FE/part per 5 ticks unchanged. No second
# tick handler: avoid double draining and keep existing anti-regress behavior.
patch("powerarmor/PowerArmorRuntime.java",
'''   if(powered(p)){
    for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),20L);
   }''',
'''   if(powered(p)){
    // B1692: real, server-authoritative FlyModule use costs 4x base suit FE.
    // No premium when merely carrying a card or after Jarvis Fly OFF.
    long suitDrain=canFly&&p.getAbilities().flying?80L:20L;
    for(EquipmentSlot slot:SLOTS)EnergyTool.consume(p.getItemBySlot(slot),suitDrain);
   }''')

# Existing card art is generated earlier in B1666 and is 64x64 filter-0 RGBA.
# Keep the familiar titanium blueprint design, but recolor illuminated pixels
# to make Fortune III (amber) and Silk Touch (violet) unmistakable in the GUI.
original = ASSETS / "textures/item/mining_shape_card.png"
raw = original.read_bytes()
assert raw.startswith(b"\x89PNG\r\n\x1a\n"), "B1692_MISSING_BASE_CARD_ART"
offset = 8
idat = bytearray()
while offset < len(raw):
    size = struct.unpack(">I", raw[offset:offset + 4])[0]
    kind = raw[offset + 4:offset + 8]
    data = raw[offset + 8:offset + 8 + size]
    if kind == b"IHDR":
        assert struct.unpack(">II", data[:8]) == (64,64), "B1692_BASE_CARD_DIMENSIONS"
        assert data[8:13] == bytes((8,6,0,0,0)), "B1692_BASE_CARD_FORMAT"
    elif kind == b"IDAT":
        idat.extend(data)
    offset += size + 12
decoded = zlib.decompress(idat)
assert len(decoded) == 64*(1+64*4), "B1692_BASE_CARD_BYTES"
assert all(decoded[row*(1+64*4)] == 0 for row in range(64)), "B1692_PNG_FILTER"

def chunk(kind, content):
    return struct.pack(">I",len(content))+kind+content+struct.pack(">I",zlib.crc32(kind+content)&0xffffffff)

def variant_art(mode):
    out = bytearray(decoded)
    for y in range(64):
        for x in range(64):
            i = y*257 + 1 + x*4
            red,green,blue,alpha = out[i:i+4]
            if not alpha or not (blue > red + 12 and green > red + 10):
                continue
            intensity = max(red,green,blue)
            if mode == "fortune_3":
                out[i:i+3] = bytes((intensity, min(255,intensity*70//100 + 28),max(18,intensity//5)))
            else:
                out[i:i+3] = bytes((min(255,intensity*80//100+25),max(30,intensity*43//100),intensity))
    png = (b"\x89PNG\r\n\x1a\n" +
      chunk(b"IHDR",struct.pack(">IIBBBBB",64,64,8,6,0,0,0)) +
      chunk(b"IDAT",zlib.compress(bytes(out),9)) + chunk(b"IEND",b""))
    return png

for mode in ("fortune_3","silk_touch"):
    name = "mining_shape_card_" + mode
    texture = ASSETS / ("textures/item/" + name + ".png")
    assert not texture.exists(), ("B1692_TEXTURE_COLLISION",name)
    texture.write_bytes(variant_art(mode))
    jsonfile(ASSETS / ("models/item/" + name + ".json"), {
        "parent":"minecraft:item/generated",
        "textures":{"layer0":"obsidiannetwork:item/" + name}})
    jsonfile(ASSETS / ("items/" + name + ".json"), {
        "model":{"type":"minecraft:model","model":"obsidiannetwork:item/" + name}})

# Two in-world crafting upgrades. Base Shape Card recipe and previously
# configured cards remain unaffected; upgraded cards can select new bounds.
jsonfile(DATA / "recipe/mining_shape_card_fortune_3.json", {
    "type":"minecraft:crafting_shaped",
    "pattern":["LLL","LCL","LDL"],
    "key":{"L":"minecraft:lapis_lazuli","C":"obsidiannetwork:mining_shape_card",
           "D":"minecraft:diamond"},
    "result":{"id":"obsidiannetwork:mining_shape_card_fortune_3","count":1}})
jsonfile(DATA / "recipe/mining_shape_card_silk_touch.json", {
    "type":"minecraft:crafting_shaped",
    "pattern":["SSS","SCS","SES"],
    "key":{"S":"minecraft:string","C":"obsidiannetwork:mining_shape_card",
           "E":"minecraft:emerald"},
    "result":{"id":"obsidiannetwork:mining_shape_card_silk_touch","count":1}})

for lang, names in {
 "de_de":{"mining_shape_card_fortune_3":"Mining-Shape-Card – Glück III",
          "mining_shape_card_silk_touch":"Mining-Shape-Card – Behutsamkeit"},
 "en_us":{"mining_shape_card_fortune_3":"Mining Shape Card – Fortune III",
          "mining_shape_card_silk_touch":"Mining Shape Card – Silk Touch"}
}.items():
    path = ASSETS / ("lang/" + lang + ".json")
    content = json.loads(path.read_text(encoding="utf-8"))
    for id, value in names.items():
        key = "item.obsidiannetwork." + id
        assert key not in content, ("B1692_LANG_COLLISION",key)
        content[key] = value
    path.write_text(json.dumps(content,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

assert "suitDrain=canFly&&p.getAbilities().flying?80L:20L" in (J/"powerarmor/PowerArmorRuntime.java").read_text()
assert "machine.effectivePickaxe(world)" in (J/"mining/V178MiningBuilderBE.java").read_text()
print("B1692_THREE_MINING_CARDS_VANILLA_FORTUNE_III_SILK_TOUCH_AND_ACTUAL_FLIGHT_4X_FE_PASS")
