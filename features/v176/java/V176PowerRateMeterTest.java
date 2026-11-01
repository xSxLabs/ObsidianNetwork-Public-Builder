package dev.obsidiannetwork.power;
public final class V176PowerRateMeterTest {
 private static void yes(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  var m=new V176PowerRateMeter();
  m.committed(1,100,0);
  m.committed(1,300,10);
  yes(m.inputPerTick(1)==20);
  yes(m.outputPerTick(1)==0);
  m.committed(2,0,400);
  yes(m.outputPerTick(2)==20);
  yes(m.inputPerTick(23)==0 && m.outputPerTick(23)==0);
  m.committed(24,2000,0);
  yes(m.inputPerTick(24)==100);
  System.out.println("V176_POWER_MONITOR_ROLLING_20T_REAL_TRANSACTION_RATES_PASS");
 }
}
