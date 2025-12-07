# Metodologia HackNation S&T Index

## 1. Wprowadzenie
Stability & Transformation Index (S&T) to autorski model scoringowy służący do oceny kondycji i potencjału branż przemysłowych. Model opiera się na twardych danych historycznych (GUS, KRZ) oraz wskaźnikach wyprzedzających (ArXiv, Capex).

---

## 2. Stability Score (Oś Y)
Ocenia bieżącą kondycję finansową i odporność na wstrząsy. Składa się z 3 filarów ważonych dynamicznie przez użytkownika (domyślnie: 40/30/30).

### Składowe:
1.  **Zyskowność (Profitability):** Średnia z dwóch znormalizowanych wskaźników:
    *   *Marża Netto (Net Profit Margin):* (Zysk Netto / Przychody). Norma: -5% do +20%.
    *   *Odsetek Firm Rentownych:* (% firm z wynikiem >= 0). Norma: 40% do 100%.
2.  **Wzrost (Growth):**
    *   *Dynamika Przychodów r/r:* (Przychody T / Przychody T-1). Norma: -10% do +20%.
3.  **Bezpieczeństwo (Safety):** Średnia z trzech wskaźników:
    *   *Płynność (Cash Ratio):* (Gotówka / Zobowiązania Krótkoterminowe). Norma: 0.0 do 1.2.
    *   *Zadłużenie (Debt Leverage):* (Zobowiązania Ogółem / Przychody). Odwrócone. Norma: 0.0 do 4.0.
    *   *Ryzyko Upadłości (Bankruptcy Risk):* (% Upadłości w branży). Odwrócone. Norma: 0% do 4%.

---

## 3. Transformation Score (Oś X)
Ocenia potencjał przyszłego rozwoju i zdolność do adaptacji technologii. Składa się z 2 filarów (50/50).

### Składowe:
1.  **Intensywność Inwestycyjna (Capex Intensity):**
    *   (Nakłady Inwestycyjne / Przychody). Mierzy, jak dużą część przychodów branża reinwestuje.
    *   Norma: 0% do 15%.
2.  **Innowacyjność AI (ArXiv Papers):**
    *   Liczba publikacji naukowych na ArXiv.org zawierających słowa kluczowe "AI" + [Nazwa Branży].
    *   Dane są **temporalne** (zmienne w czasie) dla lat 2019-2026 (prognoza).
    *   Norma: 0 do 5000 publikacji.

---

## 4. Forecasting Engine (Prognozowanie)
System generuje prognozy na lata 2025-2026.

### Metoda:
*   **Regresja Liniowa:** Stosowana dla większości wskaźników finansowych (Przychody, Marża, Dług).
*   **AI Hype Filter:** Dla wskaźnika `Arxiv_Papers` model uczy się **wyłącznie na danych od 2019 roku**. Pozwala to uchwycić wykładniczy trend adopcji GenAI i ignoruje "płaskie" lata wcześniejsze.
*   **S&T Recalculation:** Po wyliczeniu prognoz dla składowych (np. przyszła Marża, przyszłe ArXiv), model przelicza S&T Score dla lat przyszłych, używając tych samych wag co dla danych historycznych.

---

## 5. Źródła Danych
*   **GUS (Główny Urząd Statystyczny):** Dane finansowe przedsiębiorstw niefinansowych (roczne).
*   **KRZ (Krajowy Rejestr Zadłużonych):** Postępowania upadłościowe i restrukturyzacyjne.
*   **ArXiv API:** Metadane publikacji naukowych.
