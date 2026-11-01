package dev.obsidiannetwork.powerarmor;

public final class V176MicroMgRulesTest {
 private static void okay(boolean value,String message) {
  if(!value)throw new AssertionError(message);
 }
 public static void main(String[] args){
  var r=V176MicroMgRules.class;
  okay(V176MicroMgRules.FE_PER_SHOT==3000L,"FE cost");
  okay(V176MicroMgRules.COOLDOWN_TICKS==1,"minimum 1 tick, 16 shots/sec every 4 of 5");
  okay(!V176MicroMgRules.shouldShowAttackAction(true,false),"module-gated wheel");
  okay(!V176MicroMgRules.shouldShowAttackAction(false,true),"worn-only wheel");
  okay(V176MicroMgRules.shouldShowAttackAction(true,true),"equipped module");
  okay(V176MicroMgRules.shouldForceAttackOff(true,false),"remove module => OFF");
  okay(V176MicroMgRules.follows(V176MicroMgRules.CompanionMode.FOLLOW),"follow");
  okay(!V176MicroMgRules.shootsAutomatically(V176MicroMgRules.CompanionMode.FOLLOW),"follow NEVER shoots");
  okay(V176MicroMgRules.follows(V176MicroMgRules.CompanionMode.TURRET),"turret follows too");
  okay(V176MicroMgRules.shootsAutomatically(V176MicroMgRules.CompanionMode.TURRET),"turret auto fire");
  okay(!V176MicroMgRules.follows(V176MicroMgRules.CompanionMode.NONE),"disabled never follows");
  okay(!V176MicroMgRules.canManualFire(true,false,true,3000,100,-1),"no module");
  okay(!V176MicroMgRules.canManualFire(true,true,false,3000,100,-1),"attack OFF");
  okay(!V176MicroMgRules.canManualFire(true,true,true,2999,100,-1),"low FE");
  okay(V176MicroMgRules.canManualFire(true,true,true,3000,100,-1),"first shot");
  okay(V176MicroMgRules.canManualFire(true,true,true,3000,102,100),"second shot after 2 ticks");
  okay(!V176MicroMgRules.canManualFire(true,true,true,3000,104,100),"cooldown");
  okay(V176MicroMgRules.canManualFire(true,true,true,3000,105,100),"cooldown ready");
  long previous=-1L;int bullets=0;
  for(long now=0;now<20;now++)
   if(V176MicroMgRules.canSpawn(3000,now,previous)){bullets++;previous=now;}
  okay(bullets==16,"exactly 16 real FE projectile authorizations per 20 ticks, got "+bullets);
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.FOLLOW,
   true,true,false,true,50,3000,100,-1),"follow cannot attack");
  okay(V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   true,true,false,true,256,3000,100,-1),"turret range inclusive");
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   true,true,false,true,257,3000,100,-1),"turret range");
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   true,false,false,true,100,3000,100,-1),"no passive mobs");
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   true,true,true,true,100,3000,100,-1),"no owned pets");
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   true,true,false,false,100,3000,100,-1),"no shooting through walls");
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   true,true,false,true,Double.NaN,3000,100,-1),"invalid target distance");
  okay(!V176MicroMgRules.canTurretFire(V176MicroMgRules.CompanionMode.TURRET,
   false,true,false,true,100,3000,100,-1),"no gun module");
  okay(V176MicroMgRules.actionbar(true).equals("Attack Mode: ON"),"ON label");
  okay(V176MicroMgRules.actionbar(false).equals("Attack Mode: OFF"),"OFF label");
  System.out.println("V176_MICRO_MG_RULES_22_CASES_PASS");
 }
}
