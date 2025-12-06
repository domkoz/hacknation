# **`MASTER PROJECT PLAN: S&T Index (Stability & Transformation)`**

**`Wersja:`** `3.0 (Execution Ready) Autor: Zespół Jednoosobowy (HackNation 2025) Status: Dokument Błyskawicznego Wdrożenia (Hackathon Mode)`

---

## **`1. KONTEKST BIZNESOWY I CELE`**

### **`1.1. Diagnoza Problemu (The "Why")`**

`Bank (PKO BP) posiada ogromną ilość danych historycznych, które świetnie mówią, co było (sprawozdania finansowe), ale słabo radzą sobie z przewidywaniem tego, co będzie.`

* **`Problem:`** `Tradycyjne modele ryzyka są reaktywne. Nie widzą "czarnych łabędzi" ani nagłych trendów konsumenckich, dopóki nie pojawią się w bilansie za rok.`  
* **`Wyzwanie:`** `Opracowanie indeksu, który łączy "twardą" ocenę kondycji z "miękką" oceną potencjału na 12-36 miesięcy.`

### **`1.2. Rozwiązanie: S&T Index`**

`Hybrydowy system oceny branż (oparty na kodach PKD/NACE), który dla każdego sektora generuje:`

1. **`Pozycję Obecną (Current State):`** `Gdzie branża jest dzisiaj (Finanse).`  
2. **`Wektor Przyszłości (Future Vector):`** `Gdzie branża będzie za rok (Trendy + AI).`  
3. **`Narrację Decyzyjną (AI Boardroom):`** `Zrozumiałe uzasadnienie wyniku.`

### **`1.3. Odbiorcy (Target Users)`**

* **`Analitycy Ryzyka:`** `Szukają ostrzeżeń przed upadłościami ("Kill Switch").`  
* **`Menedżerowie Sprzedaży/Strategii:`** `Szukają sektorów rosnących, by sprzedawać kredyty.`

---

## **`2. METODOLOGIA I MODEL MATEMATYCZNY (S&T ENGINE)`**

`To jest serce Twojego projektu – sekcja punktowana za "Metodologię" (25%).`

### **`2.1. Definicja Branży`**

`Analiza na poziomie Działów PKD (2 cyfry) lub Grup (3 cyfry).`

* *`Przykład:`* `Dział 62 (Oprogramowanie), Dział 41 (Roboty budowlane).`

### **`2.2. Algorytm Oceny (Scoring Model)`**

#### **`OŚ X: STABILITY SCORE (Waga: 50%) – "Fundament"`**

`Mierzy bezpieczeństwo finansowe branży. Dane z GUS/Pont Info/Sprawozdań. Wzór: Stability = (0.4 * Rentowność) + (0.3 * Płynność) + (0.3 * Dynamika_YoY)`

| `Zmienna` | `Opis` | `Źródło` |
| :---- | :---- | :---- |
| `Rentowność (Profitability)` | `Wynik netto / Przychody ogółem.` | `GUS BDL` |
| `Płynność (Liquidity)` | `Zdolność do spłaty (Aktywa obrotowe / Zobowiązania krótkoterminowe).` | `GUS BDL` |
| `Dynamika YoY` | `Zmiana przychodów rok do roku (np. 2023 vs 2024).` | `GUS` |
| `Korekta Energetyczna` | `Mnożnik: Jeśli branża jest energochłonna (np. Hutnictwo), wynik mnożymy przez 0.85 (kara za ryzyko cen energii).` | `Tabela statyczna (Mock)` |

`Eksportuj do Arkuszy`

#### **`OŚ Y: TRANSFORMATION SCORE (Waga: 50%) – "Potencjał"`**

`Mierzy przyszłość i sentyment rynkowy. Dane alternatywne. Wzór: Transformation = (0.6 * Google_Slope) + (0.4 * AI_Sentiment)`

| `Zmienna` | `Opis` | `Źródło` |
| :---- | :---- | :---- |
| `Trend Google (Slope)` | `Nachylenie linii trendu wyszukiwań dla słów kluczowych branży (ostatnie 12 msc).` | `Pytrends / Google Trends` |
| `AI Sentiment` | `Ocena (0-100) generowana przez LLM na podstawie nagłówków newsowych (symulowana).` | `LLM / News API` |

`Eksportuj do Arkuszy`

### **`2.3. Wektor Predykcji (Time Travel)`**

`Na wykresie każdy punkt ma "cień" lub strzałkę.`

* **`Punkt A (Teraz):`** `(Stability_Current, Transformation_Current)`  
* **`Punkt B (Prognoza +12msc):`** `Przesuwamy punkt po osiach:`  
  * `Jeśli Trend Google jest silnie rosnący -> Oś X (Przychody) powinna wzrosnąć w przyszłości.`  
  * `Wektor wizualizuje kierunek zmian (Wzrost/Stagnacja/Recesja).`

### **`2.4. Flagi Specjalne (Logika Biznesowa)`**

1. **`KILL SWITCH (Bezpiecznik):`**  
   * `Jeśli Zadłużenie > X LUB Wskaźnik Upadłości > Y% -> Branża otrzymuje status CRITICAL.`  
   * *`Efekt w UI:`* `Bąbelek pulsuje na czerwono, niezależnie od wyniku Stability/Transformation.`  
2. **`HIDDEN GEM (Ukryty Diament):`**  
   * `Jeśli Stability > 60 ORAZ Transformation > 80 -> Status OPPORTUNITY.`  
   * *`Efekt w UI:`* `Bąbelek oznaczony diamentem/gwiazdką.`

---

## **`3. ARCHITEKTURA "AI BOARDROOM" (WARSTWA ORYGINALNOŚCI)`**

`To jest Twój "wyróżnik" punktowany za Pomysł i Uzasadnienie (15% + 20%).`

`Zamiast generować jeden tekst, system symuluje debatę dwóch agentów AI.`

### **`3.1. Persony Agentów (Role-Playing)`**

`Skrypt generujący (Python + API LLM) musi używać precyzyjnych System Prompts:`

**`AGENT 1: CRO (Chief Risk Officer) - "Pani Krystyna"`**

* **`Charakter:`** `Sceptyczna, konserwatywna, cytuje regulacje KNF.`  
* **`Fokus:`** `Dług, koszty stałe, ryzyko upadłości, szkodowość branży.`  
* **`Prompt Keyword:`** `"Act as a conservative bank Risk Officer. Focus on debt ratios, bankruptcy rates, and economic downturns. Be critical."`

**`AGENT 2: CSO (Chief Strategy Officer) - "Pan Mateusz"`**

* **`Charakter:`** `Entuzjasta technologii, patrzy na USA/Azję, używa buzzwordów ("Disruption", "Scalability").`  
* **`Fokus:`** `Google Trends, wzrosty, nowe nisze rynkowe.`  
* **`Prompt Keyword:`** `"Act as a visionary Market Strategist. Focus on growth potential, social trends, and future revenue opportunities. Be optimistic."`

### **`3.2. Techniczny Workflow AI (Pre-caching)`**

`Aby uniknąć awarii podczas demo, narracje generujemy przed prezentacją.`

1. **`Input:`** `Wyniki liczbowe dla top 10-15 branż (CSV).`  
2. **`Processing:`** `Pętla w Pythonie wysyła dane do LLM z prośbą o wygenerowanie dialogu.`  
3. **`Output:`** `Zapis do pliku assets/ai_debates.json w strukturze:`

*`{`*

  *`"PKD_62": {`*

    *`"CRO_Opinion": "Branża przesycona, rosnące koszty pracy...",`*

    *`"CSO_Opinion": "Popyt na AI rośnie wykładniczo, to dopiero początek...",`*

    *`"Final_Verdict": "BUY - Mimo kosztów, potencjał jest ogromny."`*

  *`}`*

*`}`*

*`4. Frontend: Aplikacja tylko odczytuje ten plik. Zero ryzyka błędu API na żywo.`*

---

## **4\. IMPLEMENTACJA TECHNICZNA (STACK)**

### **4.1.** 

Struktura Projektu (Repozytorium) 

/project\_root

│

├── /data

│   ├── raw\_gus\_data.csv       \# Surowe dane finansowe

│   ├── mapping\_pkd.csv        \# Nazwy branż i kody

│   └── manual\_risk\_factors.csv \# Tabela z ryzykiem ESG/Energii

│

├── /scripts

│   ├── 01\_data\_cleaner.py     \# ETL: CSV \-\> Pandas DataFrame

│   ├── 02\_calc\_index.py       \# Matematyka: Obliczanie S\&T Score

│   └── 03\_ai\_generator.py     \# Generowanie debat (run once)

│

├── /app

│   ├── main.py                \# Aplikacja Streamlit

│   └── assets/                \# CSS, logo, JSON z debatami

│

├── requirements.txt

└── README.md

### **4.2. Kluczowe Biblioteki**

* `pandas`: Obróbka danych.  
* `streamlit`: Interfejs użytkownika.  
* `plotly`: Interaktywny wykres bąbelkowy (scatter plot).  
* `pytrends`: Pobieranie danych z Google Trends (jeśli API pozwoli, inaczej CSV).

## **5\. INTERFEJS UŻYTKOWNIKA (DASHBOARD UX)**

### **Ekran Główny**

* **Nagłówek:** "S\&T Index Boardroom – PKO BP Hackathon Edition".  
* **Wykres Centralny (Bubble Chart):**  
  * **Oś X:** Kondycja Finansowa (0-100).  
  * **Oś Y:** Potencjał Transformacji (0-100).  
  * **Rozmiar Bąbla:** Wielkość branży (Przychody).  
  * **Kolor:** Poziom Ryzyka (Czerwony/Żółty/Zielony).  
* **Filtry:** Wybór sektora (Usługi, Produkcja, Handel).

### **Panel Boczny (Detail View)**

Po kliknięciu w bąbelek:

1. **Nazwa Branży \+ Kod PKD.**  
2. **Wskaźniki:** Duże liczby (np. "Rentowność: 12%").  
3. **Sekcja "AI Boardroom":**  
   * Zdjęcie/Awatar "Pani Krystyny" \+ jej cytat.  
   * Zdjęcie/Awatar "Pana Mateusza" \+ jego cytat.  
   * **Werdykt:** "Rekomendacja: ZWIĘKSZYĆ FINANSOWANIE".

---

## **6\. HARMONOGRAM PRACY (SPRINT PLAN)**

### **Faza 1: Przygotowanie Danych (0:00 \- 2:00)**

1. Stworzenie pliku CSV z listą 15-20 reprezentatywnych branż (różne sektory: Budownictwo, IT, Gastronomia, Transport).  
2. Ręczne lub pół-automatyczne uzupełnienie danych finansowych (z GUS lub "zmockowanie" wiarygodnych danych, jeśli pobieranie z GUS będzie trudne).  
3. Pobranie danych Google Trends (CSV) dla tych 20 branż.

### **Faza 2: Silnik Analityczny (2:00 \- 4:00)**

1. Napisanie skryptu scalającego dane.  
2. Implementacja wzoru na `Stability Score` i `Transformation Score`.  
3. Zastosowanie logiki "Kill Switch" (oznaczenie branż zagrożonych).

### **Faza 3: Generowanie AI (4:00 \- 6:00)**

1. Setup API (OpenAI/Gemini).  
2. Uruchomienie skryptu generującego debaty dla wybranych 20 branż.  
3. Zapisanie wyników do JSON.

### **Faza 4: Budowa Aplikacji (6:00 \- 9:00)**

1. Postawienie Streamlit.  
2. Wpięcie wykresu Plotly.  
3. Ostylowanie panelu bocznego (CSS, ładne fonty).  
4. Implementacja "wektorów/strzałek" na wykresie.

### **Faza 5: Finalizacja (9:00 \- Koniec)**

1. Przygotowanie Prezentacji PDF (max 10 slajdów).  
2. Nagranie 3-minutowego demo (opcjonalnie, ale warto).  
3. Sprawdzenie repozytorium (czy jest `requirements.txt`).  
4. .

---

## **7\. CZEKLISTA DOSTARCZENIA (DELIVERABLES)**

Zgodnie z regulaminem i wymaganiami wyzwania:

* \[ \] **Repozytorium Kodu:** Czysty kod, Python.  
* \[ \] **Plik CSV/XLSX:** Gotowy indeks ze wskaźnikami dla analizowanych branż.  
* \[ \] **Prezentacja PDF:**  
  * Slajd 1: Problem i Rozwiązanie.  
  * Slajd 2: Metodologia (Wzory S\&T).  
  * Slajd 3: AI Boardroom (Persony).  
  * Slajd 4: Prezentacja Dashboardu (Screenshot).  
  * Slajd 5: Wnioski (Ranking branż: Top/Bottom).  
* \[ \] **Uzasadnienie Metodologii:** W prezentacji musi być jasno opisane, dlaczego wybrałeś takie wagi.

## **8\. STRATEGIA "NA PUNKTY" (SCORING HACKS)**

1. **Związek z wyzwaniem (20%):** Używaj słownictwa bankowego ("Portfel kredytowy", "Ekspozycja na ryzyko", "PKD").  
2. **Oryginalność (15%):** AI Boardroom to Twój klucz. Podkreślaj to w prezentacji.  
3. **Kompletność (20%):** Dashboard musi działać. Lepiej mieć 10 branż i działający interfejs niż 1000 branż i błędy w kodzie.  
4. **Ocena Metodologii (25%):** Wyjaśnij "Kill Switch" i "Wektory Czasu". To pokazuje dojrzałość analityczną.  
5. **Uzasadnienie (20%):** W prezentacji miej slajd "Dlaczego te dane?". Odpowiedź: "Bo łączymy twardy fundament z miękkim potencjałem".

