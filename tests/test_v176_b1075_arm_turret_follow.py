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
        self.assertIn("player.getYHeadRot()-player.yBodyRot",SRC)
        self.assertIn("Math.toRadians(player.getXRot())",SRC)
        self.assertIn("B1079_WORN_ARM_AIM_ANCHOR",SRC)
        self.assertIn("drawArm(pose,event.getSubmitNodeCollector()",SRC)
        self.assertIn("drawArm(post,nodes,light,",SRC)
        self.assertIn("TURRET_STAND_ID",SRC)
        self.assertIn("if(!(xsxEntity instanceof ArmorStand xsxStand)",SRC)
    def test_b1041_generated_stand_pose_anchor_matches_real_source(self):
        # CI B1075 previously failed because a comment separates try{ and
        # post.translate(...). Guard the real generated source, not a guess.
        b1041=(Path(__file__).resolve().parents[1]/
               "features/v176/apply-v176-b1041-player-stand-post-renderer.py").read_text()
        generated=b1041[b1041.index(" public static void submitFromPost("):]
        enter="  post.pushPose();\n  try{"
        shift="   post.translate(0.0F,1.5F,0.0F);"
        self.assertEqual(generated.count(enter),1)
        self.assertEqual(generated.count(shift),1)
        self.assertIn("// Post is in ArmorStand root-world pose",generated)
        self.assertIn('enter="  post.pushPose();\\n  try{"',SRC)
        self.assertIn("B1078_STAND_POST_RENDER_ANCHOR",SRC)
        self.assertNotIn("B1075_STAND_POST_ROOT",SRC)
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
    def test_clean_logout_and_no_cell_mutation(self):
        self.assertIn("@SubscribeEvent public static void logout",SRC)
        self.assertIn("PowerArmorRecallTickets.ticket",SRC)
        self.assertIn("B1075_CELL_TERMINAL_REGRESSION",SRC)
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
