#!/usr/bin/env python3
"""v1.7.4 B437: bounded, client-side-only particles on operating multiblocks.

Particles originate from one controller per multiblock (not every fuel rod or
casing) and depend on live BE data. No changes to tick rates or transport.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def change(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V174_B437_ANIMATION_DRIFT",rel,s.count(old),old[:75])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
change("reactor/ReactorControllerBlock.java",
 ' private InteractionResult open(Level world,BlockPos p,Player player){',
 r''' // V174_REACTOR_BOUNDED_ANIMATION_437: controller-only; maximum one
 // client particle on an animation callback, even on a 64x64x64 reactor.
 @Override public void animateTick(BlockState state,Level level,BlockPos pos,
     net.minecraft.util.RandomSource rand){
  if(rand.nextInt(6)!=0)return;
  if(!(level.getBlockEntity(pos) instanceof ReactorControllerBlockEntity reactor))return;
  if(reactor.guiFuelTicks()<=0||reactor.guiWater()<20||reactor.guiRodAssemblies()<=0)return;
  level.addParticle(net.minecraft.core.particles.ParticleTypes.END_ROD,
      pos.getX()+.2+.6*rand.nextDouble(),
      pos.getY()+.96,
      pos.getZ()+.2+.6*rand.nextDouble(),
      0,.012,0);
 }
 private InteractionResult open(Level world,BlockPos p,Player player){''')
change("powerbank/PowerbankBlock.java",
 ' private InteractionResult access(Level level,BlockPos p,Player user){',
 r''' // V174_POWERBANK_BOUNDED_ANIMATION_437: no FX on each casing or port.
 @Override public void animateTick(BlockState state,Level world,BlockPos pos,
     net.minecraft.util.RandomSource rand){
  if(mode!=Mode.CONTROLLER||rand.nextInt(9)!=0)return;
  if(!(world.getBlockEntity(pos) instanceof PowerbankBlockEntity bank)||bank.guiEnergy()<=0L)return;
  world.addParticle(net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK,
      pos.getX()+.15+.7*rand.nextDouble(),
      pos.getY()+.9,
      pos.getZ()+.15+.7*rand.nextDouble(),
      0,.007,0);
 }
 private InteractionResult access(Level level,BlockPos p,Player user){''')
change("pump/ElectricWaterPumpBlock.java",
 ' private InteractionResult open(Level l,BlockPos pos,Player user){',
 r''' // V174_PUMP_BOUNDED_ANIMATION_437: one gentle droplet, not a block scan.
 @Override public void animateTick(BlockState s,Level l,BlockPos pos,
     net.minecraft.util.RandomSource rand){
  if(rand.nextInt(9)!=0)return;
  if(!(l.getBlockEntity(pos) instanceof ElectricWaterPumpBlockEntity be)
      ||be.guiEnergy()<200L||be.guiWater()<=0)return;
  l.addParticle(net.minecraft.core.particles.ParticleTypes.SPLASH,
      pos.getX()+.2+.6*rand.nextDouble(),pos.getY()+.92,
      pos.getZ()+.2+.6*rand.nextDouble(),0,.012,0);
 }
 private InteractionResult open(Level l,BlockPos pos,Player user){''')
print("V174_MULTIBLOCK_ANIMATIONS_437_PASS: bounded controller-only particles; no server FX")
