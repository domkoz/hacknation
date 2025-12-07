# Instrukcja Instalacji i Uruchomienia (Zero-to-Hero)

Ten dokument przeprowadzi Cię krok po kroku przez instalację aplikacji **HackNation S&T Index** na czystej maszynie (macOS/Linux/Windows).

## 1. Wymagania Wstępne
Upewnij się, że masz zainstalowane:
-   **Python 3.9+** (https://www.python.org/downloads/)
-   **Ollama** (do działania lokalnego AI) (https://ollama.com/)
-   **Git** (do pobrania repozytorium)

## 2. Pobranie Projektu
Otwórz terminal i wykonaj:
```bash
git clone <URL_REPOZYTORIUM>
cd hacknation
```

## 3. Konfiguracja Środowiska (Virtual Environment)
Zalecamy użycie wirtualnego środowiska, aby nie zaśmiecać systemu.

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 4. Instalacja Zależności
Mając aktywne środowisko (zobaczysz `(venv)` w terminalu), uruchom:
```bash
pip install -r requirements.txt
```

## 5. Konfiguracja Modelu AI (Ollama)
Aplikacja korzysta z lokalnego modelu językowego **Gemma 2**. Jest darmowy, prywatny i działa offline.

1.  Zainstaluj Ollama (jesli nie masz).
2.  W terminalu pobierz model (to może chwilę potrwać - ok. 5GB):
```bash
ollama pull gemma2
```
3.  Upewnij się, że Ollama działa w tle:
```bash
ollama serve
```

## 6. (Opcjonalnie) Google Gemini Key
Aplikacja może korzystać z modelu Gemini Pro (w chmurze) zamiast Ollama. Jeśli wolisz Gemini:
1.  Skorzystaj z `.env.example`:
```bash
cp .env.example .env
```
2.  Edytuj plik `.env` i wklej swój klucz API:
```text
GEMINI_API_KEY=twoj_klucz_tutaj
```
3.  Aplikacja automatycznie wykryje klucz. Aby wymusić Oslamę mimo klucza, zmień `USE_OLLAMA=False` w `app/main.py`.

## 7. Uruchomienie Aplikacji
```bash
streamlit run app/main.py
```
Aplikacja otworzy się automatycznie w przeglądarce pod adresem `http://localhost:8501`.

## 🆘 Rozwiązywanie Problemów

### "ModuleNotFoundError: No module named..."
Upewnij się, że aktywowałeś środowisko wirtualne (`source venv/bin/activate`) i zainstalowałeś zależności (`pip install -r requirements.txt`).

### "Ollama connection refused"
Upewnij się, że Ollama działa (`ollama serve`).

### Wykresy się nie wyświetlają
Sprawdź czy nie masz włączonego Dark Mode w systemie operacyjnym, czasem Streamlit/Plotly może mieć problem z doborem kontrastu (choć aplikacja ma wymuszony motyw).
