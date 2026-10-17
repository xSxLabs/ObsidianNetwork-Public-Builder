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
