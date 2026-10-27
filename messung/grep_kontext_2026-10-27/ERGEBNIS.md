# Ergebnis: `grep -C` gegen frugal-memory (2026-10-27)

Plan: `PLAN.md` (vor der Messung festgelegt).

## Gemessen

275 echte `recall`-Fragen, Korpus B mit 1.756 .md-Dateien (Stand 2026-09-25).
Kosten = Zeichen der grep-Ausgabe je Frage, Median. A (frugal-memory, recall +
zeige) Median 4.471 Zeichen, B1 (grep -l + fünf Dateien ganz lesen) 22.072.

| Arm | Median Zeichen | B3/A | Gold im Ausschnitt |
|---|---:|---:|---:|
| B3-C3 (Hauptarm, k = 3) | 290.580 | 64,99 | 92,4 % |
| B3-C0 (nur Trefferzeilen) | 134.462 | 30,07 | 92,4 % |
| B3-C3-250 (nach 250 Zeilen gekappt) | 27.089 | 6,06 | 36,4 % |

Strategiewahl laut Plan mit Kenntnis des Golds: C3 nahm 42-mal „und“
(Median 21.564), 233-mal „oder“ (Median 341.778). Bei „oder“ bringt fast jede
Frage Hunderte Trefferzeilen aus dem ganzen Korpus.

## Kriterium

B3-C3/A ≥ 1,1 → frugal-memory billiger. **64,99: erfüllt.** Das Urteil kippt in
keinem Arm (kleinster Wert 6,06 bei C3-250). Der Zeichen-/Token-Unterschied
(1,87 gegen 2,03 Zeichen je Token, rund 8 % zugunsten von B3) ändert daran nichts.

## Größter freier Parameter

Die Kappung bei 250 Zeilen (C3 gegen C3-250: Faktor 10,7 in den Kosten). Sie
macht B3 billig, aber nur, weil sie das Gold abschneidet (36 % statt 92 %).
Selbst gekappt bleibt B3 6-mal so teuer wie A.

## Gegenprobe (nachträglich, zählt nicht)

Die Plan-Wahl „Gold zuerst“ zog Fragen auf die teure Strategie „oder“, wenn
nur dort Gold stand. Ein Agent kennt das Gold nicht. Gegenprobe mit der Wahl
„erst eng (und), nur bei leerer Ausgabe breit (oder)“ (`WAHL=agent`):

| Arm | B3/A | Gold im Ausschnitt |
|---|---:|---:|
| B3-C3 | 28,19 | 74,9 % |
| B3-C0 | 14,86 | 74,9 % |
| B3-C3-250 | 6,06 | 34,2 % |

„und“ lieferte bei 109 Fragen etwas. Die Plan-Wahl hat B3 also rund 2,3-fach
verteuert, am Urteil ändert das nichts.

## Grenzen

Zeichen der Ausgabe, nicht ob der Ausschnitt zum Antworten reicht. Ein
iterierender Agent (Begriffe nachschärfen, erst `grep -l`, dann lesen) landet
im Wesentlichen beim B1-Weg; der ist mit 22.072 Zeichen der billigste
gemessene grep-Weg. A findet Gold per Konstruktion (Fragen aus dem Betrieb).

## Fazit

Der Einwand des Auditors trifft die Zahl nicht: Die naive Basis (Datei ganz
lesen) ist in diesem Bestand **billiger** als der „sorgfältige“ Weg über
`grep -C`, weil eine breite Suche über 1.756 Dateien Hunderte Trefferzeilen mit
Kontext ausspuckt. Die README-Aussage „grep -C nicht gemessen“ kann durch
„gemessen, 6- bis 65-mal so teuer je nach Kappung“ ersetzt werden. Offen bleibt
nur, ob ein geschickt iterierender Agent unter B1 kommt; das ist eine andere
Messung mit echtem Agenten statt Skript.
