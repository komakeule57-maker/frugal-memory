# Ergebnis: fester Deckel für `selten` in `verdichten` (2026-10-27)

Plan: `PLAN.md` (vor der Messung festgelegt).

## Gemessen

Echte Einträge (`korpus_a.json`), eingelesen per `remember`, Stufen 400 / 800 /
1.593. Eine gepatchte Kopie, ein Stellrad `SELTEN_DECKEL`, Paare aus dem echten
Codepfad mitgeschrieben. Zeit: Median aus 3 Läufen auf einem Laptop mit 2 Kernen.

| Einträge | Arm | selten | Kandidatenpaare | Paare ≥ 0,5 | Zeit |
|---:|---|---:|---:|---:|---:|
| 400 | heute | 20 | 23.745 | 1 | 1,40 s |
| 800 | heute | 40 | 98.942 | 1 | 8,12 s |
| 800 | Deckel 25 | 25 | 67.440 | 1 | 5,95 s |
| 1.593 | heute | 79 | 509.500 | 7 | 60,70 s |
| 1.593 | Deckel 25 | 25 | 147.941 | 7 | 19,26 s |
| 1.593 | Deckel 40 | 40 | 257.512 | 7 | 33,98 s |

Bei 400 Einträgen sind alle Arme gleich (Deckel 25 greift erst ab 520 Einträgen, Deckel 40 ab 820).
Heutige Regel: doppelte Einträge → rund 7,5-fache Zeit (Kandidaten ×5,1).

## Kriterium (bei 1.593)

≥ 95 % der Paare und ≤ 50 % der Zeit, der größere qualifizierte Deckel gilt.

- Deckel 25: 7/7 Paare, 31,7 % der Zeit → **erfüllt**.
- Deckel 40: 7/7 Paare, 56,0 % der Zeit → verfehlt (Zeit).

**Übernommen würde Deckel 25.**

## Größter freier Parameter

Die Zahl der echten Paare: 7 Paare sind nur 2 Gruppen (ein Paar und ein
Viererblock). Ein einziges verlorenes Paar hätte 85,7 % bedeutet und das
Kriterium gerissen.

## Gegenprobe (nachträglich, zählt nicht)

Ähnlichkeitsschwelle gesenkt, um mehr Paare zu bekommen:

| Schwelle | Paare heute | Deckel 25 findet | Deckel 40 findet |
|---:|---:|---:|---:|
| 0,5 | 7 | 7 | 7 |
| 0,3 | 15 | 15 | 15 |
| 0,2 | 73 | 73 | 73 |

Alle Paare sind natürlich gewachsen: derselbe echte Bestand, nichts
eingebaut oder umformuliert. Ab Schwelle 0,3 sind es aber eher ähnliche als
doppelte Einträge; die Gegenprobe prüft also, ob der Deckel Ähnlichkeit
übersieht, nicht die Fundrate bei echten Dubletten.

Kein Paar ging verloren, auch nicht bei 73. Plausibel: wer sich zu 20 % oder
mehr gleicht, teilt fast immer auch einen Stamm, der in höchstens 25 Einträgen
vorkommt.

## Grenzen

Ein Bestand, überwiegend deutsch. Zeiten vom Laptop (2 Kerne), absolut
höher als auf einem Arbeitsrechner. Auch mit Deckel wächst die Zeit weiter
(1.593: 19 s); der Deckel flacht die Kurve ab, beseitigt sie nicht.

## Fazit

Der Einwand des Auditors stimmt: `verdichten` wird mit dem Bestand
überproportional langsamer (eine Minute bei 1.593 Einträgen auf dem Laptop).
Deckel 25 drittelt die Zeit, ohne in diesem Bestand ein einziges Paar zu
verlieren, auch nicht in der Gegenprobe mit zehnmal so vielen Paaren. Er kann
ins nächste Release. Bei sehr großen Beständen bleibt `verdichten` ein
Werkzeug für gelegentliche Läufe. Wo die verbleibenden 19 s liegen
(Paarvergleich oder Stammbildung für alle Einträge), ist nicht gemessen; vor
weiterem Drehen an der Schwelle gehört ein Profil davor.
