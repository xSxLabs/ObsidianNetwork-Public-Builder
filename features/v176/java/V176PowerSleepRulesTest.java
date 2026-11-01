package dev.obsidiannetwork.powerarmor;
public final class V176PowerSleepRulesTest {
    public static void main(String[] args) {
        var r=V176PowerSleepRules.Rejection.NONE;
        if(V176PowerSleepRules.validate(true,true,false,true,false)!=r)throw new AssertionError();
        if(V176PowerSleepRules.validate(true,false,false,true,false)!=V176PowerSleepRules.Rejection.DAYTIME)throw new AssertionError();
        if(V176PowerSleepRules.validate(true,true,true,true,false)!=V176PowerSleepRules.Rejection.HOSTILE_NEARBY)throw new AssertionError();
        if(V176PowerSleepRules.validate(false,true,false,true,false)!=V176PowerSleepRules.Rejection.NOT_WEARING_SUIT)throw new AssertionError();
        System.out.println("V176_POWER_ARMOR_SLEEP_NIGHT_MONSTER_GATE_PASS");
    }
}
