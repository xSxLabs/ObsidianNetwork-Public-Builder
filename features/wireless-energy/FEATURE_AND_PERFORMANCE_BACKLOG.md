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
