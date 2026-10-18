# Feature-Branch: Network Transmitter / Network Receiver

Status: **In Entwicklung – #241 echter Nether→Overworld-FE-Test grün, #242 Rollback-Testfixture rot, #243 Wiederholung läuft; noch keine Ingame-Freigabe**. Branch `feature-wireless-energy-networks` wurde aus dem grünen Projekt-Performance-Build #232 abgezweigt (inklusive Dokumentationsstand `4c204269f4580cf6c1d6fe2830c067c9f02960ad`). Keine Änderungen an `projekt-performance` oder privaten Quellen.

## Verbindliche Benennung und Funktionsumfang

Es gibt **genau zwei neue Blöcke**: `network_transmitter` (**Network Transmitter**) und `network_receiver` (**Network Receiver**), jeweils auch als BlockItem. Kein Plug Transmitter und keine dritte Steuer-/Ladeeinheit.

- Transmitter wird an ein vorhandenes FE-/Energiekabelsystem angeschlossen; nimmt FE **transaktional** entgegen und puffert eine begrenzte Energiemenge.
- Receiver empfängt Energie desselben auswählbaren Funknetzwerks, unabhängig von Abstand und Dimension. Lädt angeschlossene Maschinen und Energiekabel über NeoForge-FE-Sided-Capabilities.
- Mehrere benannte Funknetzwerke; Anlage, Auswahl, Umbenennung und idealerweise Löschung über eine gemeinsame GUI. Netzwerk-IDs getrennt von sichtbaren Namen; Berechtigungen/Owner-Prüfung serverseitig, keine versehentlich offenen Netze.
- Individuelle Netzwerk-Option **Wireless Charging**, mit unabhängigem Ein/Aus für **Inventar**, **Curios**, **Rüstung**, **Nebenhand** und **Hotbar**. Hotbar getrennt vom restlichen Inventar definieren. Curios muss optional bleiben und über eine isolierte Kompatibilitätsschicht laufen; kein Klassenladen der Curios-API ohne installierte Mod. Externe FE-fähige Items berücksichtigen.
- Alle Konfigurationen und Energiepuffer nach Server-Neustart wiederherstellen. Vorzugsweise eine serverseitige SavedData-Verwaltung für Netzwerk-Identität und Zugriffsrechte.
- Keine impliziten Chunk-Tickets durch drahtlose Energie: Ein Sender zählt nur, solange sein Chunk geladen ist. Dimensionen dürfen abweichen. Crossdim-Verbrauch läuft auf dem Serverthread; keine Client-Autorität.
- Das System muss Energiebilanz und NeoForge-Transactions wahren: jeder Abbruch rollt **Senderentnahme und Empfängeraufnahme** zurück. Keine Energieverdopplung, keine negativen Puffer, keine unendlichen Rekursionszyklen.
- Performance: kein globaler Block-/Chunk-Scan, keine per-Tick-Suche nach sämtlichen Maschinen, kein zusätzlicher Netzgraph-BFS. Senderindex nach Netz-ID, begrenztes Round-Robin-Budget und seltener Work-Tick (z. B. alle fünf Ticks). Curios-/Spielerinventar-Abfrage höchstens einmal pro relevantem Spieler/Intervall, **nicht** pro Block.

## Umsetzungsfolge und Abnahmekriterien

1. Netzwerk- und Energiekern mit fail-closed Modelltests: Netztrennung, Weltwechsel, Chunk unload/reload, Transaktionen, Rollbacks, Gerätebegrenzung.
2. Zwei Block-/BlockEntity-Registrierungen, FE-Capabilities und Ressourcen (Blocks, Items, Loot, Rezepte, Kreativtab, Sprache).
3. Netzwerkverwaltung und UI samt Paketen mit serverseitiger Validierung; kein freier Name aus ungeprüften Clientpaketen.
4. Wireless Charging für alle fünf Kategorien, inklusive Curios-Adapter und Energie-Items anderer Mods.
5. Dedizierter Server, zwei echte Dimensionen, GameTests für FE-Bilanzen und Rejoin/Restart; vollständige Feature-JAR erst nach erfolgreichem CI, danach Ingame-Abnahme.

## Geschützte Referenz

[Performance-Build #232](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/39074849743) ist der funktional geprüfte Ausgangspunkt; die drahtlose Energie wird im eigenen Branch entwickelt und nicht in den Performance-Branch zurückgemischt. Die am 18.10.2026 vom Nutzer gemeldeten ca. 34 MSPT wurden noch nicht durch ein kontrolliertes Vergleichsprofil bestätigt.
