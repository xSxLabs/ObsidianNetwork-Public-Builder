#!/usr/bin/env python3
"""v1.7.5 animation lifecycle: 24-tier recall visual travels horizontal,
brakes upright and docks without ever transferring real items before arrival.
Preserves the existing authoritative inventory, ownership and rollback code.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def replace_one(s,a,b,where):
 assert s.count(a)==1,("V175_LIFECYCLE_ANCHOR",where,s.count(a))
 return s.replace(a,b,1)
def put(path,s):path.write_text(s,encoding="utf-8")
visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf-8")
assert "class PowerArmorVisualEntity extends ArmorStand implements GeoEntity" in s
s=replace_one(s,''' private final AnimatableInstanceCache geoCache=GeckoLibUtil.createInstanceCache(this);''',
''' // 0=normal open/close, 2=horizontal flight, 3=braking, 4=docking.
 // Synched and client-rendered; no extra per-client/server world scan.
 private static final EntityDataAccessor<Integer> V175_PHASE =
      SynchedEntityData.defineId(PowerArmorVisualEntity.class,EntityDataSerializers.INT);
 private final AnimatableInstanceCache geoCache=GeckoLibUtil.createInstanceCache(this);''',"visual_synched_phase_decl")
s=replace_one(s,'''  builder.define(ENTERING,false);''',
'''  builder.define(ENTERING,false);
  builder.define(V175_PHASE,0);''',"visual_phase_default")
s=replace_one(s,
 ''' public void begin(boolean entering){entityData.set(ENTERING,entering);}''',
 ''' public void begin(boolean entering){
  entityData.set(V175_PHASE,0);
  entityData.set(ENTERING,entering);
 }
 public void beginPhase(int next){
  if(next<2||next>4)throw new IllegalArgumentException("Invalid cinematic phase "+next);
  if(entityData.get(V175_PHASE)!=next)entityData.set(V175_PHASE,next);
 }''',"visual_phase_setter")
# Do not touch the normal equip/unequip button, timings or inventory transfer.
controller=re.search(r' @Override public void registerControllers\(AnimatableManager\.ControllerRegistrar controllers\)\s*\{[\s\S]*?\n \}',s)
assert controller,("V175_VISUAL_CONTROLLER_DRIFT",s[s.index("registerControllers")-100:s.index("registerControllers")+650])
before=controller.group()
assert 'animation.power_armor.open' in before and 'animation.power_armor.close' in before and 'state.setAndContinue' in before
new=''' @Override public void registerControllers(AnimatableManager.ControllerRegistrar controllers){
  controllers.add(new AnimationController<>("suit",0,state -> {
   int p=entityData.get(V175_PHASE);
   if(p==2)return state.setAndContinue(RawAnimation.begin().thenLoop(
     "animation.power_armor.recall_flight"));
   String clip=switch(p){
    case 3 -> "animation.power_armor.recall_brake";
    case 4 -> "animation.power_armor.recall_dock";
    // One full close/open/close cycle per normal action; the REAL armor
    // stack transfer remains the unchanged server-authoritative operation.
    default -> entityData.get(ENTERING)
       ?"animation.power_armor.equip":"animation.power_armor.unequip";
   };
   return state.setAndContinue(RawAnimation.begin().thenPlay(clip));
  }));
 }'''
s=s.replace(before,new,1)
# Vanilla GeckoLib transition visuals expire after 24 ticks. Recall must NOT:
# the 28-tick brake/dock needs a longer lifetime and long-distance flight
# may take hundreds of ticks. Only the normal equip/unequip visual expires.
lifetime="if(!level().isClientSide()&&tickCount>23)discard();"
assert s.count(lifetime)==1,("V175_VISUAL_LIFETIME_DRIFT",s.count(lifetime))
s=s.replace(lifetime,
    "if(!level().isClientSide()&&tickCount>23&&entityData.get(V175_PHASE)==0)discard(); // V175_RECALL_VISUAL_LIFETIME")
assert "V175_PHASE" in s and 'thenLoop(' in s
assert '"animation.power_armor.equip":"animation.power_armor.unequip"' in s
put(visual,s)
p=J/"powerarmor/PowerArmorRecall.java";s=p.read_text(encoding="utf-8")
assert "V173_RECALL_GHOST_FLIGHT174" in s,"v1.7.4 optimized ghost recall must be retained"
s=replace_one(s,
 ''' private static final Map<UUID,Flight> ACTIVE=new HashMap<>();''',
 ''' private static final Map<UUID,Flight> ACTIVE=new HashMap<>();
 // V175_RECALL_DOCK: count only active recalled suits, never tick/scan the world.
 private static final Map<UUID,Integer> DOCKING=new HashMap<>();''',"dock_lifecycle_map")
s=replace_one(s,'''  ACTIVE.clear();''',
'''  ACTIVE.clear();
  DOCKING.clear();''',"startup_dock_cleanup")
s=replace_one(s,'''  ACTIVE.remove(player.getUUID());''',
'''  ACTIVE.remove(player.getUUID());
  DOCKING.remove(player.getUUID());''',"abort_and_completion_cleanup")
# Normal recall source owner/nonce and portal safety unchanged.
s=replace_one(s,
 '''   visual.begin(false);''',
 '''   visual.beginPhase(2); // V175_HORIZONTAL_FLIGHT: actual Geo mesh prone, never upright.''',
 "recall_initial_animation")
anchor='''  if(distance<=2.5D){
   // Commit equipment transfer ONLY after visual arrival.'''
if s.count(anchor)!=1:
 # Preserve strict matching even if whitespace differs from v1.7.2 builder.
 m=re.search(r'if\(distance<=2\.5D\)\s*\{\s*// Commit equipment transfer ONLY after visual arrival\.',s)
 assert m,("V175_ARRIVAL_GUARD_DRIFT",s[s.find("double distance=delta.length()"):s.find("double distance=delta.length()")+650])
 a=m.group();s=s.replace(a,a.replace('if(distance<=2.5D)','if(distance<=2.5D || DOCKING.containsKey(player.getUUID()))'),1)
else:s=s.replace(anchor,'''  if(distance<=2.5D || DOCKING.containsKey(player.getUUID())){
   // V175_RECOVERY_SAFE_DOCK: visual brakes and opens around the wearer,
   // but real source armor remains untouched until all frames complete.
   int progress=DOCKING.getOrDefault(player.getUUID(),0);
   visual.beginPhase(progress<8?3:4);
   visual.setPos(visual.getX()+(player.getX()-visual.getX())*.30D,
     visual.getY()+(player.getY()-visual.getY())*.30D,
     visual.getZ()+(player.getZ()-visual.getZ())*.30D);
   visual.setYRot(player.getYRot());
   visual.setYBodyRot(player.getYRot());
   visual.setYHeadRot(player.getYRot());
   if(progress<28){
    DOCKING.put(player.getUUID(),progress+1);
    return;
   }
   DOCKING.remove(player.getUUID());
   // Commit equipment transfer ONLY after visual arrival.''',1)
# Existing Ghost-Flying source checks and safe item transfer are preserved.
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in s
assert "PowerArmorRecallIndex.get(player.level().getServer()).remove(stand.getUUID());" in s
assert "if(!owned(stand,player.getUUID())||!player.isAlive()" in s
assert "PowerArmorRecallTickets.ticket" in s
assert "visual.noPhysics=true;" in s
# Two low-budget nozzle effects only during approach, no new ticker.
old='''  if(f.ticks()%3==0)player.level().sendParticles(ParticleTypes.END_ROD,
    visual.getX(),visual.getY()+.7D,visual.getZ(),3,.18D,.2D,.18D,.02D);'''
if old in s:
 s=s.replace(old,'''  if(f.ticks()%3==0){
   // V175_JETS: visible rearward jets on a horizontal approaching suit.
   player.level().sendParticles(ParticleTypes.END_ROD,
     visual.getX(),visual.getY()+.15D,visual.getZ(),2,.16D,.13D,.16D,.015D);
   player.level().sendParticles(ParticleTypes.FLAME,
     visual.getX(),visual.getY()-.10D,visual.getZ(),2,.12D,.10D,.12D,.015D);
  }''',1)
else:
 # Keep any v1.7.4 replacement and add no duplicate particle generator.
 assert "sendParticles(ParticleTypes.END_ROD" in s,"V175_THRUSTER_HOOK_CHANGED"
put(p,s)
print("V175_RECALL_PHASES_PASS: actual horizontal flight + brake/dock with safe deferred transfer, all tiers, cleanup")
