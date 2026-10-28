"""English surface of the lab notebook (`--messbuch`) - the default since 0.3.0.

Same pattern as werkzeuge_en.py and texte_en.py together: thin wrappers with
English tool and parameter names around the German functions in messbuch.py,
plus the message table that messbuch._t reads. Status and verdict names are
mapped at the border (running <-> laeuft); the file itself is unchanged.
"""

import messbuch as mb


def series(key: str = "", project: str = "", status: str = "", search: str = "",
           all: bool = False, full: bool = False, table: bool = False) -> str:
    """Read the lab notebook. Without key: open and recently evaluated series with notes on what to check. With key: the whole series.

    Args:
        key: e.g. "vision/lr-sweep", or just "lr-sweep" if unique. With * a pattern ("vision/lr-*") that filters.
        search: Words in question, criterion, conclusion, recipe.
        all: Also old and finished series.
        full: For one series also superseded entries and the whole history.
        table: Cross-section as a table (verdict, recipe, criterion, short conclusion), sorted by start.
    """
    return mb.reihen(kennung=key, projekt=project, status=status, suche=search,
                     alle=all, voll=full, tabelle=table)


def new_series(key: str, question: str, criterion: str, plan: str = "",
               builds_on: str = "", backfill: str = "", started: str = "") -> str:
    """New measurement series, BEFORE the first run. The criterion gets a timestamp.

    Args:
        key: project/short-name, e.g. "vision/lr-sweep".
        criterion: What is measured, how, and what decides better/worse. Empty = later only the verdict observation.
        plan: Plan file as machine:path.
        builds_on: Keys of predecessor series, comma-separated.
        backfill: Only for series entered after the fact: where and from when the criterion comes.
        started: With backfill: when the series really started, YYYY-MM-DD.
    """
    return mb.reihe_anlegen(key, question, criterion, plan=plan, baut_auf=builds_on,
                            nachtrag=backfill, begonnen=started)


def edit_series(key: str, status: str = "", criterion: str = "", reason: str = "",
                note: str = "", plan: str = "", superseded_by: str = "", started: str = "",
                builds_on: str = "") -> str:
    """Amend or change a series; everything goes into its history.

    Args:
        status: planned, running, paused, aborted (with reason) or superseded (with superseded_by).
        criterion: After the first measurement only with reason, then stays marked.
        note: Free note (interim state, observation).
        started: Only for backfilled series: true start date, YYYY-MM-DD.
        builds_on: Add predecessors, comma-separated; "-key" removes a wrong one.
    """
    return mb.reihe_aendern(key, status=status, kriterium=criterion, grund=reason, notiz=note,
                            plan=plan, abgeloest_durch=superseded_by, begonnen=started,
                            baut_auf=builds_on)


def recipe(key: str, command: str, arm: str = "", code: str = "", parameters: str = "",
           seed: str = "", machine: str = "", logs: str = "", note: str = "",
           supersedes: str = "") -> str:
    """How the run is computed, so that someone else can repeat it. Enter at the start.

    Args:
        command: The call, verbatim.
        code: File or commit plus md5/hash.
        logs: Where the raw data lives, machine:path.
        supersedes: Recipes this one replaces, e.g. "r3".
    """
    return mb.rezept(key, command, arm=arm, quelltext=code, parameter=parameters, seed=seed,
                     rechner=machine, logs=logs, notiz=note, ersetzt=supersedes)


def measurements(key: str, rows: str, source: str = "", supersedes: str = "") -> str:
    """Measurements, one row per value: `quantity | value | arm | seed | n` (last three optional).

    seed = random start (e.g. 1234), not a time of day. The value stays verbatim ("32/32", "1.65").
    One malformed row rejects them all.

    Args:
        source: Where the numbers come from (script, log, file).
        supersedes: Measurements these replace, e.g. "m3,m4".
    """
    return mb.messwerte(key, rows, quelle=source, ersetzt=supersedes)


def result(key: str, verdict: str, conclusion: str, open_questions: str = "", file: str = "") -> str:
    """Evaluate a series; a new result supersedes the previous one.

    Args:
        verdict: met, partial (several criteria, not all), missed, tie, inconclusive, invalid, observation (no criterion beforehand).
        conclusion: What FOLLOWS from it, not the numbers repeated.
        open_questions: What explicitly stays open.
        file: Result file as machine:path.
    """
    return mb.ergebnis(key, verdict, conclusion, offen=open_questions, datei=file)


WERKZEUGE = (series, new_series, edit_series, recipe, measurements, result)


TEXTE_EN = {
    # Fehler und Eingaben
    "Fehler: {exc}": "Error: {exc}",
    "'#{n}' ohne Rechnernamen (Stelle: ...{stelle}...). Das Messbuch kann sich mehrere Rechner teilen, und jedes Gedaechtnis zaehlt von 1 an - bitte mit dem Namen des Gedaechtnisses schreiben (Vorgabe: der Rechnername), z. B. {name}#{n}. Nichts gespeichert.":
        "'#{n}' without a memory name (at: ...{stelle}...). Several machines can share the notebook, and every memory counts from 1 - please write it with the name of the memory (default: the host name), e.g. {name}#{n}. Nothing saved.",
    "Keine Kennung angegeben.": "No key given.",
    "'{k}' ist mehrdeutig: {liste}. Bitte die volle Kennung.": "'{k}' is ambiguous: {liste}. Please give the full key.",
    "Keine Reihe '{k}' im Messbuch.": "No series '{k}' in the notebook.",
    " Gemeint: {nah}?": " Did you mean: {nah}?",
    " Neu anlegen mit reihe_anlegen.": " Create it with new_series.",
    "'{p}{n}' ist kein {was} (erwartet {praefix}<Zahl>). Nichts gespeichert.":
        "'{p}{n}' is not a {was} (expected {praefix}<number>). Nothing saved.",
    "In '{ids}' steht keine Nummer der Form {praefix}12. Nichts gespeichert.":
        "'{ids}' contains no number of the form {praefix}12. Nothing saved.",
    "{praefix}{n} gehoert nicht zu dieser Reihe. Nichts gespeichert.":
        "{praefix}{n} does not belong to this series. Nothing saved.",
    "{praefix}{n} ist schon abgeloest ({wie}). Nichts gespeichert.":
        "{praefix}{n} is already superseded ({wie}). Nothing saved.",
    "abgeloest durch {durch} am {tag}": "superseded by {durch} on {tag}",
    "Rezept": "recipe",
    "Messwert": "measurement",
    "Ergebnis": "result",
    # reihe_anlegen
    "Kennung '{k}' hat nicht die Form projekt/kuerzel (z. B. bild/lr-suche).":
        "Key '{k}' is not of the form project/short-name (e.g. vision/lr-sweep).",
    "Ohne Frage keine Reihe.": "No series without a question.",
    "begonnen= nur zusammen mit nachtrag= - eine neue Reihe beginnt heute.":
        "started= only together with backfill= - a new series starts today.",
    "begonnen='{b}' hat nicht die Form JJJJ-MM-TT.": "started='{b}' is not of the form YYYY-MM-DD.",
    "'{k}' gibt es schon. Ergaenzen mit reihe_aendern, ansehen mit reihen.":
        "'{k}' already exists. Amend it with edit_series, read it with series.",
    "angelegt": "created",
    " (Nachtrag: {n})": " (backfill: {n})",
    "Angelegt: {k} ({s}).": "Created: {k} ({s}).",
    " OHNE Kriterium: das Ergebnis kann dann nur eine Beobachtung sein. Nachtragen per reihe_aendern(kriterium=...), solange noch kein Messwert steht.":
        " WITHOUT a criterion: the result can then only be an observation. Add one with edit_series(criterion=...) while there is no measurement yet.",
    " Nicht im Messbuch: {liste} (bleibt als Verweis stehen).":
        " Not in the notebook: {liste} (kept as a reference).",
    # reihe_aendern
    "`ausgewertet` setzt nur das Werkzeug ergebnis - der Status soll nie mehr behaupten, als im Messbuch steht.":
        "`evaluated` is set only by the result tool - the status should never claim more than the notebook holds.",
    "Status '{s}' gibt es nicht. Erlaubt: {erlaubt}.": "There is no status '{s}'. Allowed: {erlaubt}.",
    "Nichts zu aendern angegeben.": "Nothing to change given.",
    "Abbrechen nur mit Grund. Nichts geaendert.": "Aborting only with a reason. Nothing changed.",
    "Status abgeloest braucht abgeloest_durch=<Kennung der Nachfolge-Reihe>.":
        "Status superseded needs superseded_by=<key of the successor series>.",
    "abgeloest durch {k}": "superseded by {k}",
    "von Hand": "by hand",
    "Status {s}": "status {s}",
    "Status {alt} -> {neu} ({warum})": "Status {alt} -> {neu} ({warum})",
    "Seit {wann} stehen Messwerte. Ein Kriterium, das nach dem Ergebnis gesetzt wird, findet immer einen Sieger - aendern nur mit grund=..., und die Aenderung bleibt an der Reihe sichtbar. Nichts geaendert.":
        "There have been measurements since {wann}. A criterion set after the result always finds a winner - change it only with reason=..., and the change stays visible on the series. Nothing changed.",
    "(keins)": "(none)",
    "{ts}, nach Messwerten seit {wann}: {grund}": "{ts}, after measurements since {wann}: {grund}",
    "Kriterium geaendert, vorher: {alt}": "Criterion changed, before: {alt}",
    " | Grund: {g}": " | reason: {g}",
    "Kriterium": "criterion",
    " (NACH Messwerten, bleibt markiert)": " (AFTER measurements, stays marked)",
    "begonnen= nur bei nachgetragenen Reihen - die anderen beginnen am Tag der Anlage. Nichts geaendert.":
        "started= only for backfilled series - the others start on the day they were created. Nothing changed.",
    "begonnen auf {b} gesetzt": "started set to {b}",
    "begonnen {b}": "started {b}",
    "{v} kann nicht auf sich selbst aufbauen. Nichts geaendert.": "{v} cannot build on itself. Nothing changed.",
    "{k} baut nicht auf {v} auf - nichts herauszunehmen. Nichts geaendert.":
        "{k} does not build on {v} - nothing to remove. Nothing changed.",
    "Baut auf: {a}": "Builds on: {a}",
    "baut auf {a}": "builds on {a}",
    "baut auf: schon eingetragen": "builds on: already entered",
    "Plan: {p}": "Plan: {p}",
    "Plan": "plan",
    "Notiz": "note",
    # rezept, messwerte, ergebnis
    "Ohne Befehl kein Rezept.": "No recipe without a command.",
    "Rezept {neu}": "Recipe {neu}",
    ", loest {alt} ab": ", supersedes {alt}",
    ", loesen {alt} ab": ", supersede {alt}",
    "{neu} fuer {k}": "{neu} for {k}",
    ". Status jetzt: {s}.": ". Status now: {s}.",
    "Zeile {nr} ('{zeile}') hat nicht die Form 'Groesse | Wert | ...'. Nichts gespeichert.":
        "Row {nr} ('{zeile}') is not of the form 'quantity | value | ...'. Nothing saved.",
    "Zeile {nr} hat {n} Felder, hoechstens 5 (Groesse | Wert | Arm | Start | n). Nichts gespeichert.":
        "Row {nr} has {n} fields, at most 5 (quantity | value | arm | seed | n). Nothing saved.",
    "Keine Messwerte in `zeilen`.": "No measurements in `rows`.",
    "Messwerte {neu}": "Measurements {neu}",
    " Die Reihe hat KEIN Kriterium - diese Werte koennen nur eine Beobachtung tragen.":
        " The series has NO criterion - these values can only support an observation.",
    "Urteil '{u}' gibt es nicht. Erlaubt: {erlaubt}.": "There is no verdict '{u}'. Allowed: {erlaubt}.",
    "Ohne Fazit kein Ergebnis.": "No result without a conclusion.",
    "{k} hat kein Kriterium - ohne Massstab gibt es kein '{u}'. Moeglich: {moeglich}. Nichts gespeichert.":
        "{k} has no criterion - without a yardstick there is no '{u}'. Possible: {moeglich}. Nothing saved.",
    "Ergebnis {neu}: {u}": "Result {neu}: {u}",
    "Ergebnis {neu}": "Result {neu}",
    " Es steht kein Messwert im Messbuch - die Zahlen, auf denen das Urteil ruht, nachtragen?":
        " There is no measurement in the notebook - add the numbers the verdict rests on?",
    " Achtung: das Kriterium wurde nach den ersten Messwerten geaendert ({wann}).":
        " Note: the criterion was changed after the first measurements ({wann}).",
    # Lesen
    "seit {n} Tagen kein Eintrag - laeuft der Prozess noch?": "no entry for {n} days - is the process still running?",
    "Messwerte ohne Ergebnis": "measurements without result",
    "ohne Kriterium": "no criterion",
    "Kriterium nach Messwerten geaendert": "criterion changed after measurements",
    "ohne Rezept": "no recipe",
    "Kriterium: KEINS - Ergebnisse dieser Reihe sind Beobachtungen.":
        "Criterion: NONE - results of this series are observations.",
    "nachgetragen, Beleg: {n}": "backfilled, source: {n}",
    "NACH den ersten Messwerten geaendert: {wie}": "changed AFTER the first measurements: {wie}",
    "festgelegt {ts}, NACH dem ersten Messwert ({erst})": "fixed {ts}, AFTER the first measurement ({erst})",
    "festgelegt {ts}": "fixed {ts}",
    ", vor dem ersten Messwert": ", before the first measurement",
    ", noch kein Messwert": ", no measurement yet",
    "Kriterium ({wann}):": "Criterion ({wann}):",
    ", begonnen {b}": ", started {b}",
    ", angelegt {a}, zuletzt {z}": ", created {a}, last {z}",
    "Frage: {f}": "Question: {f}",
    " (nicht im Messbuch)": " (not in the notebook)",
    "Darauf baut: {liste}": "Built on by: {liste}",
    "Rezepte:": "Recipes:",
    "quelltext": "code",
    "parameter": "parameters",
    "seed": "seed",
    "rechner": "machine",
    "logs": "logs",
    "notiz": "note",
    "Messwerte (Groesse | Wert | Arm | Start | n):": "Measurements (quantity | value | arm | seed | n):",
    "  Quelle: {q}": "  Source: {q}",
    "Ergebnis e{id} [{ts}]: {u}": "Result e{id} [{ts}]: {u}",
    "  Fazit: {f}": "  Conclusion: {f}",
    "  Offen: {o}": "  Open: {o}",
    "  Datei: {d}": "  File: {d}",
    "rezept": "recipe(s)",
    "messwert": "measurement(s)",
    "ergebnis": "result(s)",
    "Abgeloest und ausgeblendet: {liste} - voll=True zeigt sie.": "Superseded and hidden: {liste} - full=True shows them.",
    "Chronik": "History",
    " (juengste 8 von {n}, voll=True zeigt alle)": " (latest 8 of {n}, full=True shows all)",
    "| Reihe | Beginn | Stand | Frage | Rezept | Kriterium | Fazit |":
        "| Series | Start | State | Question | Recipe | Criterion | Conclusion |",
    "KEINS": "NONE",
    "{n} Reihen zu '{s}'": "{n} series for '{s}'",
    " (beste zuerst)": " (best first)",
    "{n} Reihen": "{n} series",
    " zu {m}": " for {m}",
    "Keine Reihe gefunden.": "No series found.",
    "Das Messbuch ist leer. Eine Reihe anlegen mit reihe_anlegen.": "The notebook is empty. Create a series with new_series.",
    ", nach Beginn - ganze Reihe per reihen(kennung=...):": ", by start - whole series via series(key=...):",
    "Ausgeblendet: {liste} (aelter als {tage} Tage oder erledigt) - alle=True zeigt sie.":
        "Hidden: {liste} (older than {tage} days or finished) - all=True shows them.",
}
