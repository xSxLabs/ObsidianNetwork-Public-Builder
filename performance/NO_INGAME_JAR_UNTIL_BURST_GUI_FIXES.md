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
