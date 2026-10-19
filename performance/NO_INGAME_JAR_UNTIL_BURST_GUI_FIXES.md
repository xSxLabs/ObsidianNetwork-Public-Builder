# Projekt Performance Wireless – Sperre der nächsten Ingame-JAR

Stand: 18.10.2026. Nutzerfreigabe: **KEINE neue Ingame-Test-JAR zusenden**, bis alle bekannten GUI-/Burst-/Crafting-Lags behoben und getestet sind.

## Sichere Basis
- Grüner Build 286: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39149864423
- Eingefrorener Build 280: `freeze/performance-wireless-b280-green`
- Alle weiteren Builds sind **nur interne CI-Kandidaten**, auch wenn GitHub Actions automatisch ein Artefakt erstellt.
- Grün bei Kompilierung, synthetischen Tests und Headless GameTests bedeutet noch **keine** erwiesene Verbesserung unter realer GUI-Last.

## Offene Sperren (alle erforderlich)

| ID | Konkretes Problem | Erforderlicher Beleg | Status |
|---|---|---|---|
| P1 | Schnelles Massen-/Shift-Crafting über Crafting Terminal verursacht Hänger | reale Menu/Netzwerk-Burst-Interaktionen, vollständige Crafting-Zählung und Zutatenkonservation, Tick-p95/p99 | OFFEN |
| P2 | Schnelle Masseneinlagerung über Crafting Terminal | realer Menü-Packet/QuickMove-Burst auf 50-Drive-Netz, exakte Speicherung/Restmengen, keine Duplikate, p95/p99 | OFFEN |
| P3 | Autocrafter-GUI verursacht Tick-Spitzen | serverseitiges Öffnen, Status/Job-Preview unter hoher Last, reale p95/p99/GC; kein bloßer Source-Grep | OFFEN |
| P4 | Network Controller-GUI (auch klein, besonders 50 Drives) verursacht Lag | wiederholtes Öffnen/Schließen, mit/ohne aktive Jobs, 21 Felder, p95/p99 und Sync | OFFEN |
| P5 | Drive-GUI verursacht Tick-Spitzen | reale 16-Slot-GUI und 50-Drive-Last, NBT-Erhaltung; Client-Slot-Sichtbarkeit separat prüfen | OFFEN |
| P6 | Autocrafting-Zutatenreservierung und Abbruch | reservierte Mengen im Terminal nicht als frei verfügbar, Konkurrenzjobs, persistente Wiederherstellung, exakte Refunds | OFFEN/NICHT VOLLSTÄNDIG VERIFIZIERT |
| P7 | Regressionsschutz | 16 reale Zellen inklusive 8..15, 50×16-Zellen, Wireless legitim upgraded-only, Eigentümerrechte, 1TX/8RX, 100 Geräte, FE-/Item-Erhaltung, echter JVM-Neustart | bestehende Tests grün; bei jeder Änderung erneut ausführen |
| P8 | **Leistungsnachweis** | A/B derselben gespeicherten Welt, exakter JAR-SHA-256, gleicher Server, Spieler/Last; isolierte 60–120-Sekunden-Phasen für idle, burst craft, deposit, open GUIs und transfer; Spark Server-Thread MSPT mean/p95/p99/max und GC | OFFEN |

## Aktueller Testausbau
- Build 287: CI-only Test für 50 echte Drives, 800 belegte Zellen, 450 neue DriveContainer-Instanzen, 14.400 realen Slot-Lesezugriffen und NBT-/Belegungsprüfungen. Diese Messwerte sind **kein** Client-GUI-Test und **keine** Server-MSPT-Messung. Nicht als P5 oder P8 vollständig bestanden kennzeichnen.
- Bereits bestehende Tests: 50 Drives, 800 Zellen, reales Bulk-Insert/Extract, 20 Tick-Work-Samples, Autocraft-Reservierung und Restore, Wireless-Last, dedizierter Neustart.
- Bestehende AFK-Spark-Profile beschreiben Solar/ENERGY/Importer-Last, **nicht** die reproduzierbare schnelle Crafting-/GUI-Burst-Belastung. Zahlen daraus nicht als Beleg für P1–P5 verwenden.

## Technische Arbeitsreihenfolge
1. Präzise serverseitige GUI-/Terminal-Burst-Workloads als GameTests ohne Testklassen in der Distribution.
2. Im kompilierten Source/Profil Hotpaths identifizieren (z.B. `StorageTerminalMenu.matchingCraftRecipes`, `quickMoveStack`, `broadcastChanges`, Controller-Status und Autocraft-`jobViews`).
3. Fail-closed kleine Optimierungen mit funktionaler Äquivalenz, nicht Zeitbudget künstlich drosseln.
4. Vollständige Python- und Java-/Minecraft-/Curios-/JVM-Neustart-Matrix.
5. Kontrollierte A/B Messung. **Vorher keine Ingame-JAR an den Nutzer geben.**

Selbst ein erfolgreicher interner CI-Build entfernt keine dieser Sperren ohne zugehörige Testbelege.


## Interner Fortschritt 18.10.2026 – Builds #287 bis #293
- **#287 GRÜN:** 50 echte Drives/800 Zellen, 450 Instanzen des serverseitigen DriveContainer, 14.400 Slot-Lesezugriffe einschließlich Slot 8–15. Keine TPS-/Client-GUI-Aussage.
- **#288 GRÜN:** TerminalInventoryBlockEntity.setCraftItem lässt nur bei **exakt unveränderten** ItemStack-Daten (Item, Komponenten/NBT und Anzahl) redundante NeoForge Extract/Insert-Transaktionen aus; vorhandene schreibende Transaktionen bleiben bei jeder realen Änderung unverändert. Binärer JAR-Gate und 107 Python-Tests grün.
- **#289 GRÜN:** Reale NeoForge ItemStack-Handler-GameTests mit 4.500 No-op-Schreibversuchen über 9 Slots; absichtlich veränderte Count-, Tool-DAMAGE-Komponenten und Empty-Slots vollständig korrekt. Curios-aus/-an, JVM-Neustart und vorbestehende Wireless/Drive-Tests erneut bestanden.
- **#290 GRÜN:** Redundanter zweiter broadcastChanges()-Durchlauf nach rebuildRecipeChoice im Crafting-Terminal entfernt. Beide notwendigen Recipe-Ergebnispfade bleiben laut kompiliertem Bytecode eigenständig synchronisiert. Noch kein echter Spieler-Burstnachweis.
- **#291 ROT:** Neu eingeführter Testfixture-Unit-Test veränderte einen Stringmarker durch Suffix \`_OLD\`, wodurch der Originalstring weiterhin als Teilstring enthalten war. Fail-closed-Test stoppte vor Java-Kompilation; **keine** bewiesene Java-Regression. Korrigiert, den Marker vollständig zu ersetzen.
- **#292 gestaffelte CI-Prüfung:** erster realer Minecraft-GameTest für 720 tatsächliche \`StorageTerminalMenu.quickMoveStack\`-Aktionen mit ServerPlayer und 50-Drive-Live-Storage. Exakte per-Click-Item-Erhaltung, Quellenleerung und vollständige Rückentnahme; abhängig vom JVM-Lauf grün/rot bewerten.
- **#293 gestaffelte CI-Prüfung:** zusätzlich 180 echte Controller-GUI- und 180 echte Autocrafter-GUI-Servermenüinstanzen inklusive Status-/Preview-Lesezugriffen auf voller Topologie, 9 Laufzeitstichproben; Ergebnisse vor Prüfung **nicht** als grün markieren.

Alle Komponenten und CI-GameTests sind **kein** Ersatz für kontrollierte vollständige serverseitige MSPT mean/p95/p99- und GC-Messungen bei hoher Spieler-Interaktion auf derselben gespeicherten Welt. **Keine JAR-Freigabe.**

## Build #294–#297: belastbare Testbefunde, 18.10.2026

- **#294–#295 ROT:** Im echten 720er Terminal-QuickMove-Test war der Belegzähler auf `ItemKey.simple` statt auf dem exakten `MinecraftItemStackCodec.describe(...).key()` aufgebaut. Die Testausgabe `got 0 before=0` allein darf NICHT als tatsächlicher Itemverlust interpretiert werden.
- **#296, Curios-abwesend, PASS:** `REAL_CRAFTING_TERMINAL_QUICKMOVE_50DRIVE_BURST_V1` meldet 720 erfolgreiche serverseitige Shift-Einlagerungen, 46.080 Items mit vollständiger Rückentnahme; 50 echte Drives und 800 echte Zellen. Das beweist nur diesen Testfall.
- **#296, Curios-abwesend, PASS:** `REAL_50_DRIVE_TERMINAL_SHIFT_CRAFT_15_TICKS_V1` meldet 15 echte Serverticks, 240 Logs zu 960 Planken; Testarbeitszeit Median 8.112.018 ns und höchster Stichprobenwert 18.298.476 ns; nicht Server-MSPT.
- **#296, Curios-abwesend, PASS:** 180 Controller- und 180 Autocrafter-Menüs bei 50 Drives/800 Zellen. Controller je 20 aufeinanderfolgende Öffnungen: Median 107.822.248 ns, p90 143.651.269 ns; Autocrafter Median 1.903.900 ns. Dies ist ein signifikanter Kandidat für Controller-Open-Optimierung, aber kein A/B-Beleg einer Mod-Verschlechterung.
- **#296, Curios-anwesend, ROT:** `UnsupportedOperationException: Payload curios:sync_data may not be sent to the client!` beim `GameTestHelper.makeMockServerPlayerInLevel()` / Curios-Sync zum headless Testclient. Der Test bricht wegen dieser Testspieler-Netzwerkinteraktion ab; kein Beleg eines produktiven Wireless-Ladefehlers.
- **#297, ausstehend:** Alle drei Server-Menübelastungs-GameTests nutzen stattdessen `NeoForge FakePlayerFactory.getMinecraft(level)`. Die Aktionen, Zähler und sämtliche Curios-anwesend/-abwesend PASS-Gates bleiben eingeschaltet. GitHub-Lauf: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39155266497. Keinen Erfolg behaupten bevor beide Servervarianten tatsächlich erfolgreich sind.

Weitere Einschränkung: Der reale Server-Tick-Ring in #296 hatte 100 Samples mit p95 10.011.739 ns und p99 60.753.064 ns. Dies ist ein unkontrolliertes gemischtes GameTest-Fenster und darf nicht als A/B-Performance-Gewinn verkauft werden. Zusätzlich wurde unter GUI-Stress ein `Can't keep up`-Warnhinweis protokolliert. **Build 297 ist ausschließlich CI, keine Nutzer-JAR.** Nächster Schritt nach gültiger vollständiger CI: teure Controller-Menüöffnung analysieren, sichere invalidierte Caches und einen kontrollierten p95/p99-Vergleich prüfen. P1–P8 bleiben bis zu vollständigem Praxis-/A/B-Beleg gesperrt.

## Grüner Build #297 und Messplan für #298

- **#297 GRÜN**, [GitHub-Run](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39155266497): vollständiger Headless-Minecraft/GameTest-Lauf **ohne Curios und mit Curios**, inklusive 50 Drives / 800 Zellen, 720 realen Terminal-Shift-Einlagerungen und 46.080 erhaltenen Items, 15 echten Shift-Craft-Ticks (240 Logs -> 960 Planken), 180 Controller- plus 180 Autocrafter-Öffnungen, Wireless-100-Receiver-Test, Zwei-Eigentümer-Autorisierung und separatem Neustart. Keine Client-Render- oder kontrollierte A/B-MSPT-Messung.
- **#298 CI-Messstufe:** pro 20 echten GUI-Öffnungen Konstruktor und 21 Controller-Statusabfragen beziehungsweise Autocrafter-Status/Preview getrennt mit `System.nanoTime()` messen; 9 wiederholte Trials, Median/p90, keine harte Performance-Schwelle aufgrund CI/JIT/GC. Zum Schutz weiterhin identische Item-/FE-/Drive-/Curios-Gates und kein Nutzer-JAR-Artefakt ausgeben.

## Build #298: Ursache der Controller-GUI-Arbeitszeit eingegrenzt

- **#298 GRÜN**, https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39158977938. Echte Minecraft-Menüs auf 50 Drives/800 Cells (9 Trials mit jeweils 20 Controller- und 20 Autocrafter-Öffnungen), mit und ohne Curios, beide GameTests grün. 123 Python-Tests plus JVM-/Wireless-/Neustartgates.
- **Controller-Konstruktor** pro 20 Öffnungen Median **306.416 ns**, p90 **1.654.125 ns**. **Statusabfragen derselben 20 Menüs** Median **107.283.821 ns**, p90 **156.878.257 ns**. Daher liegt die teure Arbeit im Controller-Status-Snapshot, NICHT in der Objektkonstruktion. Die unabhängigen Median-Werte nicht als additiven genauen Gesamtwert behandeln.
- **Autocrafter** Konstruktor Median **394.574 ns**, Status/Preview Median **2.186.670 ns** je 20 Öffnungen. Die Vergleichszahlen sind innerhalb desselben Runs auf verschiedenen Codepfaden; kein CPU-Geschwindigkeitsnachweis.
- **#299:** neue fail-closed Parser- und Mutationstests prüfen GUI-Metriken inkl. Vollständigkeit, monotone Quantile, 9x20 Trial-Format, Curios-an/-aus und falsche MSPT-Interpretationen.
- **#300:** CI-only Real-GameTest zerlegt Controller-Status-Kosten in 6 Helfer: Controller-Runtime-Lookup, Drive-Zahl, Autocrafter-Zahl, aktive/blockierte Jobs, Templates. Damit kann nach grünem Test ein konservativer, konkreter Laufzeit-Fix gewählt werden. Die neuen Timing-Probes dürfen keine Server-MSPT-Aussage ersetzen; no user JAR release.

**Freigabesperre P1–P8 bleibt bestehen.** Volle regressionssichere Leistung ist erst mit A/B auf identischer gespeicherter Welt nachgewiesen.

## Build #300 Messung / #301 Korrektur / #302 Re-Test

- **#299 GRÜN**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39159534160 ; strenge Parser-Prüfungen in beiden Curios-Konfigurationen, vollständige JVM-/Neustartmatrix.
- **#300 GRÜN**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39159706366 ; auf 50-Drive-Netz Median pro **20 Controller Status-Helfer-Aufrufe**: `WorldTopologyBridge.autocrafterCount` = 99.933.139 ns; Runtime-Lookup = 9.043 ns; Drives = 77.127 ns; aktive Jobs = 9.616 ns; blockierte Jobs = 10.959 ns; Templates = 51.222 ns. Gemessene Zeit ist nicht Server-MSPT.
- **#301 ROT im vorgeschalteten Python-Gleichwertigkeitstest**: Die neue vereinfachte Autocrafter-Zählung iterierte direkt die vorberechnete aktive Komponentenmenge; im Sonderfall angrenzender Autocrafter verändert deren Iterationsreihenfolge den `seen`-Zustand und somit das Ergebnis. **Fail-closed vor Java-Build, daher nicht freigeben.**
- **#302 CI-Kandidat**: Preserve exakt das bisherige `graph().nodes()`-Iterationsverhalten; nur die **pro Knoten wiederholte** `runtimeForNode`-Komponentensuche wird durch einen einmalig pro Aufruf aufgebauten live `ownerNodes`-Set-Membership-Test ersetzt. Keinerlei persistente Caches; keine Änderung an Items, FE, Wireless oder regulären Autocrafting-Rollbacks. Zusätzliche 4.000 randomisierte Graph-/Block-/Chunk-/Conflict-Modelle und echter Java-50-Drive-GameTest mit exakt einem angeschlossenen Autocrafter. Zusätzlich verifiziert ein `javap`-Gate die finale Bytecode-Struktur.
- Auch wenn #302 grün wird, fehlen weiterhin kontrollierte Vergleichswerte für Spark-MSPT/TPS und echte Client-GUI-Interaktionen; alle P1–P8-Sperren bleiben bestehen.


## Build #302 – CI-Erfolg und isolierte Arbeitszeitmessung

- **#302 GRÜN:** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39165915921 – 127 Python-Tests (einschl. 4.000 deterministischen Gleichwertigkeitsfällen), vollständige Java-/GameTest-Matrix, Curios vorhanden/nicht vorhanden, 16 echte Drive-GUI-Zellen inkl. unterer Reihe, 50 Drives/800 Cells, 720 reale Terminal-QuickMoves (46.080 erhaltene Items), 15 Shift-Craft-Ticks (240 Logs/960 Planken), Wireless-Autorisierung und echter dedizierter Neustart. Finaler JAR-Bytecode-Gate `AUTOCRAFTER_COUNT_COMPONENT_ONCE_BYTECODE_GATE_V1 PASS`.
- **Vergleich isolierter, unkontrollierter CI-Arbeitszeiten (20 Vorgänge pro Trial, Median)**: #300 `autocrafterCount` 99.933.139 ns, #302 4.305.975 ns; komplette Controller-Statusphase #300 107.484.312 ns, #302 14.167.965 ns. Das entspricht ungefähr 23,2× und 7,6× weniger CPU-Arbeitszeit in diesen getrennten CI-Messungen. Aufgrund unterschiedlicher Laufzeit-/JIT-/GC-Bedingungen und fehlender echter Client-/Server-A/B-MSPT-Messung **keine garantierte Ingame-Beschleunigung** behaupten.
- **#303 Kandidat:** die Controller-Geräteübersicht `connectedDeviceCounts` prüft bisher dieselben angrenzenden Fremdmaschinen wiederholt auf 6-seitige Item-Capabilities, obwohl `external` bereits ein Set ist. Per-Aufruf-`checkedExternal` vermeidet mehrfaches Nachschlagen, behält Reihenfolge, Chunk-/Block-Checks und exakte Verarbeitungsklassifikation; `Direction.values()` wird innerhalb des Aufrufs wiederverwendet. Weitere 4.000 randomisierte Gleichwertigkeitsfälle, JVM-GameTests und Bytecode-Check. Keine persistente Welt-/Capability-Cache-Struktur.

Alle P1–P8-Sperren und **keine Ingame-Test-JAR** bleiben bestehen, bis die reproduzierbare Server-MSPT/Client-Belastungsprüfung erfolgreich erfolgt.

## Build #303 – zweiter Controller-Fix CI-grün, kein Ingame-Release

- **#303 GRÜN:** https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39166617752 – 129 Python-Tests (mit jeweils 4.000 Graph-/Nachbar-Modellfällen für die beiden neuesten Optimierungen), Java-Build, reale postpatch Minecraft GameTests, Curios an/aus, 50 Drives/800 echte Zellen, 720 real quickmoves/46.080 erhaltene Items, 15 Shift-Craft-Ticks, Wireless, NBT/Drive16 und Restart. Finale Bytecode-Gates `AUTOCRAFTER_COUNT_COMPONENT_ONCE_BYTECODE_GATE_V1 PASS` und `COMPILED_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1 PASS` bestätigen beide Runtime-Optimierungen in der gebauten JAR.
- Implementierung `connectedDeviceCounts`: innerer `checkedExternal`-Set überspringt wiederholte Capability-Abfragen **nur während eines synchronen Zähldurchlaufs**. Die ersten Erkennungen, Block-/Chunk-Checks, unterstützte Maschinentypen und gezählten Geräte bleiben bestehen, ohne Tick-übergreifenden Cache.
- **Controller-Statusphase** 20 Menüöffnungen Median (unkontrollierte CI, nicht Server-MSPT): #300 107.484.312 ns, #302 14.167.965 ns, #303 12.756.740 ns (ohne Curios); #303 mit Curios 9.999.904 ns. **#302 zu #303 ist wegen Run-to-Run-Varianz kein belastbar erwiesener Zusatzgewinn.** Größte bestätigte Pfadänderung ist weiterhin `autocrafterCount`-BFS-Elision.
- Eingefrorener **CI-only** Wiederherstellungszweig: `freeze/performance-wireless-b303-ci-green` @ `8381cbcc5b1c4c489ac7b791db73fc54e4f77e31`. Nicht als Ingame-validierte JAR kennzeichnen.
- **Freigabesperre bleibt aktiv**: noch keine kontrollierten A/B-Spark-Serverdaten mit identischem JAR/world/hardware, noch kein realer Client-Screen-Stress mit Schnellcrafting/Massenlagerung. Ohne diese Tests P1–P8 nicht pauschal als erledigt markieren und dem Nutzer keine Test-JAR zusenden.

## Build #304 grün und #305 gemischte GUI-/Crafting-Last (19.10.2026)

- **#304 GRÜN**: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39167486135. In 15 echten Serverticks (50 Drives, 800 Zellen) werden 240 Logs exakt zu 960 Planken verarbeitet. Zusätzlich erfolgen 360 ergebnisbezogene Shift-Klicks in bereits ausgeschöpften Ticks; 120 neu eingelegte Logs bleiben unverbraucht, ohne zusätzliche Outputs oder Duplikate. Curios vorhanden/abwesend, 129 Python-Tests, Java, Wireless, Drive16, Neustart erfolgreich.
- **#305 Testausbau, keine Runtime-Änderung**: während derselben 15 Crafting-Ticks nun 30 Controller- und 30 Autocrafter-Menüöffnungen samt Live-Status-/Preview-Prüfung auf dem echten 50-Drive-Netz. Craft- und GUI-Arbeitszeit separat protokollieren (Median/p95 GUI), keine Inventar- oder FE-Änderung durch den Test. Fail-closed bei abweichendem Status, unvollständigen Operationen, veränderter Preview oder fehlender Ausgabezeile. Volle Dual-Curios-/Neustart-/Drive-/Wireless-Matrix; Ergebnis vor erfolgreicher CI **nicht** als grün markieren.
- Mit unterschiedlichen CI-Läufen ist keine nachgewiesene TPS/MSPT-Verbesserung messbar; Client-GUI-Renderer und kontrollierte Spark A/B-Phasen bleiben ausstehend. **Ingame-JAR bleibt gesperrt.**
