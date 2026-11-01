#!/usr/bin/env python3
"""Add real reactor/powerbank NETWORK ports as validated multiblock shells.

Existing ITEM/FLUID/FE ports remain intact. Each network port uses its own
block item and shares the existing linked-port block entity: no parallel
controller inventories, no chunk force-loading, no forged client state.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def patch(rel,old,new,n=1):
 p=J/rel
 src=p.read_text(encoding="utf-8")
 assert src.count(old)==n,("V176_NETWORK_PORT_DRIFT",rel,old[:100],src.count(old),n)
 p.write_text(src.replace(old,new,n),encoding="utf-8")
def output(rel,data):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_NETWORK_PORT_ASSET_EXISTS",str(p))
 p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

for kind in ("REACTOR","POWERBANK"):
 stem="reactor_network_port" if kind=="REACTOR" else "powerbank_network_port"
 blockClass=("dev.obsidiannetwork.reactor.ReactorPortBlock" if kind=="REACTOR"
             else "dev.obsidiannetwork.powerbank.PowerbankBlock")
 field=f"{kind}_NETWORK_PORT"
 anchor=(f"   public static final DeferredBlock<dev.obsidiannetwork.reactor.ReactorPortBlock> REACTOR_POWER_PORT ="
          if kind=="REACTOR" else
         f"    public static final DeferredBlock<dev.obsidiannetwork.powerbank.PowerbankBlock> POWERBANK_OUTPUT =")
 registration=(
   f"    public static final DeferredBlock<{blockClass}> {field} =\n"
   f'        BLOCKS.registerBlock("{stem}",p -> new {blockClass}(p,{blockClass}.Mode.NETWORK),\n'
   "            p -> p.mapColor(MapColor.METAL).strength(3.5F,9.0F).requiresCorrectToolForDrops());\n"
   f"    public static final DeferredItem<BlockItem> {field}_ITEM =\n"
   f'        ITEMS.registerSimpleBlockItem("{stem}",{field});\n')
 patch("ObsidianNetwork.java",anchor,registration+anchor)
 creative=("            output.accept((ItemLike)REACTOR_POWER_PORT_ITEM.get());"
           if kind=="REACTOR" else
           "            output.accept((ItemLike)POWERBANK_OUTPUT_ITEM.get());")
 patch("ObsidianNetwork.java",creative,creative+
       f"\n            output.accept((ItemLike){field}_ITEM.get());")
 output(f"assets/obsidiannetwork/blockstates/{stem}.json",
       {"variants":{"":{"model":f"obsidiannetwork:block/{stem}"}}})
 output(f"assets/obsidiannetwork/models/block/{stem}.json",
       {"parent":"minecraft:block/cube_all","textures":{"all":"minecraft:block/crying_obsidian"}})
 output(f"assets/obsidiannetwork/items/{stem}.json",
       {"model":{"type":"minecraft:model","model":f"obsidiannetwork:block/{stem}"}})
 output(f"data/obsidiannetwork/loot_table/blocks/{stem}.json",
       {"type":"minecraft:block","pools":[{"rolls":1,
           "entries":[{"type":"minecraft:item","name":"obsidiannetwork:"+stem}]}]})
 output(f"data/obsidiannetwork/recipe/{stem}.json",
       {"type":"minecraft:crafting_shaped","pattern":["ENE","PMP","ENE"],
        "key":{"E":"minecraft:ender_pearl","N":"minecraft:netherite_ingot",
         "M":("obsidiannetwork:reactor_controller" if kind=="REACTOR"
              else "obsidiannetwork:powerbank_controller"),
         "P":"minecraft:prismarine_crystals"},
        "result":{"id":"obsidiannetwork:"+stem,"count":1}})
 tags=R/"data/minecraft/tags/block/mineable/pickaxe.json"
 doc=json.loads(tags.read_text(encoding="utf-8"))
 if "obsidiannetwork:"+stem not in doc["values"]:
  doc["values"].append("obsidiannetwork:"+stem)
 tags.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
 for lang in ("de_de","en_us"):
  loc=R/f"assets/obsidiannetwork/lang/{lang}.json"
  doc=json.loads(loc.read_text(encoding="utf-8"))
  key="block.obsidiannetwork."+stem
  assert key not in doc,key
  doc[key]=(kind.title()+" Network Port" if lang=="en_us"
            else ("Reaktor-Netzwerkport" if kind=="REACTOR" else "Powerbank-Netzwerkport"))
  loc.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

patch("reactor/ReactorPortBlock.java","public enum Mode {ITEM,FLUID,POWER}",
      "public enum Mode {ITEM,FLUID,POWER,NETWORK}")
patch("reactor/ReactorPortBlock.java",
      " private static final MapCodec<ReactorPortBlock> P=simpleCodec(p->new ReactorPortBlock(p,Mode.POWER));",
      " private static final MapCodec<ReactorPortBlock> P=simpleCodec(p->new ReactorPortBlock(p,Mode.POWER));\n"
      " private static final MapCodec<ReactorPortBlock> N=simpleCodec(p->new ReactorPortBlock(p,Mode.NETWORK));")
patch("reactor/ReactorPortBlock.java",
      "case ITEM->I;case FLUID->F;case POWER->P;",
      "case ITEM->I;case FLUID->F;case POWER->P;case NETWORK->N;")
patch("reactor/ReactorPortBlockEntity.java",
      " private ReactorControllerBlockEntity controller(){",
      " public ReactorControllerBlockEntity xsxNetworkController(){return controller();}\n"
      " private ReactorControllerBlockEntity controller(){")
patch("reactor/ReactorStructure.java",
      "||s.is(ObsidianNetwork.REACTOR_POWER_PORT.get())",
      "||s.is(ObsidianNetwork.REACTOR_POWER_PORT.get())\n   ||s.is(ObsidianNetwork.REACTOR_NETWORK_PORT.get())")
patch("reactor/ReactorStructure.java",
      "||state.is(ObsidianNetwork.REACTOR_POWER_PORT.get()))ports.add(p);",
      "||state.is(ObsidianNetwork.REACTOR_POWER_PORT.get())\n"
      "     ||state.is(ObsidianNetwork.REACTOR_NETWORK_PORT.get()))ports.add(p);")
patch("registry/ModBlockEntities.java",
      "(Block)ObsidianNetwork.REACTOR_POWER_PORT.get()}));",
      "(Block)ObsidianNetwork.REACTOR_POWER_PORT.get(),\n"
      "                     (Block)ObsidianNetwork.REACTOR_NETWORK_PORT.get()}));")

patch("powerbank/PowerbankBlock.java","public enum Mode {CONTROLLER,INPUT,OUTPUT}",
      "public enum Mode {CONTROLLER,INPUT,OUTPUT,NETWORK}")
patch("powerbank/PowerbankBlock.java",
      " private static final MapCodec<PowerbankBlock> O=simpleCodec(p->new PowerbankBlock(p,Mode.OUTPUT));",
      " private static final MapCodec<PowerbankBlock> O=simpleCodec(p->new PowerbankBlock(p,Mode.OUTPUT));\n"
      " private static final MapCodec<PowerbankBlock> N=simpleCodec(p->new PowerbankBlock(p,Mode.NETWORK));")
patch("powerbank/PowerbankBlock.java",
      "case CONTROLLER->C;case INPUT->I;case OUTPUT->O;",
      "case CONTROLLER->C;case INPUT->I;case OUTPUT->O;case NETWORK->N;")
patch("powerbank/PowerbankBlockEntity.java",
      " private PowerbankBlockEntity controller(){",
      " public PowerbankBlockEntity xsxNetworkController(){return controller();}\n"
      " private PowerbankBlockEntity controller(){")
patch("powerbank/PowerbankGeometry.java",
      "||s.is(ObsidianNetwork.POWERBANK_OUTPUT.get());",
      "||s.is(ObsidianNetwork.POWERBANK_OUTPUT.get())\n"
      "   ||s.is(ObsidianNetwork.POWERBANK_NETWORK_PORT.get());")
patch("powerbank/PowerbankGeometry.java",
      "if(s.is(ObsidianNetwork.POWERBANK_OUTPUT.get())){outputs++;ports.add(p);}",
      "if(s.is(ObsidianNetwork.POWERBANK_OUTPUT.get())){outputs++;ports.add(p);}\n"
      "    if(s.is(ObsidianNetwork.POWERBANK_NETWORK_PORT.get()))ports.add(p);")
patch("registry/ModBlockEntities.java",
      "(Block)ObsidianNetwork.POWERBANK_OUTPUT.get()}));",
      "(Block)ObsidianNetwork.POWERBANK_OUTPUT.get(),\n"
      "                     (Block)ObsidianNetwork.POWERBANK_NETWORK_PORT.get()}));")
print("V176_REAL_MULTIBLOCK_NETWORK_PORTS_TWO_TYPES_REGISTERED")
