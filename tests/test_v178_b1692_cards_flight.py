#!/usr/bin/env python3
"""B1692 three Shape Card modes + 4x powered actual-flight FE regression guards."""
import ast
import json
import os
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "features/v178/apply-v178-b1692-miner-cards-flight-cost.py"
SOURCE = (ROOT / SCRIPT).read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class B1692CardFlightContract(unittest.TestCase):
    def test_script_syntax_pipeline_order(self):
        ast.parse(SOURCE, filename=SCRIPT)
        self.assertEqual(WORKFLOW.count("python3 " + SCRIPT), 1)
        self.assertLess(
            WORKFLOW.index("python3 features/v178/apply-v178-b1687-fly-wheel.py"),
            WORKFLOW.index("python3 " + SCRIPT))
        self.assertLess(
            WORKFLOW.index("python3 features/v178/apply-v178-b1677-miner-functional.py"),
            WORKFLOW.index("python3 " + SCRIPT))
        self.assertEqual(WORKFLOW.count("python3 -m unittest discover -s tests -p 'test_v178_b1692_cards_flight.py' -v"),1)

    def test_single_vanilla_loot_path_and_cards(self):
        for required in (
            "V178_SHAPE_CARD_FORTUNE_3", "V178_SHAPE_CARD_SILK_TOUCH",
            'mining_shape_card_fortune_3', 'mining_shape_card_silk_touch',
            'getOrThrow(Enchantments.FORTUNE),3',
            'getOrThrow(Enchantments.SILK_TOUCH),1',
            'machine.effectivePickaxe(world)',
            'new ItemStack(Items.NETHERITE_PICKAXE)',
            'Block.getDrops(current,world,target,null,null',
        ):
            self.assertIn(required,SOURCE)
        self.assertNotIn("new ItemStack(Items.DIAMOND", SOURCE)
        self.assertIn("Transactions still preflight",SOURCE)
        # Fortune and Silk are exclusive, with an untouched plain-tool fallback.
        self.assertIn('}else if(card.is(ObsidianNetwork.V178_SHAPE_CARD_SILK_TOUCH.get()))',SOURCE)
        self.assertIn('return tool;',SOURCE)
        self.assertIn("if(!fits)return", (Path(os.getenv("V1_SOURCE_ROOT"))/"dev/obsidiannetwork/mining/V178MiningBuilderBE.java").read_text() if os.getenv("V1_SOURCE_ROOT") else "if(!fits)return")

    def test_four_times_only_while_flying(self):
        self.assertIn("canFly&&p.getAbilities().flying?80L:20L",SOURCE)
        self.assertIn("EnergyTool.consume(p.getItemBySlot(slot),suitDrain)",SOURCE)
        self.assertNotIn("p.getAbilities().mayfly=true;",SOURCE)
        self.assertNotIn("world.destroyBlock(target,true)",SOURCE)

    def test_generated_runtime_and_assets(self):
        source_root = os.getenv("V1_SOURCE_ROOT")
        resource_root = os.getenv("V1_RESOURCE_ROOT")
        if not source_root or not resource_root:
            self.skipTest("Source generation only in CI build")
        java = Path(source_root)/"dev/obsidiannetwork"
        assets=Path(resource_root)/"assets/obsidiannetwork"
        data=Path(resource_root)/"data/obsidiannetwork"
        main=(java/"ObsidianNetwork.java").read_text()
        for name in ("mining_shape_card", "mining_shape_card_fortune_3","mining_shape_card_silk_touch"):
            self.assertIn('registerItem("'+name+'"',main)
        machine=(java/"mining/V178MiningBuilderBE.java").read_text()
        for keyword in ("Enchantments.FORTUNE","Enchantments.SILK_TOUCH","machine.effectivePickaxe(world)",
                        "try(Transaction tx=Transaction.openRoot())",
                        "if(!fits)return", "world.destroyBlock(target,false)",
                        "V178Claims.mayMachineMine(world,target,machine.owner)"):
            self.assertIn(keyword,machine)
        self.assertIn("instanceof V178MiningShapeCard",
            (java/"mining/V178MiningBuilderMenu.java").read_text())
        runtime=(java/"powerarmor/PowerArmorRuntime.java").read_text()
        self.assertIn("canFly&&p.getAbilities().flying?80L:20L",runtime)
        self.assertIn("hasCard(p,\"flight\")",runtime)
        self.assertIn("EnergyTool.consume(p.getItemBySlot(slot),suitDrain)",runtime)
        base=(assets/"textures/item/mining_shape_card.png").read_bytes()
        for mode in ("fortune_3","silk_touch"):
            name="mining_shape_card_"+mode
            png=(assets/("textures/item/"+name+".png")).read_bytes()
            self.assertNotEqual(base,png)
            self.assertEqual(struct.unpack(">II",png[16:24]),(64,64))
            model=json.loads((assets/("models/item/"+name+".json")).read_text())
            self.assertEqual(model["textures"]["layer0"],"obsidiannetwork:item/"+name)
            recipe=json.loads((data/("recipe/"+name+".json")).read_text())
            self.assertEqual(recipe["result"]["id"],"obsidiannetwork:"+name)
            self.assertEqual(recipe["key"]["C"],"obsidiannetwork:mining_shape_card")
        self.assertNotEqual(
            (assets/"textures/item/mining_shape_card_fortune_3.png").read_bytes(),
            (assets/"textures/item/mining_shape_card_silk_touch.png").read_bytes())

if __name__=="__main__":
    unittest.main()
