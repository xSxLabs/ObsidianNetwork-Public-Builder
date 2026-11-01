package dev.obsidiannetwork.powerarmor;

/**
 * Pure server-side safety/balance rules for v1.7.6 FE-powered arm Micro-MG.
 * No GUI/display state may authorize a projectile. The real server must check
 * these predicates again and debit FE once, after successful spawn.
 */
public final class V176MicroMgRules {
 private V176MicroMgRules(){}
 public static final long FE_PER_SHOT=3000L;
 public static final int COOLDOWN_TICKS=1; // 4 of 5 ticks => 16 shots/sec at 20 TPS
 public static final int AUTO_TARGET_RANGE_SQ=16*16;
 public static final int MANUAL_MAX_RANGE=24;
 public static final float DAMAGE_HP=2.0f;

 /** NONE is an internal disabled state, not a third Actionswheel option. */
 public enum CompanionMode { NONE, FOLLOW, TURRET }

 public static boolean shouldShowAttackAction(boolean fullyWorn,boolean moduleInstalled){
  return fullyWorn&&moduleInstalled;
 }
 public static boolean shouldForceAttackOff(boolean fullyWorn,boolean moduleInstalled){
  return !shouldShowAttackAction(fullyWorn,moduleInstalled);
 }
 public static boolean follows(CompanionMode mode){
  return mode==CompanionMode.FOLLOW||mode==CompanionMode.TURRET;
 }
 public static boolean shootsAutomatically(CompanionMode mode){
  return mode==CompanionMode.TURRET;
 }
 public static boolean cooldownReady(long tick,long lastShotTick){
  if(lastShotTick<0)return true; // First trigger responds instantly.
  return tick>=lastShotTick && tick-lastShotTick>=COOLDOWN_TICKS
      &&tick%5L!=4L; // 0,1,2,3,5,6,7,8,... 16 shots per second
 }
 public static boolean canSpawn(long fe,long tick,long lastShotTick){
  return fe>=FE_PER_SHOT&&cooldownReady(tick,lastShotTick);
 }
 public static boolean canManualFire(boolean fullyWorn,boolean moduleInstalled,
     boolean attackModeOn,long fe,long tick,long lastShotTick){
  return shouldShowAttackAction(fullyWorn,moduleInstalled)
      &&attackModeOn&&canSpawn(fe,tick,lastShotTick);
 }
 public static boolean canTurretFire(CompanionMode mode,boolean moduleInstalled,
     boolean targetHostile,boolean targetOwnedOrFriendly,boolean hasLineOfSight,
     double distanceSq,long fe,long tick,long lastShotTick){
  return shootsAutomatically(mode)&&moduleInstalled&&targetHostile
      &&!targetOwnedOrFriendly&&hasLineOfSight
      &&Double.isFinite(distanceSq)&&distanceSq>=0.0
      &&distanceSq<=AUTO_TARGET_RANGE_SQ
      &&canSpawn(fe,tick,lastShotTick);
 }
 public static String actionbar(boolean active){
  return active?"Attack Mode: ON":"Attack Mode: OFF";
 }
}
