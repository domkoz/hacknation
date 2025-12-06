# S&T Index (Stability & Transformation) - Hackathon Edition

## 🎯 Cel Projektu
Analiza branż w dwóch wymiarach:
1.  **Fundament (Stability):** Kondycja finansowa, dług, płynność.
2.  **Potencjał (Transformation):** Trendy Google, Sentyment AI, Innowacyjność.

## 🚀 Jak uruchomić?

1.  Zainstaluj zależności (jeśli jeszcze tego nie zrobiłeś):
    ```bash
    pip install -r requirements.txt
    ```

2.  Uruchom aplikację:
    ```bash
    streamlit run app/main.py
    ```

## 📂 Struktura Danych
*   `data/raw_gus_data.csv`: Dane finansowe (Mock)
*   `data/processsed_index.csv`: Przeliczone wskaźniki (S&T Score)
*   `app/assets/ai_debates.json`: Wygenerowane debaty AI Boardroom

## 🤖 AI Boardroom
Unikalna funkcja symulująca debatę dwóch person:
*   **CRO (Chief Risk Officer):** Skupiony na ryzyku i liczbach.
*   **CSO (Chief Strategy Officer):** Skupiony na wzroście i wizji.

## ⚠️ Logika "Kill Switch"
Branże z wysokim ryzykiem upadłości są oznaczone jako **CRITICAL** (czerwony kolor) i mają rekomendację "REJECT" niezależnie od potencjału.
