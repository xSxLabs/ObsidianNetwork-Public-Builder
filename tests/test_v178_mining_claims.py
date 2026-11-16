#!/usr/bin/env python3
"""B1618 tests: chunk ownership, mining builder and non-regression contracts."""
import ast, os, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
C=(R/"features/v178/apply-v178-claims.py").read_text()
M=(R/"features/v178/apply-v178-mining-builder.py").read_text()
class V178ClaimsMining(unittest.TestCase):
 def test_prior_green_baseline_unchanged(self):
  for f in ("apply-v177-jarvis-voice.py","apply-v177-armor-station-docked-refill.py",
            "apply-v177-backpack-builder-supply-performance.py",
            "apply-v178-jei-terminal-session.py","apply-v178-global-perf.py"):
   self.assertIn(f,W)
  for f in ("apply-v178-claims.py","apply-v178-mining-builder.py"):
   self.assertIn("python3 features/v178/"+f,W)
  self.assertLess(W.index("apply-v178-global-perf.py"),W.index("apply-v178-claims.py"))
  self.assertLess(W.index("apply-v178-claims.py"),W.index("apply-v178-mining-builder.py"))
 def test_python_and_claims_protocol(self):
  for s in (C,M):ast.parse(s)
  for t in ("RegisterTicketControllersEvent","TICKETS.forceChunk(level","dirty=true",
            "autosave(ServerTickEvent.Post","V178ClaimsRequest","playToServer(TYPE,CODEC",
            "sendToServer(new dev.obsidiannetwork.claims.V178ClaimsRequest",
            "mouseClicked(net.minecraft.client.input.MouseButtonEvent",
            "getPlayerOrException()","readByteArray(625)","MAX_LOADED","MAX_CLAIMS",
            "REQUEST_TICKS","StandardCopyOption.ATOMIC_MOVE"):
   self.assertIn(t,C)
  self.assertNotIn('sendCommand("xsxchunks view',C)
  self.assertNotIn("mouseClicked(double mx,double my,int button)",C)
  self.assertIn("breakBlock(BreakBlockEvent event)",C)
  self.assertIn("net.neoforged.neoforge.event.level.block.BreakBlockEvent",C)
  self.assertIn("ClientPacketDistributor.sendToServer",C)
  self.assertNotIn("BlockEvent.BreakEvent",C)
  self.assertNotIn("net.neoforged.neoforge.network.PacketDistributor.sendToServer",C)
  self.assertIn("REQUEST_CENTERS",C)
 def test_explosion_and_piston_claim_border_protection(self):
  self.assertIn("protectExplosion(ExplosionEvent.Detonate event)",C)
  self.assertIn("import net.neoforged.neoforge.event.level.PistonEvent;",C)
  self.assertNotIn("BlockEvent.PistonEvent",C)
  self.assertIn("event.getAffectedBlocks().removeIf",C)
  self.assertIn("claims.containsKey(key(pos.getX()>>4,pos.getZ()>>4))",C)
  self.assertIn("protectPiston(PistonEvent.Pre event)",C)
  self.assertIn("piston.relative(event.getDirection())",C)
  self.assertIn("event.setCanceled(true);",C)
  self.assertNotIn("getChunk(",C[C.index(" // B1643:"):C.index(" private static void tell(")])
  if os.environ.get("V1_SOURCE_ROOT"):
   generated=(Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/claims/V178Claims.java").read_text()
   self.assertIn("protectExplosion(ExplosionEvent.Detonate event)",generated)
   self.assertIn("protectPiston(PistonEvent.Pre event)",generated)
 def test_mining_resources_and_lag_bounds(self):
  for t in ("MAX_VISITS=8","MAX_BREAKS=2","GLOBAL_BLOCK_BUDGET",
            "if(!world.hasChunkAt(target))return",
            "machine.owner.equals(V178Claims.owner(world,target))",
            "Transaction.openRoot()","tx.commit()","getAmountAsLong()",
            "mining_shape_card","mining_builder","preRemoveSideEffects",
            "ENERGY_PER_BLOCK=2000","CombinedResourceHandler"):
   self.assertIn(t,M)
  self.assertNotIn("loadChunk(",M)
 def test_build_generated_classes(self):
  if not os.environ.get("V1_SOURCE_ROOT"):return
  base=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
  for f in ("claims/V178Claims.java","claims/V178ClaimsRequest.java",
            "claims/V178ClaimsSnapshot.java","client/V178ClaimsClient.java",
            "client/V178ClaimsMapScreen.java",
            "mining/V178MiningBuilderBE.java","mining/V178MiningShapeCard.java",
            "mining/V178MiningBuilderBlock.java","mining/V178MiningBuilderCapabilities.java"):
   self.assertTrue((base/f).exists(),f)
  self.assertIn("machine.owner.equals(V178Claims.owner",
      (base/"mining/V178MiningBuilderBE.java").read_text())
if __name__=="__main__":unittest.main()
