#!/usr/bin/env python3
"""Messbuch: Messreihen mit Frage, Kriterium, Rezept, Messwerten und Ergebnis.

Betriebsart von memory_server.py, gestartet mit `--messbuch`. Eigene Datei
(MESSBUCH_DB, sonst messbuch.db wie beim Gedaechtnis: neben dem Skript bzw.
im Datenverzeichnis des Nutzers), eigene Werkzeuge; das Gedaechtnis wird in
dieser Betriebsart nicht geoeffnet. Englisch (Vorgabe seit 0.3.0, Deutsch mit MEMORY_LANG=de):
Meldungen ueber `_t`, Werkzeuge aus messbuch_en.py, Status und Urteile werden
an der Grenze uebersetzt - in der Datei stehen sie immer deutsch.

Warum nicht einfach Eintraege der Art `messwert`: eine Messreihe ist kein
Satz, sondern ein Ablauf - Frage, ein VORHER festgelegtes Kriterium, wie
gerechnet wurde, was herauskam, was daraus folgt, und spaeter vielleicht eine
Reihe, die sie abloest. Als lose Eintraege verteilt sich das auf ein Dutzend
Nummern, und niemand sieht, welche Reihe laeuft und noch keine Auswertung hat
(Anlass: 2026-10-21, zwei Projekte mit zusammen rund 80 Reihen auf zwei Rechnern).

Was die Bauart erzwingt, statt es der Sorgfalt zu ueberlassen:
  * Das Kriterium traegt einen Zeitstempel. `reihen` zeigt, ob es vor dem
    ersten Messwert stand; aendern laesst es sich danach nur mit Grund, und
    die Aenderung bleibt sichtbar.
  * Ohne Kriterium gibt es kein erfuellt/verfehlt, nur `beobachtung`.
  * Nichts wird geloescht. Messwerte, Rezepte und Ergebnisse werden
    abgeloest und bleiben mit `voll=True` lesbar.
  * Die Datei teilen sich mehrere Rechner. Eine Gedaechtnisnummer ohne
    Rechnernamen (`#452`) ist hier immer mehrdeutig und wird abgewiesen.
"""

import functools
import re
import sqlite3
import time
from difflib import get_close_matches
from pathlib import Path

import memory_server as ms


DB_PATH = ms._db_pfad(datei="messbuch.db", umgebung="MESSBUCH_DB")

# Was eine Reihe gerade ist. `ausgewertet` setzt nur `ergebnis`, damit der
# Status nie mehr behauptet, als im Messbuch steht.
STATUS = ("geplant", "laeuft", "ruht", "ausgewertet", "abgebrochen", "abgeloest")
STATUS_HAND = ("geplant", "laeuft", "ruht", "abgebrochen", "abgeloest")
OFFEN = ("geplant", "laeuft", "ruht")

# Das Urteil gegen das Kriterium. Geschlossen, aus demselben Grund wie die
# Arten des Gedaechtnisses: ein freies Feld zerfaellt und filtert nichts mehr.
URTEILE = (
    "erfuellt",       # Kriterium erfuellt
    "teilweise",      # mehrere Kriterien, nicht alle erfuellt - das Fazit nennt welche
    "verfehlt",       # Kriterium nicht erfuellt
    "gleichstand",    # Unterschied unter der Schwelle (in der Regel 10 %)
    "keine_aussage",  # die Messung kann die Frage nicht beantworten, weil ...
    "ungueltig",      # Lauf kaputt oder Aufbau falsch, nicht gewertet
    "beobachtung",    # es gab kein Kriterium vorab, also kein Urteil
)
OHNE_KRITERIUM = ("keine_aussage", "ungueltig", "beobachtung")

# Ab so vielen Tagen ohne Eintrag gilt eine laufende Reihe als still. Ein
# Hinweis zum Nachsehen ("laeuft der Prozess noch?"), keine Diagnose.
STILL_TAGE = 2
# Wie lange eine ausgewertete Reihe in der Vorgabeansicht bleibt.
FRISCH_TAGE = 14

_KENNUNG = re.compile(r"^[\w.+-]+/[\w.+-]+$")
# Eine Gedaechtnisnummer ohne Namen: `#452`, aber nicht `werkbank#452`,
# nicht `&#72;`, nicht die Farbe `#202020`.
_NACKTE_NUMMER = re.compile(r"(?<![\w#&/])#(\d{1,5})\b")
# Bereich `werkbank#2762-#2789`: das zweite Ende erbt den Namen des ersten.
_BEREICH = re.compile(r"(\w#\d{1,5})\s*(?:-|–|bis)\s*#(\d{1,5})\b")
_ID = re.compile(r"\b([rme])(\d+)\b", re.I)


# --------------------------------------------------------------------------
# Sprache. Schluessel ist der deutsche Text selbst, wie in memory_server._t;
# die Uebersetzungen stehen in messbuch_en.py. Status und Urteile stehen in der
# Datei immer deutsch und werden nur an der Grenze uebersetzt - englische Namen
# werden in beiden Sprachen angenommen.
# --------------------------------------------------------------------------
STATUS_EN = {"geplant": "planned", "laeuft": "running", "ruht": "paused",
             "ausgewertet": "evaluated", "abgebrochen": "aborted", "abgeloest": "superseded"}
URTEILE_EN = {"erfuellt": "met", "teilweise": "partial", "verfehlt": "missed",
              "gleichstand": "tie", "keine_aussage": "inconclusive", "ungueltig": "invalid",
              "beobachtung": "observation"}
_EIN = {en: de for de, en in (STATUS_EN | URTEILE_EN).items()}


def _t(vorlage: str, **werte) -> str:
    if ms._en():
        from messbuch_en import TEXTE_EN
        vorlage = TEXTE_EN.get(vorlage, vorlage)
    return vorlage.format(**werte) if werte else vorlage


def _aus(wort: str) -> str:
    """Status oder Urteil in der Sprache des Servers."""
    return (STATUS_EN | URTEILE_EN).get(wort, wort) if ms._en() else wort


def _liste(woerter) -> str:
    return ", ".join(_aus(w) for w in woerter)


def _ein(wort: str) -> str:
    """Status oder Urteil aus einer Eingabe: Kleinschreibung, Umlaute, englische Namen."""
    w = (wort or "").strip().lower()
    for a, b in (("ü", "ue"), ("ä", "ae"), ("ö", "oe"), (" ", "_"), ("-", "_")):
        w = w.replace(a, b)
    return _EIN.get(w, w)


def _jetzt() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def _tage_seit(ts: str) -> float:
    try:
        return (time.time() - time.mktime(time.strptime(ts[:16], "%Y-%m-%d %H:%M"))) / 86400
    except ValueError:
        return 0.0


# --------------------------------------------------------------------------
# Datenbank
# --------------------------------------------------------------------------
_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS reihe (
    id INTEGER PRIMARY KEY,
    kennung TEXT NOT NULL UNIQUE COLLATE NOCASE,
    projekt TEXT NOT NULL COLLATE NOCASE,
    frage TEXT NOT NULL,
    kriterium TEXT NOT NULL DEFAULT '',
    kriterium_ts TEXT NOT NULL DEFAULT '',
    kriterium_nachtraeglich TEXT NOT NULL DEFAULT '',
    nachtrag TEXT NOT NULL DEFAULT '',
    plan TEXT NOT NULL DEFAULT '',
    baut_auf TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ({", ".join(repr(s) for s in STATUS)})),
    abgeloest_durch TEXT NOT NULL DEFAULT '',
    angelegt TEXT NOT NULL,
    bewegt TEXT NOT NULL,
    begonnen TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS rezept (
    id INTEGER PRIMARY KEY,
    reihe INTEGER NOT NULL REFERENCES reihe(id),
    ts TEXT NOT NULL,
    arm TEXT NOT NULL DEFAULT '',
    befehl TEXT NOT NULL,
    quelltext TEXT NOT NULL DEFAULT '',
    parameter TEXT NOT NULL DEFAULT '',
    seed TEXT NOT NULL DEFAULT '',
    rechner TEXT NOT NULL DEFAULT '',
    logs TEXT NOT NULL DEFAULT '',
    notiz TEXT NOT NULL DEFAULT '',
    veraltet TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS messwert (
    id INTEGER PRIMARY KEY,
    reihe INTEGER NOT NULL REFERENCES reihe(id),
    ts TEXT NOT NULL,
    groesse TEXT NOT NULL,
    wert TEXT NOT NULL,
    arm TEXT NOT NULL DEFAULT '',
    start TEXT NOT NULL DEFAULT '',
    n TEXT NOT NULL DEFAULT '',
    quelle TEXT NOT NULL DEFAULT '',
    veraltet TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS ergebnis (
    id INTEGER PRIMARY KEY,
    reihe INTEGER NOT NULL REFERENCES reihe(id),
    ts TEXT NOT NULL,
    urteil TEXT NOT NULL CHECK (urteil IN ({", ".join(repr(u) for u in URTEILE)})),
    fazit TEXT NOT NULL,
    offen TEXT NOT NULL DEFAULT '',
    datei TEXT NOT NULL DEFAULT '',
    veraltet TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS chronik (
    id INTEGER PRIMARY KEY,
    reihe INTEGER NOT NULL REFERENCES reihe(id),
    ts TEXT NOT NULL,
    was TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS rezept_reihe ON rezept(reihe);
CREATE INDEX IF NOT EXISTS messwert_reihe ON messwert(reihe);
CREATE INDEX IF NOT EXISTS ergebnis_reihe ON ergebnis(reihe);
CREATE INDEX IF NOT EXISTS chronik_reihe ON chronik(reihe);
"""


def _connect() -> sqlite3.Connection:
    """Wie im Gedaechtnis: je Aufruf oeffnen, WAL, Sperrfrist, Fremdschluessel an."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=ms.SPERRFRIST)
    ms._wal_einschalten(conn)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    # `begonnen` kam am 2026-10-21 dazu: das wahre Anfangsdatum nachgetragener
    # Reihen. Ohne die Spalte sortiert die Querschnittstabelle nach dem Tag des
    # Nachtrags, und alles Alte steht auf einem Datum.
    if "begonnen" not in {z[1] for z in conn.execute("PRAGMA table_info(reihe)")}:
        conn.execute("ALTER TABLE reihe ADD COLUMN begonnen TEXT NOT NULL DEFAULT ''")
        conn.commit()
    return conn


class _Fehler(Exception):
    """Eine Eingabe, die abgewiesen wird. Die Meldung geht so an den Aufrufer."""


def _werkzeug(fn):
    """Faengt _Fehler und gibt die Meldung zurueck, statt eine Ausnahme zu werfen."""
    @functools.wraps(fn)
    def huelle(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _Fehler as exc:
            return _t("Fehler: {exc}", exc=exc)
    return huelle


def _nackte_nummern_pruefen(*texte: str) -> None:
    for text in texte:
        text = _BEREICH.sub(r"\1-\2", text or "")
        m = _NACKTE_NUMMER.search(text)
        if m:
            stelle = " ".join(text[max(0, m.start() - 30):m.end() + 10].split())
            raise _Fehler(_t(
                "'#{n}' ohne Rechnernamen (Stelle: ...{stelle}...). Das Messbuch kann sich mehrere "
                "Rechner teilen, und jedes Gedaechtnis zaehlt von 1 an - bitte mit dem Namen des "
                "Gedaechtnisses schreiben (Vorgabe: der Rechnername), z. B. {name}#{n}. Nichts gespeichert.",
                n=m.group(1), stelle=stelle, name=ms.NAME))


def _reihe(conn, kennung: str):
    """Findet eine Reihe ueber die volle Kennung oder, wenn eindeutig, ueber den Teil nach '/'."""
    k = (kennung or "").strip()
    if not k:
        raise _Fehler(_t("Keine Kennung angegeben."))
    zeile = conn.execute("SELECT * FROM reihe WHERE kennung = ?", (k,)).fetchone()
    if zeile:
        return zeile
    if "/" not in k:
        treffer = conn.execute(
            "SELECT * FROM reihe WHERE kennung LIKE ? ESCAPE '\\'",
            ("%/" + k.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_"),)).fetchall()
        if len(treffer) == 1:
            return treffer[0]
        if len(treffer) > 1:
            raise _Fehler(_t("'{k}' ist mehrdeutig: {liste}. Bitte die volle Kennung.",
                             k=k, liste=", ".join(t["kennung"] for t in treffer)))
    alle = [z[0] for z in conn.execute("SELECT kennung FROM reihe")]
    nah = get_close_matches(k, alle, n=3, cutoff=0.5)
    raise _Fehler(_t("Keine Reihe '{k}' im Messbuch.", k=k)
                  + (_t(" Gemeint: {nah}?", nah=", ".join(nah)) if nah else "")
                  + _t(" Neu anlegen mit reihe_anlegen."))


def _chronik(conn, reihe_id: int, was: str, ts: str) -> None:
    conn.execute("INSERT INTO chronik (reihe, ts, was) VALUES (?, ?, ?)", (reihe_id, ts, was))
    conn.execute("UPDATE reihe SET bewegt = ? WHERE id = ?", (ts, reihe_id))


def _status_setzen(conn, r, neu: str, ts: str, warum: str) -> None:
    if r["status"] != neu:
        conn.execute("UPDATE reihe SET status = ? WHERE id = ?", (neu, r["id"]))
        _chronik(conn, r["id"], _t("Status {alt} -> {neu} ({warum})",
                                   alt=_aus(r["status"]), neu=_aus(neu), warum=warum), ts)


def _ablosen(conn, tabelle: str, praefix: str, ids: str, reihe_id: int, durch: str, ts: str) -> list:
    """Markiert Zeilen derselben Reihe als abgeloest. Fremde oder unbekannte Ids weisen alles ab."""
    nummern = []
    for p, n in _ID.findall(ids or ""):
        if p.lower() != praefix:
            raise _Fehler(_t("'{p}{n}' ist kein {was} (erwartet {praefix}<Zahl>). Nichts gespeichert.",
                             p=p, n=n, was=_t(_NAMEN[praefix]), praefix=praefix))
        nummern.append(int(n))
    if (ids or "").strip() and not nummern:
        raise _Fehler(_t("In '{ids}' steht keine Nummer der Form {praefix}12. Nichts gespeichert.",
                         ids=ids, praefix=praefix))
    for n in nummern:
        z = conn.execute(f"SELECT reihe, veraltet FROM {tabelle} WHERE id = ?", (n,)).fetchone()
        if z is None or z["reihe"] != reihe_id:
            raise _Fehler(_t("{praefix}{n} gehoert nicht zu dieser Reihe. Nichts gespeichert.",
                             praefix=praefix, n=n))
        if z["veraltet"]:
            raise _Fehler(_t("{praefix}{n} ist schon abgeloest ({wie}). Nichts gespeichert.",
                             praefix=praefix, n=n, wie=z["veraltet"]))
    for n in nummern:
        conn.execute(f"UPDATE {tabelle} SET veraltet = ? WHERE id = ?",
                     (_t("abgeloest durch {durch} am {tag}", durch=durch, tag=ts[:10]), n))
    return nummern


_NAMEN = {"r": "Rezept", "m": "Messwert", "e": "Ergebnis"}


def _spanne(praefix: str, ids: list) -> str:
    if not ids:
        return ""
    if len(ids) > 2 and ids == list(range(ids[0], ids[-1] + 1)):
        return f"{praefix}{ids[0]}-{praefix}{ids[-1]}"
    return ", ".join(f"{praefix}{i}" for i in ids)


# --------------------------------------------------------------------------
# Werkzeuge
# --------------------------------------------------------------------------
@_werkzeug
def reihe_anlegen(kennung: str, frage: str, kriterium: str, plan: str = "",
                  baut_auf: str = "", nachtrag: str = "", begonnen: str = "") -> str:
    """Neue Messreihe, VOR dem ersten Lauf. Das Kriterium bekommt einen Zeitstempel.

    Args:
        kennung: projekt/kuerzel, z. B. "bild/lr-suche".
        kriterium: Was gemessen wird, womit, was ueber besser/schlechter entscheidet. Leer = spaeter nur Urteil beobachtung.
        plan: Plan-Datei als rechner:pfad.
        baut_auf: Vorgaenger-Kennungen, kommagetrennt.
        nachtrag: Nur fuer nachtraeglich eingetragene Reihen: woher und von wann das Kriterium stammt.
        begonnen: Mit nachtrag: wann die Reihe wirklich anfing, JJJJ-MM-TT.
    """
    kennung = (kennung or "").strip()
    if not _KENNUNG.match(kennung):
        raise _Fehler(_t("Kennung '{k}' hat nicht die Form projekt/kuerzel (z. B. bild/lr-suche).", k=kennung))
    if not (frage or "").strip():
        raise _Fehler(_t("Ohne Frage keine Reihe."))
    _nackte_nummern_pruefen(frage, kriterium, plan, nachtrag)
    begonnen = (begonnen or "").strip()
    if begonnen and not (nachtrag or "").strip():
        raise _Fehler(_t("begonnen= nur zusammen mit nachtrag= - eine neue Reihe beginnt heute."))
    if begonnen and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", begonnen):
        raise _Fehler(_t("begonnen='{b}' hat nicht die Form JJJJ-MM-TT.", b=begonnen))
    ts = _jetzt()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        if conn.execute("SELECT 1 FROM reihe WHERE kennung = ?", (kennung,)).fetchone():
            raise _Fehler(_t("'{k}' gibt es schon. Ergaenzen mit reihe_aendern, ansehen mit reihen.", k=kennung))
        vorgaenger = [v for v in re.split(r"[\s,;]+", baut_auf or "") if v]
        bekannt = {z[0].lower() for z in conn.execute("SELECT kennung FROM reihe")}
        fremd = [v for v in vorgaenger if v.lower() not in bekannt]
        cur = conn.execute(
            "INSERT INTO reihe (kennung, projekt, frage, kriterium, kriterium_ts, nachtrag, plan, "
            "baut_auf, status, angelegt, bewegt, begonnen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (kennung, kennung.split("/")[0], frage.strip(), (kriterium or "").strip(),
             ts if (kriterium or "").strip() else "", (nachtrag or "").strip(), (plan or "").strip(),
             ", ".join(vorgaenger), "geplant", ts, ts, begonnen or ts[:10]))
        _chronik(conn, cur.lastrowid, _t("angelegt")
                 + (_t(" (Nachtrag: {n})", n=nachtrag.strip()) if nachtrag else ""), ts)
        conn.commit()
    finally:
        conn.close()
    aus = _t("Angelegt: {k} ({s}).", k=kennung, s=_aus("geplant"))
    if not (kriterium or "").strip():
        aus += _t(" OHNE Kriterium: das Ergebnis kann dann nur eine Beobachtung sein. "
                  "Nachtragen per reihe_aendern(kriterium=...), solange noch kein Messwert steht.")
    if fremd:
        aus += _t(" Nicht im Messbuch: {liste} (bleibt als Verweis stehen).", liste=", ".join(fremd))
    return aus


@_werkzeug
def reihe_aendern(kennung: str, status: str = "", kriterium: str = "", grund: str = "",
                  notiz: str = "", plan: str = "", abgeloest_durch: str = "", begonnen: str = "",
                  baut_auf: str = "") -> str:
    """Reihe ergaenzen oder aendern; alles landet in ihrer Chronik.

    Args:
        status: geplant, laeuft, ruht, abgebrochen (mit grund) oder abgeloest (mit abgeloest_durch).
        kriterium: Nach dem ersten Messwert nur mit grund, bleibt dann markiert.
        notiz: Freier Vermerk (Zwischenstand, Beobachtung).
        begonnen: Nur bei nachgetragenen Reihen: wahres Anfangsdatum, JJJJ-MM-TT.
        baut_auf: Vorgaenger nachtragen, kommagetrennt; "-kennung" nimmt einen falschen wieder heraus.
    """
    _nackte_nummern_pruefen(kriterium, grund, notiz, plan)
    status = _ein(status)
    if status == "ausgewertet":
        raise _Fehler(_t("`ausgewertet` setzt nur das Werkzeug ergebnis - der Status soll nie mehr "
                         "behaupten, als im Messbuch steht."))
    if status and status not in STATUS_HAND:
        raise _Fehler(_t("Status '{s}' gibt es nicht. Erlaubt: {erlaubt}.", s=status, erlaubt=_liste(STATUS_HAND)))
    begonnen = (begonnen or "").strip()
    if begonnen and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", begonnen):
        raise _Fehler(_t("begonnen='{b}' hat nicht die Form JJJJ-MM-TT.", b=begonnen))
    if not any((status, kriterium, notiz, plan, abgeloest_durch, begonnen, (baut_auf or "").strip())):
        raise _Fehler(_t("Nichts zu aendern angegeben."))
    ts = _jetzt()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    getan = []
    try:
        r = _reihe(conn, kennung)
        if status == "abgebrochen" and not grund.strip():
            raise _Fehler(_t("Abbrechen nur mit Grund. Nichts geaendert."))
        if status == "abgeloest" or abgeloest_durch:
            if not abgeloest_durch.strip():
                raise _Fehler(_t("Status abgeloest braucht abgeloest_durch=<Kennung der Nachfolge-Reihe>."))
            nach = _reihe(conn, abgeloest_durch)
            conn.execute("UPDATE reihe SET abgeloest_durch = ? WHERE id = ?", (nach["kennung"], r["id"]))
            _status_setzen(conn, r, "abgeloest", ts, _t("abgeloest durch {k}", k=nach["kennung"])
                           + (f": {grund.strip()}" if grund.strip() else ""))
            getan.append(_t("abgeloest durch {k}", k=nach["kennung"]))
        elif status:
            _status_setzen(conn, r, status, ts, grund.strip() or _t("von Hand"))
            getan.append(_t("Status {s}", s=_aus(status)))
        if kriterium.strip():
            gemessen = conn.execute("SELECT MIN(ts) FROM messwert WHERE reihe = ?", (r["id"],)).fetchone()[0]
            if gemessen and not grund.strip():
                raise _Fehler(_t("Seit {wann} stehen Messwerte. Ein Kriterium, das nach dem Ergebnis "
                                 "gesetzt wird, findet immer einen Sieger - aendern nur mit grund=..., "
                                 "und die Aenderung bleibt an der Reihe sichtbar. Nichts geaendert.",
                                 wann=gemessen))
            alt = r["kriterium"] or _t("(keins)")
            conn.execute("UPDATE reihe SET kriterium = ?, kriterium_ts = ? WHERE id = ?",
                         (kriterium.strip(), ts, r["id"]))
            if gemessen:
                conn.execute("UPDATE reihe SET kriterium_nachtraeglich = ? WHERE id = ?",
                             (_t("{ts}, nach Messwerten seit {wann}: {grund}",
                                 ts=ts, wann=gemessen, grund=grund.strip()), r["id"]))
            _chronik(conn, r["id"], _t("Kriterium geaendert, vorher: {alt}", alt=alt)
                     + (_t(" | Grund: {g}", g=grund.strip()) if grund.strip() else ""), ts)
            getan.append(_t("Kriterium") + (_t(" (NACH Messwerten, bleibt markiert)") if gemessen else ""))
        if begonnen:
            if not r["nachtrag"]:
                raise _Fehler(_t("begonnen= nur bei nachgetragenen Reihen - die anderen beginnen am Tag "
                                 "der Anlage. Nichts geaendert."))
            conn.execute("UPDATE reihe SET begonnen = ? WHERE id = ?", (begonnen, r["id"]))
            _chronik(conn, r["id"], _t("begonnen auf {b} gesetzt", b=begonnen), ts)
            getan.append(_t("begonnen {b}", b=begonnen))
        fremd = []
        if (baut_auf or "").strip():
            liste = [v for v in r["baut_auf"].split(", ") if v]
            dazu, weg = [], []
            for v in (v for v in re.split(r"[\s,;]+", baut_auf) if v):
                raus = v.startswith("-")
                v = v.lstrip("-")
                try:
                    v = _reihe(conn, v)["kennung"]
                except _Fehler:
                    # Wie bei reihe_anlegen: eine volle Kennung darf auf etwas ausserhalb des
                    # Messbuchs zeigen. Ein Kuerzel, das nicht eindeutig aufgeht, ist ein Fehler.
                    if "/" not in v:
                        raise
                    if not raus:
                        fremd.append(v)
                if v.lower() == r["kennung"].lower():
                    raise _Fehler(_t("{v} kann nicht auf sich selbst aufbauen. Nichts geaendert.", v=v))
                if raus:
                    treffer = [x for x in liste if x.lower() == v.lower()]
                    if not treffer:
                        raise _Fehler(_t("{k} baut nicht auf {v} auf - nichts herauszunehmen. Nichts geaendert.",
                                         k=r["kennung"], v=v))
                    liste.remove(treffer[0])
                    weg.append(treffer[0])
                elif v.lower() not in {x.lower() for x in liste}:
                    liste.append(v)
                    dazu.append(v)
            if dazu or weg:
                conn.execute("UPDATE reihe SET baut_auf = ? WHERE id = ?", (", ".join(liste), r["id"]))
                aenderung = ", ".join([f"+{v}" for v in dazu] + [f"-{v}" for v in weg])
                _chronik(conn, r["id"], _t("Baut auf: {a}", a=aenderung), ts)
                getan.append(_t("baut auf {a}", a=aenderung))
            else:
                getan.append(_t("baut auf: schon eingetragen"))
        if plan.strip():
            conn.execute("UPDATE reihe SET plan = ? WHERE id = ?", (plan.strip(), r["id"]))
            _chronik(conn, r["id"], _t("Plan: {p}", p=plan.strip()), ts)
            getan.append(_t("Plan"))
        if notiz.strip():
            _chronik(conn, r["id"], notiz.strip(), ts)
            getan.append(_t("Notiz"))
        conn.commit()
        return f"{r['kennung']}: {', '.join(getan)}." + (
            _t(" Nicht im Messbuch: {liste} (bleibt als Verweis stehen).", liste=", ".join(fremd)) if fremd else "")
    finally:
        conn.close()


@_werkzeug
def rezept(kennung: str, befehl: str, arm: str = "", quelltext: str = "", parameter: str = "",
           seed: str = "", rechner: str = "", logs: str = "", notiz: str = "", ersetzt: str = "") -> str:
    """Wie gerechnet wird, so dass ein anderer es wiederholen kann. Beim Start eintragen.

    Args:
        befehl: Der Aufruf, woertlich.
        quelltext: Datei oder Commit samt md5/Hash.
        logs: Wo die Rohdaten liegen, rechner:pfad.
        ersetzt: Abgeloeste Rezepte, z. B. "r3".
    """
    if not (befehl or "").strip():
        raise _Fehler(_t("Ohne Befehl kein Rezept."))
    _nackte_nummern_pruefen(arm, notiz)  # Befehl, Parameter usw. sind woertlich: '#3' ist dort Code
    ts = _jetzt()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        r = _reihe(conn, kennung)
        cur = conn.execute(
            "INSERT INTO rezept (reihe, ts, arm, befehl, quelltext, parameter, seed, rechner, logs, notiz) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (r["id"], ts, arm.strip(), befehl.strip(), quelltext.strip(), parameter.strip(),
             seed.strip(), rechner.strip(), logs.strip(), notiz.strip()))
        neu = f"r{cur.lastrowid}"
        alt = _ablosen(conn, "rezept", "r", ersetzt, r["id"], neu, ts)
        _chronik(conn, r["id"], _t("Rezept {neu}", neu=neu) + (f" ({arm.strip()})" if arm.strip() else "")
                 + (_t(", loest {alt} ab", alt=_spanne("r", alt)) if alt else ""), ts)
        if r["status"] == "geplant":
            _status_setzen(conn, r, "laeuft", ts, _t("Rezept {neu}", neu=neu))
        conn.commit()
    finally:
        conn.close()
    return (_t("{neu} fuer {k}", neu=neu, k=r["kennung"])
            + (_t(", loest {alt} ab", alt=_spanne("r", alt)) if alt else "")
            + (_t(". Status jetzt: {s}.", s=_aus("laeuft")) if r["status"] == "geplant" else "."))


@_werkzeug
def messwerte(kennung: str, zeilen: str, quelle: str = "", ersetzt: str = "") -> str:
    """Messwerte, eine Zeile je Wert: `Groesse | Wert | Arm | Start | n` (die letzten drei optional).

    Start = Zufallsstart/Saat (z. B. 1234), keine Uhrzeit. Der Wert bleibt woertlich ("32/32", "1,65").
    Eine fehlerhafte Zeile weist alle ab.

    Args:
        quelle: Woher die Zahlen stammen (Skript, Log, Datei).
        ersetzt: Abgeloeste Messwerte, z. B. "m3,m4".
    """
    _nackte_nummern_pruefen(zeilen, quelle)
    werte = []
    for nr, zeile in enumerate((zeilen or "").splitlines(), 1):
        if not zeile.strip():
            continue
        felder = [f.strip() for f in zeile.split("|")]
        if len(felder) < 2 or not felder[0] or not felder[1]:
            raise _Fehler(_t("Zeile {nr} ('{zeile}') hat nicht die Form 'Groesse | Wert | ...'. "
                             "Nichts gespeichert.", nr=nr, zeile=zeile.strip()))
        if len(felder) > 5:
            raise _Fehler(_t("Zeile {nr} hat {n} Felder, hoechstens 5 (Groesse | Wert | Arm | "
                             "Start | n). Nichts gespeichert.", nr=nr, n=len(felder)))
        werte.append((felder + ["", "", ""])[:5])
    if not werte:
        raise _Fehler(_t("Keine Messwerte in `zeilen`."))
    ts = _jetzt()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        r = _reihe(conn, kennung)
        ids = [conn.execute(
            "INSERT INTO messwert (reihe, ts, groesse, wert, arm, start, n, quelle) VALUES (?,?,?,?,?,?,?,?)",
            (r["id"], ts, *w, quelle.strip())).lastrowid for w in werte]
        neu = _spanne("m", ids)
        alt = _ablosen(conn, "messwert", "m", ersetzt, r["id"], neu, ts)
        abloesung = _t(", loesen {alt} ab", alt=_spanne("m", alt)) if alt else ""
        _chronik(conn, r["id"], _t("Messwerte {neu}", neu=neu) + abloesung, ts)
        if r["status"] == "geplant":
            _status_setzen(conn, r, "laeuft", ts, _t("Messwerte {neu}", neu=neu))
        conn.commit()
    finally:
        conn.close()
    aus = _t("{neu} fuer {k}", neu=neu, k=r["kennung"]) + abloesung + "."
    if not r["kriterium"]:
        aus += _t(" Die Reihe hat KEIN Kriterium - diese Werte koennen nur eine Beobachtung tragen.")
    return aus


@_werkzeug
def ergebnis(kennung: str, urteil: str, fazit: str, offen: str = "", datei: str = "") -> str:
    """Reihe auswerten; ein neues Ergebnis loest das vorige ab.

    Args:
        urteil: erfuellt, teilweise (mehrere Kriterien, nicht alle), verfehlt, gleichstand, keine_aussage, ungueltig, beobachtung (kein Kriterium vorab).
        fazit: Was daraus FOLGT, nicht die Zahlen wiederholt.
        offen: Was ausdruecklich offen bleibt.
        datei: Ergebnisdatei als rechner:pfad.
    """
    u = _ein(urteil)
    if u not in URTEILE:
        raise _Fehler(_t("Urteil '{u}' gibt es nicht. Erlaubt: {erlaubt}.", u=urteil, erlaubt=_liste(URTEILE)))
    if not (fazit or "").strip():
        raise _Fehler(_t("Ohne Fazit kein Ergebnis."))
    _nackte_nummern_pruefen(fazit, offen, datei)
    ts = _jetzt()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        r = _reihe(conn, kennung)
        if not r["kriterium"] and u not in OHNE_KRITERIUM:
            raise _Fehler(_t("{k} hat kein Kriterium - ohne Massstab gibt es kein '{u}'. "
                             "Moeglich: {moeglich}. Nichts gespeichert.",
                             k=r["kennung"], u=_aus(u), moeglich=_liste(OHNE_KRITERIUM)))
        cur = conn.execute(
            "INSERT INTO ergebnis (reihe, ts, urteil, fazit, offen, datei) VALUES (?,?,?,?,?,?)",
            (r["id"], ts, u, fazit.strip(), offen.strip(), datei.strip()))
        neu = f"e{cur.lastrowid}"
        vorige = [z[0] for z in conn.execute(
            "SELECT id FROM ergebnis WHERE reihe = ? AND veraltet = '' AND id != ?", (r["id"], cur.lastrowid))]
        for v in vorige:
            conn.execute("UPDATE ergebnis SET veraltet = ? WHERE id = ?",
                         (_t("abgeloest durch {durch} am {tag}", durch=neu, tag=ts[:10]), v))
        abloesung = _t(", loest {alt} ab", alt=_spanne("e", vorige)) if vorige else ""
        _chronik(conn, r["id"], _t("Ergebnis {neu}: {u}", neu=neu, u=_aus(u)) + abloesung, ts)
        if r["status"] not in ("abgeloest",):
            _status_setzen(conn, r, "ausgewertet", ts, _t("Ergebnis {neu}", neu=neu))
        zahl = conn.execute("SELECT COUNT(*) FROM messwert WHERE reihe = ? AND veraltet = ''",
                            (r["id"],)).fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    aus = _t("{neu} fuer {k}", neu=neu, k=r["kennung"]) + f": {_aus(u)}" + abloesung + "."
    if not zahl:
        aus += _t(" Es steht kein Messwert im Messbuch - die Zahlen, auf denen das Urteil ruht, nachtragen?")
    if r["kriterium_nachtraeglich"]:
        aus += _t(" Achtung: das Kriterium wurde nach den ersten Messwerten geaendert ({wann}).",
                  wann=r["kriterium_nachtraeglich"])
    return aus


# --------------------------------------------------------------------------
# Lesen
# --------------------------------------------------------------------------
def _hinweise(conn, r) -> list:
    """Was an einer Reihe nachzusehen ist. Hinweise, keine Diagnosen."""
    h = []
    gueltig = lambda t: conn.execute(f"SELECT COUNT(*) FROM {t} WHERE reihe = ? AND veraltet = ''",
                                     (r["id"],)).fetchone()[0]
    mw, ez, rz = gueltig("messwert"), gueltig("ergebnis"), gueltig("rezept")
    if r["status"] == "laeuft" and _tage_seit(r["bewegt"]) >= STILL_TAGE:
        h.append(_t("seit {n} Tagen kein Eintrag - laeuft der Prozess noch?", n=int(_tage_seit(r["bewegt"]))))
    # Zwischenstaende einer laufenden Reihe sind normal; vergisst jemand das
    # Ergebnis, faellt die Reihe nach STILL_TAGE ueber den Hinweis darueber auf.
    if mw and not ez and r["status"] in ("geplant", "ruht"):
        h.append(_t("Messwerte ohne Ergebnis"))
    if not r["kriterium"] and r["status"] not in ("abgebrochen", "abgeloest"):
        h.append(_t("ohne Kriterium"))
    if r["kriterium_nachtraeglich"]:
        h.append(_t("Kriterium nach Messwerten geaendert"))
    if not rz and r["status"] in ("laeuft", "ausgewertet") and not r["nachtrag"]:
        h.append(_t("ohne Rezept"))
    return h


def _uebersichtszeile(conn, r) -> str:
    e = conn.execute("SELECT urteil FROM ergebnis WHERE reihe = ? AND veraltet = '' ORDER BY id DESC LIMIT 1",
                     (r["id"],)).fetchone()
    status = _aus(r["status"]) + (f": {_aus(e['urteil'])}" if e and r["status"] == "ausgewertet" else "")
    if r["status"] == "abgeloest":
        status += f" -> {r['abgeloest_durch']}"
    h = _hinweise(conn, r)
    return (f"{r['kennung']} [{status}] {r['bewegt'][:10]} {ms._titel(r['frage'], 90)}"
            + (f"  !! {'; '.join(h)}" if h else ""))


def _kriterium_zeile(conn, r) -> str:
    if not r["kriterium"]:
        return _t("Kriterium: KEINS - Ergebnisse dieser Reihe sind Beobachtungen.")
    erst = conn.execute("SELECT MIN(ts) FROM messwert WHERE reihe = ?", (r["id"],)).fetchone()[0]
    if r["nachtrag"]:
        wann = _t("nachgetragen, Beleg: {n}", n=r["nachtrag"])
    elif r["kriterium_nachtraeglich"]:
        wann = _t("NACH den ersten Messwerten geaendert: {wie}", wie=r["kriterium_nachtraeglich"])
    elif erst and erst < r["kriterium_ts"]:
        wann = _t("festgelegt {ts}, NACH dem ersten Messwert ({erst})", ts=r["kriterium_ts"], erst=erst)
    else:
        wann = _t("festgelegt {ts}", ts=r["kriterium_ts"]) + (
            _t(", vor dem ersten Messwert") if erst else _t(", noch kein Messwert"))
    return _t("Kriterium ({wann}):", wann=wann) + f"\n  {r['kriterium']}"


def _zeige(conn, r, voll: bool) -> str:
    teile = [f"{r['kennung']} - {_aus(r['status'])}" + (f" -> {r['abgeloest_durch']}" if r["abgeloest_durch"] else "")
             + (_t(", begonnen {b}", b=r["begonnen"]) if r["begonnen"] and r["begonnen"] != r["angelegt"][:10] else "")
             + _t(", angelegt {a}, zuletzt {z}", a=r["angelegt"][:10], z=r["bewegt"])]
    h = _hinweise(conn, r)
    if h:
        teile.append("!! " + "; ".join(h))
    teile.append(_t("Frage: {f}", f=r["frage"]))
    teile.append(_kriterium_zeile(conn, r))
    if r["plan"]:
        teile.append(_t("Plan: {p}", p=r["plan"]))
    if r["baut_auf"]:
        bekannt = {z[0].lower() for z in conn.execute("SELECT kennung FROM reihe")}
        teile.append(_t("Baut auf: {a}", a=", ".join(
            v + ("" if v.lower() in bekannt else _t(" (nicht im Messbuch)")) for v in r["baut_auf"].split(", "))))
    nachfolger = [z[0] for z in conn.execute(
        "SELECT kennung FROM reihe WHERE id != ? AND "
        "(',' || REPLACE(LOWER(baut_auf), ' ', '') || ',') LIKE ?",
        (r["id"], f"%,{r['kennung'].lower()},%"))]
    if nachfolger:
        teile.append(_t("Darauf baut: {liste}", liste=", ".join(nachfolger)))

    bed = "" if voll else " AND veraltet = ''"
    rz = conn.execute(f"SELECT * FROM rezept WHERE reihe = ?{bed} ORDER BY id", (r["id"],)).fetchall()
    if rz:
        teile.append(_t("Rezepte:"))
        for z in rz:
            felder = [f"{_t(k)}: {z[k]}" for k in ("quelltext", "parameter", "seed", "rechner", "logs", "notiz") if z[k]]
            teile.append(f"  r{z['id']} [{z['ts'][:10]}]" + (f" {z['arm']}:" if z["arm"] else "")
                         + f" {z['befehl']}" + "".join(f"\n      {f}" for f in felder)
                         + (f"\n      [{z['veraltet']}]" if z["veraltet"] else ""))
    mw = conn.execute(f"SELECT * FROM messwert WHERE reihe = ?{bed} ORDER BY id", (r["id"],)).fetchall()
    if mw:
        teile.append(_t("Messwerte (Groesse | Wert | Arm | Start | n):"))
        quelle = None
        for z in mw:
            if z["quelle"] != quelle and z["quelle"]:
                teile.append(_t("  Quelle: {q}", q=z["quelle"]))
            quelle = z["quelle"]
            felder = [z["groesse"], z["wert"], z["arm"], z["start"], z["n"]]
            while felder and not felder[-1]:
                felder.pop()
            teile.append(f"  m{z['id']} " + " | ".join(felder) + (f"  [{z['veraltet']}]" if z["veraltet"] else ""))
    ez = conn.execute(f"SELECT * FROM ergebnis WHERE reihe = ?{bed} ORDER BY id DESC", (r["id"],)).fetchall()
    for z in ez:
        teile.append(_t("Ergebnis e{id} [{ts}]: {u}", id=z["id"], ts=z["ts"], u=_aus(z["urteil"]))
                     + (f"  [{z['veraltet']}]" if z["veraltet"] else ""))
        teile.append(_t("  Fazit: {f}", f=z["fazit"]))
        if z["offen"]:
            teile.append(_t("  Offen: {o}", o=z["offen"]))
        if z["datei"]:
            teile.append(_t("  Datei: {d}", d=z["datei"]))
    if not voll:
        weg = {t: conn.execute(f"SELECT COUNT(*) FROM {t} WHERE reihe = ? AND veraltet != ''",
                               (r["id"],)).fetchone()[0] for t in ("rezept", "messwert", "ergebnis")}
        if any(weg.values()):
            teile.append(_t("Abgeloest und ausgeblendet: {liste} - voll=True zeigt sie.", liste=", ".join(
                f"{n} {_t(t)}" for t, n in weg.items() if n)))
    chronik = conn.execute("SELECT ts, was FROM chronik WHERE reihe = ? ORDER BY id DESC" + ("" if voll else " LIMIT 8"),
                           (r["id"],)).fetchall()
    gesamt = conn.execute("SELECT COUNT(*) FROM chronik WHERE reihe = ?", (r["id"],)).fetchone()[0]
    teile.append(_t("Chronik") + (_t(" (juengste 8 von {n}, voll=True zeigt alle)", n=gesamt)
                                  if gesamt > len(chronik) else "") + ":")
    teile.extend(f"  {z['ts']} {z['was']}" for z in reversed(chronik))
    return "\n".join(teile)


_SATZENDE = re.compile(r"(?<=[^\s.]{3}[.!?])\s")


def _kurz(text: str, laenge: int) -> str:
    """Erster Satz, hoechstens `laenge` Zeichen, tabellentauglich."""
    ganz = " ".join((text or "").split()).replace("|", "/")
    t = _SATZENDE.split(ganz, 1)[0]
    if len(t) > laenge:
        return t[:laenge - 1].rstrip() + "…"
    # Auch ein ganzer erster Satz bekommt die Auslassung, wenn mehr folgt - sonst
    # sieht "alle vier Kriterien erfuellt." vollstaendig aus, und die
    # Einschraenkung im zweiten Satz fehlt unbemerkt.
    return t + (" …" if len(t) < len(ganz) else "")


def _tabelle(conn, zeilen) -> list:
    aus = [_t("| Reihe | Beginn | Stand | Frage | Rezept | Kriterium | Fazit |"), "|---|---|---|---|---|---|---|"]
    for r in zeilen:
        e = conn.execute("SELECT urteil, fazit FROM ergebnis WHERE reihe = ? AND veraltet = '' "
                         "ORDER BY id DESC LIMIT 1", (r["id"],)).fetchone()
        rz = conn.execute("SELECT id, arm, befehl FROM rezept WHERE reihe = ? AND veraltet = '' ORDER BY id",
                          (r["id"],)).fetchall()
        arme = list(dict.fromkeys(z["arm"] for z in rz if z["arm"]))
        # Ohne Arme: Nummer und Anfang des juengsten Befehls, statt "-" trotz Rezept.
        rezept = ", ".join(arme) if arme else (f"r{rz[-1]['id']} {rz[-1]['befehl']}" if rz else "")
        stand = _aus(e["urteil"] if e and r["status"] == "ausgewertet" else r["status"])
        aus.append("| " + " | ".join([
            r["kennung"], r["begonnen"] or r["angelegt"][:10], stand, _kurz(r["frage"], 80),
            _kurz(rezept, 40) or "-", _kurz(r["kriterium"], 80) or _t("KEINS"),
            _kurz(e["fazit"], 120) if e else "-"]) + " |")
    return aus


def _suchtext(conn, r) -> str:
    stuecke = [r["kennung"], r["frage"], r["kriterium"], r["plan"], r["nachtrag"]]
    for t, spalten in (("ergebnis", "fazit || ' ' || offen || ' ' || datei"),
                       ("rezept", "arm || ' ' || befehl || ' ' || parameter || ' ' || notiz"),
                       ("messwert", "groesse || ' ' || arm"),
                       ("chronik", "was")):
        stuecke += [z[0] for z in conn.execute(f"SELECT {spalten} FROM {t} WHERE reihe = ?", (r["id"],))]
    return " ".join(s for s in stuecke if s)


@_werkzeug
def reihen(kennung: str = "", projekt: str = "", status: str = "", suche: str = "",
           alle: bool = False, voll: bool = False, tabelle: bool = False) -> str:
    """Messbuch lesen. Ohne kennung: Uebersicht offener und frisch ausgewerteter Reihen mit Hinweisen. Mit kennung: die Reihe ganz.

    Args:
        kennung: z. B. "bild/lr-suche", oder nur "lr-suche", wenn eindeutig. Mit * ein Muster ("bild/lr-*"), das filtert.
        suche: Woerter in Frage, Kriterium, Fazit, Rezept.
        alle: Auch alte und erledigte Reihen.
        voll: Bei einer Reihe auch Abgeloestes und die ganze Chronik.
        tabelle: Querschnitt als Tabelle (Urteil, Rezept, Kriterium, Fazit kurz), nach Beginn sortiert.
    """
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        muster = kennung.strip() if "*" in kennung else ""
        if kennung.strip() and not muster:
            return _zeige(conn, _reihe(conn, kennung), voll)
        sql, werte = "SELECT * FROM reihe WHERE 1", []
        if muster:
            sql += " AND lower(kennung) GLOB lower(?)"
            werte.append(muster if "/" in muster else "*/" + muster)
        if projekt.strip():
            sql += " AND projekt = ?"
            werte.append(projekt.strip())
        if status.strip():
            sql += " AND status = ?"
            werte.append(_ein(status))
        zeilen = conn.execute(sql + " ORDER BY bewegt DESC", werte).fetchall()
        if suche.strip():
            gesucht = ms._staemme(suche)
            roh = suche.strip().lower()
            bewertet = []
            for r in zeilen:
                text = _suchtext(conn, r)
                treffer = len(gesucht & ms._staemme(text)) + (2 if roh in r["kennung"].lower() else 0)
                if treffer:
                    bewertet.append((treffer, r))
            bewertet.sort(key=lambda p: (p[0], p[1]["bewegt"]), reverse=True)
            zeilen = [r for _, r in bewertet]
            kopf = (_t("{n} Reihen zu '{s}'", n=len(zeilen), s=suche.strip()) + (f" in {muster}" if muster else "")
                    + _t(" (beste zuerst)"))
            gezeigt, verborgen = zeilen, []
        else:
            if alle or status.strip() or muster:
                gezeigt, verborgen = zeilen, []
            else:
                gezeigt = [r for r in zeilen if r["status"] in OFFEN
                           or (r["status"] == "ausgewertet" and _tage_seit(r["bewegt"]) < FRISCH_TAGE)]
                verborgen = [r for r in zeilen if r not in gezeigt]
            kopf = _t("{n} Reihen", n=len(gezeigt)) + (f" in {projekt.strip()}" if projekt.strip() else "") + \
                (_t(" zu {m}", m=muster) if muster else "")
        if not zeilen:
            return _t("Keine Reihe gefunden.") if (suche or projekt or status or muster) else \
                _t("Das Messbuch ist leer. Eine Reihe anlegen mit reihe_anlegen.")
        if tabelle:
            gezeigt = sorted(gezeigt, key=lambda r: (r["begonnen"] or r["angelegt"][:10], r["angelegt"]))
            aus = [kopf + _t(", nach Beginn - ganze Reihe per reihen(kennung=...):"), *_tabelle(conn, gezeigt)]
        else:
            aus = [kopf + ":"] + [_uebersichtszeile(conn, r) for r in gezeigt]
        if verborgen:
            arten = {}
            for r in verborgen:
                arten[r["status"]] = arten.get(r["status"], 0) + 1
            aus.append(_t("Ausgeblendet: {liste} (aelter als {tage} Tage oder erledigt) - alle=True zeigt sie.",
                          liste=", ".join(f"{n} {_aus(s)}" for s, n in arten.items()), tage=FRISCH_TAGE))
        return "\n".join(aus)
    finally:
        conn.close()


WERKZEUGE = (reihen, reihe_anlegen, reihe_aendern, rezept, messwerte, ergebnis)


# Die Arbeitsregeln in Kurzform, wie ANWEISUNG im Gedaechtnis: Claude Code legt
# sie jeder Sitzung bei, in der das Messbuch eingebunden ist.
ANWEISUNG = (
    "Messbuch: Messreihen mit Frage, vorab festgelegtem Kriterium, Rezept, Messwerten und "
    "Ergebnis. Zu Beginn einer Sitzung, die Messungen betreut, reihen(): zeigt offene Reihen "
    "und was nachzusehen ist. Vor dem ersten Lauf reihe_anlegen(kennung, frage, kriterium), "
    "beim Start rezept(kennung, befehl), Zahlen per messwerte(kennung, zeilen), Auswertung per "
    "ergebnis(kennung, urteil, fazit). Nichts wird geloescht, Falsches per ersetzt= abgeloest.")
ANWEISUNG_EN = (
    "Lab notebook: measurement series with a question, a criterion fixed in advance, recipe, "
    "measurements and result. At the start of a session that looks after experiments, call "
    "series(): it lists open series and what needs checking. Before the first run "
    "new_series(key, question, criterion), at the start recipe(key, command), numbers via "
    "measurements(key, rows), evaluation via result(key, verdict, conclusion). Nothing is "
    "deleted; wrong entries are retired with supersedes=.")


def anmelden(server) -> None:
    """Ersetzt die Werkzeuge des Gedaechtnisses durch die des Messbuchs."""
    verwaltung, kern = ms._sdk_intern(server)
    for w in list(verwaltung.list_tools()):
        verwaltung.remove_tool(w.name)
    if ms._en():
        import messbuch_en
        werkzeuge = messbuch_en.WERKZEUGE
    else:
        werkzeuge = WERKZEUGE
    for fn in werkzeuge:
        server.tool()(fn)
    kern.instructions = ANWEISUNG_EN if ms._en() else ANWEISUNG
    # `"default": ""` je Parameter sagt nichts, was die Liste `required` nicht
    # schon sagt, und kostet in jeder Sitzung rund 400 Zeichen. Geprueft
    # werden die Argumente ueber fn_metadata, nicht ueber dieses Dict.
    for w in verwaltung.list_tools():
        for feld in w.parameters.get("properties", {}).values():
            if isinstance(feld, dict):
                feld.pop("default", None)
