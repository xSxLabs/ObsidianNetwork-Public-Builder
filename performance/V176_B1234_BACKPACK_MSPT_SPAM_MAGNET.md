# v1.7.6 B1234 — conservative performance, spam-kick and magnet candidate

Scope is deliberately additive to the current v1.7.6 reconstruction. Do not
modify v1.7.5 or the marked 1.7.6 Build 1224 freeze.

## Active modifications
- Item Cable endpoint view is cached across calls while ItemStack identity,
  immutable container component, and committed transaction revision agree.
- Placed Backpack item-list cache remains valid across idle server ticks and
  invalidates on actual component mutation or committed cable transfer.
- GUI wheel handles fractional input, drag is supported, and navigation uses
  bounded coalesced vanilla container-button packets, not chat command loops.
- Magnet upgrade is ON by default unless its persisted switch explicitly
  says OFF; find the first actually activated carried/worn bag, including
  optional Curios slots, rather than being blocked by an earlier disabled one.
- No gameplay energy/item rate caps and no server spam-threshold modification.
- Inspect every xSxLabs command packet callsite in generated source, log
  potential tick or wheel emitters for future targeted packet conversion.

## Required release checks
1. Complete NeoForge 26.1 Java compile + normal CI regressions in both Curios
   configurations, no new Java signature/API mismatches.
2. Cable -> Backpack and Backpack -> chest conserve exact descriptor counts
   on full/partial/rollback transactions, still updating the open GUI live.
3. Magnet receives real item entities in main/off/chest/Curios, respects
   active ON/OFF, blacklist/whitelist, remaining capacity, and no duplicates.
4. GUI scroll and drag do not send repeated /networkbackpack chat commands.
5. Existing PowerArmor manual entry/exit and freeze guards remain intact.
6. Baseline MSPT 150ms is user-reported, not a measured after-performance
   claim. Request paired same-world Spark traces for actual improvement.

The automated static source-only B1234 gates are separate from a real build;
a green static test does not by itself authorize a JAR release.
