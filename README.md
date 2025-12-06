# 🏦 HackNation: Industrial Risk Monitor (Banking Logic Edition)

> **"Nie zgaduj przyszłości – oblicz ją."** (Don't guess the future - calculate it.)

Aplikacja analityczna klasy Enterprise Grade służąca do oceny ryzyka i potencjału branż przemysłowych w Polsce. Integruje twarde dane finansowe (GUS, KRZ) z zaawansowaną analityką AI (Local LLM) i prognozowaniem.

---

## 🚀 Kluczowe Funkcje

### 1. 📊 Stability & Transformation Index (S&T Score)
Unikalny model ratingowy oceniający każdą branżę (PKD) w dwóch wymiarach:
*   **Stability Score (Fundament):** Agreguje **zyskowność, dynamikę wzrostu, bezpieczeństwo długu i płynność**. Pozwala zidentyfikować "bezpieczne przystanie".
*   **Innovation Index (Transformacja):** Agreguje **intensywność inwestycyjną (Capex)** oraz **potencjał naukowy (ArXiv AI Papers)**. Wskazuje liderów przyszłości.

### 2. 🧠 Local AI "Credit Committee" (Ollama)
Wbudowany system AI symulujący posiedzenie komitetu kredytowego. Działa **lokalnie i offline** (bez limitów API).
*   **CRO (Chief Risk Officer):** Analizuje ryzyko upadłości i zadłużenie.
*   **CSO (Chief Strategy Officer):** Ocenia potencjał wzrostu i innowacji.
*   **Werdykt Bankowy:** Konkretna rekomendacja: `INCREASE EXPOSURE`, `MAINTAIN`, `MONITOR`, lub `DECREASE EXPOSURE`.

### 3. 📈 Forecasting Engine 2026
Moduł predykcyjny wykorzystujący regresję liniową na danych 2018-2024 do prognozowania przychodów na lata **2025-2026**.

### 4. 💸 Lending Opportunity Score
Dedykowany wskaźnik dla bankowości korporacyjnej. Identyfikuje branże z "Sweet Spot":
*   Wysoki popyt na kapitał (Inwestycje).
*   Wysoka stabilność finansowa.
*   Bezpieczna płynność.

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
Aplikacja korzysta z modelu `gemma:2b` (Google), który jest lekki i szybki.
```bash
# Zainstaluj Ollama (macOS)
brew install ollama
brew services start ollama

# Pobierz model
ollama pull gemma:2b
```

### Krok 3: Uruchomienie Aplikacji
```bash
streamlit run app/main.py
```

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
