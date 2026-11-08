#!/usr/bin/env python3
"""Build-time speech renderer: one multilingual male voice, bundled offline PCM.
The Minecraft client NEVER connects to a speech API or installs TTS libraries.
This stage deliberately fails the build if the speech assets cannot be generated.
"""
import asyncio
import os
import re
import subprocess
import tempfile
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from num2words import num2words

# A German-native, multilingual male timbre makes German numbers and English
# sentences share the same speaker. More restrained, low-pitched JARVIS feel.
VOICE = "de-DE-FlorianMultilingualNeural"
ROOT = Path(os.environ["V1_SOURCE_ROOT"]).parent / "resources" / "assets" / "obsidiannetwork" / "jarvis_audio"
ROOT.mkdir(parents=True, exist_ok=True)

# One voice identity for both languages. Fixed lines are always one recording
# (not phonemes or a Minecraft text narrator).
FIXED = {
    "service": ("At your service, sir.", "Zu Ihren Diensten, Sir."),
    "offline": ("Going offline. Until next time, sir.", "Ich gehe offline. Bis zum nächsten Mal, Sir."),
    "recall": ("Armor recall initiated. I'm on my way, sir.", "Rüstungsrückruf eingeleitet. Ich bin auf dem Weg, Sir."),
    "follow": ("Follow mode command received, sir.", "Folgemodus-Befehl empfangen, Sir."),
    "turret": ("Turret mode command received, sir.", "Geschützturmmodus-Befehl empfangen, Sir."),
    "sleep_command": ("Sleep mode command received, sir.", "Schlafmodus-Befehl empfangen, Sir."),
    "attack_on": ("Attack mode activated.", "Angriffsmodus aktiviert."),
    "attack_off": ("Attack mode deactivated.", "Angriffsmodus deaktiviert."),
    "projectile": ("Incoming projectile, sir.", "Ein Geschoss nähert sich, Sir."),
    "home": ("Welcome home, sir.", "Willkommen zu Hause, Sir."),
    "cave": ("Sir, we are entering a deep cave. Visibility is limited.", "Sir, wir betreten eine tiefe Höhle. Die Sicht ist eingeschränkt."),
    "exit": ("See you later, sir.", "Bis später, Sir."),
    "sleep_begin": ("Sleeping in progress, sir.", "Schlafvorgang läuft, Sir."),
    "sleep_end": ("Sleeping finished. Good morning, sir.", "Schlafvorgang abgeschlossen. Guten Morgen, Sir."),
    "flight_on": ("Flight systems engaged, sir.", "Flugsysteme aktiviert, Sir."),
    "flight_off": ("Flight systems disengaged.", "Flugsysteme deaktiviert."),
    "critical_structure": ("Critical structural failure, sir. All armor protection systems are offline.", "Kritischer Strukturausfall, Sir. Alle Rüstungsschutzsysteme sind offline."),
    "empty_energy": ("Warning, sir. Armor energy reserves are completely depleted. Powered systems are offline.", "Warnung, Sir. Die Rüstungsenergie ist vollständig aufgebraucht."),
    "empty_paste": ("Warning, sir. NutriPaste reserves are at one percent. Immediate refilling is recommended.", "Sir, der NutriPaste-Vorrat liegt bei eins Prozent."),
    "morning": ("Good morning, sir. Welcome back.", "Guten Morgen, Sir. Willkommen zurück."),
    "afternoon": ("Good afternoon, sir. Welcome back.", "Guten Tag, Sir. Willkommen zurück."),
    "evening": ("Good evening, sir. Welcome back.", "Guten Abend, Sir. Willkommen zurück."),
}
# Pre-record critical threshold sentences as full utterances: no splices.
for percent in (25, 50):
    FIXED[f"energy_{percent}"] = (
        f"Sir, armor energy reserves have dropped to {percent} percent.",
        f"Sir, die Rüstungsenergie liegt bei {percent} Prozent.",
    )
for percent in (25, 50, 57):
    FIXED[f"paste_{percent}"] = (
        f"Sir, NutriPaste reserves are at {percent} percent.",
        f"Sir, der NutriPaste-Vorrat liegt bei {percent} Prozent.",
    )
for percent in (1, 25, 50):
    FIXED[f"integrity_{percent}"] = (
        f"Sir, armor structural integrity is at {percent} percent.",
        f"Sir, die Rüstungsintegrität liegt bei {percent} Prozent.",
    )

# Dynamic fragments only where numbers, mob names and scan counts change.
# Long parts make sentences far smoother than word-at-a-time TTS.
PARTS = {
    "diagnostics_start": ("Armor diagnostics complete.", "Rüstungsdiagnose abgeschlossen."),
    "diagnostics_ok": ("All systems operational.", "Alle Systeme einsatzbereit."),
    "diagnostics_failed": ("Armor systems offline.", "Rüstungssysteme offline."),
    "energy_prefix": ("Sir, armor energy reserves have dropped to", "Sir, die Rüstungsenergie liegt bei"),
    "paste_prefix": ("Sir, NutriPaste reserves are at", "Sir, der NutriPaste-Vorrat liegt bei"),
    "integrity_prefix": ("Sir, armor structural integrity is at", "Sir, die Rüstungsintegrität liegt bei"),
    "percent": ("percent.", "Prozent."),
    "scan_prefix": ("Sir, I am detecting", "Sir, ich erkenne"),
    "hostile_one": ("hostile entity", "feindliche Kreatur"),
    "hostile_many": ("hostile entities", "feindliche Kreaturen"),
    "passive_one": ("passive creature", "friedliche Kreatur"),
    "passive_many": ("passive creatures", "friedliche Kreaturen"),
    "player_one": ("player", "Spieler"),
    "player_many": ("players", "Spieler"),
    "boss_one": ("boss", "Boss"),
    "boss_many": ("bosses", "Bosse"),
    "join": ("and", "und"),
    "scan_distance": ("within", "im Umkreis von"),
    "blocks": ("blocks.", "Blöcken."),
    "nearest": ("The closest threat is a", "Die nächste Bedrohung ist"),
    "blocks_now": ("blocks", "Blöcke"),
    "ahead": ("ahead of you.", "vor Ihnen."),
    "behind": ("behind you.", "hinter Ihnen."),
    "left": ("to your left.", "links von Ihnen."),
    "right": ("to your right.", "rechts von Ihnen."),
}
# Vanilla threats; modded entity names remain visible as subtitles.
MOBS = ("Zombie", "Skeleton", "Creeper", "Spider", "Cave Spider", "Enderman",
        "Witch", "Slime", "Pillager", "Vindicator", "Evoker", "Phantom",
        "Drowned", "Husk", "Stray", "Blaze", "Ghast", "Piglin", "Wither Skeleton",
        "Endermite", "Silverfish", "Guardian", "Elder Guardian", "Shulker",
        "Magma Cube", "Hoglin", "Ravager", "Bogged", "Breeze", "Warden")
for mob in MOBS:
    PARTS["mob_" + re.sub(r"[^a-z0-9]+", "_", mob.lower())] = (mob, mob)

# For variable 0-100% status and actual scan counts. Use natural written-out
# number words (EN/DE), never feed unlocalized digits to an English TTS voice.
SPEECH = []
CATALOG = []
for key, pair in {**FIXED, **PARTS}.items():
    for lang, text in zip(("en", "de"), pair):
        # Duplicate phrase keys are harmless; fixed phrases are longest matches.
        SPEECH.append((lang, key, text))
        CATALOG.append((lang, text, key))
# Complete percent clauses, recorded for 0..100 separately in EACH language.
# Startup joins at sentence boundaries only: no audible joins between numbers
# and "percent" / "Prozent". Catalog retains digits for runtime matching;
# the neural voice receives fully written-out words in its native language.
for number in range(101):
    for lang in ("en", "de"):
        key = f"number_{number}"
        text = num2words(number, lang=lang)
        SPEECH.append((lang, key, text))
        for topic, english, deutsch in (
            ("integrity", "Structural integrity at {value} percent.", "Integrität {value} Prozent."),
            ("energy", "Energy reserves at {value} percent.", "Energie {value} Prozent."),
            ("paste", "NutriPaste reserves at {value} percent.", "NutriPaste {value} Prozent."),
        ):
            template = deutsch if lang == "de" else english
            clipkey = f"startup_{topic}_{number}"
            CATALOG.append((lang, template.format(value=number), clipkey))
            SPEECH.append((lang, clipkey, template.format(value=text)))

def spell_numbers(text, lang):
    # Never let the voice choose its own numerical locale from raw digits.
    return re.sub(r"(?<![A-Za-z])\\b([0-9]{1,3})\\b(?![A-Za-z])",
                  lambda m: num2words(int(m.group(1)), lang=lang), text)

async def main():
    semaphore = asyncio.Semaphore(6)
    count = 0
    async def render(lang, key, text):
        nonlocal count
        target = ROOT / lang / (key + ".wav")
        target.parent.mkdir(parents=True, exist_ok=True)
        async with semaphore:
            for attempt in range(4):
                try:
                    with tempfile.TemporaryDirectory(prefix="xsxvoice_") as tmp:
                        mp3 = Path(tmp) / "speech.mp3"
                        comm = edge_tts.Communicate(text=spell_numbers(text,lang), voice=VOICE,
                                                    rate="-5%", pitch="-15Hz")
                        await asyncio.wait_for(comm.save(str(mp3)), timeout=50)
                        if not mp3.is_file() or mp3.stat().st_size < 200:
                            raise RuntimeError("empty TTS output")
                        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-nostdin",
                                        "-y", "-i", str(mp3),
                                        "-af", "highpass=f=70,lowpass=f=8500,acompressor=threshold=-18dB:ratio=2:attack=5:release=80",
                                        "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
                                        str(target)], check=True, timeout=35)
                        with target.open("rb") as f:
                            if f.read(4) != b"RIFF":
                                raise RuntimeError("invalid PCM wave")
                        count += 1
                        return
                except Exception as exc:
                    if attempt == 3:
                        raise RuntimeError(f"JARVIS speech failed for {lang}/{key}: {exc}") from exc
                    await asyncio.sleep(2 * (attempt + 1))
    tasks = [asyncio.create_task(render(*entry)) for entry in SPEECH]
    try:
        await asyncio.gather(*tasks)
    except Exception:
        for task in tasks:
            task.cancel()
        raise
    manifest = ROOT / "catalog.tsv"
    manifest.write_text("".join(f"{lang}\t{text}\t{key}\n" for lang, text, key in CATALOG), encoding="utf-8")
    assert (ROOT / "en" / "attack_on.wav").stat().st_size > 1000
    assert (ROOT / "de" / "recall.wav").stat().st_size > 1000
    assert (ROOT / "de" / "number_42.wav").stat().st_size > 1000
    assert len(SPEECH) > 900 and count == len(SPEECH)
    assert (ROOT / "en" / "startup_energy_50.wav").stat().st_size > 1000
    assert (ROOT / "de" / "startup_paste_42.wav").stat().st_size > 1000
    print(f"V177_NATURAL_BILINGUAL_VOICE_BUNDLED: {count} WAV clips, voice={VOICE}, no narrator, no runtime downloads")

if __name__ == "__main__":
    asyncio.run(main())
