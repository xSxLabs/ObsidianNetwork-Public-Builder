package dev.obsidiannetwork.powerarmor;

/**
 * Common server authorization for the Power Armor sleep action.
 * A caller must also respect the world's normal sleep/day advancement policy.
 */
public final class V176PowerSleepRules {
    private V176PowerSleepRules() {}
    public enum Rejection { NONE, NOT_WEARING_SUIT, DAYTIME, HOSTILE_NEARBY,
                            UNSAFE_POSITION, ANOTHER_SLEEP_SESSION }
    public static Rejection validate(boolean completeWornSuit, boolean night,
                                     boolean nearbyHostile, boolean safePosition,
                                     boolean alreadySleeping) {
        if (!completeWornSuit) return Rejection.NOT_WEARING_SUIT;
        if (!night) return Rejection.DAYTIME;
        if (nearbyHostile) return Rejection.HOSTILE_NEARBY;
        if (!safePosition) return Rejection.UNSAFE_POSITION;
        if (alreadySleeping) return Rejection.ANOTHER_SLEEP_SESSION;
        return Rejection.NONE;
    }
}
