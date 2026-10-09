# xSxLabs Network Storage — isolierter v1.6-Entwicklungsbereich

**Workflow:** v1.6 · **Interne Mod-Version:** 1.1.1 · **Status:** Build #2 erfolgreich; Ingame-Test ausstehend; **Build-Lock aktiv**.

Dieses Dokument begleitet ausschließlich den Branch `networkstorage-v1.6` und den Workflow `.github/workflows/networkstorage-v1.6.yml`. Der bestehende v1.1.0 Freeze Build 490 und die bisherigen Workflows dürfen nicht überschrieben werden. Der Quellcode bleibt im privaten Repository `xSxLabs/ObsidianNetwork-Build`; der öffentliche Builder enthält nur Build-Anweisungen und diese Dokumentation.

## Gewünschte Änderungen — Prüfliste

Die folgende Liste dokumentiert **Anforderungen**, nicht bereits erfolgreich bestätigte Funktionen. Status „offen“ bedeutet: Der Patch kann in der Pipeline vorhanden sein, die tatsächliche Funktion ist aber noch nicht vollständig nachgewiesen.

| Nr. | Anforderung | Status |
| --- | --- | --- |
| 1 | MultiCable-Bündel mit NETWORK, ENERGY, ITEM und FLUID in einem Block | Offen: Build-/Ingame-Verifikation |
| 2 | Cable Facades mit Blocktexturen, platzier- und entfernbar | Offen: Ingame-Verifikation |
| 3 | Polymorph-Rezeptauswahl über 16×16-Schaltfläche | Offen: Ingame-Verifikation |
| 4 | Autocrafting: genau einen Crafter je Auftrag reservieren; bei Abschluss/Abbruch freigeben | Offen: Laufzeittest |
| 5 | Gleicher Kabeltyp platziert sich benachbart; anderer Typ bündelt ohne Schleichen | Offen: Ingame-Verifikation |
| 6 | Verschiedene Kabeltypen dürfen nicht fälschlich optisch verbunden sein | Offen: Sichtprüfung |
| 7 | ITEM-/FLUID-INPUT und -OUTPUT transportieren durch Bündel | Offen: Transporttest |
| 8 | Kabelarme reichen optisch bis zum benachbarten Block | Offen: Sichtprüfung |
| 9 | INPUT-Anschlussverdickungen aus v1.1.0 beibehalten | Offen: Sichtprüfung |
| 10 | ITEM-Importer/Exporter: Funktionsseite in Eisenplattenoptik wie bei FLUID | Offen: Sichtprüfung |
| 11 | Kabelabbau mit der Hand etwa doppelt so schnell | Offen: Ingame-Zeitvergleich |

**Texturvorgabe:** Die ITEM- und FLUID-Kabel sind bereits Pipez-ähnlich gestaltet. Keine pauschale Neugestaltung. Vorhandene Gestaltung erhalten; nur konkret festgestellte Fehler an Anschlüssen, Texturübergängen und Bündeln korrigieren. Keine fremden Texturdateien ungeprüft übernehmen.

## Build-Architektur und Schutzmaßnahmen

- Öffentlicher Builder: `xSxLabs/ObsidianNetwork-Public-Builder`, Entwicklungsbranch `networkstorage-v1.6`.
- Privater Quellcode: `xSxLabs/ObsidianNetwork-Build`, derzeit im Workflow auf Branch `v1.1.1-io-facades-teleporter` fixiert. Authentifizierung über `PRIVATE_SOURCE_TOKEN`.
- Der Workflow rekonstruiert den Mod aus einer privaten Ausgangs-JAR, wendet vorhandene private Patches an und führt Source-Gates, Java-/Gradle-Build und GameTests aus. **Ein grüner Build ersetzt keinen Ingame-Test.**
- Automatische Auslösung ausschließlich durch Änderungen an `.github/workflows/networkstorage-v1.6.yml` oder `v1.6/**` auf dem isolierten Branch; manuelle Auslösung ist ebenfalls möglich.
- Vorhandene ältere Workflows und Freeze Build 490 nicht verändern.
- **Build-Lock:** Nach Bereitstellung der ersten geprüften Ingame-Test-JAR Push-Trigger abschalten; weitere Builds nur nach ausdrücklichem Benutzerkommando **„build“**.

## Fehler- und Buildprotokoll

### 2026-10-09 — v1.6 Run #1

- [GitHub Actions Run 37955076562](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/37955076562)
- **Ergebnis:** fehlgeschlagen; keine JAR hochgeladen.
- **Erfolgreich:** öffentlicher Checkout, privater Checkout, Java-Setup und zahlreiche private Rekonstruktions-/Feature-Patches.
- **Blocker:** `AssertionError` im Python-Source-Gate nach `BUILD246 VISUAL SOURCE GATE PASS`; veraltete Prüfung erwartete `true,false` bzw. `false,false`, obwohl der Tesseract-Patch tickende Chunk-Tickets mit `true,true` bzw. `false,true` verwendet.
- **Korrektur:** Beide Assertions auf die tatsächlichen Tick-Ticket-Parameter angepasst (Commit `8b130a7fc7b76218508a326842411e17967fecd6`).
- **Noch offen:** Folge-Build muss die Korrektur bestätigen; weitere Compiler-/GameTest-Fehler sind möglich.

### 2026-10-09 — v1.6 Run #2: Build erfolgreich

- [GitHub Actions Run 37955391053](https://github.com/xSxLabs/ObsidianNetwork-Public-Builder/actions/runs/37955391053)
- **Ergebnis:** SUCCESS. Rekonstruktion, Build-/Testschritt und Artefakt-Upload erfolgreich.
- **Artefakt:** `xsxlabs-network-storage-v1.6-internal-1.1.1-ingame-test`, GitHub Artifact-ID `11628331015`, ZIP-Größe 1.280.668 Bytes; Aufbewahrung laut GitHub bis 2026-10-23.
- **Einschränkung:** Noch kein tatsächlicher Ingame-Test; elf Anforderungen nicht als ingame bestätigt markieren.
- **Build-Lock:** Push-Trigger im isolierten Branch entfernt (Commit `24e090381b74de96eb2d3d6f0799dd9ced3e4386`); manuelle Builds erst auf ausdrückliches Kommando `build`.
- **Hinweis:** Dokumentations-Push löste Run #3 aus, bevor der Push-Trigger deaktiviert wurde. Dieser bereits gestartete Lauf kann weiterlaufen; danach keine automatischen Push-Builds.

### 2026-10-09 — Isolierter Push-Build

- Commit `ed594d26cf397cebe7e7b3c1a425bd275aa2323b`: vollständigen v1.6-Workflow auf den isolierten Branch übernommen und Push-Trigger ergänzt.
- Run #2 ist erfolgreich; Run #3 wurde durch den README-Push gestartet und ist separat zu prüfen.

## Vorgehen bei neuen Problemen

1. Fehlersymptom und reproduzierbare Schritte dokumentieren; zugehörige Run-ID und relevante Logstelle aufnehmen.
2. Ursache im tatsächlichen privaten Quellcode und in den Build-Logs untersuchen.
3. Bei API-/Rendering-/Transportfragen aktuelle NeoForge-/Minecraft-Dokumentation, offizielle GitHub-Issues und vergleichbare Implementierungen recherchieren. Versionen prüfen; keine Vermutungen als Tatsachen ausgeben.
4. Minimalen Fix entwickeln; bestehende Freeze-Funktionalität und andere Kabeltypen schützen.
5. Gezielte automatisierte Tests und, nach Freigabe bzw. vor Build-Lock, Build ausführen; anschließend Ingame-Rückmeldung einarbeiten.
6. Jede Änderung mit Datum, Commit, Fehlerursache, Fix, Teststatus und verbleibenden Risiken **hier** ergänzen.


### 2026-10-09 — Ingame-Befund: Platzieren gleicher Kabeltypen fehlgeschlagen

- **Reproduktion:** Ein FLUID-Cable in der Hand halten und auf ein bereits platziertes FLUID-Cable klicken.
- **Ist:** Es wird kein benachbartes Kabel platziert; ein zusätzlicher Stützblock ist nötig.
- **Soll:** Das neue Kabel wird an der angeklickten Blockseite direkt benachbart platziert. Entsprechend für NETWORK, ENERGY, ITEM und FLUID.
- **Abgrenzung:** Klick mit einem anderen Kabeltyp soll weiterhin das vorgesehene MultiCable-Bündel ohne Schleichen ermöglichen.
- **Status:** Gemeldeter Ingame-Fehler, Ursache und Code-Fix noch offen; kein neuer Build ohne ausdrückliches `build`.

### 2026-10-09 — Ingame-Befund: falsche optische Kabelverbindungen

- **Reproduktion:** Unterschiedliche Kabeltypen einzeln nebeneinander platzieren (kein MultiCable).
- **Ist:** Die Typen bilden optisch Verbindungsarme zueinander.
- **Soll:** Einzeln platzierte Kabel verbinden sich optisch nur mit demselben Typ.
- **Status:** Gemeldeter Ingame-Fehler, Ursache und Code-Fix noch offen.

### 2026-10-09 — Ingame-Befund: ITEM-Importer/Exporter-Operationsseite

- **Referenz:** FLUID-Importer und -Exporter besitzen bereits die gewünschte hervorgehobene Operationsseite.
- **Soll:** ITEM-Importer und -Exporter sollen dieselbe Darstellung der Operationsseite erhalten; andere Texturen beibehalten.
- **Status:** Gemeldeter Ingame-Fehler, Ursache und Code-Fix noch offen.

## Ingame-Testprotokoll (noch auszufüllen)

| Datum / JAR / Run | Bereich | Reproduktion / Beobachtung | Erwartet | Fix-Commit | Nachtest |
| --- | --- | --- | --- | --- | --- |
| — | — | Noch kein bestätigter Ingame-Test | — | — | Offen |

## Definition „fertig“

Eine Test-JAR ist erst als **bereit zum Ingame-Test** zu kennzeichnen, wenn sie erfolgreich gebaut und als GitHub-Artefakt verfügbar ist und die vorgesehenen automatisierten Gates bestehen. Die elf Punkte gelten erst als **ingame bestätigt**, wenn sie entsprechend getestet wurden. Build-Erfolg und Spieltest sind getrennt zu dokumentieren.
