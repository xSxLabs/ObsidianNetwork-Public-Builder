#!/usr/bin/env python3
"""B1096: 3P-only barrel mount + failure-safe entry/visibility contracts."""
import ast
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
G=R/"features/v176"
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
ENTRY=(G/"apply-v176-b1096-entry-visibility-recovery.py").read_text("utf-8")
GUN=(G/"apply-v176-b1096-3p-forearm-mount.py").read_text("utf-8")

class B1096FailedEntryAndPlayerMount(unittest.TestCase):
 def test_python_syntax(self):
  ast.parse(ENTRY)
  ast.parse(GUN)
 def test_failed_entry_restores_original_armorstand_not_a_copy(self):
  for token in (
    "B1096_ENTRY_ROLLBACK_VISIBILITY",
    "restoreFailedSuit1096(p,c.suit())",
    "restoreVisibility662(p)",
    "CLOSING.remove(id)",
    "stand.setInvisible(false)",
    "stand.removeTag(HIDE_TAG)",
    "stand.removeTag(OPEN_TAG)",
    "if(!owned(stand,p))return",
    "PowerArmorRuntime.full(p)",
    "PowerArmorSuitWorld.tryEnter(p,stand.getId())",
    "BEFORE_HIDE_662.put(id,p.isInvisible())",
    "if(!inside(p,stand))return",
    "if(!transitionStarted)",
    "Closing unfinished=CLOSING.remove(p.getUUID())",
    "Closing unfinished=CLOSING.remove(id)",
    "p.isInvisible() && v.isClosingFor659(p.getUUID())"
  ):
   self.assertIn(token,ENTRY,token)
  # Inspect only the Java code injected into the existing stand; the
  # generator itself intentionally contains a negative safety assertion.
  recovery=ENTRY.split('helper="""',1)[1].split('"""',1)[0]
  for forbidden in ("new ArmorStand(", "new ItemStack(", "stand.discard()",
                    "PlayerInventory.add", "stand.noPhysics=false"):
   self.assertNotIn(forbidden,recovery)
 def test_thirdperson_only_no_turret_or_first_person_changes(self):
  self.assertIn("B1096_PLAYER_ONLY_FOREARM_CONTACT",GUN)
  self.assertIn("pose.translate(0.0F,0.065F,0.0F);",GUN)
  self.assertIn("wornFallback(",GUN)
  self.assertIn("drawArm(pose,event.getSubmitNodeCollector()",GUN)
  self.assertIn("B1093_WORLD_GUN_ARM_CONTACT",GUN)
  self.assertNotIn("suit.setRightArmPose(",GUN)
  self.assertNotIn("nodes.submitModelPart(BARREL,pose,",GUN)
 def test_full_pipeline_applies_after_prior_fixes(self):
  self.assertLess(W.index("python3 features/v176/apply-v176-b1093-world-gun-arm-contact.py"),
                  W.index("python3 features/v176/apply-v176-b1096-3p-forearm-mount.py"))
  # B1105: 1.7.5 manual walk-in is known good; B1096 entry injection broke it.
  # Retain the B1096 PLAYER weapon mount, but forbid the independent B1096
  # ENTRY overlay from running after the frozen v1.7.5 entry source.
  self.assertNotIn("python3 features/v176/apply-v176-b1096-entry-visibility-recovery.py", W)
  self.assertNotIn("python3 features/v176/apply-v176-b1102-critical-entry.py", W)
  self.assertLess(W.index("python3 tests/verify_v175_b662.py"),
                  W.index("python3 tests/verify_v176_exact_v175_entry.py"))
  self.assertIn("python3 features/v176/apply-v176-b1096-3p-forearm-mount.py", W)
  self.assertIn("python3 features/v176/apply-v176-b1103-all-mk-gametest.py", W)
  self.assertIn("contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')",W)
  self.assertIn("group: clean-v1.7-${{ github.ref }}",W)
  self.assertIn("cancel-in-progress: true",W)
  self.assertIn("xsxlabs-network-storage-v1.7.6-test-jar",W)
if __name__ == "__main__":unittest.main()
