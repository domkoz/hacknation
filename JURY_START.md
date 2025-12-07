# 🏆 HackNation: Instrukcja dla Jury

Witajcie! Ten dashboard analityczny pomoże Wam ocenić potencjał branż przemysłowych w czasie rzeczywistym.

> **Wersja Demo:** Aplikacja działa w trybie "View Only" z załadowanymi przykładowymi danymi i symulacjami AI. Nie wymaga instalacji modeli językowych.

## Szybki Start (3 minuty)

### 1. Pobierz Repozytorium
Otwórz terminal (lub Command Prompt/PowerShell) i wpisz:
```bash
git clone <LINK_DO_REPOZYTORIUM>
cd hacknation
```

### 2. Zainstaluj Biblioteki (Wymagany Python 3.9+)
Najlepiej w wirtualnym środowisku (opcjonalne, ale zalecane):
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Następnie zainstaluj wymagane paczki:
```bash
pip install -r requirements.txt
```

### 3. Uruchom Dashboard
```bash
streamlit run app/main.py
```

Twoja domyślna przeglądarka otworzy nową kartę z aplikacją (zazwyczaj pod adresem `http://localhost:8501`).

---

## 🔍 Co Sprawdzić (Demo Walkthrough)

1.  **Sektory Przyszłości (Bąbelki):**
    *   W panelu bocznym "Wybierz Poziom" ustaw **"Sekcje (L1)"**.
    *   Znajdź **"Sektor J"** (Software/IT) w prawej górnej ćwiartce wykresu (Wysokie Stability, Wysokie Transformation).
    *   Kliknij w bąbelek, aby zobaczyć **debatę AI** (CRO vs CSO) na temat przyszłości tej branży. (Symulacja została wygenerowana wcześniej).

2.  **Podróż w Czasie (Suwaki):**
    *   W panelu bocznym ("Konfiguracja Modelu S&T") przesuń suwaki wag (np. zwiększ "Wagę Wzrostu").
    *   Obserwuj jak bąbelki zmieniają swoje położenie w czasie rzeczywistym, reagując na Twoją strategię.

3.  **Szczegóły Innowacji (ArXiv & Capex):**
    *   Przejdź do zakładki **"Strategia (S&T)"** pod wykresem.
    *   Zobaczysz linię trendu "Transformation Score" wystrzeliwującą w górę po 2023 roku (efekt "AI Hype").

---

*Powodzenia!* 🚀
