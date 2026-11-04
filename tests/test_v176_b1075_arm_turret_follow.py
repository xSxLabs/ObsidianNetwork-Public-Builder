#!/usr/bin/env python3
"""B1075 fail-closed generator contracts. Minecraft compile/GameTests run in CI."""
import ast
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-b1075-arm-turret-long-range.py"
SRC=P.read_text(encoding="utf-8")

class B1075CompanionAndWorldGun(unittest.TestCase):
    def test_generator_is_valid_python(self):
        ast.parse(SRC)
    def test_only_companion_and_world_weapon_files_changed(self):
        for forbidden in ("cellterminal/", "StorageDriveBlockEntity.java",
                          "V176CellTerminalMenu.java","V176MicroMgFire.java",
                          "V176MicroMgProjectile.java","PowerArmorRecall.java"):
            self.assertNotIn(forbidden,SRC)
    def test_body_yaw_applied_before_arm_parent_pivot(self):
        self.assertIn("180.0F-player.yBodyRot",SRC)
        self.assertIn("180.0F-xsxStand.getYRot()",SRC)
        self.assertIn("drawArm(pose,event.getSubmitNodeCollector()",SRC)
        self.assertIn("drawArm(post,nodes,light,",SRC)
        self.assertIn("TURRET_STAND_ID",SRC)
        self.assertIn("if(!(xsxEntity instanceof ArmorStand xsxStand)",SRC)
    def test_remote_authorization_and_chunk_tickets(self):
        for word in ("PowerArmorRecallIndex.get(", "PowerArmorRecallTickets.ticket(",
                     "PowerArmorRecallPreference.get(", "owned(suit,owner)",
                     "PowerArmorSuitWorld.full(suit)", "if(matches.isEmpty())return null",
                     "if(!ticket&&!src.hasChunkAt(at))"):
            self.assertIn(word,SRC)
    def test_grounded_follow_and_follow_priority(self):
        for word in ("Heightmap.Types.MOTION_BLOCKING_NO_LEAVES",
                     "world.noCollision", "setNoGravity(false)",
                     "Vec3.atBottomCenterOf", "teleportToGroundNear",
                     "V176CompanionLongRange.horizontalSq(suit,player)",
                     "player.getDeltaMovement().lengthSqr()>0.0025D",
                     "if(player.tickCount%5==0)V176CompanionLongRange.tick(player);"):
            self.assertIn(word,SRC)
    def test_no_duplicate_entity_or_itemstacks(self):
        for forbidden in ("new ArmorStand(", "new ItemStack(", "suit.discard()",
                          "stand.discard()", "PowerArmorSuitWorld.recallEquip("):
            self.assertNotIn(forbidden,SRC)
    def test_gunmetal_not_tier_armor_texture_modified(self):
        self.assertIn("textures/entity/micro_mg_world_barrel.png",SRC)
        self.assertIn("im.save(gun,optimize=True)",SRC)
        self.assertNotIn("micro_mg_mk",SRC)

if __name__=="__main__":
    unittest.main()
