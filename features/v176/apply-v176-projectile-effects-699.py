#!/usr/bin/env python3
"""v1.7.6 B699: synchronized projectile trail and actual block/entity sparks.

No hitscan, no fake arrows, no block destruction; particles follow real
24-block server-owned bullet and expire with it.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
path=J/"powerarmor/V176MicroMgProjectile.java"
s=path.read_text(encoding="utf-8")
def edit(old,new):
 global s
 assert s.count(old)==1,("V176_B699_SOURCE_DRIFT",s.count(old),old[:100])
 s=s.replace(old,new,1)

edit('import net.minecraft.server.level.ServerLevel;',
     'import net.minecraft.server.level.ServerLevel;\nimport net.minecraft.core.particles.ParticleTypes;')
edit('''   discard();
  }
 }
 @Override protected void onHitBlock(BlockHitResult hit){''',
 '''   server.sendParticles(ParticleTypes.CRIT,hit.getLocation().x,
      hit.getLocation().y,hit.getLocation().z,4,0.04,0.04,0.04,0.05);
   discard();
  }
 }
 @Override protected void onHitBlock(BlockHitResult hit){''')
edit('''  if(!level().isClientSide())discard();
 }
 @Override public void tick(){''',
 '''  if(level() instanceof ServerLevel server){
   server.sendParticles(ParticleTypes.CRIT,hit.getLocation().x,
      hit.getLocation().y,hit.getLocation().z,3,0.035,0.035,0.035,0.03);
   discard();
  }
 }
 @Override public void tick(){''')
edit('''  super.tick();
  if(!level().isClientSide()&&tickCount>8)discard(); // 3 blocks/tick, max ~24 blocks''',
 '''  super.tick();
  if(level().isClientSide()){
   // Short moving tracer is anchored to the SYNCHRONIZED real entity.
   level().addParticle(ParticleTypes.END_ROD,getX(),getY(),getZ(),0,0,0);
  }else if(tickCount>8)discard(); // 3 blocks/tick, max ~24 blocks''')
path.write_text(s,encoding="utf-8")
assert s.count('sendParticles(ParticleTypes.CRIT')==2
assert 'level().addParticle(ParticleTypes.END_ROD,getX(),getY(),getZ(),0,0,0);' in s
print("V176_B699_REAL_BULLET_TRACERS_AND_IMPACT_SPARKS_PASS")
