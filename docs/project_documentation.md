# 📘 Dokumentacja Projektu: HackNation Industrial Monitor
**Wersja:** 1.0 (Final Hackathon Release)
**Data:** 06.12.2025

---

## 🏗️ Architektura Systemu

System opiera się na architekturze "Local-First", zapewniając pełną prywatność danych i działanie offline.

### Komponenty:
1.  **Frontend & Dashboard:** `Streamlit` (Python)
    *   Interaktywne wykresy: `Plotly` (Bubble Chart, Time Series, Drill-Down).
    *   Dynamiczne filtrowanie: Sektory, Przychody, Lata (Time Travel).
2.  **AI Engine:** `Ollama` (Local LLM)
    *   **Model:** `gemma2` (9B Parameter Model).
    *   **Zadanie:** Symulacja Komitetu Kredytowego (Debata CRO vs CSO).
3.  **Data Processing:** `Pandas`
    *   ETL Pipeline: Czyszczenie danych GUS, łączenie z KRZ, obliczanie wskaźników.
4.  **Forecasting Engine:** `Scikit-Learn / Numpy`
    *   Regresja liniowa dla predykcji przychodów (2025-2026).

---

## 📊 Źródła Danych (Data Pipeline)

System integruje 4 niezależne strumienie danych:

1.  **GUS (Główny Urząd Statystyczny):**
    *   Dane finansowe podmiotów 50+ (F-01/I-01).
    *   Zakres: Przychody, Koszty, Zysk Netto, Aktywa, Zobowiązania.
    *   Lata: 2018-2024.
2.  **KRZ (Krajowy Rejestr Zadłużonych):**
    *   Liczba postępowań upadłościowych i restrukturyzacyjnych w danym PKD.
    *   Wskaźnik: `Bankruptcy Rate` (Liczba upadłości / Liczba aktywnych firm).
3.  **ArXiv Open API:**
    *   Liczba publikacji naukowych powiązanych z frazami "AI", "Machine Learning", "Optimization" w kontekście danej branży.
    *   Wskaźnik: `Scientific Readiness Score`.


---

## 🧮 Metodologia i Wzory (Core Metrics)
Szczegółowe wzory matematyczne znajdują się w dokumentach: `docs/metrics_compendium_pl.md` oraz `docs/metrics_compendium.md`.

### 1. Stability Score (Kondycja Finansowa)
Ocenia bezpieczeństwo kredytowe branży. Korzysta z modelu wagowego (domyślnie 4:3:3).
*   **Komponenty:** Zyskowność (Marża + % Rentownych), Wzrost (YoY), Bezpieczeństwo (Dług i Płynność).
*   **Wersja Prognozy (2026):** Obliczana metodą **Absolute Scoring** (sztywne progi), aby umożliwić porównanie w czasie.

### 2. Transformation Score (f.k.a. Innovation Index)
Ocenia zdolność branży do adaptacji w przyszłości.
**Formuła:**
`Transformation = 50% Capex Intensity + 50% ArXiv AI Papers`
*   **Capex:** Inwestycje w środki trwałe.
*   **ArXiv:** Hype innowacyjny (Software/Wiedza).

### 3. Lending Opportunity Score (Dla Banku)
Identyfikuje idealnych klientów: potrzebujących kapitału (Inwestycje), ale bezpiecznych.
**Formuła:**
$$ Lending = 0.4 \times FutureTransformation(2026) + 0.4 \times CurrentStability + 0.2 \times LiquidityFactor $$

*   **Future Transformation:** Potencjał wzrostu za 2 lata.
*   **Current Stability:** Bieżąca wypłacalność.
*   **Liquidity Factor:** Cash Ratio (z limitem 1.5x) lub Odwrotność Upadłości.

---

## 🏆 Ranking & Klasyfikacja (Nowość v2.0)
System automatycznie dzieli branże na segmenty decyzyjne w zakładce "Ranking & Eksport":

1.  **⚠️ Wysokie Ryzyko (Critical):** `Bankruptcy Rate > 2.5%`.
2.  **🌟 Liderzy Przyszłości:** Wysoka Transformacja 2026 (>60) ORAZ Wysoka Stabilność 2026 (>50).
3.  **🚀 Wschodzące Gwiazdy:** Wysoka Transformacja (>60), ale niższa Stabilność.
4.  **🛡️ Bezpieczne Przystanie:** Wysoka Stabilność (>65).
5.  **💰 Cel Kredytowy:** `Lending Score > 70`.

---

## 🧠 AI Boardroom (Logika Modelu Językowego)
System nie tylko "wyświetla liczby", ale je "rozumie". Skrypt generuje prompt zawierający kontekst finansowy danej branży i uruchamia dwie Persony symulowane przez model **Ollama (gemma2)**:

### Persona 1: CRO (Chief Risk Officer)
*   **Cel:** Znaleźć ryzyko (Dług, Marża).
*   **Styl:** Sceptyczny, ostrzegawczy.

### Persona 2: CSO (Chief Strategy Officer)
*   **Cel:** Znaleźć szansę (Capex, AI).
*   **Styl:** Wizjonerski.

Werdykt debaty (`BUY`/`REJECT`) trafia na Dashboard.

---

## 🔮 Forecasting Engine 2026
Moduł predykcyjny oblicza linię trendu dla 8 kluczowych metryk (Przychody, Marża, Dług, etc.).
*   **Technologia:** `numpy.polyfit` (Regresja Liniowa OLS).
*   **Horyzont:** 2 lata (2025-2026).
*   **AI Hype Filter:** Dla danych ArXiv, model bierze pod uwagę tylko lata po 2019 r., ignorując wcześniejszy "szum".
*   **Zastosowanie:** Prognozowane metryki są używane do obliczenia **S&T Score 2026**.

---

## ⚠️ Kill Switch (Bezpiecznik)
System posiada wbudowany mechanizm bezpieczeństwa.
*   **Domyślny próg:** **4.5%** (Liczba bankructw / Liczbę firm).
*   **Efekt:** Jeśli przekroczony -> Status `CRITICAL`.
*   Nadpisuje wszystkie rekomendacje pozytywne ("Reject").


