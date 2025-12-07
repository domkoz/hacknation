# Kompendium Wskaźników i Metryk S&T
**Wersja "Źródła Prawdy": 1.1 (Edycja Ekspercka)**
**Na podstawie kodu: `app/utils.py`, `app/main.py`**

Ten dokument stanowi ostateczne odniesienie dla logiki matematycznej i biznesowej napędzającej Dashboard Stability & Transformation. Interpretuje on implementację techniczną przez trzy soczewki: **Analiza Biznesowa (KPI)**, **Data Science (Algorytmy)** oraz **Naukę Aktuarialną (Ryzyko)**.

---

## 1. Surowe Metryki Finansowe (Fundamenty)

### Marża Zysku Netto (Net Profit Margin)
*   **Wzór:** `(Zysk Netto / Przychód) * 100`
*   **Analityk Biznesowy:** Klasyczne KPI efektywności. Mówi nam, ile groszy z każdej złotówki przychodu zostaje jako zysk. Niska marża (<5%) oznacza wysoką wrażliwość na wzrost kosztów.
*   **Data Scientist:** Główna cecha dla *Stability Score*. Jest normalizowana względem standardowego zakresu (-5% do +20%), aby obsłużyć wartości odstające (outliery) bez psucia rozkładu.
*   **Aktuariusz:** Pierwsza linia obrony przed niewypłacalnością. Wyższe marże zapewniają "bufor wypłacalności" przeciwko negatywnym odchyleniom w szkodowości lub kosztach.

### Obciążenie Długiem (Debt Burden / Revenue)
*   **Wzór:** `Całkowity Dług / Przychód`
*   **Analityk Biznesowy:** Wskaźnik dźwigni. Wskazuje, ile lat przychodów zajęłaby spłata długu. Wartość >4.0x jest w tym modelu uznawana za stan zagrożenia ("Distressed").
*   **Data Scientist:** Traktowana jako *cecha odwrotna*. W normalizacji używamy `1 - norm(dług)`, ponieważ mniej znaczy lepiej. Silnie wpływa na komponent "Bezpieczeństwo".
*   **Aktuariusz:** Kluczowy predyktor prawdopodobieństwa niewypłacalności (Default Probability). Wysoka dźwignia drastycznie zwiększa Prawdopodobieństwo Ruiny w czasie spowolnienia gospodarczego.

### Wskaźnik Płynności Gotówkowej (Cash Ratio)
*   **Wzór:** `Gotówka / Zobowiązania Krótkoterminowe`
*   **Analityk Biznesowy:** "Płynność Bieżąca". Czy firma może dziś spłacić swoje rachunki? <0.2 to terytorium kryzysu płynności.
*   **Data Scientist:** Używana jako modyfikator *binarny/progowy* w Lending Score. Jest przycinana (clipped) przy 1.5x, ponieważ gromadzenie gotówki powyżej tego poziomu daje malejące korzyści dla modelu.
*   **Aktuariusz:** Reprezentuje katastroficzne ryzyko płynności. Nawet zyskowne podmioty upadają bez gotówki. Ta metryka dyktuje "Liquidity Factor", który może obniżyć ocenę końcową nawet o 20 punktów.

### Intensywność Inwestycji (Capex Intensity)
*   **Wzór:** `(Inwestycje / Przychód) * 100`
*   **Analityk Biznesowy:** Stopa reinwestycji. Mierzy, jak agresywnie sektor modernizuje swoją bazę aktywów. Wysoki Capex = Wiara w przyszły popyt.
*   **Data Scientist:** Połowa *Transformation Score*. Jest to proxy dla "Inwestycji w Infrastrukturę/Hardware".
*   **Aktuariusz:** Reprezentuje "Zakład o Przyszłość". Zwiększa ryzyko odpływu gotówki w krótkim terminie, ale zmniejsza ryzyko przestarzałości (obsolescence) w długim terminie.

### Metryka AI ArXiv (Dane Zewnętrzne)
*   **Wzór:** `Liczba publikacji AI zmapowana do kodu PKD`
*   **Analityk Biznesowy:** "Hype Innowacyjny". Mierzy czyste B+R i teoretyczne zainteresowanie AI w sektorze.
*   **Data Scientist:** Druga połowa *Transformation Score*. Proxy dla "Inwestycji w Software/Wiedzę". Ponieważ rozkład jest grubogonowy (większość ma 0, niektórzy 5000+), normalizacja używa szerokiego zakresu (0-5000), aby wyróżnić liderów.
*   **Aktuariusz:** Marker "Ryzyka Transformacji". Wysokie wyniki sugerują zmienność – model biznesowy szybko się zmienia, co wprowadza błąd estymacji w modelach opartych na danych historycznych.

---

## 2. Złożone Algorytmy Punktacji (Prognostyczne)

### A. Stability Score (Kondycja)
**Koncepcja:** Ważony indeks mierzący obecne zdrowie i odporność sektora.

**Wzór (Tryb Prognozy - Metoda Absolutna):**
```python
Stability_Score = (
    (0.40 * Znormalizowana_Zyskowność) + 
    (0.30 * Znormalizowany_Wzrost) + 
    (0.30 * Znormalizowane_Bezpieczeństwo) 
) * 100
```
*Gdzie Bezpieczeństwo = Średnia(Cash_Ratio, Odwrócony_Dług, Odwrócona_Upadłość)*

*   **Analityk Biznesowy:** To jest "Rating Kredytowy". Wynik >65 sugeruje poziom inwestycyjny. <40 sugeruje poważne kłopoty.
*   **Data Scientist:** Kombinacja liniowa nieskorelowanych cech. Mieszamy metryki "Przepływowe" (Wzrost, Zysk) z metrykami "Zasobowymi" (Dług, Gotówka), aby uniknąć przeuczenia na jednym dobrym roku.
*   **Aktuariusz:** Ten wynik to odwrotne proxy Ryzyka Niewypłacalności. Priorytetyzujemy "Bezpieczeństwo" (Dług/Gotówka) albowiem w modelowaniu ryzyka przetrwanie > wzrost.

### B. Transformation Score (Innowacyjność)
**Koncepcja:** Indeks wyprzedzający (forward-looking), mierzący adaptację technologii (Hardware + AI).

**Wzór:**
```python
Transformation_Score = (
    (0.50 * Znormalizowany_Capex) + 
    (0.50 * Znormalizowany_Arxiv)
) * 100
```

*   **Analityk Biznesowy:** "Indeks Modernizacji". Wysoki wynik oznacza, że sektor aktywnie wydaje pieniądze na zmiany. Niski wynik = Stagnacja.
*   **Data Scientist:** Model dwuczynnikowy balansujący wydatki "twarde" (Capex) vs "miękkie" (Badania). Redukuje to stronniczość przeciwko sektorom, które kupują tylko maszyny vs tym, które piszą tylko kod.
*   **Aktuariusz:** Wskaźnik Zmienności. Sektory z wynikiem >80 przechodzą zmiany strukturalne. Historyczne dane o szkodowości dla tych sektorów mogą być nieważne dla przyszłych składek.

---

## 3. "Klejnot Koronny": Lending Opportunity Score
**Koncepcja:** Ostateczna metryka decyzyjna dla Banku. Identyfikuje "Klienta Idealnego".

**Wzór:**
```python
Lending_Score = (
    (0.40 * Prognoza_Transformation_2026) + 
    (0.40 * Obecna_Stabilność) + 
    (0.20 * Czynnik_Płynności)
)
```

### Obliczenie Czynnika Płynności (`Liquidity Factor`)
Ta wewnętrzna zmienna konwertuje surowe metryki płynności/ryzyka na wynik 0-100.

**Przypadek A: Dostępny Cash Ratio (Preferowane)**
$$
\text{Czynnik Płynności} = \min\left(\frac{\text{Cash Ratio}}{1.5}, 1.0\right) \times 100
$$
*   **Logika:** Ustawiamy limit (cap) na pokryciu 1.5x.
    *   Jeśli `Cash_Ratio` = 0.75 -> Wynik = 50.
    *   Jeśli `Cash_Ratio` >= 1.5 -> Wynik = 100.

**Przypadek B: "Fallback" do Wskaźnika Upadłości (Gdy brak danych o gotówce)**
$$
\text{Czynnik Płynności} = \max\left(0, \frac{5 - \text{Wskaźnik Upadłości}}{5}\right) \times 100
$$
*   **Logika:** Liniowa kara za ryzyko upadłości do poziomu 5%.
    *   Jeśli `Bankruptcy_Rate` = 0% -> Wynik = 100.
    *   Jeśli `Bankruptcy_Rate` = 2.5% -> Wynik = 50.
    *   Jeśli `Bankruptcy_Rate` >= 5.0% -> Wynik = 0.

### Interpretacja Ekspercka
*   **Analityk Biznesowy (Sprzedaż):** "Kto potrzebuje pieniędzy I może je oddać?"
    *   *Wysoka Transformacja* = Potrzebuje pieniędzy (Capex/B+R).
    *   *Wysoka Stabilność* = Jest wypłacalny.
    *   *Cel:* Każdy wynik > 70 to "Gorący Lead".
*   **Data Scientist (Modelowanie):** To model zespołowy w czasie (temporal ensemble).
    *   Łączy $t_{current}$ (Stabilność) z $t_{future}$ (Prognoza Transformacji).
    *   Zapobiega to błędom "patrzenia we wsteczne lusterko", typowym dla standardowego scoringu kredytowego.
*   **Aktuariusz (Ryzyko):** To metryka **Zwrotu Skorygowanego o Ryzyko (Risk-Adjusted Return)**.
    *   `Liquidity Factor` działa jak funkcja kary (haircut). Jeśli firma jest niepłynna, ucinamy jej wynik niezależnie od innowacyjności. Logika: "Nie możesz innowować, jeśli zbankrutujesz."

---

## 4. Strategiczna Logika Klasyfikacji (Drzewo Decyzyjne)
**Kontekst:** Wykorzystywane w algorytmach parsowania do kategoryzacji branż w "kubełki" decyzyjne.

### ⚠️ Wysokie Ryzyko (Critical Risk)
*   **Warunek:** `Bankruptcy_Rate > 2.5%`
*   **Aktuariusz mówi:** "Nie ubezpieczać". Bazowy wskaźnik upadłości to zazwyczaj szum statystyczny. Powyżej 2.5% to gnicie systemowe.

### 🌟 Liderzy Przyszłości (Future Leaders)
*   **Warunek:** `Trans_Score_2026 > 60` ORAZ `Stability_Score_2026 > 50`
*   **Data Scientist mówi:** "Maxima Lokalne." Te podmioty optymalizują obie funkcje: Innowację i Bezpieczeństwo. Rzadkie i cenne.

### 🚀 Wschodzące Gwiazdy (Rising Stars)
*   **Warunek:** `Trans_Score_2026 > 60` (ale Stability <= 50)
*   **Analityk Biznesowy mówi:** "Wysoki Wzrost / Wysokie Ryzyko". Typowy profil VC (Venture Capital). Palą gotówkę (Niska Stabilność), by rosnąć (Wysoka Transformacja).

### 🛡️ Bezpieczne Przystanie (Safe Havens)
*   **Warunek:** `Stability_Score_2026 > 65`
*   **Aktuariusz mówi:** "Niska Wariancja". Stabilne przepływy, niski dług. Idealne pod obligacje długoterminowe o niskim ryzyku.

### 💰 Cel Kredytowy (Lending Targets)
*   **Warunek:** `Lending_Score > 70`
*   **Analityk Biznesowy mówi:** "Sweet Spot". Ta lista trafia prosto do Zespołu Sprzedaży.

---

## 5. Ewaluacja Silnika Prognostycznego
**Model:** Regresja Liniowa OLS (Ordinary Least Squares) na `n=6` (2019-2024).

*   **Krytyka Statystyczna:** Regresja liniowa na krótkim szeregu czasowym ($n<10$) jest podatna na przeuczenie (overfitting) i wrażliwa na outliery (np. szok Covid-2020).
*   **Strategia Mitygacji:**
    *   Używamy **Agregowanych Danych Sektorowych** (redukuje wariancję vs dane pojedynczych firm).
    *   Wykluczamy **Wcześniejsze Prognozy** z treningu (trenujemy tylko na danych rzeczywistych).
    *   Dla **ArXiv**, ucinamy dane sprzed 2019 roku jako nieistotny "szum" przed boomem na LLM.
*   **Ocena Ryzyka:** Model zakłada "Ciągłość Momentu" (Momentum Continuity). Nie przewiduje "Czarnych Łabędzi" (regulacje, wojny). Dlatego waga `Stability Score` (40%) działa jak "kotwica" trzymająca wynik przy rzeczywistości.
