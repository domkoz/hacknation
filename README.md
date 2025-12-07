# 🏦 HackNation: Industrial Risk Monitor (Banking Logic Edition)

> **"Nie zgaduj przyszłości – oblicz ją."** (Don't guess the future - calculate it.)

Aplikacja analityczna klasy Enterprise Grade służąca do oceny ryzyka i potencjału branż przemysłowych w Polsce. Integruje twarde dane finansowe (GUS, KRZ) z zaawansowaną analityką AI (Local LLM) i prognozowaniem.

---

## 🚀 Kluczowe Funkcje

### 1. 📊 Stability & Transformation Index (S&T Score)
Unikalny model ratingowy oceniający każdą branży (PKD) w dwóch wymiarach:
*   **Stability Score (Fundament):** Agreguje **zyskowność, dynamikę wzrostu, bezpieczeństwo długu i płynność**. Pozwala zidentyfikować "bezpieczne przystanie".
*   **Innovation Index (Transformacja):** Agreguje **intensywność inwestycyjną (Capex)** oraz **dynamikę adopcji AI (ArXiv Papers)**. Wskazuje liderów przyszłości.
    *   *New:* **Temporal Innovation Data:** Analiza trendów publikacji naukowych rok-do-roku (2019-2025).

### 2. 🧠 Local AI "Credit Committee" (Ollama)
Wbudowany system AI symulujący posiedzenie komitetu kredytowego.
*   **CRO & CSO Debate:** Dyskurs między ryzykiem a strategią.
*   **Werdykt Bankowy:** Konkretna rekomendacja (np. `INCREASE EXPOSURE`).

### 3. 📈 Forecasting Engine 2026
Moduł predykcyjny wykorzystujący regresję liniową oraz filtry "AI Hype" do prognozowania:
*   Wyników finansowych (Przychody, Marża).
*   Pozycji S&T w przyszłości (Dynamiczne ścieżki na wykresie).

### 4. 🔍 Deep Analytics & Drill-Down
*   **Interaktywny Dashboard:** Kliknij w branżę, aby zobaczyć szczegóły.
*   **Szczegółowe Wskaźniki:** Analiza upadłości, płynności i zadłużenia na poziomie sub-sektorów.

---

## 🛠️ Instalacja i Uruchomienie

### Wymagania
*   Python 3.9+
*   [Ollama](https://ollama.com/) (dla modułu AI)

### Krok 1: Instalacja Zależności
```bash
pip install -r requirements.txt
```

### Krok 2: Konfiguracja Lokalnego AI (Ollama)
Aplikacja korzysta z modelu `gemma2` (Google Gemma 2 9B Instruct), który zapewnia wysoką jakość analizy w języku polskim.

```bash
# Zainstaluj Ollama (macOS)
brew install ollama
brew services start ollama

# Pobierz model
ollama pull gemma2
```

### Krok 3: Uruchomienie Aplikacji
```bash
streamlit run app/main.py
```
> **Tip:** W panelu bocznym ("Konfiguracja Modelu S&T") możesz dostosować "Kill Switch" (próg upadłości - domyślnie **4.5%**) oraz wagi modelu.

---

## 📂 Źródła Danych (Data Pipeline)
System przetwarza i integruje dane z następujących źródeł:
1.  **GUS (Spon. 2018-2024):** Przychody, zyski, aktywa.
2.  **KRZ (Rejestr Zadłużonych):** Dane o upadłościach i restrukturyzacjach.
3.  **ArXiv API:** Liczba publikacji naukowych (AI/ML) powiązanych z branżą.
4.  **Forecasting:** Dane syntetyczne/wyliczone na podstawie trendów.

---

## ⚙️ Metodologia (Skrót)

### Stability Score (Wagi)
*   **40% Profitability:** (Marża Netto + % Firm Rentownych)
*   **30% Growth:** (Dynamika Przych. YoY)
*   **15% Debt Security:** (Debt to Revenue)
*   **15% Liquidity:** (Cash Ratio)

### Innovation Index
*   **50% Capex Intensity:** (Inwestycje / Przychody)
*   **50% Scientific Output:** (Znormalizowana liczba prac ArXiv)

---

*HackNation 2024 Project.*
