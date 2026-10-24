#!/usr/bin/env python3
"""Build104 forcefield/energy regression gates, Java compiled by GitHub Actions."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-energy-shield-104.py").read_text(encoding="utf-8")
CARDS=(ROOT/"features/v17/apply-power-armor-cards.py").read_text(encoding="utf-8")
DISKS=(ROOT/"features/v17/apply-power-armor-freestanding.py").read_text(encoding="utf-8")
COST=(ROOT/"features/v17/apply-power-armor-expensive-recipes-103.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Shield104(unittest.TestCase):
 def test_valid_python(self):
  for code in (PATCH,CARDS,DISKS,COST):ast.parse(code)
 def test_real_card_and_own_sprite(self):
  self.assertIn('"network_elytra","energy_shield"]',CARDS)
  self.assertIn('"energy_shield":"obsidiannetwork:advanced_energy_cell"',CARDS)
  self.assertIn('"energy_shield":(',DISKS)
  self.assertIn('assert len(icons)==26',DISKS)
  self.assertIn('assert len(palettes)==len(icons)==26',DISKS)
  self.assertIn('"energy_shield":"obsidiannetwork:advanced_energy_cell"',COST)
  self.assertIn('assert len(card_signatures)==24',COST)
 def test_no_free_invulnerability_or_duplication(self):
  for key in (
   'PowerArmorRuntime.powered(p)',
   'PowerArmorRuntime.hasCard(p,"energy_shield")',
   'ABSORB_FRACTION=0.60F',
   'HIT_BASE_COST=20_000L',
   'FE_PER_DAMAGE_ABSORBED=10_000.0D',
   'EventPriority.LOWEST',
   'DamageTypeTags.BYPASSES_INVULNERABILITY',
   'EnergyTool.energy(p.getItemBySlot(slot))<perPart+20L',
   'EnergyTool.consume(p.getItemBySlot(slot),perPart)',
   'event.setNewDamage(remaining-absorbed)',
   'for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)',
  ):self.assertIn(key,PATCH)
  self.assertNotIn('event.setNewDamage(0F)',PATCH)
  self.assertNotIn('ItemStack.EMPTY',PATCH)
  self.assertNotIn('ArmorLoadoutData',PATCH)
 def test_visuals_power_and_hurt_flash(self):
  for key in (
   'DustParticleOptions(0x5bbfe8,0.53F)',
   'DustParticleOptions(0x8debff,0.95F)',
   'if(wearer.tickCount%3!=0||!hasActiveShield(wearer))continue;',
   'if(wearer.hurtTime>=8)',
   'ServerLevel world=p.serverLevel()',
   'world.sendParticles(ParticleTypes.END_ROD',
   'if(++drawn>12)break;',
   'if(tier<1||tier>24)return false;',
  ):self.assertIn(key,PATCH)
 def test_workflow_and_disabled_old_cards(self):
  self.assertIn('python3 features/v17/apply-power-armor-energy-shield-104.py',WF)
  self.assertIn('BUILD104_96_ARMOR_24_UPGRADE_RECIPES PASS',WF)
  self.assertIn('if obsolete.exists():obsolete.unlink()',COST)
if __name__=="__main__":unittest.main()
