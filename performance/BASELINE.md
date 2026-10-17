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
