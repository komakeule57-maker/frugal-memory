# Plan: der sorgfältige grep-Weg (`grep -C`) gegen frugal-memory

Festgelegt am 2026-10-27, **vor** der Messung. Anlass: ein Code-Audit nannte die
4,8×-Basis (grep + ganze Datei lesen) den naiven Fall. Das README sagt seit
115da64, dass der sorgfältige Weg nicht gemessen ist. Diese Messung schließt die
Lücke auf der Kostenseite.

## Daten (unverändert, vom 2026-09-25)

- 275 echte `recall`-Fragen mit lebendem Gold aus `../ergebnis.json` (Frage,
  Gold-Ids, A-Kosten aus den Transkripten).
- Korpus B: `../korpus_md/`, eine Datei je Fakt, 1.756 Dateien, der lebende
  Bestand jenes Tages. Gold-Datei = Dateiname beginnt mit der Gold-Id.
- A (frugal-memory): Zeichen aus `ergebnis.json` (recall + folgendes zeige),
  Median 4.471. A findet Gold per Konstruktion (siehe ERGEBNIS-2026-09-25.md).

## Arm B3: `grep -C`

Dieselben Suchbegriffe und Muster wie B1 (`terme()`, `kandidaten()` aus
`gegentest.py`, importiert, nicht nachgebaut). Statt die fünf besten Dateien
ganz zu lesen, geht die Ausgabe von `grep -Ei -n -C k` in den Kontext:

- Strategie `oder`: ein grep -C über den ganzen Korpus, Muster `a|b|c`.
- Strategie `und`: grep -C nur über die Dateien, die alle Begriffe enthalten;
  dazu zählt deren Dateiliste (wie B1 die grep-Liste zählt). Die verketteten
  `grep -l`, die ein Agent dafür bräuchte, zählen **nicht**: zugunsten von B.
- Wie B1 wird je Frage die bessere Strategie genommen, und zwar mit Kenntnis
  des Golds (zuerst Gold im Ausschnitt, dann weniger Zeichen). Auch das
  begünstigt B.

Kosten = Zeichen der grep-Ausgabe. „Gold im Ausschnitt“ = eine Zeile der
Gold-Datei steht in der Ausgabe. Ob der Ausschnitt zum Antworten reicht, misst
das **nicht**.

## Arme (frei gewählte Parameter)

- **B3-C3**: k = 3, Ausgabe vollständig. **Hauptarm.**
- B3-C0: k = 0 (nur Trefferzeilen), Anschluss an die alte `grep -n`-Zahl.
- B3-C3-250: k = 3, Ausgabe nach 250 Zeilen abgeschnitten (meine Wahl, nachgebildet
  einem Werkzeug, das lange Ausgaben kappt). Das ist der größte frei gewählte
  Parameter.

## Kriterium (Hauptarm, Median der Zeichen je Frage, wie 2026-09-25)

- B3-C3 / A ≥ 1,1 → frugal-memory ist auch gegen den sorgfältigen grep-Weg billiger.
- 0,9 < B3-C3 / A < 1,1 → Gleichstand.
- B3-C3 / A ≤ 0,9 → der sorgfältige grep-Weg ist billiger.

Kippt das Urteil zwischen den Armen, ist der Befund „hängt am frei gewählten
Parameter“, und das wird so berichtet. „Gold im Ausschnitt“ wird neben den
Kosten berichtet (B1: 53 %), ist aber kein Teil des Kriteriums.

## Grenzen

Ein einzelner Bestand, Fragen aus dem Betrieb von frugal-memory (A per
Konstruktion 100 %). Zeichen statt Token: 2026-09-25 lagen .md-Text und
grep-Ausgabe bei 1,87 und 2,03 Zeichen je Token, das verschiebt B3 um rund 8 %
zu seinen Gunsten, wenn man in Token rechnet; wird im Ergebnis genannt.
