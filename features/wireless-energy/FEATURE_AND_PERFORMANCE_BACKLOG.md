# Feature / Performance Priorities

## Aktuell: Wireless Stromnetz

Entwicklung ausschließlich auf `feature-wireless-energy-networks`, ausgehend von grünem Performance Build #232. Userwunsch: exakt zwei neue Blöcke namens **Network Transmitter** und **Network Receiver**; mehrere auswählbare Netze, dim.-übergreifende FE-Übertragung, konfigurierbares Wireless Charging für Inventar, Curios, Rüstung, Offhand, Hotbar.

## Nächster separater Performance-Durchgang (nicht in Feature-Branch hineinoptimieren)

Vom Nutzer am 18.10.2026 ausdrücklich bestätigt: **schnelles Craften in großen Mengen** und **schnelles Masseneinlagern über das Crafting Terminal** erzeugen weiterhin Hänger. Build #232 ist zwar grün, aber diese Belastungsprofile sind nicht behoben/nachgewiesen.

Für `projekt-performance` zurückstellen:
1. Echte Spark-Profile unter Burst-Shift-Crafting und schnellen Einlagerfolgen erfassen (Terminal-/Menü-Latenz, StorageNetwork`insertExact`, Autocraft reservations, Networking/Slot sync, Snapshot/Kopien).
2. Server-/Client-MSPT und Spitzen getrennt aufzeichnen; niemals allein an 34ms Durchschnitt entscheiden.
3. Fail-closed Optimierungsbatch, Regressionen mit derselben Benutzeraktion/Transaktionssemantik und dedizierter Server.
4. Stabiler Rückfallstand: CI Build #232 https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39074849743

**Nicht vergessen:** Performance-Branch bleibt für Performance; Wireless Feature zuerst, erst danach Burst-Lag-Fixes.

## Zusätzliche Nutzerbefunde vom 18.10.2026 (priorisiert nach Wireless)

- Beim **Öffnen der Autocrafter-GUI** steigen die durchschnittlichen Server-Tickzeiten ruckartig an. Noch **keine gesicherte Ursachenanalyse**. Prüfen: Menu-Open, Rezept-/Lager-Queries, wiederholter Refresh, Slot-/Packet-Sync, Controller-Snapshots, nicht bloß Render-FPS. Nachgelagert Spark-Profilauswertung auf `projekt-performance`.
- Bei großem/schnellem Craften und Masseneinlagern über Crafting Terminal gibt es weiter Hänger.
- Jobbezogene Zutatenreservierung fehlt sichtbar: am Start eines Autocrafting-Jobs exakt notwendige freie Items reservieren; solange nicht mehr frei verfügbar/auszahlbar, nach Abbruch noch nicht verbrauchte Mengen korrekt zurückbuchen; dauerhafter Reservierungszustand und konkurrierende Jobs.
- Gewünschter **Antenna-Look**: beide neuen Blöcke sollen echte Modelle/Texturen als zur existierenden `wireless_antenna` passende Antennen erhalten, optisch unterschieden durch Sende- und Empfangsdetails, nicht nur normale Würfeltexturen.

**Keine Vermischung:** diese drei bestehenden Autocrafting-/Terminal-Probleme ausschließlich als Backlog in `projekt-performance`. Der Feature-Branch behält seine zwei Wireless-Blöcke als erstes Entwicklungsziel. Ingame-Spark-Profil nach Nutzerbelastung dient zur Identifikation der konkreten GUI-Hotspot-Methoden.

- **Storage-Drive-GUI**: Öffnen führt laut Nutzer ebenfalls zu abruptem Anstieg der AVG-Tickzeit, unabhängig vom schon dokumentierten Autocrafter-GUI-Problem. Getrennte Spark-Phasen/Tests mit vollen Drives, Wiederöffnen und offener GUI; Quellen verdächtig: `StorageDriveBlockEntity`, `DriveMenu`, Serialisierung/Synchronisation. Hypothesen, noch kein belegter Hotspot. Im Performance-Branch `performance/BASELINE.md` dokumentiert.
