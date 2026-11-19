"""Feste Texte der App. Der Annahmen-Text steht wörtlich auch in der README (ein Test vergleicht beide Fassungen); Zahlen kommen aus Konstanten oder Rechnungen,
die `tests/test_claims.py` nachrechnet."""

import mdx_constants as C
from mdx_evaluation import th

DONOR_GAMES = sum(r[2] for r in C.DONOR_ENUMERATION)
DONOR_TRANSFERS = sum(r[3] for r in C.DONOR_ENUMERATION)
DONOR_CASES_B = sum(r[4] for r in C.DONOR_ENUMERATION)
DONOR_CASES_S = sum(r[5] for r in C.DONOR_ENUMERATION)
DONOR_TRANSFERS_TEXT, DONOR_CASES_B_TEXT = th(DONOR_TRANSFERS), th(DONOR_CASES_B)

INTRO_MARKDOWN = """
Eine **Spediteursgenossenschaft** entscheidet mit **Stimmgewichten** (hier: Zahl der Lkw im Fuhrpark) und einer **Beschlussquote**. Die Frage: **wie oft ist ein Mitglied das, ohne das kein Beschluss fällt, und wie weit weicht diese Macht vom Stimmanteil ab?**
Gemessen wird die Macht mit zwei Indizes, dem **Banzhaf-Index** und dem **Shapley–Shubik-Index**. Stimmgewichte, Quote und Eigennutz sind **Modellannahmen**: Macht heißt hier „Wahrscheinlichkeit, das entscheidende Mitglied zu sein“, nicht Einfluss im Alltag.
Die Demo gehört zur [Linie Koalitionen und Teilen](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html). Den Shapley-Wert für Kosten einer Sammeltour zeigt die `shapley-demo`, die Verteilung von Sitzen auf Verbände die `sitzverteilung-demo`; hier geht es um die Macht, die Stimmen und Sitze verleihen.

Weiter unten: die Kernfrage mit Urteil, sieben Tabs mit Experimenten (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""

HOW_IT_WORKS_MARKDOWN = """
1. **Beschluss:** eine Koalition von Mitgliedern setzt einen Beschluss durch, wenn ihre Gewichtssumme die **Quote** erreicht. Die Quote ist die kleinste ganze Zahl, die **mehr** als den Anteil p der Gesamtgewichte ausmacht (p = 50 %: einfache Mehrheit; p = 100 %: Einstimmigkeit).
2. **Schwingspieler:** ein Mitglied ist in einer Koalition **entscheidend**, wenn sie mit ihm gewinnt und ohne es verliert.
3. **Banzhaf-Index:** zähle für jedes Mitglied alle Koalitionen, in denen es entscheidend ist; sein Anteil an der Summe dieser Zahlen ist der Index.
4. **Shapley–Shubik-Index:** lasse die Mitglieder in zufälliger Reihenfolge eintreten; entscheidend ist, wer die Quote als Erster erreicht. Der Index ist der Anteil der Reihenfolgen, in denen das Mitglied entscheidet.
5. **Zählen statt Aufzählen:** beide Zahlen lassen sich ohne Aufzählung aller 2ⁿ Koalitionen berechnen (dynamische Programmierung über Größe und Gewichtssumme). Die Grenze ist die **Gewichtssumme**, nicht die Zahl der Mitglieder.

| Kennzahl | Bedeutung | Bezugsmenge |
|---|---|---|
| **Stimmanteil** | Gewicht des Mitglieds durch Gesamtgewicht | alle Gewichte, Summe 100 % |
| **Schwingzahl** | Zahl der Koalitionen, in denen das Mitglied entscheidend ist | alle 2ⁿ⁻¹ Koalitionen ohne das Mitglied |
| **Banzhaf-Anteil** | Schwingzahl durch Summe aller Schwingzahlen | Anteil an der gesamten Macht, Summe 100 % |
| **Shapley–Shubik-Anteil** | Anteil der Reihenfolgen, in denen das Mitglied die Quote als Erstes erreicht | alle n! Reihenfolgen, Summe 100 % |
| **Vetospieler** | ohne das Mitglied erreicht keine Koalition die Quote | alle Koalitionen |
| **Nullspieler** | das Mitglied ist in keiner Koalition entscheidend (Macht 0, auch mit vielen Stimmen) | alle Koalitionen |
| **Abweichung** | halbe Summe der Beträge der Unterschiede zweier Anteilsvektoren: der Anteil, der umverteilt werden müsste | Summe 100 %, Wert 0 bis 100 Prozentpunkte |

„Quote“ heißt hier Beschlussquote, nicht Trefferquote.
"""

ASSUMPTIONS_MARKDOWN = f"""
**Annahmen**
- Die Genossenschaft beschließt mit **ganzzahligen Stimmgewichten** und einer **Quote**: ein Beschluss fällt, wenn die Gewichtssumme der Zustimmenden mindestens die Quote erreicht. Gewichte, Quote und Koalitionswerte sind Modellannahmen, keine Beobachtung.
- **Macht** bedeutet „Wahrscheinlichkeit, das entscheidende Mitglied zu sein“ unter zwei Annahmen über das Abstimmungsverhalten: alle Koalitionen sind gleich wahrscheinlich (Banzhaf) oder alle Reihenfolgen des Beitritts (Shapley–Shubik). Reale Mitglieder stimmen nach Interessen ab.
- Jedes Mitglied hat **eine Stimme mit seinem Gewicht**, ohne Absprachen und ohne Stimmenthaltung; die Gewichte sind fest.

**Grenzen**
- Die Zählung per dynamischer Programmierung ist ganzzahlig und exakt bis n = {C.N_MAX} Mitglieder und Gewichtssumme {th(C.WEIGHT_SUM_MAX)}; darüber rechnet die App nicht. Reelle Gewichte brauchen ein Raster (Tab Zählen statt Aufzählen).
- Die Zufallsreihen der Experimente ziehen Gewichte aus sechs festen Erzeugern mit je vier festen Zufalls-Seeds zu 50 Instanzen; andere Erzeuger oder Mitgliederzahlen können andere Zählungen ergeben.
- Das Preset EU-Rat Nizza rechnet **nur die Stimmbedingung** (Schwelle 255 von 345 Stimmen); die weiteren Bedingungen der Beschlussregel (Mehrheit der Staaten, Bevölkerungsanteil) sind nicht modelliert. Die Gewichte und die Schwelle stimmen mit der Wikipedia-Seite „Voting in the Council of the European Union“ überein (Sekundärquelle, 2026-11-18 abgerufen); eine Primärquelle wurde nicht geprüft.
- Die Demo trifft keine Aussage über reale Gremien, rechtliche Beschlussregeln oder Anlageentscheidungen.

**Bekannte Probleme und Unsicherheiten**
- „Das Spenderparadox kommt bei Shapley–Shubik nie vor“ ist in dieser Demo eine **Zählung, kein Beweis**: in {DONOR_TRANSFERS_TEXT} vollständig aufgezählten Einzelübertragungen (n = 3 bis 6, kleine Gewichte) trat es bei Banzhaf {DONOR_CASES_B_TEXT}-mal auf und bei Shapley–Shubik {DONOR_CASES_S}-mal.
- Der Satz, dass beide Indizes in jedem Gewichtsspiel gleich ordnen, ist eine eigene Beweisskizze (Tab Zwei Indizes) plus Aufzählung; er wurde nicht an einer Literaturstelle geprüft.
- Alle Zufallsreihen sind Messungen an erzeugten Instanzen. Die Verteilungen und Parameter sind willkürlich gewählt; echte Genossenschaftsdaten wurden nicht verwendet.
- Die Zeitangaben im Tab Zählen statt Aufzählen hängen an Rechner und Auslastung und sind kein Befund.
- Die Gewichte der Pareto- und Lognormal-Erzeuger kommen über Potenz, Logarithmus, Kosinus und Exponentialfunktion der Rechenbibliothek; eine Rundungsabweichung zwischen Plattformen könnte ein Gewicht um 1 ändern und damit eine Zählung um einen Fall.
- Im Tab Beirat sind die drei Sitzverteilungsverfahren eigener Code und nur an der Standardinstanz der Sitzverteilungs-Demo und an Divisor-Bedingungen geprüft.
"""

LIMITS_MARKDOWN = """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Gewichte sind fest und bekannt.** | Verhandeln Mitglieder über Stimmen oder tauschen sie, ändert sich die Machtverteilung; die Paradoxa im Tab Paradoxa zeigen, dass weniger Stimmen nicht immer weniger Macht heißen. | Spieltheorie der Stimmen-Verhandlung; hier nur gezeigt, nicht gelöst |
| **Alle Koalitionen oder alle Reihenfolgen sind gleich wahrscheinlich.** | Bilden sich Blöcke (feste Gruppen), ist der Owen-Wert die passende Erweiterung; im Expander Owen-Wert sieht man, dass ein Zusammenschluss dort nicht immer vorteilhaft ist. | Owen-Wert (Expander), Koalitionsbildung |
| **Eine einzige Abstimmung mit einer Quote.** | Gelten zwei Quoten zugleich (Fuhrpark und Umsatz), ordnen die beiden Indizes erstmals verschieden (Tab Zwei Gewichtssysteme). | Tab Zwei Gewichtssysteme |
| **Gewinn heißt 0 oder 1.** | Soll ein Beschluss einen Nutzen verteilen, braucht man Kern und Shapley-Wert für Nutzenspiele. Im Gewinnspiel ist der Kern nicht leer genau dann, wenn es ein Mitglied mit Veto gibt (gegen ein LP geprüft für n bis 5 und Gewichte bis 5). | `kern-demo`, `shapley-demo` |
| **Sitze folgen den Mitgliedern.** | Das Sitzverteilungsverfahren verschiebt die Macht stärker als die Sitze (Tab Beirat). | `sitzverteilung-demo` (Verfahren), Tab Beirat (Macht) |
| **Zählen ist billig.** | Die Zählung hängt an der Gewichtssumme: bei sehr großen oder reellen Gewichten braucht man ein Raster und verliert Genauigkeit (Tab Zählen statt Aufzählen). | Tab Zählen statt Aufzählen |
"""

NOT_IMPLEMENTED_MARKDOWN = """
- **Allianzbildung und Owen-Wert als eigene Demo:** nur der Expander mit der Messung zum Zusammenschluss; die Stabilität von Allianzen ist nicht gebaut.
- **Kern und Shapley-Wert für Kostenspiele** (Sammeltouren, Standorte, Zuordnung): `kern-demo`, `shapley-demo` und die weiteren Demos der Linie Koalitionen und Teilen.
- **Doppelte Mehrheit als eigener Experimentierraum** (zum Beispiel Köpfe und Gewicht): nur der Schnitt zweier Gewichtssysteme im Tab Zwei Gewichtssysteme.
- **Reale Gremien als Behauptung:** das Preset EU-Rat Nizza ist ein Rechenbeispiel der Stimmbedingung, kein Urteil über den Rat; Vergleichswerte aus der Literatur wurden nicht herangezogen.
- **Normiertes Penrose-Maß, Johnston-Index, Deegan–Packel-Index** und weitere Machtindizes.
- **Reelle Gewichte ohne Raster, Enthaltungen, Absprachen und Interessen** der Mitglieder.
"""

RANK_THEOREM_MARKDOWN = r"""
**Satz.** In einem Gewichtsspiel ordnen der Banzhaf- und der Shapley–Shubik-Index die Mitglieder **gleich**: das Mitglied $i$ steht bei dem einen Index genau dann vor $j$, wenn es auch bei dem anderen vor $j$ steht, und die beiden sind bei dem einen genau dann gleichauf, wenn sie es bei dem anderen sind. Die **Werte** der beiden Indizes dürfen trotzdem abweichen.

**Beweisskizze** (eigene Herleitung, nicht an einer Literaturstelle geprüft). Sei $w_i \ge w_j$ und $v$ das 0/1-Gewinnspiel. Dann gilt für jede Koalition $T$ ohne $i$ und $j$: $v(T \cup i) \ge v(T \cup j)$. Teilt man die Summen über alle Koalitionen danach, ob sie $j$ (bzw. $i$) enthalten, kürzen sich die Terme mit beiden Mitgliedern, und es bleibt

$$\eta_i - \eta_j = 2 \sum_{T \subseteq N \setminus \{i,j\}} \bigl[ v(T \cup i) - v(T \cup j) \bigr]$$

$$\varphi_i - \varphi_j = \sum_{T \subseteq N \setminus \{i,j\}} \bigl( c_{|T|} + c_{|T|+1} \bigr) \bigl[ v(T \cup i) - v(T \cup j) \bigr], \qquad c_k = \frac{k!\,(n-k-1)!}{n!} > 0$$

Alle Summanden $v(T \cup i) - v(T \cup j)$ sind $\ge 0$ und hängen nicht vom Index ab; beide Differenzen sind positive Vielfache derselben Summanden. Also ist die eine Differenz genau dann $> 0$, wenn es die andere ist, und beide sind genau dann $0$, wenn alle Summanden $0$ sind.

**Warum der Satz im Schnitt zweier Gewichtssysteme fällt:** dort kann $v(T \cup i) - v(T \cup j)$ je nach $T$ das Vorzeichen wechseln, und der Beweis greift nicht mehr. Ob die Indizes dann verschieden ordnen, zeigt die Messung im Tab Zwei Gewichtssysteme.

**Was gemessen ist:** der Knopf unten zählt alle Gewichtsspiele einer festen Aufzählung (der Satz ist ein Beweis, die Aufzählung eine Gegenprobe des Codes).
"""

HARSANYI_MARKDOWN = r"""
Jedes einfache Spiel $v$ lässt sich in **Einstimmigkeitsspiele** zerlegen: $v(S) = \sum_{T \subseteq S} \Delta(T)$. Die Dividende $\Delta(T)$ ist der Teil des Werts, den nur die ganze Gruppe $T$ gemeinsam erzeugt. Der Shapley–Shubik-Wert eines Mitglieds ist die Summe von $\Delta(T)/|T|$ über alle $T$ mit ihm, der unnormierte Banzhaf-Wert (Schwingzahl durch $2^{n-1}$) die Summe von $\Delta(T)/2^{|T|-1}$. Die beiden Indizes unterscheiden sich also nur darin, wie sie eine Dividende auf die Mitglieder der Gruppe verteilen.

Beispiel **[4, 3, 2, 1], Quote 6** (die Mitglieder heißen A bis D): die Dividenden ungleich null sind Δ({A,B}) = Δ({A,C}) = Δ({B,C,D}) = 1 und Δ({A,B,C}) = Δ({A,B,C,D}) = −1.
Die Dividenden erklären, wie die Werte entstehen. Dass sie die **Abweichung** zwischen den Indizes erklären, hat sich nicht durchgehend gezeigt (siehe README, Befunde und Korrekturen gegenüber dem Plan); deshalb ist dies ein Expander und kein eigener Tab.
"""

MATH_MARKDOWN = r"""
**Lesehilfe.** Gegeben sind $n$ Mitglieder mit ganzzahligen Gewichten und eine Quote. Gesucht ist für jedes Mitglied, wie oft es für den Beschluss entscheidend ist.

| Symbol | Bedeutung |
|---|---|
| $N = \{1, \dots, n\}$ | die Mitglieder |
| $w_i$ | Gewicht (Stimmen) von Mitglied $i$, ganzzahlig und mindestens 1 |
| $W = \sum_i w_i$ | Gesamtgewicht |
| $p$ | Beschlussquote als Anteil, $0{,}5 \le p \le 1$ |
| $q$ | Quote als ganze Zahl: kleinste ganze Zahl mit $q > pW$, bei $p = 1$ gilt $q = W$ |
| $v(S)$ | Wert einer Koalition $S$: 1, wenn $\sum_{i \in S} w_i \ge q$, sonst 0 |
| $\eta_i$ | Schwingzahl von $i$ (Zahl der Koalitionen, in denen $i$ entscheidend ist) |
| $\beta_i,\ \varphi_i$ | Banzhaf-Anteil und Shapley–Shubik-Anteil von $i$ |
| $C(s,k)$ | Zahl der Teilmengen der Größe $s$ mit Gewichtssumme $k$ |
| $D_i(s,k)$ | dasselbe ohne das Mitglied $i$ |

**Quote und Beschluss.**

$$q = \lfloor pW \rfloor + 1 \quad (p < 1), \qquad q = W \quad (p = 1)$$

$$v(S) = \begin{cases} 1 & \text{wenn } \sum_{i \in S} w_i \ge q \\ 0 & \text{sonst} \end{cases}$$

**Banzhaf-Index.**

$$\eta_i = \bigl| \{ S \subseteq N \setminus \{i\} : v(S) = 0,\ v(S \cup \{i\}) = 1 \} \bigr|, \qquad \beta_i = \frac{\eta_i}{\sum_{k \in N} \eta_k}$$

**Shapley–Shubik-Index.**

$$\varphi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n - |S| - 1)!}{n!} \bigl( v(S \cup \{i\}) - v(S) \bigr)$$

**Zählen statt Aufzählen.** Die Tabelle $C$ aller Mitglieder entsteht Mitglied für Mitglied; die Rücknahme von $i$ ergibt die Tabelle ohne $i$:

$$C_j(s,k) = C_{j-1}(s,k) + C_{j-1}(s-1,\ k - w_j)$$

$$D_i(s,k) = C(s,k) - D_i(s-1,\ k - w_i)$$

Mitglied $i$ ist entscheidend, wenn die Summe $k$ der übrigen Mitglieder in der Koalition zwischen $q - w_i$ und $q - 1$ liegt:

$$\eta_i = \sum_{s=0}^{n-1} \ \sum_{k = q - w_i}^{q-1} D_i(s,k), \qquad n!\,\varphi_i = \sum_{s=0}^{n-1} s!\,(n-1-s)! \sum_{k = q - w_i}^{q-1} D_i(s,k)$$

Der Aufwand wächst mit $n^2 W$ (Größe mal Gewichtssumme), nicht mit $2^n$.

**Abweichung zweier Anteilsvektoren.**

$$\delta(a, b) = \frac{1}{2} \sum_{i \in N} \lvert a_i - b_i \rvert$$

**Vetospieler und Kern.** Ein Mitglied $i$ hat ein Veto, wenn $W - w_i < q$. Im Gewinnspiel (Wert 1 für gewinnende Koalitionen) ist der Kern genau dann nicht leer, wenn es ein Mitglied mit Veto gibt.

**Modell oder Skizze?** Dies ist das vollständige Modell der Berechnung. Die Zufallsreihen der Experimente (Erzeuger, Seeds, Zellen) stehen in der README und im Code `mdx_experiments.py`.

**Literatur.** Die Indizes gehen auf Banzhaf und auf Shapley und Shubik zurück; die Quellenangaben wurden hier nicht an den Originaltexten geprüft und sind deshalb nicht aufgeführt.
"""
