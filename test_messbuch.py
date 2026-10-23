#!/usr/bin/env python3
"""Tests fuer das Messbuch (messbuch.py, `memory_server.py --messbuch`).

Laufen lassen: `.venv/bin/python test_messbuch.py`

Wie test_memory.py ohne pytest, und jeder Test bekommt eine frische
Wegwerfdatei. Das echte Messbuch wird nie geoeffnet.
"""

import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

os.environ["MEMORY_FC_AUS"] = "1"
os.environ["MEMORY_NAME"] = "werkbank"   # der Name, den die Meldung zur nackten Nummer vorschlaegt
os.environ.pop("MEMORY_LANG", None)
import messbuch as mb  # noqa: E402

HIER = Path(__file__).resolve().parent
mb.DB_PATH = Path(tempfile.mkdtemp(prefix="mbtest-import-")) / "messbuch.db"


def _neu(kennung="bild/LK", kriterium="Kette >= 30/32 und T >= 2,0"):
    aus = mb.reihe_anlegen(kennung, "Haelt die Kette mit 16 Paaren?", kriterium)
    assert aus.startswith("Angelegt"), aus
    return aus


def _db():
    conn = mb._connect()
    conn.row_factory = mb.sqlite3.Row
    return conn


# --------------------------------------------------------------------------
def test_kennung_braucht_projekt_und_kuerzel():
    assert mb.reihe_anlegen("LK", "f", "k").startswith("Fehler"), "ohne Projekt angenommen"
    _neu()
    assert "gibt es schon" in mb.reihe_anlegen("BILD/lk", "f", "k"), "Gross/klein als zweite Reihe"


def test_kuerzel_reicht_wenn_eindeutig():
    _neu("bild/LK")
    assert mb.reihen(kennung="LK").startswith("bild/LK"), mb.reihen(kennung="LK")
    _neu("ton/LK")
    aus = mb.reihen(kennung="LK")
    assert "mehrdeutig" in aus and "ton/LK" in aus, aus
    assert "Gemeint: bild/LK" in mb.reihen(kennung="bild/LKK"), "kein Vorschlag bei Tippfehler"


def test_kriterium_nach_messwert_nur_mit_grund_und_sichtbar():
    _neu()
    assert mb.reihe_aendern("LK", kriterium="T >= 1,5").startswith("bild/LK"), "vor Messwerten frei"
    mb.messwerte("LK", "T | 1,65 | langplus=45 | 1234")
    aus = mb.reihe_aendern("LK", kriterium="T >= 1,6")
    assert aus.startswith("Fehler") and "Sieger" in aus, aus
    assert "T >= 1,5" in mb.reihen(kennung="LK"), "abgewiesene Aenderung trotzdem geschrieben"
    aus = mb.reihe_aendern("LK", kriterium="T >= 1,6", grund="Schwelle aus GA falsch abgeschrieben")
    assert "NACH Messwerten" in aus, aus
    zeige = mb.reihen(kennung="LK")
    assert "NACH den ersten Messwerten geaendert" in zeige and "Kriterium nach Messwerten geaendert" in zeige, zeige
    assert "vorher: T >= 1,5" in zeige, "altes Kriterium nicht in der Chronik"
    assert "Achtung" in mb.ergebnis("LK", "erfuellt", "Kette haelt."), "Ergebnis verschweigt die Aenderung"


def test_kriterium_vor_dem_ersten_messwert_wird_bestaetigt():
    _neu()
    mb.messwerte("LK", "Kette | 32/32")
    assert "vor dem ersten Messwert" in mb.reihen(kennung="LK")


def test_ohne_kriterium_kein_urteil():
    _neu(kriterium="")
    aus = mb.ergebnis("LK", "erfuellt", "sieht gut aus")
    assert aus.startswith("Fehler") and "beobachtung" in aus, aus
    assert mb.ergebnis("LK", "beobachtung", "Echo waechst mit.").startswith("e"), "beobachtung abgewiesen"


def test_nackte_gedaechtnisnummer_wird_abgewiesen():
    _neu()
    aus = mb.reihe_aendern("LK", notiz="siehe #452")
    assert aus.startswith("Fehler") and "werkbank#452" in aus, aus
    assert mb.reihe_aendern("LK", notiz="siehe werkbank#452").startswith("bild/LK")
    # Farben und HTML-Entitaeten sind keine Nummern
    assert mb.reihe_aendern("LK", notiz="Farbe #202020, &#72;").startswith("bild/LK")


def test_fehlerhafte_messwertzeile_speichert_nichts():
    _neu()
    aus = mb.messwerte("LK", "Kette | 32/32\nnur ein Feld\nT | 1,65")
    assert aus.startswith("Fehler") and "Zeile 2" in aus, aus
    conn = _db()
    assert conn.execute("SELECT COUNT(*) FROM messwert").fetchone()[0] == 0, "halbe Eingabe gespeichert"
    conn.close()


def test_abloesen_fremder_ids_speichert_nichts():
    _neu("bild/LK")
    _neu("bild/GA")
    mb.messwerte("GA", "Kette | 16/16")          # m1, gehoert zu GA
    aus = mb.messwerte("LK", "Kette | 32/32", ersetzt="m1")
    assert aus.startswith("Fehler") and "nicht zu dieser Reihe" in aus, aus
    conn = _db()
    assert conn.execute("SELECT COUNT(*) FROM messwert").fetchone()[0] == 1, "neue Zeile trotz Fehler gespeichert"
    assert conn.execute("SELECT veraltet FROM messwert WHERE id = 1").fetchone()[0] == "", "fremde Zeile abgeloest"
    conn.close()


def test_abloesen_blendet_aus_und_voll_holt_zurueck():
    _neu()
    mb.messwerte("LK", "T | 1,56")                  # m1
    aus = mb.messwerte("LK", "T | 1,65", ersetzt="m1")
    assert "loesen m1 ab" in aus, aus
    kurz, lang = mb.reihen(kennung="LK"), mb.reihen(kennung="LK", voll=True)
    assert "1,56" not in kurz and "1 messwert" in kurz, kurz
    assert "1,56" in lang and "abgeloest durch m2" in lang, lang


def test_ablauf_geplant_laeuft_ausgewertet_und_neues_ergebnis_loest_ab():
    _neu()
    assert "[geplant]" in mb.reihen()
    assert "laeuft" in mb.rezept("LK", "./lauf langplus=45", arm="langplus=45", rechner="labor")
    mb.messwerte("LK", "Kette | 32/32 | langplus=45 | 1234\nT | 1,65 | langplus=45 | 1234")
    assert "!!" not in mb.reihen(), "Zwischenstand einer laufenden Reihe als Mangel gemeldet"
    mb.reihe_aendern("LK", status="ruht", grund="GPU belegt")
    assert "Messwerte ohne Ergebnis" in mb.reihen()
    mb.ergebnis("LK", "teilweise", "Kette haelt, Abstand nicht.")
    aus = mb.ergebnis("LK", "teilweise", "Kette haelt, Abstand nicht, weil das Echo mitwaechst.")
    assert "loest e1 ab" in aus, aus
    ueb = mb.reihen()
    assert "[ausgewertet: teilweise]" in ueb and "!!" not in ueb, ueb
    zeige = mb.reihen(kennung="LK")
    assert "Echo mitwaechst" in zeige and "Abstand nicht.\n" not in zeige, zeige


def test_ausgewertet_setzt_nur_ergebnis():
    _neu()
    assert mb.reihe_aendern("LK", status="ausgewertet").startswith("Fehler")
    assert mb.reihe_aendern("LK", status="abgebrochen").startswith("Fehler"), "Abbruch ohne Grund"
    assert "abgebrochen" in mb.reihe_aendern("LK", status="abgebrochen", grund="GPU belegt")


def test_abloesen_einer_reihe_verweist_in_beide_richtungen():
    _neu("bild/GK")
    mb.reihe_anlegen("bild/LK", "Haelt die Kette mit langen Kanten?", "Kette >= 30/32", baut_auf="bild/GK, bild/M3")
    assert "Darauf baut: bild/LK" in mb.reihen(kennung="GK")
    assert "bild/M3 (nicht im Messbuch)" in mb.reihen(kennung="bild/LK")
    mb.reihe_aendern("GK", status="abgeloest", abgeloest_durch="LK")
    assert "[abgeloest -> bild/LK]" in mb.reihen(alle=True)


def test_stille_reihe_wird_gemeldet():
    _neu()
    mb.rezept("LK", "./lauf")
    conn = _db()
    conn.execute("UPDATE reihe SET bewegt = '2026-01-01 10:00'")
    conn.commit()
    conn.close()
    assert "kein Eintrag - laeuft der Prozess noch?" in mb.reihen()


def test_uebersicht_blendet_altes_aus_und_zaehlt_es():
    _neu("bild/LK")
    _neu("bild/GK")
    mb.ergebnis("GK", "verfehlt", "kippt bei 1200.")
    conn = _db()
    conn.execute("UPDATE reihe SET bewegt = '2026-01-01 10:00' WHERE kennung = 'bild/GK'")
    conn.commit()
    conn.close()
    aus = mb.reihen()
    assert "bild/GK" not in aus.split("Ausgeblendet")[0] and "1 ausgewertet" in aus, aus
    assert "bild/GK" in mb.reihen(alle=True)
    assert "bild/GK" not in mb.reihen(projekt="ton")


def test_suche_ueber_stammformen_und_fazit():
    _neu("bild/LK")
    _neu("ton/zwerg")
    mb.ergebnis("LK", "teilweise", "Die Trennabstaende bleiben unter der Schwelle.")
    aus = mb.reihen(suche="Trennabstand Schwelle")
    assert aus.splitlines()[1].startswith("bild/LK") and "ton/zwerg" not in aus, aus


def test_server_bietet_nur_die_messbuchwerkzeuge_und_oeffnet_kein_gedaechtnis():
    tmp = Path(tempfile.mkdtemp(prefix="mbtest-server-"))
    code = ("import sys; sys.argv += ['--messbuch']; import memory_server as ms; ms._messbuch_einrichten(); "
            "print(sorted(t.name for t in ms.server._tool_manager.list_tools())); "
            "print(repr(ms.server._lowlevel_server.instructions))")
    import messbuch_en
    for sprache, werkzeuge in (("de", mb.WERKZEUGE), ("en", messbuch_en.WERKZEUGE)):
        env = dict(os.environ, MEMORY_DB=str(tmp / "memory.db"), MESSBUCH_DB=str(tmp / "messbuch.db"),
                   MEMORY_LANG=sprache)
        aus = subprocess.run([sys.executable, "-c", code], cwd=HIER, env=env, capture_output=True, text=True)
        assert aus.returncode == 0, aus.stderr
        namen = eval(aus.stdout.strip().splitlines()[-2])
        assert namen == sorted(f.__name__ for f in werkzeuge), (sprache, namen)
        # Die Anweisung des Gedaechtnisses (recall, remember) hat hier nichts verloren.
        anweisung = eval(aus.stdout.strip().splitlines()[-1])
        assert "recall" not in anweisung and werkzeuge[0].__name__ + "()" in anweisung, anweisung
    assert not (tmp / "memory.db").exists(), "Gedaechtnis im Messbuchbetrieb angelegt"



def test_tabelle_sortiert_nach_beginn_und_kuerzt():
    mb.reihe_anlegen("ton/kopie-v1", "Kopiert der Zwerg?", "r(96) >= 0,5. Sonst nicht.", nachtrag="aus kriterien.txt", begonnen="2026-10-09")
    _neu("ton/kopie-v2")
    mb.rezept("kopie-v1", "./lauf.sh", arm="gleich|profil")
    mb.ergebnis("kopie-v1", "verfehlt", "Kopiert nicht. Weiter mit v2.")
    zeilen = mb.reihen(suche="kopie", tabelle=True).splitlines()
    assert zeilen[1].startswith("| Reihe"), zeilen
    assert zeilen[3].startswith("| ton/kopie-v1 | 2026-10-09 | verfehlt"), zeilen[3]
    assert "gleich/profil" in zeilen[3] and "Weiter mit v2" not in zeilen[3], "Pipe nicht ersetzt oder Fazit nicht gekuerzt"
    assert "Kopiert nicht. …" in zeilen[3], "gekuerzter Satz ohne Auslassungszeichen"
    assert zeilen[4].startswith("| ton/kopie-v2 |"), zeilen
    assert "begonnen 2026-10-09" in mb.reihen(kennung="kopie-v1")


def test_begonnen_nur_mit_nachtrag():
    aus = mb.reihe_anlegen("ton/x", "f", "k", begonnen="2026-10-09")
    assert aus.startswith("Fehler") and "nachtrag" in aus, aus
    assert mb.reihe_anlegen("ton/x", "f", "k", nachtrag="n", begonnen="9.10.").startswith("Fehler")
    _neu("ton/y")
    assert mb.reihe_aendern("ton/y", begonnen="2026-10-01").startswith("Fehler"), "begonnen ohne Nachtrag geaendert"
    mb.reihe_anlegen("ton/z", "f", "k", nachtrag="aus Datei")
    assert "begonnen 2026-10-01" in mb.reihe_aendern("ton/z", begonnen="2026-10-01")
    assert "begonnen 2026-10-01" in mb.reihen(kennung="ton/z")


def test_alte_datei_bekommt_spalte_begonnen():
    conn = mb.sqlite3.connect(mb.DB_PATH)
    conn.executescript(mb._SCHEMA.replace(",\n    begonnen TEXT NOT NULL DEFAULT ''", ""))
    conn.execute("INSERT INTO reihe (kennung, projekt, frage, status, angelegt, bewegt) "
                 "VALUES ('a/b', 'a', 'f', 'geplant', '2026-10-21 09:00', '2026-10-21 09:00')")
    conn.commit()
    conn.close()
    assert "| a/b | 2026-10-21 | geplant" in mb.reihen(tabelle=True)

# --------------------------------------------------------------------------
def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fehler = 0
    for name, fn in tests:
        mb.DB_PATH = Path(tempfile.mkdtemp(prefix="mbtest-")) / "messbuch.db"
        try:
            fn()
            print(f"ok    {name}")
        except Exception:
            fehler += 1
            print(f"FEHLER {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - fehler}/{len(tests)} bestanden")
    return 1 if fehler else 0




def test_tabelle_zeigt_rezept_auch_ohne_arm():
    _neu("ton/kopier-a")
    mb.rezept("kopier-a", "python lauf.py --seed 3")
    mb.ergebnis("kopier-a", "verfehlt", "Nein.")
    zeile = mb.reihen(kennung="ton/kopier-*", tabelle=True).splitlines()[3]
    assert "python lauf.py" in zeile and "| r" in zeile, zeile


def test_bereich_erbt_rechnernamen_und_meldung_zeigt_stelle():
    _neu("ton/b")
    assert not mb.reihe_aendern("b", notiz="siehe labor#2762-#2789 und werkbank#4 bis #9").startswith("Fehler")
    fehler = mb.reihe_aendern("b", notiz="wie in Notiz #77 beschrieben")
    assert "Stelle: ...wie in Notiz #77" in fehler, fehler
    # Im Befehl ist '#3' Code, keine Gedaechtnisnummer
    assert not mb.rezept("b", "awk '{print $1}' liste#3 | sed 's/#1//'", parameter="farbe #3").startswith("Fehler")


def test_kennungsmuster_filtert_statt_volltext():
    _neu("ton/kopier-x")
    _neu("ton-evo/welt")
    mb.reihe_aendern("welt", notiz="kopier nichts, nur Welt")
    aus = mb.reihen(kennung="ton/kopier-*", tabelle=True)
    assert "ton/kopier-x" in aus and "welt" not in aus, aus
    assert "ton-evo/welt" in mb.reihen(suche="kopier")
    assert "ton/kopier-x" in mb.reihen(kennung="kopier-*")


def test_baut_auf_nachtraeglich_setzen_und_herausnehmen():
    _neu("ton-evo/kuehl")
    _neu("ton-evo/glr")
    _neu("ton-evo/halb")
    assert "+ton-evo/kuehl" in mb.reihe_aendern("halb", baut_auf="kuehl, ton-evo/glr")
    assert "Baut auf: ton-evo/kuehl, ton-evo/glr" in mb.reihen(kennung="halb")
    assert "Darauf baut: ton-evo/halb" in mb.reihen(kennung="kuehl")
    assert "schon eingetragen" in mb.reihe_aendern("halb", baut_auf="ton-evo/kuehl")
    assert "Nicht im Messbuch: ton/alt" in mb.reihe_aendern("halb", baut_auf="ton/alt")
    assert "-ton-evo/glr" in mb.reihe_aendern("halb", baut_auf="-glr")
    zeige = mb.reihen(kennung="halb", voll=True)
    assert "Baut auf: ton-evo/kuehl, ton/alt" in zeige and "Baut auf: -ton-evo/glr" in zeige, zeige
    assert mb.reihe_aendern("halb", baut_auf="halb").startswith("Fehler")
    assert mb.reihe_aendern("halb", baut_auf="gibtsnicht").startswith("Fehler")
    assert mb.reihe_aendern("halb", baut_auf="-ton-evo/glr").startswith("Fehler")


def test_englisch_ein_ganzer_ablauf_ohne_deutsche_meldung():
    """MEMORY_LANG=en: englische Werkzeuge, Meldungen, Status und Urteile; die Datei bleibt deutsch."""
    tmp = Path(tempfile.mkdtemp(prefix="mbtest-en-"))
    code = """
import memory_server as ms, messbuch as mb, messbuch_en as en
print(en.new_series("vision/lr", "Does warmup help?", "loss < 2.0 at step 1000"))
print(en.recipe("lr", "python train.py --warmup 100", seed="1"))
print(en.measurements("lr", "loss | 1.93 | warmup | 1"))
print(en.result("lr", "met", "Warmup is worth keeping."))
print(en.series())
print(en.series(key="lr"))
print(en.edit_series("lr", status="laeuft"))
print(en.result("lr", "erfuellt", "German verdict names are accepted too."))
print(en.series(key="lr", table=False))
c = mb._connect(); print("DATEI", sorted({r[0] for r in c.execute("SELECT urteil FROM ergebnis")}))
"""
    env = dict(os.environ, MEMORY_LANG="en", MESSBUCH_DB=str(tmp / "messbuch.db"))
    aus = subprocess.run([sys.executable, "-c", code], cwd=HIER, env=env, capture_output=True, text=True)
    assert aus.returncode == 0, aus.stderr
    text = aus.stdout
    for erwartet in ("Created: vision/lr (planned).", "r1 for vision/lr. Status now: running.",
                     "m1 for vision/lr.", "e1 for vision/lr: met.", "[evaluated: met]",
                     "Criterion (fixed", "Recipes:", "History", "status running", "supersedes e1"):
        assert erwartet in text, (erwartet, text)
    for deutsch in ("Angelegt", "fuer ", "Reihe", "Kriterium", "laeuft", "erfuellt", "Chronik"):
        assert deutsch not in text.split("DATEI")[0], (deutsch, text)
    assert "DATEI ['erfuellt']" in text, "Urteil nicht deutsch in der Datei"


if __name__ == "__main__":
    sys.exit(main())
