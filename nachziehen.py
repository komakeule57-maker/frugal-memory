#!/usr/bin/env python3
"""Rechnet die abgeleiteten Spalten neu und bringt das Markenverzeichnis in Deckung.

Warum es das braucht: `mem.stems` und `mem.teile` sind Momentaufnahmen.
`teile` haengt am Vokabular des Augenblicks, `stems` an den Regeln in
morphologie.py - und beide werden nur beim Einfuegen gerechnet. Ein UPDATE auf
`tags` (so geschehen in migration_marken.py) oder eine geaenderte Stemmer-Regel
laesst sie lautlos driften; gemessen waren es 27 Eintraege, davon 20, deren
Projektmarke fuer die Stammsuche unsichtbar war (#1424).

Nach jedem Eingriff laufen lassen, der `content` oder `tags` ausserhalb von
`remember` anfasst, und nach jeder Aenderung an morphologie.py.

    python3 nachziehen.py [--dry-run] [--archive]

--dry-run (--probe) zeigt nur an, was sich aendern wuerde; --archive (--archiv) nimmt sich das
Literaturarchiv vor (archive.db bzw. ARCHIVE_DB) statt des Gedaechtnisses.

Ohne MEMORY_LANG bleibt die Datei in ihrer Sprache (memory_server._sprache_folgen).
Mit MEMORY_LANG in der anderen Sprache wird sie umgerechnet - so wechselt man.
"""

import sys

import memory_server
import morphologie
from memory_server import (
    _connect, _marken_nachtragen, _nachziehen,
    _vokabel_nachtragen,
)


HILFE = """usage: frugal-memory-nachziehen [--dry-run] [--archive]

Recomputes the derived search columns and the word and tag directories.
Run it after editing the database by hand or switching MEMORY_LANG.
  --dry-run   only show what would change (also --probe)
  --archive   work on the literature archive instead (also --archiv)"""

# Jeder Schalter in beiden Sprachen; Unbekanntes wird abgewiesen, bevor die
# Datei auch nur geoeffnet ist (bis 0.3.0 legte `--help` sie an und schrieb).
SCHALTER = {"--probe": "probe", "--dry-run": "probe",
            "--archiv": "archiv", "--archive": "archiv"}


def main() -> int:
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(HILFE)
        return 0
    unbekannt = [a for a in sys.argv[1:] if a not in SCHALTER]
    if unbekannt:
        print(f"frugal-memory-nachziehen: unknown option {', '.join(unbekannt)} - nothing done.\n\n{HILFE}",
              file=sys.stderr)
        return 2
    gewollt = {SCHALTER[a] for a in sys.argv[1:]}
    probe = "probe" in gewollt
    if "archiv" in gewollt:
        memory_server._archiv_einrichten()
    # Rechnet ohnehin alles in der Sprache des Servers neu (MEMORY_LANG, sonst
    # die der Datei), darf
    # also auch die Sprachmarke der Datei umschreiben. Mit --probe wird sie
    # wie alles andere zurueckgerollt.
    # Zurueckgesetzt wird im finally: wer main() aus einem laufenden Prozess
    # ruft (die Tests), behielte sonst die Erlaubnis fuer jede spaetere Verbindung.
    memory_server.SPRACHE_UMSTELLEN = True
    try:
        conn = _connect()
    finally:
        memory_server.SPRACHE_UMSTELLEN = False
    print(f"Sprache: {morphologie.SPRACHE}")
    try:
        # ZUERST das Woerterbuch: `_nachziehen` zerlegt die Komposita dagegen,
        # ein veraltetes Verzeichnis wuerde also in die Spalten geschrieben.
        woerter = _vokabel_nachtragen(conn)
        print(f"Woerterbuch: {woerter} Woerter")
        geaendert = _nachziehen(conn)
        print(f"Abgeleitete Spalten: {len(geaendert)} Eintraege weichen ab"
              + (f" ({', '.join('#'+str(i) for i in geaendert[:12])}"
                 + (", ..." if len(geaendert) > 12 else "") + ")" if geaendert else ""))
        vorher = {r[0] for r in conn.execute("SELECT marke FROM marken")}
        anzahl = _marken_nachtragen(conn)
        nachher = {r[0] for r in conn.execute("SELECT marke FROM marken")}
        print(f"Marken im Verzeichnis: {anzahl}"
              + (f", neu: {', '.join(sorted(nachher - vorher))}" if nachher - vorher else "")
              + (f", entfallen: {', '.join(sorted(vorher - nachher))}" if vorher - nachher else ""))
        # Ketten werden hier NICHT mehr neu erkannt. Bis 0.3.0 tat
        # nachziehen das ueber den ganzen Bestand und band dabei auch neue,
        # unabhaengige Eintraege zu "zerschnittenen Memos" zusammen. Ketten
        # entstehen nur noch beim Import, unter dem, was er eingelesen hat.
        glieder = conn.execute(
            "SELECT count(*) FROM eintrag WHERE kopf IS NOT NULL").fetchone()[0]
        print(f"Zerschnittene Memos: {glieder} Kettenglieder (unveraendert)")
        if probe:
            conn.rollback()
            print("--probe: nichts geschrieben.")
        else:
            conn.commit()
            print("Geschrieben.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
