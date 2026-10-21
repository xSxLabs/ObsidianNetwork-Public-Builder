#!/usr/bin/env python3
"""Build 378: fail-closed synthetic patch and exact per-player check scope."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/wireless-energy/apply-network-elytra-speedcheck.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.6.yml"

def run_patch(folder,drift=False):
    j=Path(folder)/"java/dev/obsidiannetwork"
    resources=Path(folder)/"resources"
    for name,code in (
        ("item/NetworkElytraItem.java",
         "BOOST_MAX_SPEED = 2.4D\nSHIFT_COST_PER_5_TICKS = 1500L\n"
         "FLIGHT_COST_PER_5_TICKS = 125L\nXSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1\n"),
        ("wireless/NetworkElytraCurios.java","CuriosApi.getCuriosInventory(player)\n"),
        ("mixin/NetworkElytraCuriosGlideMixin.java","XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1\n")
    ):
        p=j/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(code)
    mix=resources/"obsidiannetwork.mixins.json"
    mix.parent.mkdir(parents=True,exist_ok=True)
    init={"package":"dev.obsidiannetwork.mixin",
          "mixins":["ExistingMixin","NetworkElytraCuriosGlideMixin"]}
    if drift:init["mixins"].remove("NetworkElytraCuriosGlideMixin")
    mix.write_text(json.dumps(init)+"\n")
    env={**os.environ,"V1_SOURCE_ROOT":str(Path(folder)/"java"),
         "V1_RESOURCE_ROOT":str(resources)}
    result=subprocess.run([sys.executable,str(PATCH)],env=env,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return result,j,mix

class NetworkElytraSpeedCheckTests(unittest.TestCase):
    def test_hook_compiles_as_server_only_mixin_without_changing_flight_math(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,j,mix=run_patch(tmp)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            generated=(j/"mixin/NetworkElytraSpeedCheckMixin.java").read_text()
            data=json.loads(mix.read_text())
            self.assertEqual(data["mixins"],
                             ["ExistingMixin","NetworkElytraCuriosGlideMixin",
                              "NetworkElytraSpeedCheckMixin"])
            for part in ("@Mixin(ServerGamePacketListenerImpl.class)",
                         '@Inject(method="shouldCheckPlayerMovement"',
                         "if (!isFallFlying || !result.getReturnValueZ()) return;",
                         "p.isFallFlying()","p.onGround()",
                         "p.getItemBySlot(EquipmentSlot.CHEST)",
                         'ModList.get().isLoaded("curios")',
                         "NetworkElytraCurios.find(p)",
                         "instanceof NetworkElytraItem",
                         "EnergyTool.energy(wing) < NetworkElytraItem.FLIGHT_COST_PER_5_TICKS",
                         "Double.isFinite(motion.x)","motion.lengthSqr() > 6.76D",
                         "result.setReturnValue(false);",
                         "require=1"):
                self.assertIn(part,generated)
            self.assertNotIn(".getGameRules()",generated)
            self.assertNotIn("GameRules.",generated)
            self.assertNotIn("setDeltaMovement(",generated)
            self.assertEqual((j/"item/NetworkElytraItem.java").read_text().count(
                "BOOST_MAX_SPEED = 2.4D"),1)

    def test_missing_old_flight_guard_aborts_without_creating_mixin(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,j,mix=run_patch(tmp,drift=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((j/"mixin/NetworkElytraSpeedCheckMixin.java").exists())
            self.assertNotIn("NetworkElytraSpeedCheckMixin",mix.read_text())

    def test_vanilla_gate_scope_truth_table(self):
        # Mirrors ONLY the gating booleans; real Minecraft startup + Curios
        # GameTests and compiled-JAR verifier remain mandatory in CI.
        def bypass(elytra_check,vanilla_check,flying,grounded,wing,energy,speed):
            return (elytra_check and vanilla_check and flying and not grounded
                    and wing and energy>=125 and 0<=speed<=2.6)
        for kind in ("no_wing","ordinary_elytra","empty_network_wing","landed",
                     "not_flying","not_elytra_check","vanilla_already_false",
                     "impossible_velocity"):
            values={
                "elytra_check":True,"vanilla_check":True,"flying":True,
                "grounded":False,"wing":True,"energy":125,"speed":2.4}
            if kind=="no_wing" or kind=="ordinary_elytra": values["wing"]=False
            if kind=="empty_network_wing":values["energy"]=0
            if kind=="landed": values["grounded"]=True
            if kind=="not_flying":values["flying"]=False
            if kind=="not_elytra_check":values["elytra_check"]=False
            if kind=="vanilla_already_false":values["vanilla_check"]=False
            if kind=="impossible_velocity":values["speed"]=3.0
            self.assertFalse(bypass(**values),kind)
        self.assertTrue(bypass(True,True,True,False,True,125,2.4))

    def test_workflow_orders_mixin_after_existing_ground_guard(self):
        wf=WORKFLOW.read_text()
        self.assertEqual(wf.count("python3 features/wireless-energy/apply-network-elytra-speedcheck.py"),1)
        self.assertLess(wf.index("python3 features/wireless-energy/apply-network-elytra-landing.py"),
                        wf.index("python3 features/wireless-energy/apply-network-elytra-speedcheck.py"))
        self.assertIn("tests/verify_compiled_network_elytra_speedcheck.py",wf)

if __name__=="__main__":
    unittest.main()
