# Automatische Langvideo-Vorschau

Der GitHub-Workflow `Homepage und neueste Langvideos` liest stündlich um Minute 23
den öffentlichen Videos-Reiter von Andy on Tour und veröffentlicht genau drei
fertige Langvideos. Shorts, Live-Sendungen und geplante Premieren bleiben außen vor.
Es werden weder Videos heruntergeladen noch YouTube-Zugangsdaten benötigt.

Der Workflow läuft auch bei ausgeschaltetem Mac. GitHub kann geplante Läufe
verzögern; die Aktualisierung erfolgt deshalb nicht sekundengenau. In öffentlichen
Repos deaktiviert GitHub Zeitpläne nach 60 Tagen ohne Repository-Aktivität.
Bei Bedarf unter Actions den Workflow wieder aktivieren.

Die Website wird mit GitHub Actions veröffentlicht. Der Workflow braucht nur
Lesezugriff auf den Repository-Inhalt und im Veröffentlichungsjob `pages: write`
und `id-token: write`. Kein Schreibzugriff auf Quellcode, kein persönlicher Token.
Unter Settings > Pages muss als Source `GitHub Actions` ausgewählt sein.

Die aktuelle Homepage im Repository ist gleichzeitig die Sicherungsversion.
Der Workflow ändert nur den Videoabschnitt im temporären Build. Fehler beim Abruf,
falsche Kanal-ID oder weniger als drei geeignete Videos brechen die Veröffentlichung
ab. Die zuletzt veröffentlichte Homepage bleibt dann online.

Manuell prüfen: Actions > Homepage und neueste Langvideos > Run workflow.
Rückkehr zum bisherigen Betrieb: Settings > Pages > Deploy from a branch > main / (root).
Danach den Workflow deaktivieren. Damit erscheint die im Repository gespeicherte
Version, ohne weitere automatische Videoaktualisierung.
