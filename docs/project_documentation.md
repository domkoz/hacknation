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
4.  **Google Trends (Proxy):**
    *   Zainteresowanie społeczne daną branżą (Sentyment).

---

## 🧮 Metodologia i Wzory (Core Metrics)

Serce systemu. Każda branża otrzymuje zestaw ocen punktowych (0-100 lub znormalizowanych 0-1).

### 1. Stability Score (Kondycja Finansowa)
Ocenia bezpieczeństwo kredytowe branży.
**Formuła:**
$$ Stability = 0.4 \times P + 0.3 \times G + 0.15 \times D + 0.15 \times L $$

*   **P (Profitability):** Znormalizowana Marża Zysku Netto + % Firm Rentownych.
*   **G (Growth):** Dynamika Przychodów r/r (Year-over-Year).
*   **D (Debt Security):** Odwrotność wskaźnika Dług/Przychody (Im mniej długu, tym lepiej).
*   **L (Liquidity):** Wskaźnik Płynności (Cash Ratio).

### 2. Innovation Index (Potencjał Transformacji)
Ocenia zdolność branży do adaptacji w przyszłości.
**Formuła:**
$$ Transformation = 0.5 \times CI + 0.5 \times SO $$

*   **CI (Capex Intensity):** Nakłady Inwestycyjne (Capex) / Przychody Ogółem.
*   **SO (Scientific Output):** Znormalizowana liczba publikacji ArXiv.

### 3. Lending Opportunity Score (Dla Banku)
Identyfikuje idealnych klientów: potrzebujących kapitału (Inwestycje), ale bezpiecznych.
**Formuła:**
$$ Lending = 0.4 \times Capex + 0.4 \times Stability + 0.2 \times Liquidity $$

---

## 🧠 AI Boardroom (Logika Modelu Językowego)

System nie tylko "wyświetla liczby", ale je "rozumie". Skrypt generuje prompt zawierający kontekst finansowy danej branży i uruchamia dwie Persony:

### Persona 1: CRO (Chief Risk Officer)
*   **Cel:** Znaleźć ryzyko.
*   **Kluczowe metryki:** Debt Ratio, Bankruptcy Rate, Marża.
*   **Styl:** Sceptyczny, rzeczowy, ostrzegawczy.

### Persona 2: CSO (Chief Strategy Officer)
*   **Cel:** Znaleźć szansę.
*   **Kluczowe metryki:** Capex, ArXiv Papers, Forecast Growth.
*   **Styl:** Wizjonerski, nastawiony na wzrost.

### Final Verdict & Credit Decision
Model na podstawie debaty wydaje werdykt:
*   **Decyzja:** `BUY`, `HOLD`, `REJECT`.
*   **Rekomendacja Bankowa:** `INCREASE_EXPOSURE` (Zwiększ zaangażowanie), `MAINTAIN` (Utrzymaj), `MONITOR` (Obserwuj), `DECREASE_EXPOSURE` (Redukuj).

---

## 🔮 Forecasting Engine 2026

Moduł predykcyjny oblicza linię trendu dla przychodów.
*   Jeśli trend historyczny (2019-2024) jest stabilny ($R^2 > 0.6$), system projektuje wzrost na lata 2025-2026.
*   Prognoza jest wizualizowana jako **linia przerywana** na wykresach Drill-Down.
*   Jest również "inputem" dla modelu AI (CSO powołuje się na prognozy).

---

## ⚠️ Kill Switch (Bezpiecznik)

System posiada wbudowany mechanizm bezpieczeństwa.
Jeśli:
1.  `Bankruptcy Rate` > 2.5% (Wysokie ryzyko systemowe)
2.  `Cash Ratio` < 0.1 (Brak płynności)

Wtedy:
*   Branża otrzymuje status **CRITICAL**.
*   Kolor na wykresie zmienia się na Czerwony.
*   Rekomendacja AI automatycznie nadpisana lub silnie sugerująca "REJECT".

---

*Dokumentacja wygenerowana automatycznie przez Antigravity Agent.*
