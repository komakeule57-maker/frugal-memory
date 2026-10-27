# Plan: ein fester Deckel für `selten` in `verdichten`

Festgelegt am 2026-10-27, **vor** der Messung. Anlass: Code-Audit. `verdichten`
vergleicht nur Paare, die einen seltenen Wortstamm teilen; „selten“ heißt
höchstens `len(zeilen) // 20` Einträge. Die Schwelle wächst mit dem Bestand,
die Zahl der Paare damit etwa quadratisch. Vorschlag: Schwelle fest deckeln.

## Daten

`../vergleich_2026-10-26/korpus_a.json`: 1.593 echte Einträge mit Marke und Art
(privat, wird nicht veröffentlicht). Eingelesen in der gespeicherten
Reihenfolge per `remember` in eine Wegwerf-Datenbank. Wachstumsstufen: Kopie
der Datenbank nach 400 und 800 Einträgen, dazu alle 1.593.

## Aufbau

**Eine** Kopie von `memory_server.py` mit **einem** Stellrad: in
`selten = max(2, len(zeilen) // 20)` wird `min(..., SELTEN_DECKEL)` eingesetzt,
`SELTEN_DECKEL = None` heißt wie heute. Die Ersetzung ist per `assert alt in
quelle` abgesichert. Die gefundenen Paare (Ähnlichkeit ≥ 0,5) schreibt die Kopie
an derselben Stelle mit, an der `verdichten` sie bildet, nicht im Skript
nachgerechnet.

Arme: heute (n // 20: 20 / 40 / 79), Deckel 25, Deckel 40. Zeit: Median von 3
Läufen auf einem Laptop mit 2 Kernen (absolute Zeiten höher als auf einem Arbeitsrechner).

## Kriterium (bei 1.593 Einträgen)

Ein Deckel wird übernommen, wenn er

1. mindestens **95 %** der Paare findet, die die heutige Regel findet, und
2. die Laufzeit auf höchstens **50 %** der heutigen senkt.

Erfüllen mehrere Deckel beides, gilt der größere (vorsichtigere). Erfüllt
keiner beides, bleibt die heutige Regel, und die gemessene Zeitkurve wird
dokumentiert.

## Grenzen

Ein Bestand, eine Sprache (überwiegend deutsch). Paare über der Schwelle sind
Kandidaten, keine geprüften Dubletten.
