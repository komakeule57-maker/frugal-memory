#!/usr/bin/env python3
"""Tests fuer das Literaturarchiv (`memory_server.py --archiv`).

Laufen lassen: `.venv/bin/python test_archiv.py`

Das Archiv ist dieselbe Maschine wie das Gedaechtnis - was dort gilt, prueft
test_memory.py. Hier steht nur, was die Betriebsart anders macht: Datei,
Name an jeder Nummer, Arten, Quellenabgleich, Beschreibungen. Wie dort ohne
pytest, und jeder Test bekommt eine frische Wegwerfdatei.
"""

import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

os.environ["MEMORY_FC_AUS"] = "1"
os.environ.pop("MEMORY_LANG", None)
os.environ.pop("ARCHIVE_NAME", None)
os.environ["ARCHIVE_DB"] = str(Path(tempfile.mkdtemp(prefix="archtest-import-")) / "archive.db")
import memory_server as ms  # noqa: E402

HIER = Path(__file__).resolve().parent
ms._archiv_einrichten()

_BEFUND_A = ("Collage: Mehrkomponenten-Gleitkomma fuer Training mit wenig Speicher.\n"
             "Link: https://arxiv.org/abs/2405.03637 (geoeffnet)\n"
             "Befund: kommt ohne float32-Hauptkopie der Gewichte aus.\n"
             "Belegstaerke: Abstract")


# --------------------------------------------------------------------------
def test_dieselbe_quelle_wird_gemeldet_auch_bei_anderem_wortlaut():
    """Zwei Projekte beschreiben dasselbe Paper verschieden - der Wortvergleich
    sieht keine Dublette, die arXiv-Nummer schon."""
    ms.remember(_BEFUND_A, tags="int8-training projekt-a", art="befund")
    aus = ms.remember("Mehrkomponenten-Gleitkomma statt float32-Hauptkopie (arXiv 2405.03637), "
                      "spart Speicher beim Vortraining grosser Modelle. Beleg: Abstract",
                      tags="training-speicher projekt-b", art="methode")
    assert "Dieselbe Quelle steht schon im Archiv" in aus, aus
    assert "  archiv#1 (2405.03637)" in aus, aus


def test_dieselbe_quelle_per_doi_und_link():
    ms.remember("NITI, DOI 10.1109/TPDS.2022.3149787. Beleg: Volltext", tags="int8-training", art="befund")
    ms.remember("Ein Werkzeug, https://github.com/beispiel/werkzeug/ Beleg: Volltext",
                tags="werkzeuge", art="werkzeug")
    aus = ms.remember("Integer-only Training, doi.org/10.1109/TPDS.2022.3149787. Beleg: Abstract",
                      tags="int8-training", art="methode")
    assert "  archiv#1 (10.1109/TPDS.2022.3149787)" in aus, aus
    aus = ms.remember("Dasselbe Repo: http://www.github.com/beispiel/werkzeug Beleg: Volltext",
                      tags="werkzeuge", art="werkzeug")
    assert "  archiv#2 (github.com/beispiel/werkzeug)" in aus, aus
    # Nur ein Rechnername ist keine Fundstelle: sonst traefe er jeden Eintrag, der ihn nennt.
    aus = ms.remember("Anderes Repo auf https://github.com/ganz/anders und https://github.com Beleg: Volltext",
                      tags="werkzeuge", art="werkzeug")
    assert "Dieselbe Quelle" not in aus, aus


def test_abgeloeste_quelle_wird_nicht_mehr_gemeldet():
    ms.remember(_BEFUND_A, tags="int8-training", art="befund")
    ms.remember(_BEFUND_A + " (ergaenzt)", tags="int8-training", art="befund", ersetzt="1")
    aus = ms.remember("Nochmal arXiv:2405.03637. Beleg: Abstract", tags="int8-training", art="befund")
    assert "  archiv#2 (" in aus and "  archiv#1 (" not in aus, aus


def test_fehlende_fundstelle_und_belegstaerke_werden_angemahnt():
    aus = ms.remember("Kleine Modelle lernen Zellautomaten schlecht.", tags="zellautomaten", art="befund")
    assert "Keine Fundstelle erkannt" in aus and "Belegstaerke fehlt" in aus, aus
    aus = ms.remember(_BEFUND_A, tags="int8-training", art="befund")
    assert "Keine Fundstelle" not in aus and "Belegstaerke fehlt" not in aus, aus
    # Eine Luecke hat naturgemaess keine Fundstelle, eine Spur keinen Beleg.
    aus = ms.remember("Niemand misst Kopfbreiten unter 16.", tags="winzige-transformer", art="luecke")
    assert "Keine Fundstelle" not in aus and "Belegstaerke" not in aus, aus
    aus = ms.remember("Eine Zweitmeinung nennt Silva 2024 Chess Transformer.", tags="schach", art="spur")
    assert "Keine Fundstelle" not in aus and "Belegstaerke" not in aus, aus


def test_jede_nummer_traegt_den_archivnamen():
    aus = ms.remember(_BEFUND_A, tags="int8-training", art="befund")
    assert aus.startswith("Gespeichert archiv#1 "), aus
    assert "archiv#1" in ms.zeige("archiv#1") and "archiv#1" in ms.recall("Collage")
    assert "archiv#1" in ms.einordnen("1", art="methode")
    assert "gehoert zum Gedaechtnis" in ms.zeige("werkbank#1")


def test_spur_ist_ausgeblendet_und_wird_gezaehlt():
    ms.remember("Eine Zweitmeinung nennt eine Arbeit zu flauschigen Zellautomaten.", tags="zellautomaten", art="spur")
    aus = ms.recall("flauschigen Zellautomaten")
    assert "Keine Treffer" in aus and "1 Spuren/Verworfene ausgeblendet" in aus, aus
    assert "archiv#1" in ms.recall("flauschigen Zellautomaten", art="spur")
    ms.remember("Erfunden: Grcic 2023 zu flauschigen Zellautomaten, nicht auffindbar.",
                tags="zellautomaten", art="verworfen")
    aus = ms.recall("flauschigen Zellautomaten")
    assert "Keine Treffer" in aus and "2 Spuren/Verworfene ausgeblendet" in aus, aus
    assert "archiv#2" in ms.recall("flauschigen Zellautomaten", art="spur,verworfen")


def test_arten_des_gedaechtnisses_gelten_im_archiv_nicht():
    aus = ms.remember("Ein Fallstrick.", tags="x", art="fallstrick")
    assert aus.startswith("Fehler") and "befund" in aus, aus


def test_memory_db_trifft_nie_das_archiv():
    """Ein gesetztes MEMORY_DB (Gedaechtnis) darf das Archiv nicht umleiten - und umgekehrt."""
    alt = {k: os.environ.pop(k, None) for k in ("ARCHIVE_DB", "MEMORY_DB")}
    try:
        os.environ["MEMORY_DB"] = "/home/x/frugal-memory/memory.db"
        repo = Path("/irgendwo/frugal-memory")
        assert ms._db_pfad(repo, "archive.db", "ARCHIVE_DB") == repo / "archive.db"
        os.environ["ARCHIVE_DB"] = "/home/x/archiv/archive.db"
        assert ms._db_pfad(repo) == Path("/home/x/frugal-memory/memory.db")
        paket = Path("/usr/lib/python3/site-packages")
        assert ms._db_pfad(paket, "archive.db", "UNGESETZT").parts[-2:] == ("frugal-memory", "archive.db")
    finally:
        for k, v in alt.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def test_beschreibungen_und_anweisung_sind_die_des_archivs():
    werkzeuge = {w.name: w.description for w in ms.server._tool_manager.list_tools()}
    assert werkzeuge["remember"].startswith("Stores one literature entry"), werkzeuge["remember"][:80]
    for name in ("remember", "recall", "einordnen"):
        assert "befund" in werkzeuge[name] and "fallstrick" not in werkzeuge[name], name
    assert "archiv#N" in ms.server._lowlevel_server.instructions


def test_server_startet_mit_schalter_und_englisch():
    """`--archiv` ueber main(), deutsch und englisch: Werkzeuge, Arten, Name, Datei."""
    tmp = Path(tempfile.mkdtemp(prefix="archtest-start-"))
    code = """
import sys, memory_server as ms
sys.argv += ["--archiv"]
ms.server.run = lambda **k: None
ms.main()
w = {t.name: t.description for t in ms.server._tool_manager.list_tools()}
print(sorted(w))
print(ms.DB_PATH.name, ms.NAME)
print("finding" in w["remember"] or "befund" in w["remember"], "pitfall" in w["remember"] or "fallstrick" in w["remember"])
print(ms.remember("A paper, https://arxiv.org/abs/2405.03637 Evidence: abstract", tags="t", art=sys.argv[1]))
"""
    for sprache, art, name, gespeichert in (("de", "befund", "archiv", "Gespeichert archiv#1"),
                                             ("en", "finding", "archive", "Stored archive#1")):
        env = dict(os.environ, MEMORY_LANG=sprache, ARCHIVE_DB=str(tmp / f"archive-{sprache}.db"),
                   MEMORY_DB=str(tmp / "memory.db"))
        aus = subprocess.run([sys.executable, "-c", code, art, "x"], cwd=HIER, env=env,
                             capture_output=True, text=True)
        assert aus.returncode == 0, aus.stderr
        zeilen = aus.stdout.strip().splitlines()
        assert zeilen[1] == f"archive-{sprache}.db {name}", zeilen
        assert zeilen[2] == "True False", (sprache, zeilen)
        assert zeilen[3].startswith(gespeichert), (sprache, zeilen)
    assert not (tmp / "memory.db").exists(), "Gedaechtnis im Archivbetrieb angelegt"


# --------------------------------------------------------------------------
def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fehler = 0
    for name, fn in tests:
        ms.DB_PATH = Path(tempfile.mkdtemp(prefix="archtest-")) / "archive.db"
        del ms._OFFENE_FRAGEN[:]
        try:
            fn()
            print(f"ok    {name}")
        except Exception:
            fehler += 1
            print(f"FEHLER {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - fehler}/{len(tests)} bestanden")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
