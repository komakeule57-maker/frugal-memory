# Ergebnis: Vereinigung in `verdichten` vorgerechnet (2026-10-27)

Kriterium vor der Messung festgelegt: übernommen, wenn die
Paarmengen bei Schwelle 0,5, 0,3 und 0,2 identisch sind, die Ähnlichkeit je
Paar um höchstens 1e-9 abweicht und die Laufzeit bei Schwelle 0,5 auf
höchstens 70 % fällt.

## Gemessen

Anlass: Das Profil vom selben Tag (Nachtrag in
`../verdichten_deckel_2026-10-27/ERGEBNIS.md`) fand rund 60 % der Laufzeit in
einer Zeile, der Gewichtssumme über `sa | sb`, je Kandidatenpaar neu
gerechnet. Änderung: die Summe je Eintrag einmal vorrechnen und
`vereint = summe[a] + summe[b] - gemeinsam` nehmen, was rechnerisch dasselbe ist.

Eine gepatchte Kopie (Stand be0487a, Deckel 25), ein Stellrad
`VORGERECHNET`, Paare samt Ähnlichkeit aus dem echten Codepfad mitgeschrieben.
1.593 echte Einträge, Laptop mit 2 Kernen, Median aus 3 Läufen.

| Schwelle | Paare heute | Paare vorgerechnet | max. Abweichung | Zeit heute | Zeit vorgerechnet |
|---:|---:|---:|---:|---:|---:|
| 0,5 | 7 | 7 (gleich) | 1,1e-16 | 18,57 s | 5,18 s (27,9 %) |
| 0,3 | 15 | 15 (gleich) | 1,1e-16 | 18,88 s | 5,20 s |
| 0,2 | 73 | 73 (gleich) | 1,1e-16 | 18,88 s | 5,26 s |

**Kriterium erfüllt.**

Gegenprobe am eingebauten Code (`gleichheit.py`): die ganze Ausgabe von
`verdichten` bei allen drei Schwellen, alter Stand gegen neuen, ist Zeichen
für Zeichen identisch (29.812 Zeichen, 70 Gruppen).

## Grenzen

Ein Bestand, ein Rechner. Die Abweichung von 1e-16 ist Rundung; ein Paar, das
genau auf der Schwelle läge, könnte in seltenen Fällen kippen. Bei den 73
geprüften Paaren (die kleineren Mengen sind darin enthalten) kam das nicht vor.

## Fazit

Der Hebel aus dem Profil war der richtige: `verdichten` braucht bei 1.593
Einträgen auf dem Laptop jetzt 5 statt 61 Sekunden (Deckel und Vorrechnung
zusammen), mit derselben Ausgabe. Weiteres Tuning lohnt erst, wenn ein Bestand
deutlich größer wird; der Rest ist die Schnittmenge je Paar und die
Stammbildung.
