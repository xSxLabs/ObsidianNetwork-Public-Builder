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
