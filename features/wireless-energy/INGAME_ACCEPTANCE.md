# Wireless Energy Networks – Ingame-Abnahme

Stand 18.10.2026 · Branch `feature-wireless-energy-networks` · **kein Ingame-Freeze**

Die CI-Prüfungen sind zwingend, aber ersetzen den Client-/Multiplayer- und Neustarttest nicht.
Nur ein vom Nutzer tatsächlich im Spiel bestätigter Build wird als `INGAME OK` markiert.

## Voraussetzungen

- Minecraft 26.1.2 / NeoForge 26.1.2.106, jeweils dieselbe getestete ObsidianNetwork-JAR auf Client und dediziertem Server.
- Keine alte JAR der Mod parallel laden. Vor dem Test vollständige Welt- und Spieler-Backups anfertigen.
- Für den optionalen Curios-Test zwei Teststarts: einmal **ohne** Curios und einmal **mit** einer zur installierten Version passenden Curios-Mod und einem FE-fähigen Item.
- Testwelt mit Overworld und Nether. Zwei Spieler für die Netzwerkrechte. Baseline der serverseitigen MSPT mit Spark erfassen.

## Abnahmeszenarien

1. **Blocks/Assets:** Network Transmitter und Network Receiver erscheinen einzeln im Kreativtab, haben verschiedene Antennensignale, korrekte Rotation, Rezepte und Drops. Keine neue dritte Wireless-Steuereinheit.
2. **Realer Stromfluss:** Energy Cell → Energiekabel/Bundle → Transmitter, Luftlücke, Receiver → Energy Cell/Maschine. Am Ziel steigt der FE-Wert; Gesamtbilanz aller beteiligten Speicher bleibt erhalten.
3. **Crossdim und geladene Chunks:** Sender im Nether, Receiver in Overworld, transferieren bei geladenem Sender-Chunk; danach Sender-Chunk entladen. Energie muss dort pausieren – Wireless allein darf keine Chunks laden. Nach erneutem Laden setzt die Versorgung fort.
4. **Mehrere Funknetze:** Zwei unterschiedlich benannte Netze mit verschiedenen Sendern/Receivern. Kein Transfer zwischen getrennten Netz-IDs; Namen ändern IDs nicht. Nach Umbenennung bleibt der Link erhalten. Löschen erfordert zweimaliges Bestätigen und darf die lokale FE im Transmitter nicht vernichten. Nach Löschen darf kein FE mehr über die alte ID fließen.
5. **Besitzerrechte:** Spieler A erstellt Netz und platziert Geräte. Spieler B darf A's Geräte/GUIs nicht konfigurieren, A's Netz nicht auswählen oder umbenennen/löschen. Nach Blockabbau oder Dimensionswechsel müssen alte Menüaktionen scheitern. Das öffentliche Main-Netz ist für private Konfiguration kein Ersatz.
6. **Wireless Charging:** Für *jedes Netz einzeln* Inventar, Curios, Rüstung, Nebenhand, Hotbar ein-/ausschalten. Hotbar und restliches Inventar getrennt prüfen, auch bei mehreren gleichzeitigen Netzen. Nie mehr als insgesamt 16.000 FE pro Spieler je 20-Tick-Ladeintervall.
7. **Curios optional:** Start ohne Curios muss fehlerfrei sein. Mit Curios müssen ausgerüstete kompatible Energie-Items nur dann geladen werden, wenn Curios für das betreffende Netz an ist.
8. **Persistenz/Neustart:** Mindestens zwei private Netze und mehrere Geräte konfigurieren. Gespeicherte Sender-FE, Netz-ID/Name/Owner sowie fünf Ladeoptionen vor Serverstopp protokollieren. Server vollständig stoppen und neu starten; sämtliche Werte müssen unverändert sein. Derselbe Link muss ohne Neuerstellung funktionieren.
9. **Mehrere Empfänger:** Ein Receiver mit FE-Abnehmern an mehreren Seiten darf **zusammen** höchstens 16.000 FE pro fünf Ticks übertragen. Mehrere Sender desselben Netzes sollen über längere Zeit Energie liefern, ohne den ersten dauerhaft zu bevorzugen.
10. **Performance:** Vergleich von Baseline gegen 10/50/100 aktive Transmitter/Receiver, jeweils mit leeren und vollen Zielmaschinen. In Spark insbesondere Receiver-Ticker, `WirelessEnergyRuntime.available/pull`, ItemAccess/Curios und SaveData prüfen. Server-MSPT, P95/P99 und Lagspitzen statt bloßer FPS oder durchschnittlicher TPS dokumentieren.

## Fehlerbericht

Bei Problemen folgende Informationen festhalten: getestete **Buildnummer und Actions-Run**, Mod-JAR-SHA-256, Dimensionen, Anzahl Sender/Receiver, Netzwerk-ID, Ladeoptionen, Reproduktionsschritte, erwartete/tatsächliche FE-Bilanz, Log und Spark-Profil. Testwelten nicht ohne Backup überschreiben.

## CI versus Ingame

- Grüne CI belegt nur die tatsächlich gelaufenen Source-, Java- und GameTests.
- NBT/Codec-Roundtrip belegt **keinen** vollständigen Welt-Save/Neustart.
- Nether-GameTest lädt seinen Testchunk selbst und belegt **nicht** automatisches Produktion-Chunkloading.

## Abschluss: reale Laufzeit- und Spark-Abnahme

Der Teststand #255 bestätigt Curios-Ladefähigkeit/Bridge-Linkage mit und ohne das optionale Mod, aber **keinen** ausgerüsteten Curios-Energiegegenstand. Curios allein hat standardmäßig keine nutzbaren Slots. Für Szenario 7 daher eine passende Slot-Konfiguration/Addon mit tatsächlichem Slot und einem FE-fähigen Item installieren; andernfalls gilt ein leerer Curios-Adapter nicht als erfolgreicher Ladebeweis.

Die Dichte-Regression #256/#257 erzeugt im GameTest nur einen echten **FE-Funktionstest unter gleichzeitig geladener Last**: 10, 50 und 100 Sender+Empfänger+EnergyCell-Kombinationen, mit erhaltener FE-Gesamtbilanz. **Kein** Wert daraus ist eine kontrollierte Spark-MSPT- oder P95/P99-Verbesserung. Für die finale Spielabnahme bei identischen Server-Einstellungen je Phase 60–120 Sekunden aufzeichnen: 0 Wireless-Geräte; 10/10; 50/50; 100/100. Zusätzlich jeweils „Quelle vorhanden / Quelle weg“, Ziel leer / Ziel voll, einmal offene und geschlossene Wireless-GUI. P50/P95/P99, maximale MSPT, GC-Spikes und „Can't keep up“-Meldungen vergleichen, dann das zugehörige Spark-Profil sichern.

Nach erfolgreichem CI-Build nur den **enthaltenen Mod-JAR** aus dem Actions-Artefakt installieren, nicht das ZIP als Mod verwenden. Vor jedem Client- oder Serverstart Welt-Backup und Abgleich der JAR-Versionen. Der separate Branch `projekt-performance` bleibt weiterhin unbeeinflusst.
