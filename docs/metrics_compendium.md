# S&T Metrics & Formulas Compendium
**Source of Truth Version: 1.1 (Expert Analytics Edition)**
**Based on Codebase: `app/utils.py`, `app/main.py`**

This document serves as the definitive reference for the mathematical and business logic powering the Stability & Transformation Dashboard. It interprets technical implementation through three lenses: **Business Analysis (KPIs)**, **Data Science (Algorithms)**, and **Actuarial Science (Risk)**.

---

## 1. Raw Financial Metrics (The Fundamentals)

### Net Profit Margin
*   **Formula:** `(Net_Profit / Revenue) * 100`
*   **Business Analyst:** A classic efficiency KPI. Tells us how much of every zloty earned remains as profit. Low margin (<5%) implies high sensitivity to cost shocks.
*   **Data Scientist:** A primary feature for the *Stability Score*. It is normalized against a standard range (-5% to +20%) to handle outliers without skewing the distribution.
*   **Actuary:** The first line of defense against insolvency. Higher margins provide a "solvency buffer" against adverse variance in claims or costs.

### Debt Burden (Debt/Revenue)
*   **Formula:** `Total_Debt / Revenue`
*   **Business Analyst:** Leverage ratio. Indicates how many years of revenue it would take to pay off debt. >4.0x is typically considered distressed in this model.
*   **Data Scientist:** Treated as an *inverse feature*. In normalization, `1 - norm(debt)` is used because lower is better. Heavily affects the "Safety" component.
*   **Actuary:** A key predictor of default probability. High leverage drastically increases the ruin probability (Probability of Ruin) during economic downturns.

### Cash Ratio (Liquidity)
*   **Formula:** `Cash / Liabilities_Short`
*   **Business Analyst:** "Current Liquidity". Can the company pay off its immediate bills today? <0.2 is critical liquidity crisis territory.
*   **Data Scientist:** Used as a *binary-like* modifier in the Lending Score. It's clipped at 1.5x because hoarding cash beyond that yields diminishing returns for model scoring.
*   **Actuary:** Represents catastrophic liquidity risk. Even profitable entities fail without cash. This metric dictates the "Liquidity Factor" which can penalize the final score by up to 20 points.

### Capex Intensity
*   **Formula:** `(Investment / Revenue) * 100`
*   **Business Analyst:** Reinvestment rate. Measures how aggressively a sector is upgrading its asset base. High Capex = Confidence in future demand.
*   **Data Scientist:** One half of the *Transformation Score*. It proxies "Hardware/Infrastructure Investment".
*   **Actuary:** Represents "Betting on the Future". Increases short-term cash outflow risk but decreases long-term obsolescence risk.

### ArXiv AI Metric (External)
*   **Formula:** `Count of AI Papers mapped to PKD Code`
*   **Business Analyst:** "Innovation Hype". Measures pure R&D and theoretical interest in AI within the sector.
*   **Data Scientist:** The second half of the *Transformation Score*. It proxies "Software/Intellectual Investment". Because distribution is heavy-tailed (most 0, some 5000+), normalization uses a wide range (0-5000) to distinguish leaders.
*   **Actuary:** A marker for "Transformation Risk". High scores imply volatility—the business model is changing rapidly, introducing estimation error in historical data models.

---

## 2. Composite Scoring Algorithms

### A. Stability Score (Kondycja)
**Concept:** A weighted index measuring the current health and resilience of the sector.

**Formula (Forecast Mode - Absolute):**
```python
Stability_Score = (
    (0.40 * Normalized_Profitability) + 
    (0.30 * Normalized_Growth) + 
    (0.30 * Normalized_Safety) 
) * 100
```
*Where Safety = Avg(Cash_Ratio, Inverted_Debt, Inverted_Bankruptcy)*

*   **Business Analyst:** This is the "Credit Rating". A score >65 implies Investment Grade. <40 implies heavy distress.
*   **Data Scientist:** A linear combination of uncorrelated features. We mix "Flow" metrics (Growth, Profit) with "Stock" metrics (Debt, Cash) to prevent overfitting to a single good year.
*   **Actuary:** This score is an inverse proxy for Default Risk. We prioritize "Safety" (Debt/Cash) heavily (30% total weight) because in risk modeling, survival > growth.

### B. Transformation Score (Innowacyjność)
**Concept:** A forward-looking index measuring adoption of future technologies (Hardware + AI).

**Formula:**
```python
Transformation_Score = (
    (0.50 * Normalized_Capex) + 
    (0.50 * Normalized_Arxiv)
) * 100
```

*   **Business Analyst:** "Modernization Index". High score means the sector is actively spending money to change. Low score = Stagnation/Legacy.
*   **Data Scientist:** Two-factor model balancing "hard" spend (Capex) vs "soft" spend (Research). This reduces bias against sectors that only buy machines vs those that only write code.
*   **Actuary:** Volatility Indicator. Sectors with score >80 are undergoing structural shifts. Historical loss data for these sectors may be invalid for future premiums.

---

## 3. The "Crown Jewel": Lending Opportunity Score
**Concept:** The final decision metric for the Bank. It identifies the "Perfect Customer".

**Formula:**
```python
# In code (app/utils.py):
# final_score = (0.4 * pot_score) + (0.4 * stab_score) + (0.2 * liq_score)

Lending_Score = (
    (0.40 * Future_Transformation_2026) + 
    (0.40 * Current_Stability) + 
    (0.20 * Liquidity_Factor)
)
```

### Liquidity Factor Calculation (`liq_score`)
This internal variable converts raw liquidity/risk metrics into a 0-100 score.

**Case A: Cash Ratio Available (Preferred)**
$$
\text{Liquidity Factor} = \min\left(\frac{\text{Cash Ratio}}{1.5}, 1.0\right) \times 100
$$
*   **Logic:** We set a cap at 1.5x coverage.
    *   If `Cash_Ratio` = 0.75 -> Score = 50.
    *   If `Cash_Ratio` >= 1.5 -> Score = 100.

**Case B: Fallback to Bankruptcy Rate (If no Cash data)**
$$
\text{Liquidity Factor} = \max\left(0, \frac{5 - \text{Bankruptcy Rate}}{5}\right) \times 100
$$
*   **Logic:** Linear penalty for bankruptcy risk up to 5%.
    *   If `Bankruptcy_Rate` = 0% -> Score = 100.
    *   If `Bankruptcy_Rate` = 2.5% -> Score = 50.
    *   If `Bankruptcy_Rate` >= 5.0% -> Score = 0.

---

### Expert Interpretation
*   **Business Analyst (Sales):** "Who needs money AND can pay it back?"
    *   *High Transformation* = Needs money (Capex/R&D).
    *   *High Stability* = Can pay it back.
    *   *Target:* Any score > 70 is a "Hot Lead".
*   **Data Scientist (Modeler):** This is a temporal ensemble model.
    *   It combines $t_{current}$ (Stability) with $t_{future}$ (Transformation Forecast).
    *   This prevents "Looking in the rear-view mirror" errors common in standard credit scoring.
*   **Actuary (Risk):** This is a **Risk-Adjusted Return** metric.
    *   The `Liquidity_Risk_Factor` acts as a penalty function (haircut). If a company is illiquid, we cap their score regardless of how innovative they are. Logic: "You can't innovate if you are bankrupt."

---

## 4. Strategic Classification Logic (The Decision Tree)
**Context:** Used in the Parsing algorithms to categorize industries into actionable buckets.

### ⚠️ Wysokie Ryzyko (Critical Risk)
*   **Condition:** `Bankruptcy_Rate > 2.5%`
*   **Actuary Says:** "Do not underwrite." The base rate of failure is statistical noise level. Above 2.5%, it's systemic rot.

### 🌟 Liderzy Przyszłości (Future Leaders)
*   **Condition:** `Trans_Score_2026 > 60` AND `Stability_Score_2026 > 50`
*   **Data Scientist Says:** "The Global Maxima." These entities optimize both functions: Innovation and Safety. Rare and valuable.

### 🚀 Wschodzące Gwiazdy (Rising Stars)
*   **Condition:** `Trans_Score_2026 > 60` (but Stability <= 50)
*   **Business Analyst Says:** "High Growth / High Risk". Typical VC or Venture Debt profile. They burn cash (Low Stability) to grow (High Trans).

### 🛡️ Bezpieczne Przystanie (Safe Havens)
*   **Condition:** `Stability_Score_2026 > 65`
*   **Actuary Says:** "Low Variance". Stable cash flows, low debt. Ideal for low-yield, long-term bond holdings.

### 💰 Cel Kredytowy (Lending Targets)
*   **Condition:** `Lending_Score > 70`
*   **Business Analyst Says:** "The Sweet Spot". This overlap includes Leaders and strong Rising Stars. This list goes to the Sales Team.

---

## 5. Forecasting Engine Evaluation
**Model:** OLS Linear Regression on `n=6` (2019-2024).

*   **Statisticians Critique:** linear regression on short time series ($n<10$) is prone to overfitting and sensitive to outliers (e.g. Covid-2020 shock).
*   **Mitigation Strategy:**
    *   We use **Aggregated Sector Data** (reduces variance vs single company data).
    *   We exclude **Forecast Data** from training (train on Real only).
    *   For **ArXiv**, we truncate pre-2019 data as irrelevant "noise" before the LLM boom.
*   **Risk Assessment:** The model assumes "Momentum Continuity". It cannot predict "Black Swans" (Regulatory bans, new wars). Therefore, the `Stability Score` weight (40%) acts as an anchor to reality.
