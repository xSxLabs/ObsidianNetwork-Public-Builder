#!/usr/bin/env python3
"""v1.7.7: Attack Mode manual Micro-MG bullets fly farther and deal double damage.

Only explicit player-fired projectiles are tuned. Automatic companion/turret
bullets still expire after eight ticks and use the original hit damage.
No changes to FE/shot, fire rate, targeting, collisions or loot ownership.
"""
import os
from pathlib import Path

ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(path,old,new):
 file=ROOT/path
 source=file.read_text(encoding="utf-8")
 assert source.count(old)==1,("V177_MICRO_MG_EXTENDED_SOURCE_DRIFT",path,source.count(old),old[:100])
 file.write_text(source.replace(old,new,1),encoding="utf-8")

# Mark only shots created by an actual manual /powerarmor fire request. A
# companion's automated shot never receives this server-side marker.
patch("powerarmor/V176MicroMgFire.java",
 '''  shot.setOwner(p);
  shot.setPos(origin.x,origin.y,origin.z);''',
 '''  shot.setOwner(p);
  shot.addTag("xsxlabs_v177_attack_mode_bullet");
  shot.setPos(origin.x,origin.y,origin.z);''')

# Base rules remain at 4 HP and 8 ticks for turret/automatic bullets.
# Use real server-owned entity-tag metadata so manual bullets keep 48 ticks
# after loading from disk as well as on the original spawn tick.
patch("powerarmor/V176MicroMgProjectile.java",
 '''    living.hurtServer(server,damageSources().thrown(this,owner),V176MicroMgRules.DAMAGE_HP);''',
 '''    // Double damage ONLY for manual Attack Mode shots: 4 HP -> 8 HP.
    float damage=entityTags().contains("xsxlabs_v177_attack_mode_bullet")
        ?V176MicroMgRules.DAMAGE_HP*2.0F:V176MicroMgRules.DAMAGE_HP;
    living.hurtServer(server,damageSources().thrown(this,owner),damage);''')

patch("powerarmor/V176MicroMgProjectile.java",
 '''  }else if(tickCount>8)discard(); // 3 blocks/tick, max ~24 blocks''',
 '''  }else if(tickCount>(entityTags().contains("xsxlabs_v177_attack_mode_bullet")?48:8))
   discard(); // manual ~100-120 blocks (48 ticks), automatic unchanged at 8 ticks''')

print("V177_ATTACK_MODE_BULLETS_48_TICKS_DOUBLE_8_HP_TURRET_UNCHANGED_PASS")
