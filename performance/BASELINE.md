# Projekt Performance — Baseline und Sicherheitsregeln

Ausgangscommit: `b86b00aaaeb356ecfdf1065576b995f42169fe2e` (`perf-round2-bulk-crafting-after-111`).

## Änderungsregeln
- Änderungen nur auf `projekt-performance` im Public Builder; privates Build-Repository nur lesend.
- Vor jedem Eingriff reproduzierbaren Baseline-Build und Profilingdaten erfassen.
- Kein Release ohne Funktions-, Persistenz- und Performance-Regressionstests.
- Kein Itemverlust, keine Duplikation, keine Änderung der Crafting-Semantik oder des Conduit-Modus.
- Source-Gates und grüne CI ersetzen keinen echten Dedicated-Server-Neustart oder GUI-Lasttest.

## Reproduktionsmatrix
1. 64.000er Equipment Cell mit mindestens 257 unterschiedlichen Descriptoren: 25 Entnahme-/Einsetzzyklen, Inventar und NBT nach Save/Reload vergleichen, Tick-p95/p99 erfassen.
2. Crafting Terminal: mindestens 100 schnelle Craft-Aktionen, korrekten Zutatenverbrauch und Output sowie Tick-p95/p99 prüfen.
3. Bulk Storage: mindestens 100 schnelle Einlagerungszyklen über mehrere Drives und volle Cells, Bestandsintegrität und Tick-p95/p99 prüfen.
4. ITEM-Conduit: zwei Inventare verbinden, Modi setzen, Welt speichern, Dedicated-Serverprozess beenden und neu starten, Chunks laden, tatsächlichen Transfer nachweisen.

## Messdisziplin
- Gesamt-MSPT von isolierter Methodenlaufzeit trennen.
- CPU, Allocations, GC, Snapshot-/NBT-Bytes, Cache-Hits, Netzwerk-Scans und Paketfrequenz messen.
- Vorher/Nachher unter identischer Last vergleichen und Regressionen zurücknehmen.

Status: Baseline und Reproduktion noch nicht vollständig nachgewiesen. Diese Datei dokumentiert Kriterien, keine bestandenen Tests.

## Verifizierte Ausgangsbasis (GitHub Actions #195)
- Workflow: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39041948828
- Ergebnis: CI erfolgreich; **8/8 GameTests bestanden**.
- Volle Equipment Cell (64.000 Einheiten, 257 Descriptoren, 25 Einsetz-/Entnahmezyklen): Gesamt 1.778.226.697 ns, Insert 1.238.784.288 ns, Remove 381.643.027 ns, Decode 157.210.333 ns. Maximale einzelne Insert-Phase 152.560.406 ns.
- Bulk Storage (100 Zyklen, 200 Operationen à 4.096): 6.605.112 ns.
- **Einschränkung:** Der ursprüngliche GameTest läuft vor einigen finalen Performance-Patches. Diese Zahlen sind daher eine Zwischenquellen-Baseline, kein Nachweis für die final gebaute JAR.
- #196 scheiterte, weil der öffentliche Checkout noch auf den alten Branch zeigte; dies war ein Workflow-Fehler, keine bewiesene Java-Regression. Korrigiert in `758c7645aa9f0578abf51b491138f8ec6dc3bc6e`.
- Neuer Ansatz: `patches/equipment-redundant-reconcile-elision.py` verhindert einen doppelten Reconcile nach erfolgreichem Inventory-Commit, behält den expliziten Fallback bei.
- Zusätzlicher Post-Patch-GameTest wurde eingefügt; seine Resultate sind noch nicht als bestanden bestätigt.
- Ein GameTest ist kein Client-GUI-Stresstest und keine persistenzgeprüfte, echte Dedicated-Server-Neustartsequenz.

## Offene Release-Blocker
1. Reproduzierbarer Ingame-GUI-Test mit wiederholtem Schließen/Öffnen und 64k Equipment Cell.
2. Schnelle GUI-Crafting- und Bulk-Deposit-Belastung mit Ergebnis-/Bestandsprüfung.
3. ITEM-Conduit: serverübergreifender Prozess-Neustart mit **derselben gespeicherten Welt** und nachgewiesenem echtem Itemtransfer.
4. Vergleichbare p95/p99-MSPT- und GC-Messungen vor/nach Optimierung.

## Zusätzliche Hotpath-Befunde (aus #195-Quellendumps)
- `StorageDriveBlockEntity.onContentsChanged(index)` ruft bereits `reconcileRuntimeSlot(index)`. `insertCellAt(slot,...)` rief nach `tx.commit()` nochmals `reconcileRuntimeSlot(slot)`. Der neue Patch überspringt bei bereits initialisierter Equipment-Zelle den zweiten Durchlauf und behält das explizite Reconcile bei fehlender Initialisierung als Fallback.
- `ItemConduitTicker.tick` bricht außerhalb der Tick-Phase `gameTime % 5 == 0` sofort ab. Die darin liegende Bedingung `dirty || gameTime % 5 == 0` ist daher bei jedem tatsächlich ausgeführten Transfertick wahr: Der Endpoint-Cache wird alle fünf Ticks neu aufgebaut. Das ist ein möglicher weiterer Scan-Hotpath, **noch kein validierter Änderungskandidat**.
- Der zuvor ersetzte Refresh-Ausdruck `Math.floorMod(System.identityHashCode(network), 1) * 5` ist mathematisch immer 0. Seine Ersetzung durch `0` ist äquivalent und beweist daher allein **keine** Behebung des ITEM-Conduit-Neustartfehlers.
- Conduit-Caching nicht aggressiv verlängern, bevor ein echter Neustart-/Persistenztest existiert.

## Erfolgreicher Post-Patch-Test #198
- Lauf: https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39042938373
- **Ergebnis: erfolgreich.** Sowohl vor als auch nach den finalen Patches alle 8 erforderlichen GameTests bestanden. `EQUIPMENT_REDUNDANT_RECONCILE_ELISION_V1 PASS`, `EQUIPMENT_RECONCILE_FALLBACK_GATE PASS`, `POSTPATCH_EQUIPMENT_AND_CONDUIT_GAMETEST PASS`.
- Im selben CI-Lauf: 25 Zyklen / 257 Descriptoren **vor finalen Patches** Gesamt 1.584.452.918 ns, Insert 1.134.225.652 ns, Remove 301.604.711 ns, Decode 148.091.332 ns.
- **Nach finalen Patches** Gesamt 947.192.084 ns, Insert 777.954.492 ns, Remove 2.685.478 ns, Decode 166.027.577 ns.
- Das entspricht ~40 % niedrigerer Laufzeit im Test. Vergleich nicht isoliert: zusätzliche Patches und zweiter JVM-Testlauf (Warm-up/GC-Effekte) können die Differenz beeinflussen. **Keine** p95/p99-MSPT- oder GUI-Werte.
- Bulk-Test vor finalen Patches 4.467.672 ns, nach finalen Patches 4.656.886 ns (100 Zyklen); keine statistisch gesicherte Differenz.
- Weiterer Kandidat: `patches/item-conduit-duplicate-scan-elision.py` verschiebt die bereits vorhandene Same-Tick-Transfer-Sperre vor den Endpoint-Scan. Testläufe noch ausstehend.
- GameTest-Härtung: Prüfung aller 256 Einzeldescriptoren in jedem der 25 Zyklen zusätzlich zum Hauptbestand von 63.744 und der Typanzahl 257.

## Nachprüfung am 17.10.2026: Builds #199 und #200
- [Build #199](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39043327992): `success`; `ITEM_CONDUIT_DUPLICATE_SCAN_ELISION_V1 PASS`, `ITEM_DUPLICATE_SCAN_ELISION_SOURCE_GATE PASS`, `POSTPATCH_EQUIPMENT_AND_CONDUIT_GAMETEST PASS`; vor/nach finalen Patches je 8/8 GameTests bestanden. Equipment-Gesamttest 1.859.649.083 ns vor, 1.091.091.560 ns nach finalen Patches.
- [Build #200](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39043428820): `success`; zusätzlich 256 individuelle Equipment-Descriptoren pro Zyklus geprüft, zusammen mit den 63.744 Items des Hauptdescriptors. Vor/nach finalen Patches je 8/8 GameTests bestanden. Equipment-Gesamttest 3.018.368.439 ns vor, 1.817.697.773 ns nach finalen Patches.
- Die Gegenüberstellungen sind **keine statistisch kontrollierten Performance-Benchmarks**. Sie enthalten JIT/GC- und Warm-up-Effekte. Relative Einsparung innerhalb #199 ca. 41 % und innerhalb #200 ca. 40 %, ohne belastbaren isolierten TPS-/MSPT-Beweis.
- Der ITEM-Conduit-Patch besteht Quelltextgates und vorhandene Conduit-GameTests. Ein Prozess-Neustart mit derselben gespeicherten Serverwelt und anschließendem tatsächlichen ITEM-Transfer wurde weiterhin **nicht** getestet.
- Codex-Kontingent ist keine notwendige Voraussetzung für GitHub-Codeprüfung und GitHub-Actions-Validierung über die bestehende Repository-Verbindung.


## Nachprüfung Builds #201 bis #204 (17.10.2026)

- [Build #201](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39043654628) gehört zum **anderen** Branch `perf-round2-bulk-crafting-after-111`. Die dortigen **9 GameTests bestanden**; der neue echte Dedicated-Server-Test erreichte nach erfolgreichem erstem Lauf die Dateiprüfung nicht: `Dedicated server did not save level.dat and region data`. Das ist eine Harness-/Ablagepfad- oder Persistenzdiagnose, **kein Beweis** für korrektes Itemverhalten nach einem zweiten Prozessstart.
- [Build #202](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39044825470) auf `projekt-performance`: fehlgeschlagen am streng geprüften neuen Testfixture-Anker (`64k GameTest anchor changed; fail closed`), weil YAML-Heredoc-Einrückung bereits entfernt war. **Kein Java-Produktionsfehler**; Anker im Script repariert.
- Zusätzliches test-only Script `patches/equipment-dirty-serialization-gametest.py`: nach 25 vorhandenen vollen Zellzyklen unveränderten Snapshot prüfen, im angehängten `EquipmentCellStore` sieben Einheiten entnehmen, serialisierten Bestand verifizieren, sieben wieder einfügen und auf korrekte Rückgabe beim Entfernen prüfen. Der Test läuft vor und nach finalen Runtime-Patches; keine Testklasse wird in die Distribution übernommen.
- Neustarttest `tests/integration/item_conduit_restart.py` und `ItemConduitRestartProbe.java` aus dem #201-Teststand in den isolierten Performance-Branch übernommen. Zwei eigenständige Dedicated-Server-JVMs, dieselbe gespeicherte Welt, vier ITEM-Topologien, reale Chests, konservierter Inhalt und Moduskonfiguration; der Harness sucht jetzt **eindeutig** nach `level.dat` unter dem dedizierten Testverzeichnis, statt eine unbestätigte Weltpfadposition anzunehmen. Tests bleiben fail-closed.
- #203 wurde durch die erste Workflow-Integration angestoßen, #204 durch die direkte Korrektur eines JSON-Newline-Escapes. Diese neuen Runs sind **nicht** als bestanden dokumentiert, solange ihre Ergebnisse nicht geprüft sind.
- Nicht als Release freigeben, bis vor allem Prozess-Neustarttest und realistische GUI-/p95/p99-MSPT-Tests bestätigt sind.


## Diagnose der roten Builds #202, #203 und #204

- **#202**: Nur Python-Testfixture-Anchor fehlgeschlagen (YAML-Heredoc-Einrückung), keine Java-Regression. Testfixture später korrigiert.
- **#203 und #204**: 8/8 GameTests sowohl vor als auch nach den Performance-Patches bestanden; neuer Mutations-/Persistenztest für Equipment Cell ebenfalls in beiden Durchläufen bestanden. Der nachgeschaltete echte Server-Reboot-Test stoppte nach der ersten erfolgreichen JVM, weil der Harness `level.dat` **und** mindestens ein `world/region/*.mca` direkt am angenommenen Pfad verlangte.
- **Evidenz #201** (Fehlerartefakt `12105370401`): `item-conduit-restart-before.json` beweist ersten Dedicated-Server-Prozess mit vier realen ITEM-Topologien, 60 Transfer-Ticks, vier leeren Source-Chests und exakt gefüllten Destination-Chests mit 37 Cobblestone, 5 Diamonds und 3 Emeralds; die Logdatei meldet normalen Shutdown und `All dimensions are saved`. Der Test kam **nicht** zum zweiten JVM-Prozess; über Persistenz beim Neustart ist deshalb noch nichts bewiesen.
- **Korrektur #205**: Kein blinder Pass bei fehlender `.mca`: ein nichtleeres `level.dat` bleibt Pflicht, die Region-Dateisuche ist rekursiv und wird protokolliert. Entscheidend ist, dass die **zweite unabhängige JVM** die alten Chests samt exakten Inventaren und Kabelkonfiguration tatsächlich lädt, dann weitere Items transportiert, eine Unterbrechung übersteht und die Bestände prüft. Wenn dies fehlschlägt, bleibt die CI rot und zusätzliche JSON-/Textlogs werden als Fehlerartefakt hochgeladen.
- Vor dem teuren Workflow laufen drei Python-Unit-Tests für Level-/Regiondatei-Invarianten. Alle drei wurden im laufenden #205-Log als `ok` bestätigt.
- **#205**: gestartet, Auswertung noch ausstehend. Ohne bestandene zweite JVM weiterhin keine Freigabe.


## Build #205: reproduzierter ITEM-Transferdefekt nach echtem Prozess-Neustart

- [#205](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39046458721) scheiterte **nicht** mehr an der Weltdatei-Prüfung. Zwei eigenständige Java-Prozesse wurden gestartet, und die erste Welt wurde normal gespeichert und durch den zweiten Prozess geladen.
- Alle drei Python-Manifest-Unit-Tests bestanden; die acht erforderlichen GameTests bestanden sowohl vor als auch nach den Runtime-Patches, inklusive Mutations- und Serialisierungstest der Equipment Cell.
- **Echter funktionaler Befund:** Von vier ITEM-Kabelwegen liefen nach Neustart drei korrekt (nur Bundles, Bundle–Standalone–Bundle, Standalone–Bundle–Standalone). Die reine Verbindung aus drei Standalone-ITEM-Kabeln transportierte nach Neustart die neu eingefüllten **7 Goldbarren und 9 Redstone** nicht; die Quelle behielt beide Stacks über 1200 Ticks. Vor Neustart transportierte dieselbe Route alle 5 Diamonds und 3 Emeralds.
- Log/JSON-Evidenz im Fehlerartefakt [#205 – `xsxlabs-performance-failure-evidence`](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39046458721/artifacts/12106137387). Quell- und Ziel-Chunks sowie Item-Capabilities waren verfügbar; der gespeicherte IMPORT/EXPORT-Modus der Endkabel war intakt.
- **Nicht** als Performance-/Save-Gate-Problem abtun und **nicht** als Release freigeben. Weder Produktions-Ticker-Frequenz noch Cache-Intervalle auf Verdacht ändern. Nächster Schritt #206: test-only genaue Diagnostik aller drei Kabelsegmente (west-/ostseitiger Mode) und gemischte BFS-Erreichbarkeit vor/nach Neustart; dann minimalen ursächlichen Patch.


## Build #206: Konnektivität und Persistenz der Standalone-Leitung nachgewiesen

- [#206](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39047673567): wieder rot im **echten zweiten Serverprozess**; vorhandene Testmatrix und Equipment-Integritätsgates bleiben zu bewerten, nicht umgehen.
- Vor **und** nach Neustart meldeten die drei reinen ITEM-Kabel unverändert: Quelle `WEST=IMPORT, EAST=CONNECTED`, Mitte `WEST=CONNECTED, EAST=CONNECTED`, Ziel `WEST=CONNECTED, EAST=EXPORT`. `ConduitRuntime.mixedPositions(...)` findet vor und nach Neustart exakt alle drei Kabel bei x=14,15,16, y=100, z=6.
- Der unveränderte Modus und die unveränderte BFS-Reichweite schließen einen einfachen NBT-Modusverlust oder eine getrennte Kabeltopologie als alleinige Ursache aus. Reale zweite JVM transportiert nur die reine Standalone-Linie nicht.
- **#207** ist ein bewusst fail-closed Diagnosebuild. Am Timeout protokolliert der test-only Probe zusätzlich `cableAllows`, die `exports()`-Endpointzahl und genau einen direkten Aufruf der vorhandenen `transferItem(WEST)`-Methode; auch wenn dies Items bewegen sollte, bleibt der Test rot. Dadurch lassen sich Tick-Scheduling und eigentliche Transportroutine unterscheiden, bevor der Runtime-Code modifiziert wird.

## Nachprüfung Builds #207 und #208 (17.10.2026)

- [#207](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39048308809): fehlgeschlagen beim verpflichtenden dedizierten ITEM-Neustarttest, **nicht** bei Java-Kompilation. Der erste Serverprozess transportierte die Testitems; nach Neustart wurden drei von vier Strecken erfolgreich, die reine dreiteilige Standalone-ITEM-Strecke behielt 7 Goldbarren und 9 Redstone für 1201 Ticks im Quellinventar.
- Forensik aus `xsxlabs-performance-failure-evidence`: In der blockierten Standalone-Strecke sind IMPORT/EXPORT-Modi, Chunk-Loading, Capability und BFS-Positionen vorhanden. `discovered_exports=13`, aber `filter_allows_gold=false` und `filter_allows_redstone=false`. Auch direkte diagnostische `transferItem(WEST)`-Invocation (nur im Test, CI bleibt fail-closed) bewegte kein Item. Damit ist ein reiner Ticker-Ausfall unwahrscheinlich; der ITEM-Filter blockierte den Transfer.
- [#208](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39049469303): **erfolgreich**. `patches/item-cable-empty-filter-load.py` überspringt leere persistierte Ghost-Filter-IDs, bevor sie zu Whitelist-Einträgen werden können. Explizite nichtleere Filter und die 18 Positions-Slots bleiben erhalten. Source-Patch läuft fail-closed bei verändertem Anker; Python-Vertragstests bestanden.
- `ITEM_CONDUIT_PROCESS_RESTART_V1 PASS`: zwei verschiedene Dedicated-Server-JVM-PIDs (5010, 5280), dieselbe gespeicherte Welt, vier Topologien (`three_bundles`, `three_standalone`, `bundle_standalone_bundle`, `standalone_bundle_standalone`). Ersttransfer 40 Ticks, Nach-Neustart-Transfer 80 Ticks. Konfiguration nach Reload erhalten, Item-Bestände korrekt, Trenn- und Wiederanschlusstest bestanden; Erfolg nur durch reale Tests, nicht durch einen übersprungenen Gate.
- Sowohl vor als auch nach finalen Performance-Patches **8/8 GameTests bestanden**; zusätzliche Equipment-Zell-Mutations- und Speicherprüfungen erfolgreich. `POSTPATCH_EQUIPMENT_AND_CONDUIT_GAMETEST PASS`; `BUILD 101 ALL AUTOMATABLE GATES PASS`.
- Build-Artefakt: [#208 performance candidate](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39049469303/artifacts/12106962385) enthält `xSxLabs-Network-Storage-1.1.1.jar`, Diagnose- und Neustartreports sowie `perf-hotpaths.json`. Kontrollierte SHA-256 der JAR: `d11d85a402e08f5b3925f8128a7fd0082a9c767827fa522c7c65a3476ec35129`. Kein temporärer `restarttest`-Probe-Klasseneintrag im JAR gefunden.
- **Release weiterhin nicht freigegeben**: echte Client-/GUI-Lasttests (64k-Equipment-Cell öffnen/schließen/wiedereinsetzen, schnelles Crafting, schnelle Bulk-Deposits) und robuste p95/p99-MSPT-/GC-Vorher-Nachher-Messungen fehlen. Source-Gates, synthetische Benchmarks und 8 GameTests dürfen nicht als vollständiger TPS-Nachweis ausgegeben werden.

## Build #209: Bulk-Preflight und Autocrafting-Idle-Reservierungen (17.10.2026)

- [CI #209](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39052936693) **success**, Head `85b42a45821be77edb27bbbd7bad1319c881f325`. Performance-Patches nur im öffentlichen `projekt-performance`-Branch. Das private Repository wurde nicht geändert.
- `patches/perf-bulk-preview-snapshot-elision.py`: Nur bei `StorageNetwork.previewInsertExact` wird der schreibfreie `List.copyOf(existing)`-Snapshot durch eine direkte Iteration der bereits vorhandenen Quellenmenge ersetzt. `insertExact` und `extract` behalten ihre defensiven Snapshots. Fail-closed-Gates untersagen eine Änderung, sobald `StorageCellStore.previewInsertExact` Mutation aufweist.
- `patches/perf-autocraft-idle-reservation-elision.py`: Bei `MinecraftAutocraftingService.reserveAvailable` werden unveränderte, immutable `ProcessingRequest`-Objekte wiederverwendet; erst bei einem tatsächlichen Reserve-Erfolg entsteht eine neue Liste. Extraktionsaufrufe, Reihenfolge, `Math.addExact`, Diagnostik und `List.copyOf(inputs)` bleiben erhalten.
- **Acht neue Python-Tests bestanden**, darunter 5000 synthetische Bulk-Preflight-Vergleiche und 12000 zufallsbasierte Reservierungsfälle samt Mengenerhaltung; diese Modelle sind keine Minecraft-Performance-Messung.
- Beide Runtime-Patches meldeten `PASS`; zusätzlich `BULK_AUTOCRAFT_SAFE_FASTPATH_SOURCE_GATE PASS`. Vor und nach Runtime-Patches jeweils **8/8 GameTests** bestanden. `POSTPATCH_EQUIPMENT_AND_CONDUIT_GAMETEST PASS`; der echte Prozess-Neustarttest bestätigte alle vier ITEM-Kabelwege in zwei separaten Server-JVMs (PIDs 5095 und 5364); `BUILD 101 ALL AUTOMATABLE GATES PASS`.
- Bulk-GameTest-Markierung #209 bei 100 Zyklen / 200 Storage-Operationen: **vor finalen Patches 16.992.505 ns**, **danach 10.857.995 ns**. Referenz #208 nach finalen Patches: **7.402.747 ns**. Wegen wechselnder JVM-Warm-up-, GC- und Lastbedingungen ist **kein isolierter Bulk-Speedup der neuen Änderung nachgewiesen**. Ein größerer Wert gegenüber #208 darf nicht verschwiegen werden.
- [Performance-Kandidat #209](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39052936693/artifacts/12108372802) wurde als GitHub-Actions-Artefakt hochgeladen. **Kein Release**: GUI-/Rapid-Crafting- und Bulk-Einlagerungs-Stresstests sowie kontrollierte p95/p99-MSPT-/GC-Vergleiche stehen weiterhin aus. Build #208 bleibt als zusätzlicher geprüfter Rückfallpunkt erhalten.

## Build #213: Reale Autocraft-Reservierungstests und verifizierter Performance-Bericht (17.10.2026)

- [#210](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39055634585): **rot durch Testharness**, nicht eine neue Java-Produktionsregression. Eine neue CI-only Echt-Netzwerk-Probe verlangte unveränderte `ProcessingRequest`-Objektidentität bereits beim unoptimierten Vor-Patch-Durchlauf. Dies wurde korrekt auf nach Anwendung des Patches beschränkt.
- [#211](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39055729481): **grün**, einschließlich 8/8 GameTests vor/nach, echter ITEM-Neustart und exakt wiederhergestellter Reservierung. Die erste Baseline-Mikromessung dieses Laufs ist **ungültig**, weil ein Short-Circuit 500 Testaufrufe ausließ. Folgender Build macht die Aufrufe zwingend und pinnt die Checkout-SHA.
- [#212](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39055871405): **grün** mit `github.sha`-gepinntem Quellstand, 11 Python-Tests, vor/nach je **8/8 GameTests**, echter ITEM-Prozess-Neustart auf gleicher Welt mit vier Topologien. Temporäre `FiftyDriveTest`-Reflexionsprobe führt 4500 reale `reserveAvailable`-Aufrufe pro Phase am **800-Zellen/50-Drive-Netzwerk** aus. Vor Patch wird korrekter Bestand geprüft; danach muss beim Null-Transfer das identische immutable `ProcessingRequest` erhalten bleiben. Bei tatsächlich reservierbaren 10 Einheiten muss neu reserviert, das Storage-Index-Delta exakt 10 sein, und das exakte Restore + Cleanup alle 17 zunächst eingefügten Einheiten vollständig wiederherstellen.
- #212 echte Idle-Reservierungs-Phase: Median **2.668.045 ns vor** / **2.044.626 ns nach** (9 Stichproben à 500 Reflexionsaufrufe). Diese Messung beinhaltet Reflection- und JVM-Effekte, **kein** JMH-/TPS-/GUI-Beweis. 50-Drive-Benchmark Median **7.606.014 ns vor** / **4.278.744 ns nach** für je 2000 Storage-Operationen; Bulk-Einzeltest **7.659.603 ns vor** / **8.135.282 ns nach** für 200 Operationen, also dort geringfügig langsamer. Unterschiedliche Test-JVMs und Last verursachen Schwankungen.
- **Zusätzlicher Reportfehler identifiziert**: Bis #212 schrieb die bestehende `numbers_in`-Regex zwar Marker-Listen, aber nur leere `{}`-Messwerte in `diagnostic-report.json`. Keine Java-/Mod-Regression; reine CI-Diagnostik. `performance/metric_parser.py` und sechs neue Python-Tests verwerfen leere Zeilen und lesen benannte Werte sowie die historische unbenannte Bulk-Dauer.
- [#213](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39056550235): **grün**, insgesamt **17 Python-Tests**, 8/8 GameTests je vor/nach, `PERFORMANCE_MACHINE_READABLE_METRICS_GATE PASS`, echter Neustart mit vier Kabelstrecken, `BUILD 101 ALL AUTOMATABLE GATES PASS`. JSON im Artefakt ist **geprüft gefüllt**, inklusive Equipment/64k, Bulk-100-Zyklen-Dauer und Autocraft-Median/p90. Die numerischen Mindestfelder werden seitdem fail-closed validiert.
- #213: Idle-Autocraft-Median für 500 reflektive Aufrufe **2.564.439 ns vor** / **1.450.150 ns nach**; p90 **10.017.693 ns** / **3.042.277 ns**. Bulk-200-Operationen **4.402.575 ns** / **4.634.880 ns** – **kein** nachgewiesener Bulk-Geschwindigkeitsgewinn. Weiterhin nicht isolierte JVM- und GC-Effekte; daher keine Prozentbehauptung für TPS.
- [Build-Artefakt #213](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39056550235/artifacts/12109518937) enthält `xSxLabs-Network-Storage-1.1.1.jar`, gefülltes `diagnostic-report.json`, Restart-Reports und Hotpath-Audit. JAR-SHA256: `059a9efa1887c017cb27c8fbbbe6cc236b326dfb0e85a04ae96d154f1ce01ae8`. Sie ist **identisch** zur JAR aus #212 (Test-/CI-Änderungen allein), mit **null** enthaltenen `build103`- oder `restarttest`-Klassen.
- **Release weiterhin blockiert:** echte Client-GUI-Last (64k Cell Close/Reload/Reinsert, Shift-/Autocrafting bei vielen Rezepten, schnelle Bulk-Einlagerung) und kontrollierte p95/p99-Server-MSPT/GC-Vergleiche fehlen; ein erfolgreicher automatisierter GameTest ersetzt diese nicht. Builds #208, #209 und #213 stehen als geprüfte Rückfallpunkte bereit.

## Build #214 – Reale 20-Tick-Speichermesswerte (17.10.2026)

- [Build #214](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39057700572) grün auf Commit 27a2740a8bf399d14329c2bf4c91359c3a637740: 21 Python-Tests, vor und nach Runtime-Patches jeweils 8/8 GameTests, vier reale ITEM-Neustarttopologien und gefülltes JSON mit streng geprüften Einzelmessungen.
- Speicherarbeit pro Tick für 200 echte Operationen / 20 Ticks: p95 337.768 ns vor und 397.178 ns nach Patch, Maximum 370.387 ns vor und 412.451 ns nach Patch. Nachher in dieser Stichprobe langsamer. Das sind keine kontrollierten, unabhängigen MSPT-/GC- oder Client-GUI-Messungen.
- Nächster diagnostischer Schritt: Test-only-Sampling der echten MinecraftServer Tickzeit-Ringdaten und GC-MXBean-Zähler im 50-Drive-GameTest, ohne Änderung an Produktionscode. Dies ersetzt keine kontrollierte p95/p99-MSPT-/GC- oder GUI-Validierung.

## Energie-Projekt Performance, Build #219 (Spark-Hotpath)

- Die reale Spark-Profilerstellung isoliert `EnergyConduitTicker.tick()` und `CableEnergyHandler.insert/extract` als dominante Server-Thread-Hotspots. `#218` ist mit allen automatisierten Prüfungen grün (Run 39064748599) und sicherer Rückfallpunkt.
- Neues fail-closed Patch `patches/spark-energy-ephemeral-endpoint-handlers.py`: eine Capability-Auflösung beim Finden jedes angeschlossenen Endpunkts statt erneut innerhalb aller Energie-Quell-Ziel-Paare. Die Endpunktliste und Handler werden pro `tick()`-Aufruf frisch erstellt und niemals über Ticks hinweg gespeichert. Die ursprüngliche Paarreihenfolge, `Transaction.openRoot`, `extract(1000)`, `insert`, Refund und Commit bleiben erhalten.
- Abgedeckt durch 3000 deterministische zufällige FE-Konservationsmodellfälle, Quellform-/Negativtests und vollständige Minecraft-Regression in GitHub Actions. Unverändert: Netzwerksuche pro `tick()`, Solarpanel-Code, Quell- und Zielmodi. **Kein kontrollierter Vorher-Nachher-TPS-Beweis.** Nach Freigabe gezielter Powah-/Bundle-Lasttest und Cache-Invalidierung für stärkere Beschleunigung.

## Spark-Energie-Round 2, Build #219/#220 (17.10.2026)

- [Build #219](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39065595500) **grün**: 37 Python-Tests, 8/8 GameTests vor und nach dem Patch, vier reale ITEM-Neustarttopologien. Der neue Energie-Ticker wertet Capability-Handler nur einmal pro Endpunkt/Dispatch aus; kein Handler-Cache zwischen Ticks.
- Darauf aufbauend optimiert der nächste Build den nach Spark auffälligen `ConduitTopology.invalidateIfChanged`-Pfad: statt sechs linearer `network.nodes().stream()`-Scans pro Bundle-Tick wird ein stets bei Add/Remove/Replace aktualisierter Positionsindex verwendet. Die echte physische Nachbarprüfung, `nodeChanged`-Invalidierung, FE-Mengen und Transaktionen bleiben unangetastet. Tests decken explizit Duplikatpositionen sowie Split/Merge und fail-closed Quellform ab.
- Keine Aussage über eine erzielte TPS-Steigerung: kontrollierter Vergleich unter realer Powah- und Solar-Last noch nicht durchgeführt.

## Spark-Energie: Builds #226 bis #229 (17.10.2026)

- [#226](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39071119530) **grün**. Bündel: NeoForge-invalidation-sensitiver Solar-Nachbar-ENERGY-Cache, unveränderte BFS-Positionen ohne überflüssige `.immutable()`-Kopien und hoisted `Direction.values()` in Conduit-Topologieprüfungen. Grün bedeutet CI-/GameTest-Erfolg, nicht nachgewiesene TPS-Gewinne.
- [#227](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39071901478) und [#228](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39071961770) **rot** am streng begrenzten Source-Patch für Topologie-Nachbarpositionen: die Kontrolle verlangte exakt ein `network.nodeChanged(node)`, der rekonstruierte Klassencode enthält aber mehrere solche Aufrufstellen. Die vorherigen Spark-Patches bis inklusive primitive BFS-Schlüssel liefen laut Logs erfolgreich durch; Java-Kompilierung und GameTests wurden wegen des Fail-closed-Gates **nicht** erreicht. #228 war ein unnötig duplizierter Start derselben Revision der Runtime-Patches.
- Neuer Commit passt ausschließlich die formale Prüfung an: exakt je ein erwarteter zu ersetzender Nachbar-Ausdruck, aber nur *Existenz* statt exakter Anzahl für die unveränderten Topologie-Dirty-Marker. Zusätzlicher Python-Regressionstest fordert den Erhalt beider `nodeChanged`-Aufrufstellen. [#229](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39072328702) validiert die drei gepackten Spark-Änderungen erneut (Status zum Zeitpunkt des Eintrags: läuft).
- Noch offen: vollständige CI-/GameTest-Bestätigung von #229, controlled Powah/Solar/Conduit-Last-Benchmark und erneutes Spark-Profil **auf genau der neuen JAR**. Keine Freigabe für stable oder automatischer Ingame-Test allein aus grünen Quelltests. #226 ist bis dahin der letzte bestätigte grüne Stand.

## Build #231/#232: Spark-BFS, Conduit-Scan und Ingame-Testkandidat (17.10.2026)

- [#230](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39072754350) rot **nur** wegen falscher Python-Einrückung in neuem CI-Postpatch-Gate (kein Java-Compile-/GameTest-Nachweis für diesen Lauf). In #231 korrigiert.
- [#231](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39073816944) grün: 61 Python-Tests; jeweils 8/8 GameTests vor und nach Performance-Patches; echte ITEM-Server-Neustartprüfung; JAR-Hash `6a33f145ae93dcc2c4bc7ed65472b7608d2619e53f3d067072405432c8c547e2`; Bundle/Solar/Energy-Fixes aus #226 und die drei BFS/Topology/Ticker-Patches aus #227-#231 bestätigt.
- [#232](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39074849743) **grün**; CI-Head `e45737303a0e244984773135424496649d6a4a95`; 65 Python-Tests, inklusive 50.000 modellbasierter Endpoint-Guard-Gleichwertigkeitsfälle, 8/8 GameTests vor und nach Runtime-Patches, echter ITEM-Neustart zweier dedizierter Serverprozesse, gefüllter Diagnosebericht und sämtliche Automatik-Gates grün. [CI-Artefakt #232](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39074849743/artifacts/12116941195).
- Zusätzlicher fail-closed Patch `patches/spark-conduit-runtime-neighbor-direction-reuse.py` bündelt `Direction.values()` in `ConduitRuntime` in ein privates statisches Enum-Array und verwendet in `scanEndpoints` dieselbe Nachbarposition für Live-Chunkcheck, `traversable()`-Prüfung und Blockstate-Rejektion. IO-Modi, Reihenfolge, Blockzustandsabfragen, Netzwerktraversierung und FE-Transaktionen werden nicht zwischengespeichert. Der lokale Bytecode-Vergleich gegen #231 bestätigt eine Reduktion der `Direction.values()`-Aufrufstellen in ConduitRuntime von 3 auf 1 und der `getBlockPos()`-Aufrufstellen innerhalb `scanEndpoints` von 3 auf 1.
- Installierbare Ingame-Test-JAR `xSxLabs-Network-Storage-1.1.1.jar` aus #232: SHA-256 **`ebb6fba44b9f429bb537d24d35243bf7daae97ffd08f7b304713ef97083d11be`**, 1.537.586 Bytes, `META-INF/neoforge.mods.toml` vorhanden; keine `build103`-/`restarttest`-Klassen. ZIP-Artefakt-Digest ist NICHT der JAR-Hash.
- Warnung zur **Performance-Messung**: Der unkontrollierte GameTest-Tickring in #232 zeigte p95 ~7,00 ms vorher und ~10,71 ms danach sowie p99 ~57,96 / ~92,49 ms. Diese Werte umfassen verschiedene GameTest-Lastphasen, sind nicht kontrolliert oder Spark/Powah-Last und belegen deshalb **weder Verbesserung noch Regression** der Server-TPS. Auch die Bulk-Mikromessung schwankte. Kein Stable-Release: reale Spark-Vergleichsmessung derselben Welt unter Powah-/Solar-/Conduit-Last, GUI-Stress und Nutzer-Ingame-Feedback erforderlich.
- **Status:** #232 ist für einen kontrollierten **Ingame-Test als Kandidat bereit**, nicht ingame-bestätigt und nicht in die geschützten v1.1.0-Freezes zu übernehmen. #231 bleibt ein zweiter grüner Rückfallpunkt.

## Ausstehender Autocrafting-Reservierungspuffer und Terminal-Burst-Lag (Nutzermeldung 18.10.2026)

**Priorität nach dem separat entwickelten Wireless-Energiesystem:** Der Nutzer meldet weiterhin Hänger bei sehr schnellem Massencrafting und schnellem Masseneinlagern über das Crafting Terminal. Zusätzlich werden Materialien beim Start eines Autocrafting-Jobs laut Ingame-Test **nicht exklusiv reserviert**; im Terminal erscheinen sie weiter als frei verfügbar.

**Sollverhalten – serverseitige exakte Job-Reservierung (kein bloßer UI-Trick):**

1. Bei Annahme eines Jobs die **genau für die auszuführenden Rezepte benötigten Mengen** pro Item-/Komponenten-Identität atomar aus dem frei verfügbaren Terminalbestand in eine jobgebundene Reservierungsbilanz buchen; mehrere Jobs dürfen dieselben Items nicht doppelt reservieren. Genügt der Bestand nicht, fehlende Mengen sauber melden/erzeugen; nie ungesichert überreservieren.
2. Reservierte Items sind für normale Entnahme, Quick-Move, manuelles Crafting und andere Jobs **nicht mehr frei verfügbar/sichtbar als verfügbar**. Bei einer Übersicht dürfen sie optional ausdrücklich separat als „reserviert“ erscheinen; nie als entnehmbarer Bestand.
3. Die Crafting-Stufen verbrauchen ausschließlich ihre reservierten Zutaten; Ausgaben/Zwischenergebnisse werden nachvollziehbar dem Job zugeordnet. Zwischenstände müssen Produktionsketten/Subjobs korrekt abbilden (kein vorschnelles Reservieren bereits fertiger Zwischenergebnisse; Mengen nach vollständigem Rezeptgraph und Batchanzahl).
4. Bei Abbruch/Fehlschlag wird **jede noch nicht verbrauchte Menge** genau einmal zurückgebucht und sofort wieder im Terminal angezeigt. Bereits tatsächlich verbrauchte Eingaben sind nicht künstlich rückgängig zu machen; erzeugte Outputs werden nach festgelegter Semantik korrekt verwahrt oder zurückgegeben.
5. Persistenz und Wiederaufnahme über Welt-Neustart; Freigabe bei Jobverlust, Netzwerk-Split/Merge, Device-/Drive-Entfernung, Weltentladung und konkurrierenden Abbrüchen – kein Ghost-Reserve, kein Dupe, kein Itemverlust.
6. Reservierungsbuchungen, Inventar-Snapshot und Terminal-Synchronisierung performant batchen, statt bei jedem schnellen Craft-/Einlagerereignis den gesamten Speicher zu kopieren/neu zu indexieren.

**Pflichtregressionen:** zwei konkurrierende Jobs mit knappen Zutaten; exakt richtige Mengen bei Stacks/verschachtelten Rezepten; parallele Terminal-Entnahme; Cancel vor Start / während Teilfortschritt / nach Finish; Servercrash vor/nach Reservierung und Restart; Netzwerk-Split/Merge und volle Drives; Performance-Spark während 50–100 schneller Benutzeraktionen. Automatisierte Modelltests ergänzen, dann reale Minecraft-GameTests und Nutzer-Ingame-Test. Vorherige „idle reservation elision“ darf keine fachliche Job-Reservierung umgehen.

**Isolation:** Diese Aufgaben im Branch `projekt-performance` als nachgelagerten, ausdrücklich noch **nicht implementierten** Performance-/Funktionsfix behandeln; Feature-Branch `feature-wireless-energy-networks` bleibt zunächst exklusiv für zwei Antennenblöcke, benannte drahtlose FE-Netze und Wireless Charging. Builds #231/#232 bleiben unverändert als grüne Ausgangspunkte.

## Autocrafter-GUI verursacht sprunghaften Anstieg der AVG-Tickzeit (Nutzermeldung 18.10.2026)

- Nutzer beobachtet: **Bereits das Öffnen der Autocrafter-GUI** lässt den Spark-/Server-`avg tick ms` unmittelbar nach oben springen. Die Werte, Dauer und Methode sind noch nicht quantitativ belegt; konkrete Hotspot-Methoden werden im angekündigten neuen Spark-Bericht erwartet.
- **Separat** von Massencrafting und schnellem Einlagern isolieren: zunächst GUI schließen/öffnen unter unveränderter Weltlast (mehrmals), nach Öffnen für einen Messzeitraum untätig lassen und prüfen, ob der Spike nur beim Öffnen oder dauerhaft bei offener GUI auftritt. GUI-Start, Listenrefresh, Paketsynchronisierung, Rezeptgraph, StorageNetwork-Snapshots, `MinecraftAutocraftingService`, `AutocrafterBlockEntity`, `AutocrafterMenu` und Client-Rendering unterscheiden.
- Auflösung: nicht unkritisch auf durchschnittliche Tickzeit allein schließen; Serverthread-Spark-Sample/Hotpaths, MSPT-p95/p99, Client-FPS und Paketsynchronisation auseinanderhalten.
- Ziel nach Wireless-Feature: Autocrafter-Menü **ohne teure Vollindex-/Craftability-Neuberechnung je Bildschirmaktualisierung**; gezielte invalidierungsbasierte Aktualisierung, paginierte/gebündelte Synchronisierung nur bei echten Änderungen, kurze Serverthread-Operationen; keine veralteten Verfügbarkeitsanzeigen oder Dupe-/Reserve-Regressionsfälle.
- Testgates: 20× GUI öffnen/schließen auf belegtem Controller, 60 Sekunden offen/idle, paralleles Autocrafting, 50 Drives/800 Zellen, Save-/Reload, andere Spieler, gemischte Rezeptbäume, getrennte Profile mit/ohne GUI. Alle Tests nur soweit mit reproduzierbarer realer Last aussagekräftig.
- Bisher **nur dokumentiert**. Keine Implementierung oder falsche Aussage zu der Ursache; `projekt-performance` bleibt bis zum Wireless-Abschluss code-seitig unverändert.

## Storage-Drive-GUI verursacht sprunghaften Tickzeit-Anstieg (Nutzermeldung 18.10.2026)

- Nutzerbeobachtung: Auch beim **Öffnen des Storage-Drive-GUIs** steigt die angezeigte durchschnittliche Server-Tickzeit abrupt. Keine konkrete Messreihe oder Stacktrace vorliegend; keine Ursache vorwegnehmen.
- Als **eigenständigen** GUI-Lastfall erfassen, getrennt vom zuvor gemeldeten Autocrafter-GUI-Anstieg. Gemeinsame Hotspots möglich, jedoch noch nicht belegt.
- Spark-Profil je getrennt mit geschlossener GUI, unmittelbar nach Öffnen und 30–60 Sekunden offen; mit einem bzw. vielen gefüllten Laufwerken. Unterscheiden: einmalige vollständige Slot-/Nbt-/Datensatzaufnahme beim Öffnen, wiederholtes `broadcastChanges`/Menü-Sync im Tick, Materialisierung großer Equipment-/Storage-Cell-Inhalte, `StorageDriveBlockEntity` und `DriveMenu`, serverseitige Daten-Serialisierung sowie rein clientseitiges Rendering.
- Nach abgeschlossenem Wireless-Feature in `projekt-performance` optimieren; **keine** pauschale Unterdrückung von Aktualisierungen oder Persistenz, keine Vollbestandskopien je Tick, nur validierte inkrementelle/differenzielle Snapshots und bedarfsorientierte Synchronisierung.
- Regressionen: volles Drive mit hohen Slotzahlen und vollen Item-/Equipment-Cells, wiederholtes Öffnen/Schließen, Mehrspielersicht, Slotwechsel während offener GUI, Laden/Neustart, Entnahme und Sortierung, Vergleich Server-MSPT-p95/p99 statt nur Durchschnitt.
- Bis dahin **nur dokumentiert; keine Implementierung**. Bestehende grüne Build-#232-JAR bleibt Ausgangspunkt.

## Network-Controller-GUI: Lag auch im kleinen Netz, zusätzliche MSPT-Skalierung bei 50 vollen Drives (18.10.2026)

- **Final präzisierte Nutzerbeobachtung:** Das **Öffnen der Network-Controller-GUI laggt auch im kleinen Netz**, bestehend aus Network Controller, Crafting Terminal und einem Storage Drive. Dabei ist **kein deutlicher Anstieg des durchschnittlichen MSPT** erkennbar. Mitspieler bemerken trotzdem Lags; der Server meldet `Can't keep up!`. **In großen Netzwerken mit ca. 50 vollständig gefüllten Drives treten ebenfalls Lags auf, und zusätzlich steigt dann der durchschnittliche MSPT deutlich an.** Kein Zustand ist als „lagfrei“ zu bezeichnen.
- Zwei separat zu diagnostizierende Symptome: (A) **kurze, für AVG-MSPT schlecht sichtbare Server-Blockade / Spitzenlast beim GUI-Öffnen, bereits im Kleinnetz**, (B) **zusätzlicher mit Netzgröße/Drive-Füllstand ansteigender Aufwand** bei großen Netzen. Ursache und möglicher gemeinsamer Stack sind erst durch Spark belegt.
- **Reproduktionsmatrix:** kleines Netz mit Controller + Crafting Terminal + 1 Drive; gleiche Topologie mit 50 leeren Drives; 50 teilweise gefüllte Drives; 50 komplett gefüllte Drives. Wiederholtes Öffnen mit offener/geschlossener GUI; mindestens zwei Spieler zur subjektiven Multiplayer-Lag-Messung.
- **Messung:** Spark-Serverthread-Profil unmittelbar beim Öffnen sowie bei länger offenem Menü, p95/p99/max MSPT und Tick-Walltime zusätzlich zum AVG, `Can't keep up!`-Zeitpunkte/Dauer, GC-Pausen, initiale Inventar-/Controller-Pakete, mögliche serverseitige Vollbestandskopie und Synchronisation. Falls möglich dieselbe Weltlast für Vergleichsphasen.
- **Unbestätigte Verdachtsbereiche:** Controller-Menu-Open, vollständige Drive-/Cell-Snapshots, `WorldTopologyBridge`, Menü-/Paketinitialisierung, Netzwerk- und Indexabfragen, Blockierung durch Serialization/IO. Nicht allein anhand von Symptomatik den Fehler einer bestimmten Klasse zuschreiben.
- **Spätere Regressionstests:** beide Größenvarianten dürfen weder blockieren noch `Can't keep up!` auslösen; schnelle GUI-Folgen, große Storage Cells, konkurrierende Lageroperationen, Server-Restart, Client/FPS getrennt.
- **Priorität:** nach dem isolierten Wireless-Stromnetz auf `projekt-performance`. Gegenwärtig nur der Fehlerbericht korrigiert; keine Performance-Quelländerung und kein neuer Build. Build #232 bleibt grüne Ausgangsbasis.
