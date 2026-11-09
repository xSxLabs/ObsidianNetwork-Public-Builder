#!/usr/bin/env python3
"""B145x regression preflight for v1.7.7 no-break suit, sleep, speech."""
from pathlib import Path
root=Path("features/v177")
integrity=(root/"apply-v177-armor-integrity-repair.py").read_text(encoding="utf-8")
voice=(root/"apply-v177-jarvis-voice.py").read_text(encoding="utf-8")
tts=(root/"generate-v177-natural-voice.py").read_text(encoding="utf-8")
sleep=(root/"apply-v177-power-sleep-fix.py").read_text(encoding="utf-8")
homes=(root/"apply-v177-jarvis-sethome-bridge.py").read_text(encoding="utf-8")
flow=Path(".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

# The original four suits remain UNBREAKABLE and preserve their item IDs.
# Vanilla durability must NOT be used as a decreasing 0-HP integrity meter.
for phrase in (
    'SUIT_HITPOINTS=1000',
    'HP_KEY="xsxlabs_armor_integrity_hp"',
    'CustomData.update(DataComponents.CUSTOM_DATA,stack',
    'setHitpoints(stack,hitpoints(stack)-hitpoints)',
    'setHitpoints(stack,hitpoints(stack)+restore)',
    'explosion?10:collision?5:2',
    'LivingIncomingDamageEvent',
    'EventPriority.HIGHEST',
    'noBrokenAttributes',
    'PowerArmorRuntime.full(p)&&totalHitpoints(p)<=0',
    'g.text(mc.font,"INTEGRITY",0,0,color);',
):
    assert phrase in integrity,phrase
assert 'stack.setDamageValue(Math.min(max(stack)' not in integrity
assert 'stack.setDamageValue(Math.max(0,stack.getDamageValue()-restore))' not in integrity
assert 'p.setItemSlot(' not in integrity
assert 'stack.shrink(' not in integrity
assert 'stack.setCount(0)' not in integrity

# No more perpetual STANDING/SLEEPING overwrite; actual sleepingPos is held.
for phrase in (
    'p.startSleeping(p.blockPosition())',
    'CanContinueSleepingEvent',
    'event.setContinueSleeping(true)',
    'if(p.isSleeping())p.stopSleepInBed(true,true)',
):
    assert phrase in sleep,phrase

# Every major audible announcement is separately switchable.
for phrase in (
    'flight_on|Flight ON', 'flight_off|Flight OFF',
    'sleep_begin|Sleep begins','sleep_end|Sleep finishes',
    'home|Welcome back at home', 'startup_integrity|Entry integrity',
    'startup_energy|Entry energy','startup_paste|Entry NutriPaste',
    '< PREV', 'NEXT >', 'on("flight_on")','on("flight_off")',
    'on("energy_"+e)','on("paste_"+n)','on("integrity_"+a)',
    'enqueue(2,"Welcome back, sir.","Willkommen zurück, Sir.")',
):
    assert phrase in voice,phrase
# Follow and turret confirmations must play immediately when a suit is nearby but unworn.
assert 'else directly("Follow mode command received, sir."' in voice
assert 'else directly("Turret mode command received, sir."' in voice
assert 'if(available())enqueue(1,"Follow mode command received, sir."' in voice
assert 'if(available())enqueue(1,"Turret mode command received, sir."' in voice
assert 'event.setParseResults(new ParseResults<>(' in homes
assert 'if(!success)return;' in homes
assert 'getRespawnConfig()' in homes
assert 'config.respawnData().pos()' in homes
assert 'nearest_distance_' in tts
assert 'nearest_" + key' in tts
assert '"en-GB-RyanNeural"' in tts
assert '"de-DE-FlorianMultilingualNeural"' in tts

# Everything belongs to branch 1.7.7, never the 1.7.6 freeze.
assert 'if [ "$GITHUB_REF_NAME" = "1.7.7" ] || [ "$GITHUB_REF_NAME" = "1.7.7.1-ultra-performance" ]; then' in flow
assert 'python3 features/v177/apply-v177-power-sleep-fix.py' in flow
print("V177_INTEGRITY_SLEEP_PAGED_JARVIS_VOICE_CONTRACT_PASS")
