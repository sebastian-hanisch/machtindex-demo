# Macht in der Genossenschaft: wer entscheidet wirklich? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-machtindex-demo.streamlit.app/)**

Teil der [Linie Koalitionen und Teilen](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html). Die Vorläufer sind `shapley-demo` (Shapley-Wert als Kostenanteil einer Sammeltour, wo der Wert alle Reihenfolgen braucht) und `kern-demo`; die Brücke zur Sitzverteilung bildet `sitzverteilung-demo`. Hier geht es um etwas anderes: um die **Macht**, die Stimmen und Sitze in einer Abstimmung verleihen. Nachbarn in der Linie: `graphspiel-demo` (dort verbindet ein Netz die Betriebe, nur zusammenhängende Gruppen arbeiten zusammen, die Verteilungsregel ist der Myerson-Wert), `flussspiel-demo` (nennt diese Demo als Vorgänger: dort der Veto-Spieler als Machtfall) und `kern-zeilenerzeugung-demo` (dort reichen im Gewichtsspiel nach deren README wenige hundert Zeilen für n bis 100; hier ist der Kern des Gewinnspiels nur die Veto-Regel für n bis 5).

Vehikel ist eine **Spediteursgenossenschaft**: Mitglieder mit ganzzahligen Stimmgewichten (Lkw im Fuhrpark) beschließen mit einer **Quote**: ein Beschluss fällt, wenn die Gewichtssumme der Zustimmenden mindestens die Quote erreicht. Stimmgewichte, Quote und Koalitionswerte sind **Modellannahmen**; Macht heißt hier „Wahrscheinlichkeit, das entscheidende Mitglied zu sein“, nicht Einfluss im Alltag.

## Kernfrage

**Wie oft ist ein Mitglied das, ohne das kein Beschluss fällt, und wie weit weicht diese Macht vom Stimmanteil ab?** Gemessen wird mit dem **Banzhaf-Index** (Anteil der Koalitionen, in denen das Mitglied entscheidend ist) und dem **Shapley–Shubik-Index** (Anteil der Reihenfolgen des Beitritts, in denen es die Quote als Erstes erreicht). Die App beantwortet die Frage für die eingestellte Genossenschaft mit einem live berechneten Urteil und stellt sieben Tabs mit acht Experimenten daneben (Macht gegen Stimmanteil, Quote als Regler, Zwei Indizes, Zwei Gewichtssysteme, Paradoxa, Zählen statt Aufzählen, Beirat).

## Modell

- **Quote:** `q = ⌊p·W⌋ + 1` (mehr als der Anteil p der Gesamtgewichte W; p = 50 % ist die einfache Mehrheit); bei p = 100 % (Einstimmigkeit) gilt q = W. Regler für p: 50,0 bis 100,0 % in Schritten von 0,1.
- **Schwingspieler, Banzhaf, Shapley–Shubik:** Formeln im Expander **📐 Mathematische Formulierung** der App (je Display-Gleichung ein eigener Block, mit Lesehilfe und Symboltabelle).
- **Zählen statt Aufzählen:** dynamische Programmierung über (Größe, Gewichtssumme) mit Rücknahme je Mitglied; ganzzahlig und exakt für n bis 60 und Gewichtssumme bis 100.000. Aufwand etwa n²·W (Hypothese aus dem Bau, nicht aus der Literatur belegt; die Zahl der Koalitionen 2ⁿ geht nicht ein).
- **Maß für Abweichungen:** die halbe Summe der Beträge der Unterschiede zweier Anteilsvektoren (der Anteil, der umverteilt werden müsste), in Prozentpunkten.

## Methodik

- **Vier Rechenwege im Kern** (`mdx_game.py`), die in den Tests gegeneinander laufen: Aufzählung aller Koalitionen in reinem Python, Aufzählung aller Reihenfolgen (n bis 8), Aufzählung über die Gewinntabelle mit numpy (beliebige einfache Spiele, auch der Schnitt zweier Gewichtssysteme) und die DP.
- **Experimente** (`mdx_experiments.py`): Zufallsinstanzen aus sechs Erzeugern (fast gleich: ganze Zahl von 8 bis 12; gleichverteilt: ganze Zahl von 1 bis 20; gestuft: 3, 10 oder 30, je mit gleicher Wahrscheinlichkeit; Pareto mit α = 1,2 und α = 2,5: Gewicht ⌊3·(1−u)^(−1/α)⌋ mit u gleichverteilt in [0, 1), mindestens 1; lognormal: Gewicht ⌊exp(2 + z)⌋ mit z standardnormal nach Box–Muller, mindestens 1), je Zelle vier feste Zufalls-Seeds mit je 50 Instanzen (200 Instanzen je Zelle), der Beirat mit je 75 (300). Der Zufall kommt aus SplitMix64 (`mdx_rng.py`, wörtliche Kopie aus `ab-test-demo`). Alle Zählungen sind exakt, Anteile exakte Brüche, wo ein Vergleich an einer Toleranz hängen könnte.
- **Paradoxa:** Stimme abgeben, zwei Mitglieder zusammenlegen, ein Mitglied aufspalten, ein neues Mitglied aufnehmen; die Quote bleibt als Zahl gleich, beim neuen Mitglied wird sie mit demselben Anteil p neu bestimmt.
- **Quellen:** geprüft sind nur arXiv 2304.10002 (Owen-Aussage, siehe unten) und die Gewichte des Vertrags von Nizza (Wikipedia, 2026-11-18, Summe 345, Schwelle 255). Banzhaf 1965, Shapley und Shubik 1954 und die Literatur zu Paradoxa und Komplexität sind **nicht geprüft** und werden nicht zitiert.
- **Owen-Wert, Harsanyi-Dividenden:** nur als Expander (Zusammenschluss zweier Gruppen; Zerlegung in Einstimmigkeitsspiele).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen gelten für die genannten Erzeuger, Mitgliederzahlen und Quoten (Modellannahmen) und sind Messungen an erzeugten Instanzen; „Zelle“ heißt Erzeuger, n und Quote. Jede Zeile nennt ihren Test (`tests/test_claims.py`, wenn nicht anders angegeben).

| Frage | Befund (Voraussetzung, Zahl der Läufe) | Test |
|---|---|---|
| Fuhrpark 7 (40, 25, 10, 8, 5, 3, 2 Lkw), einfache Mehrheit: folgt die Macht den Stimmen? | Gesamtgewicht 93, Quote 47. Das Mitglied mit 25 Lkw hat 26,9 % der Stimmen und 10,6 % der Macht (Banzhaf), genau so viel wie das mit 10 Lkw (10,8 % der Stimmen) und das mit 8 Lkw (8,6 % der Stimmen): alle drei haben die Schwingzahl 10; das Mitglied mit 40 Lkw hat 43,0 % der Stimmen und 57,4 % der Macht. Bei mehr als 2/3 (Quote 63) hat es ein Veto. Seine Macht ist dann 46,8 % (Banzhaf) bzw. 56,0 % (Shapley–Shubik). | `test_fleet_preset_numbers` |
| Weicht die Macht vom Stimmanteil ab, auch ohne schweren Tail? | In **59 von 72 Zellen** (6 Erzeuger, n = 5, 7, 9, Quote über 1/2, 3/5, 2/3, 3/4; je Zelle 200 Instanzen) weicht die Macht (Banzhaf) im Mittel um mindestens 5 Prozentpunkte vom Stimmanteil ab; Spanne 2,6 Prozentpunkte (gleichverteilt, n = 9, Quote über 3/5) bis 21,7 (lognormal, n = 5, einfache Mehrheit). Auch ohne schweren Tail weicht die Macht ab: bei fast gleichen Gewichten (8 bis 12) liegt die Abweichung zwischen 3,2 und 13,1 Prozentpunkten (in 6 von 12 Zellen mindestens 5), bei Pareto mit α = 2,5 zwischen 3,7 und 11,0 (je 12 Zellen). | `test_generator_table_*` |
| Wie oft gibt es Nullspieler und Diktatoren? | Hängt am Erzeuger: n = 5, einfache Mehrheit, 200 Instanzen: Anteil der Instanzen mit Nullspieler 0 % (fast gleich), 37 % (gleichverteilt), 50 % (gestuft), 37 % (Pareto α = 1,2), 7,5 % (Pareto α = 2,5), 54 % (lognormal); mit Diktator 0, 5, 22,5, 27, 6,5, 32 %. Bei gestuften Gewichten sinkt der Anteil mit n (50, 40,5, 35 % bei n = 5, 7, 9). | `test_generator_table_null_players_*` |
| Weichen die beiden Indizes in ihren **Werten** ab? | Ja, und mehr bei Quote über 3/4 als bei einfacher Mehrheit (bei Einstimmigkeit sind beide Indizes gleich): in den 18 Zellen mit einfacher Mehrheit höchstens 3,3 Prozentpunkte (halbe Abweichungssumme; größte Abweichung eines Mitglieds im Mittel höchstens 2,5), in den 18 Zellen mit Quote über 3/4 bis 10,7. | `test_generator_table_index_deviation_grows_with_the_quote` |
| Ordnen sie die Mitglieder verschieden? | **In einem Gewichtsspiel nie** (Satz mit Beweisskizze, Tab Zwei Indizes): in allen **26.832** aufgezählten Gewichtsspielen (n = 3 bis 7, kleine Gewichte, alle Quoten über der Hälfte) ist die Rangordnung gleich, obwohl die Werte in 10.565 dieser Spiele verschieden sind. | `test_rank_theorem_enumeration_counts` |
| Im Schnitt zweier Gewichtssysteme? | Dort ja: in 0 bis 135 von je 200 Instanzen (12 Zellen: gleichverteilt und lognormal, n = 6, 8, 9, Quote über 1/2 und 2/3) ordnen die Indizes verschieden; in einer Zelle nie (gleichverteilt, n = 6, Quote über 2/3). Echte Umkehrung (ein Mitglied vor einem anderen bei Banzhaf, dahinter bei Shapley–Shubik) in 0 bis 86 Instanzen je Zelle, bei n = 6 in keiner. Ein Beispiel mit n = 7 (Preset im Tab) ist durch die Aufzählung aller 5.040 Reihenfolgen gegengeprüft; ein von Hand rechenbares Beispiel fand sich nicht. | `test_two_systems_*` |
| Wo liegt die beste Quote? | n = 7, 200 Instanzen je Erzeuger: die Quote mit der kleinsten Abweichung Macht gegen Stimmanteil liegt im Mittel bei 61 % bis 71 % der Gesamtstimmen und in 190 bis 200 von 200 Instanzen über der einfachen Mehrheit; die Abweichung sinkt gegenüber der einfachen Mehrheit auf das 1/2,8 (gleichverteilt) bis 1/5,5 (Pareto α = 1,2), jeweils Verhältnis der Mittelwerte der Banzhaf-Abweichung. Bei Einstimmigkeit hat jedes Mitglied die Macht 1/7 und die Abweichung zum Stimmanteil steigt (zum Beispiel gleichverteilt von 6,2 auf 21,8 Prozentpunkte). Das gilt für diese Erzeuger und n = 7, kein Naturgesetz. | `test_best_quote_*`, `test_unanimity_*` |
| Spenderparadox (ein Mitglied gibt eine Stimme ab und gewinnt Machtanteil)? | **Vollständig aufgezählt** (alle nichtfallenden Gewichtsvektoren, n = 3 bis 5 mit Gewichten bis 8, n = 6 mit Gewichten bis 5; alle Quoten über der Hälfte; alle Einzelübertragungen): bei **139 von 251.040** Übertragungen bei Banzhaf (n = 5: 100, n = 6: 39, n = 3 und 4: keine), bei Shapley–Shubik in **keiner**. Das kleinste Beispiel: Gewichte 1, 1, 1, 2, 4, Quote 7; das Mitglied mit 4 gibt eine Stimme an das mit 2: Banzhaf-Anteil 8/20 = 40,0 % → 7/17 = 41,2 %, Shapley–Shubik 50,0 % → 45,0 %. Die Zählung ist kein Beweis. In den Zufallsreihen (n = 6, vier Erzeuger, 200 Instanzen je Zelle) bei Quote über 1/2 in keinem der 23.055 Fälle, bei Quote über 2/3 in 52 von 23.055. | `test_donor_*` |
| Zusammenschluss zweier Mitglieder? | n = 6, alle 15 Paare, 3.000 Paare je Zelle: der Block hat bei Banzhaf **weniger** Macht als die beiden vorher zusammen in 20 bis 337 von 3.000 Paaren (Quote über 1/2: 20 bis 259; über 2/3: 233 bis 337). Bei Quote über 1/2 ist die Richtung bei beiden Indizes in allen 12.000 Paaren gleich, bei 2/3 verschieden in 21 bis 318 Paaren je Zelle. | `test_merge_counts_and_direction_agreement` |
| Aufspaltung? | n = 6, Mitglieder mit Gewicht mindestens 2: beide Teile zusammen haben bei Banzhaf **mehr** Macht in 2.014 von 9.222 Fällen (8 Zellen), weniger in 5.118. | `test_split_counts` |
| Neues Mitglied? | Ein altes Mitglied gewinnt Machtanteil in 1.064 von 1.600 Instanzen (Banzhaf; 8 Zellen mit je 200). Keine Wertung: die Anteile summieren sich zu 1, und die neu bestimmte Quote springt. | `test_new_member_counts` |
| Zählen statt Aufzählen: stimmt die DP? | Gleich den Aufzählungen in allen Orakel-Instanzen (n bis 12), und beim Vertrag-von-Nizza-Beispiel (n = 27, nur die Stimmbedingung 255 von 345) gleich der Aufzählung aller 2²⁶ Teilmengen je verschiedenem Gewicht: Stimmanteil / Banzhaf / Shapley–Shubik in Prozent für das Mitglied mit 29 Stimmen 8,41 / 7,78 / 8,67, mit 14 Stimmen 4,06 / 4,26 / 3,99, mit 3 Stimmen 0,87 / 0,94 / 0,82. Banzhaf liegt bei allen Mitgliedern bis 14 Stimmen über dem Stimmanteil, Shapley–Shubik nur bei den sechs Mitgliedern mit 27 oder 29 Stimmen. Beim Reglermaximum (n = 60, Gewichtssumme 100.000) liegt das Zählfeld unter 50 MB und die Summe der Reihenfolgenzähler ist 60!. Laufzeiten stehen nicht im Test. | `test_oracle_machtindex.py`, `test_preset_nizza_numbers`, `test_the_dp_table_for_the_slider_maximum_fits_and_runs` |
| Rundung reeller Gewichte? | 200 lognormale Gewichtsvektoren (n = 8) auf ganze Gewichte mit Summe 30, 100, 300, 1.000, 10.000 gerundet, Bezug Summe 100.000: im Mittel größte Abweichung des Banzhaf-Anteils 2,50 / 0,97 / 0,32 / 0,13 / 0,011 Prozentpunkte; über 1 Prozentpunkt in 150 / 82 / 23 / 8 / 1 von 200. Das feine Raster ist selbst eine Näherung. | `test_raster_numbers` |
| Beirat (Brücke zur Sitzverteilung)? | Standardinstanz der `sitzverteilung-demo` (acht Verbände, 40 Sitze; Quote 18,43 des größten, README der Nachbar-Demo): der größte Verband hat 46,1 % der Mitglieder; mit 18 Sitzen (45,0 %, Hamilton und Webster) hat er bei Beschluss mit mehr als der Hälfte der Sitze 78,2 % der Macht (Banzhaf) und 67,9 % (Shapley–Shubik), mit 20 Sitzen (50,0 %, Jefferson) 91,3 % und 85,7 %. Zufallsreihe (acht Verbände, lognormale Größen, 16, 24, 48, 64 Sitze, 300 Instanzen je Zeile): Jefferson liegt in allen 8 Zeilen bei Sitzen und beiden Machtmaßen am weitesten vom Mitgliederanteil; die Banzhaf-Macht weicht 2,5- bis 10,9-mal so weit vom Mitgliederanteil ab wie die Sitze bei σ = 1,2 (in 52 bis 84 von 300 Instanzen hat ein Verband die ganze Macht), 1,2- bis 2,7-mal bei σ = 0,5 (nie); bei Shapley–Shubik 2,5- bis 10,0-mal bzw. 1,2- bis 2,9-mal. | `test_board_*` |
| Owen-Wert: ist ein Zusammenschluss zweier Gruppen immer vorteilhaft? | Nein, nicht im Abstimmungsspiel: n = 6, Gewichte 1 bis 9, 300 Zusammenschlüsse: nachteilig 5, unverändert 132, vorteilhaft 163 (größte Einbuße 1/30 des Gesamtwerts); n = 5: 0 / 200 / 100. Im Flughafenspiel (Kostenspiel) bei n = 6: 0 / 69 / 231, bei n = 5: 0 / 73 / 227; in diesen 600 gerechneten Zusammenschlüssen trat dort kein nachteiliger Fall auf (die Literatur nennt „immer vorteilhaft“ dort einen Satz). | `test_owen_merge_counts` |
| Harsanyi-Dividenden: erklären sie die Abweichung der Indizes? | Nicht durchgehend: Pearson-Korrelation zwischen der Dividendenmasse ab Größe 3 und der Abweichung Banzhaf gegen Shapley–Shubik in sechs Zellen (n = 8, 50 Instanzen eines Zufalls-Seeds, drei Erzeuger, Quote über 1/2 und 3/4) von −0,25 bis 0,66, in vier Zellen betragsmäßig unter 0,3; Werte unter 0,3 sind bei 50 Instanzen nicht von 0 zu unterscheiden. | `test_harsanyi_*` |
| Kern des Gewinnspiels | Der Kern ist nicht leer genau dann, wenn es ein Mitglied mit Veto gibt: gegen ein LP geprüft in allen Spielen mit n = 3 bis 5 und Gewichten bis 5 (alle Quoten über der Hälfte). | `test_oracle_machtindex.py` |

## Befunde und Korrekturen gegenüber dem Plan

Die Zahlen des Einzelplans waren Hypothesen aus einer Vormessung mit anderem Zufallsgenerator; im Bau neu gemessen:

- **Bestätigt (andere Zufallsinstanzen, gleiche Größenordnung):** Macht weicht auch ohne Pareto-Tail ab; Nullspieler hängen am Erzeuger (nicht nur am Tail); Werte der Indizes weichen bei einfacher Mehrheit höchstens um 3,3 und bei Quote über 3/4 bis 10,7 Prozentpunkte ab; beste Quote 61 bis 71 % statt der geplanten 60 bis 70 %; Spenderparadox 139 von 251.040 bei Banzhaf und 0 bei Shapley–Shubik (genau die geplanten Zahlen); Zusammenschluss; Beirat (Banzhaf-Faktoren 2,5 bis 10,9 statt der geplanten 2,6 bis 11,4 und 1,2 bis 2,7 statt 1,2 bis 3,1); Owen 5 von 300 nachteilig.
- **„Die Indizes ordnen in Gewichtsspielen verschieden“ ist ein Satz, kein Befund** (0 von 26.832 aufgezählten Spielen; Plan: 0 von 11.008). Anders im Schnitt zweier Gewichtssysteme: bis 135 von 200 Instanzen (Plan: bis 140).
- **Harsanyi-Dividenden erklären die Abweichung nicht durchgehend** (Plan: −0,29 bis 0,44, nur Expander; hier −0,25 bis 0,66, in zwei Zellen mit Quote über 3/4 deutlich höher). Es bleibt bei einem Expander, aber der Satz „erklärt die Abweichung nicht“ des Plans gilt hier nur eingeschränkt.
- **Owen:** Die Aussage „immer vorteilhaft“ steht in Abschnitt 3.1 von arXiv 2304.10002 (Gómez-Rodríguez, Davila-Pena, Casas-Méndez; über die HTML-Fassung selbst gelesen) mit Verweis auf Vázquez-Brage u. a. (1997) für Flughafenprobleme mit Gruppen; die Arbeit von 1997 ist nicht gelesen; in der Demo ist die Spielklasse Flughafen mit 0 nachteiligen Fällen von 600 bestätigt. Die Auftragsallianz-Zahlen des Plans (12 von 400) sind hier nicht nachgebaut und werden nicht genannt.
- **Port und Präfix:** Port 10041 (laut Bauauftrag in `.claude/launch.json` eingetragen), Präfix `mdx_` (Ordner `machtindex-demo`).
- **Hypothesen H1 bis H11 des Einzelplans:** keine musste verworfen werden außer den beiden oben (Rang-Satz H3 und Harsanyi H8), die der Plan schon als Satz bzw. Expander eingestuft hatte. H10 („Neues Mitglied“) bleibt ein Experiment ohne Wertung.

## Ehrliche Grenzen

**Annahmen**
- Die Genossenschaft beschließt mit **ganzzahligen Stimmgewichten** und einer **Quote**: ein Beschluss fällt, wenn die Gewichtssumme der Zustimmenden mindestens die Quote erreicht. Gewichte, Quote und Koalitionswerte sind Modellannahmen, keine Beobachtung.
- **Macht** bedeutet „Wahrscheinlichkeit, das entscheidende Mitglied zu sein“ unter zwei Annahmen über das Abstimmungsverhalten: alle Koalitionen sind gleich wahrscheinlich (Banzhaf) oder alle Reihenfolgen des Beitritts (Shapley–Shubik). Reale Mitglieder stimmen nach Interessen ab.
- Jedes Mitglied hat **eine Stimme mit seinem Gewicht**, ohne Absprachen und ohne Stimmenthaltung; die Gewichte sind fest.

**Grenzen**
- Die Zählung per dynamischer Programmierung ist ganzzahlig und exakt bis n = 60 Mitglieder und Gewichtssumme 100.000; darüber rechnet die App nicht. Reelle Gewichte brauchen ein Raster (Tab Zählen statt Aufzählen).
- Die Zufallsreihen der Experimente ziehen Gewichte aus sechs festen Erzeugern mit je vier festen Zufalls-Seeds zu 50 Instanzen; andere Erzeuger oder Mitgliederzahlen können andere Zählungen ergeben.
- Das Preset EU-Rat Nizza rechnet **nur die Stimmbedingung** (Schwelle 255 von 345 Stimmen); die weiteren Bedingungen der Beschlussregel (Mehrheit der Staaten, Bevölkerungsanteil) sind nicht modelliert. Die Gewichte und die Schwelle stimmen mit der Wikipedia-Seite „Voting in the Council of the European Union“ überein (Sekundärquelle, 2026-11-18 abgerufen); eine Primärquelle wurde nicht geprüft.
- Die Demo trifft keine Aussage über reale Gremien, rechtliche Beschlussregeln oder Anlageentscheidungen.

**Bekannte Probleme und Unsicherheiten**
- „Das Spenderparadox kommt bei Shapley–Shubik nie vor“ ist in dieser Demo eine **Zählung, kein Beweis**: in 251.040 vollständig aufgezählten Einzelübertragungen (n = 3 bis 6, kleine Gewichte) trat es bei Banzhaf 139-mal auf und bei Shapley–Shubik 0-mal.
- Der Satz, dass beide Indizes in jedem Gewichtsspiel gleich ordnen, ist eine eigene Beweisskizze (Tab Zwei Indizes) plus Aufzählung; er wurde nicht an einer Literaturstelle geprüft.
- Alle Zufallsreihen sind Messungen an erzeugten Instanzen. Die Verteilungen und Parameter sind willkürlich gewählt; echte Genossenschaftsdaten wurden nicht verwendet.
- Die Zeitangaben im Tab Zählen statt Aufzählen hängen an Rechner und Auslastung und sind kein Befund.
- Die Gewichte der Pareto- und Lognormal-Erzeuger kommen über Potenz, Logarithmus, Kosinus und Exponentialfunktion der Rechenbibliothek; eine Rundungsabweichung zwischen Plattformen könnte ein Gewicht um 1 ändern und damit eine Zählung um einen Fall.
- Im Tab Beirat sind die drei Sitzverteilungsverfahren eigener Code und nur an der Standardinstanz der Sitzverteilungs-Demo und an Divisor-Bedingungen geprüft.

## Tests

**222 Tests** (`pytest tests -q -n 8 -p no:cacheprovider`, Laufzeit rund 3,5 Minuten (unter Last durch andere Läufe) auf dem Entwicklungsrechner, vor allem die AppTest-Läufe der Experimente und die Aufzählungen). Zusammensetzung:

- **Kern gegen Handrechnung** (`test_algorithm.py`): Mini-Instanzen von Hand gerechnet (`conftest.py`), je Einheit eine Prüfung.
- **Orakel** (`test_oracle_machtindex.py`, rund 6 s): die vier Rechenwege gegeneinander; Shapley–Shubik aus der Definition mit Brüchen; Indizes aus Harsanyi-Dividenden; Vetospieler gegen den Kern per LP (scipy nur im Test); DP gegen Python-Ganzzahlzählung bei n = 20 und n = 60; EU-Rat Nizza (n = 27) gegen die Aufzählung aller 2²⁶ Teilmengen (rund 2 s, rund 200 MB); Owen-Formel gegen alle Reihenfolgen; Sitzverteilung gegen die Divisor-Bedingung und die Zahlen der Sitzverteilungs-Demo.
- **Eigenschaften** (`test_eigenschaften_machtindex.py`): Effizienz, Symmetrie, Monotonie, Nullspieler in beiden Indizes zugleich, Umbenennen, Skalieren, der Rang-Satz an 26.832 Spielen.
- **Zahlen der README** (`test_claims.py`): jede Zeile der Befunde-Tabelle mit ihrer Voraussetzung.
- **Verdikte** (`test_verdicts.py`): jede Schwelle und jede Zahl im Text an handgesetzten Zeilen; **Presets** (`test_presets.py`): jedes Preset durch das Verdikt und durch den Klick; **Randfälle** (`test_edge_cases.py`): n = 1, 2, Quote an beiden Rändern, Gewicht 0, Reglerränder; **Oberfläche** (`test_app.py`, `test_layout.py`, `test_footer.py`): jeder Knopf, jeder Regler am Minimum und Maximum, Permalink, Hervorhebung des Presets.
- **Szenario** (`test_scenario.py`): Erzeuger, Handeingabe, Kopie von SplitMix64 gegen das Original (`ab-test-demo/abt_rng.py`); **Laufzeit-Importe** (`test_runtime_imports.py`); **README** (`test_readme.py`): geteilter Text, Testzahl.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore`, `.streamlit/config.toml` | Git- und Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfrage, sieben Tabs mit Experimenten, Expander, Formeln |
| `mdx_game.py` | Kern: Quote, vier Rechenwege, Anteile, Vetospieler, Schnitt zweier Systeme |
| `mdx_paradoxes.py` | Übertragung, Zusammenlegen, Aufspalten, neues Mitglied; vollständige Aufzählung des Spenderparadoxes |
| `mdx_experiments.py` | Messreihen der Experimente (feste Zufalls-Seeds), Hilfen der Tabs |
| `mdx_harsanyi.py`, `mdx_owen.py`, `mdx_seats.py` | Dividenden; Owen-Wert (Formel und Definition); Hamilton, Jefferson, Webster und Macht der Sitze |
| `mdx_scenario.py`, `mdx_rng.py` | Erzeuger und Handeingabe; SplitMix64 (wörtliche Kopie aus `ab-test-demo`) |
| `mdx_evaluation.py` | Kennzahlen der Instanz, Verdikte als reine Funktionen |
| `mdx_constants.py`, `mdx_presets.py`, `mdx_layout.py` | Grenzen, Presets, Permalink; fester Kopf |
| `mdx_texts.py`, `mdx_visualization.py` | Feste Texte (Annahmen-Text wörtlich wie in dieser README); Plotly-Abbildungen |
| `requirements.txt`, `requirements-dev.txt` | Laufzeit (streamlit, numpy, pandas, plotly); dazu pytest und scipy (nur Gegenprobe) |
| `tests/` | siehe Abschnitt Tests |

## Bewusst nicht umgesetzt

- **Allianzbildung und Owen-Wert als eigene Demo:** nur der Expander mit der Messung zum Zusammenschluss; die Stabilität von Allianzen ist nicht gebaut.
- **Kern und Shapley-Wert für Kostenspiele** (Sammeltouren, Standorte, Zuordnung): `kern-demo`, `shapley-demo` und die weiteren Demos der Linie Koalitionen und Teilen.
- **Doppelte Mehrheit als eigener Experimentierraum** (zum Beispiel Köpfe und Gewicht): nur der Schnitt zweier Gewichtssysteme im Tab Zwei Gewichtssysteme.
- **Reale Gremien als Behauptung:** das Preset EU-Rat Nizza ist ein Rechenbeispiel der Stimmbedingung, kein Urteil über den Rat; Vergleichswerte aus der Literatur wurden nicht herangezogen.
- **Normiertes Penrose-Maß, Johnston-Index, Deegan–Packel-Index** und weitere Machtindizes.
- **Reelle Gewichte ohne Raster, Enthaltungen, Absprachen und Interessen** der Mitglieder.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Die Streamlit-Cloud-Einstellung der Python-Version ist nicht festgelegt; die CI läuft mit 3.12, lokal wurde mit 3.14 gebaut. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Koalitionen und Teilen: Macht und Aufteilung](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html).
