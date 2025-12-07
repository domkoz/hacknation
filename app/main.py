import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os
import utils # Local import
import charts # Local import

# --- CONSTANTS ---
color_map = {
    'CRITICAL': '#ff4b4b',
    'OPPORTUNITY': '#2ecc71',
    'Neutral': '#3498db'
}

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="S&T Index Boardroom",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD ASSETS ---
try:
    # Adjust path if running locally from root
    css_path = os.path.join(os.path.dirname(__file__), 'assets/style.css')
    utils.load_css(css_path)
except FileNotFoundError:
    st.warning("CSS file not found.")

# --- LOAD DATA ---
try:
    df_all = utils.load_data()
    debates = utils.load_debates()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    # Logo handling
    try:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'logo', 'logo-pko-bank-polski.svg')
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.warning(f"Logo not found at {logo_path}")
    except Exception as e:
        st.error(f"Logo error: {e}")
    st.title("S&T Dashboard")
    
    # --- TIME SLIDER (New!) ---
    min_year = int(df_all['Year'].min())
    # Limit max year to 2024 as per request (forecasts shown separately)
    max_year = 2024 
    
    selected_year = st.slider("Wybierz Rok:", min_value=min_year, max_value=max_year, value=2024)
    
    st.divider()
    
    # Filter by Year first
    df = df_all[df_all['Year'] == selected_year].copy()
    
    # --- VIEW SELECTOR ---
    view_mode = st.radio("Tryb Widoku:", ["Macierz S&T (Główna)", "Analiza Ryzyka (Upadłości)", "🏆 Ranking & Eksport"], index=0)
    
    # --- SCORE CONFIGURATION ---
    with st.expander("⚙️ Konfiguracja Modelu S&T"):
        st.caption("Dostosuj wagi komponentów dla Stability Score:")
        w_growth = st.slider("Wzrost (Dynamika)", 0.0, 10.0, 4.0, 0.5)
        w_profit = st.slider("Zyskowność (Marża)", 0.0, 10.0, 6.0, 0.5)
        w_safety = st.slider("Bezpieczeństwo (Dług/Płynność)", 0.0, 10.0, 3.0, 0.5)
        st.divider()
        kill_switch_limit = st.slider("⚠️ Próg upadłości (Kill Switch %)", 0.0, 10.0, 4.5, 0.1, help="Branże powyżej tej wartości otrzymają status CRITICAL.")
        
    st.divider()
    
    # --- DYNAMIC STATUS RECALCULATION ---
    # Overwrite Status based on new Kill Switch Limit
    def recalc_status(row):
        # 1. Check Kill Switch
        if row.get('Bankruptcy_Rate', 0) > kill_switch_limit:
            return 'CRITICAL'
        # 2. Check Opportunity (Mock thresholds based on scores)
        if row.get('Stability_Score', 0) > 60 and row.get('Transformation_Score', 0) > 60:
            return 'OPPORTUNITY'
        return 'Neutral'
        
    df['Status'] = df.apply(recalc_status, axis=1)

    # --- LEVEL OF DETAIL ---
    level_map = {
        "Sekcje (Makro)": "L1",
        "Działy (2 cyfry)": "L2",
        "Grupy (3 cyfry)": "L3",
        "Klasy (4 cyfry)": "L4"
    }
    selected_level_label = st.radio("Poziom Szczegółowości:", list(level_map.keys()), index=0)
    selected_level = level_map[selected_level_label]
    
    # Filter Logic
    if selected_level == "L1":
        # Sections (SEK_A, SEK_B...)
        df = df[df['PKD_Code'].astype(str).str.startswith('SEK_')]
    elif selected_level == "L2":
        # Divisions (01., 02. -> Length 3)
        df = df[(df['PKD_Code'].astype(str).str.len() == 3) & (~df['PKD_Code'].astype(str).str.startswith('SEK'))]
    elif selected_level == "L3":
        # Groups (01.1 -> Length 4)
        df = df[df['PKD_Code'].astype(str).str.len() == 4]
    elif selected_level == "L4":
        # Classes (01.11 -> Length 5, excluding SEK_)
        df = df[(df['PKD_Code'].astype(str).str.len() == 5) & (~df['PKD_Code'].astype(str).str.startswith('SEK'))]
    
    # Sector Filter (using first digit of PKD as proxy if Sector col mock is gone, or using the new Sector col if available)
    # The new real index script assigns "Ogólny" or we can infer.
    # Let's try to extract Sector from Industry Name to make it cooler or just show top 100 to avoid lag.
    
    # Ensure Sector column exists, if not fill it
    # Ensure Sector column exists or populate it dynamically
    # This logic maps every PKD code to its parent Macro Section (e.g. 41.20 -> Section F Construction)
    if 'Sector' not in df.columns or df['Sector'].iloc[0] == 'All':
        # 1. Define Ranges
        ranges = {
            'A': (1, 3), 'B': (5, 9), 'C': (10, 33), 'D': (35, 35), 'E': (36, 39),
            'F': (41, 43), 'G': (45, 47), 'H': (49, 53), 'I': (55, 56), 'J': (58, 63),
            'K': (64, 66), 'L': (68, 68), 'M': (69, 75), 'N': (77, 82), 'O': (84, 84),
            'P': (85, 85), 'Q': (86, 88), 'R': (90, 93), 'S': (94, 96)
        }
        
        # 2. Get Section Names Map (Code -> Name) for clean display
        # We look at global df_all to ensure we have the names even if current year is filtered
        section_rows = df_all[df_all['PKD_Code'].astype(str).str.startswith('SEK_')]
        # Create map: "A" -> "ROLNICTWO...", "B" -> "GÓRNICTWO..."
        section_map = {}
        for _, row in section_rows.iterrows():
            code = str(row['PKD_Code']) # SEK_A
            letter = code.split('_')[1]
            name = row['Industry_Name']
            section_map[letter] = f"{letter} - {name}"

        # 3. Helper to find sector
        def find_sector(pkd):
            pkd = str(pkd)
            if pkd.startswith('SEK_'):
                letter = pkd.split('_')[1]
                return section_map.get(letter, pkd)
            
            # Numeric
            try:
                digits = int(pkd[:2])
                for letter, (start, end) in ranges.items():
                    if start <= digits <= end:
                        return section_map.get(letter, f"Sekcja {letter}")
            except:
                pass
            return "Inne"

        df['Sector'] = df['PKD_Code'].apply(find_sector)
        
    unique_sectors = sorted(df['Sector'].dropna().unique())
    selected_sector = st.selectbox("Wybierz Sektor:", ["Wszystkie"] + list(unique_sectors))
    
    if selected_sector != "Wszystkie":
        filtered_df = df[df['Sector'] == selected_sector]
    else:
        filtered_df = df

    # Revenue Filter
    min_rev_val = int(df['Revenue'].min())
    max_rev_val = int(df['Revenue'].max())
    
    # Filter by Revenue first (to avoid skews from micro entities in normalization)
    revenue_threshold = st.slider("Minimalne Przychody (mln PLN):", min_value=min_rev_val, max_value=max_rev_val, value=min_rev_val)
    filtered_df = filtered_df[filtered_df['Revenue'] >= revenue_threshold].copy()
    
    st.sidebar.divider()
    with st.sidebar.expander("ℹ️ Metodologia i Wzory"):
        st.markdown("""
        **1. Stability Score (Kondycja):**
        *   **40%** Zyskowność (Marża Netto + % Rentownych)
        *   **30%** Wzrost (Dynamika Przych. YoY)
        *   **15%** Bezpieczeństwo Długu (Debt/Revenue)
        *   **15%** Płynność (Cash Ratio)
        
        **2. Innovation Index (Transformacja):**
        *   **50%** Inwestycje (Capex Intensity)
        *   **50%** Nauka (Liczba Publikacji ArXiv AI)
        
        **3. Lending Opportunity (Bank):**
        *   **40%** Potencjał (Transformation Score 2026 - Prognoza)
        *   **40%** Stabilność (Current Stability Score)
        *   **20%** Płynność (Cash Ratio / Inverse Risk)
        
        **4. Prognoza (Forecast):**
        *   Model liniowy (Linear Regression) na danych 2019-2024.
        *   Predykcja dla lat 2025-2026.
        """)
    
    # --- DYNAMIC STABILITY & TRANSFORMATION SCORE CALCULATION ---
    # We use the SHARED UTILITY to ensure consistency between the Matrix Chart and the Time Series Forecast.
    # This ensures that sidebar sliders affect BOTH the bubbles and the future trend lines.
    # And it ensures normalization is ABSOLUTE (comparable across years) rather than RELATIVE (checking who is best in 2024).
    
    if not filtered_df.empty:
        # Recalculate scores using the same logic as the forecast
        filtered_df = utils.recalculate_future_st_scores(
            filtered_df, 
            w_growth=w_growth, 
            w_profit=w_profit, 
            w_safety=w_safety
        )
         
        st.info("💡 **Instrukcja:** Kliknij w bąbelek na wykresie, aby zobaczyć debatę Zarządu.")
        st.caption(f"Dane dla roku: {selected_year}. Liczba branż: {len(filtered_df)}")


# --- HELPER: AGGREGATES DISPLAY ---
def display_aggregates(df_subset, title="Globalny Wynik (Suma)"):
    # Calculate aggregates
    # Note: df_subset should be non-overlapping (e.g. only Sections, or only Divisions)
    
    # --- CALCULATE 5 KEY METRICS ---
    
    # 1. Total Revenue (Wielkość)
    total_revenue = df_subset['Revenue'].sum()
    
    # 2. Revenue Dynamics (Wzrost)
    # Weighted avg dynamics or Total Current Rev / Total Prev Rev - 1
    # We need to reconstruct Total Prev Rev.
    # RevPrev = Revenue / (1 + Dynamics_YoY)
    current_revs = df_subset['Revenue']
    current_dyns = df_subset['Dynamics_YoY']
    # Avoid zero div
    prev_revs = [r / (1 + d) if (not pd.isna(d) and d != -1) else r for r, d in zip(current_revs, current_dyns)]
    total_prev_rev = sum(prev_revs)
    
    agg_dynamics = ((total_revenue - total_prev_rev) / total_prev_rev * 100) if total_prev_rev else 0
    
    # 3. Net Profit Margin (Rentowność)
    # Sum(Net Profit) / Sum(Revenue)
    total_net_profit = df_subset.get('Net_Profit', pd.Series(0)).sum()
    agg_net_margin = (total_net_profit / total_revenue * 100) if total_revenue else 0
    
    # 4. Debt Burden (Zadłużenie)
    # Sum(Total Debt) / Sum(Revenue)
    total_debt = df_subset.get('Total_Debt', pd.Series(0)).sum()
    agg_debt_ratio = (total_debt / total_revenue) if total_revenue else 0
    
    # 5. Cash Ratio (Płynność)
    # Sum(Cash) / Sum(Short Term Liabilities)
    total_cash = df_subset.get('Cash', pd.Series(0)).sum()
    total_short_liab = df_subset.get('Liabilities_Short', pd.Series(0)).sum()
    agg_cash_ratio = (total_cash / total_short_liab) if total_short_liab else 0
    
    # 6. Relative Risk (Ryzyko)
    # Sum(Bankruptcies) / Sum(Entities) * 100
    if 'Bankruptcy_Count' in df_subset.columns:
        total_bankrupt = df_subset['Bankruptcy_Count'].sum()
    else:
        total_bankrupt = (df_subset['Bankruptcy_Rate'] * df_subset['Entity_Count'] / 100).sum()
    
    total_entities = df_subset['Entity_Count'].sum()
    agg_risk_percent = (total_bankrupt / total_entities * 100) if total_entities else 0
    
    
    # Display 5 Cols
    st.markdown(f"#### 📊 {title}")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    c1.metric("Wielkość (Przychody)", f"{total_revenue/1000:,.1f} mld", f"{agg_dynamics:+.1f}% r/r")
    c2.metric("Rentowność (Marża)", f"{agg_net_margin:.1f}%", help="Zysk Netto / Przychody")
    c3.metric("Zadłużenie (Dług/Przychody)", f"{agg_debt_ratio:.2f}x", help="Dług / Przychody")
    c4.metric("Płynność (Gotówka)", f"{agg_cash_ratio:.2f}", help="Gotówka / Zobowiązania Krótkie")
    c5.metric("Ryzyko (Upadłości)", f"{agg_risk_percent:.2f}%", f"{total_bankrupt:,.0f} firm", delta_color="inverse", help="% Firm, które ogłosiły upadłość")
    
    st.divider()

# --- MAIN LAYOUT ---
st.title(f"S&T Index ({selected_year})")
st.markdown("### `System Diagnostyki Branżowej AI PKO BP` (Real Data)")

# DISPLAY GLOBAL AGGREGATES FOR CURRENT SELECTION
display_aggregates(filtered_df, title=f"Agregat dla: {selected_level_label} | {selected_sector}")

col_main, col_details = st.columns([2, 1])
# --- RISK VIEW LOGIC ---
if view_mode == "Analiza Ryzyka (Upadłości)":
    st.markdown("### 🛡️ Radar Ryzyka: Dług vs Upadłość")
    st.markdown("""
    **Oś X: Zadłużenie (Debt/Revenue)**
    *Mierzy "dźwignię finansową" branży.*
    Im wyższa wartość, tym bardziej zadłużona branża względem swoich przychodów.
    
    **Oś Y: Wskaźnik Upadłości (%)**
    *Mierzy realne bankructwa.*
    Odsetek firm, które ogłosiły upadłość w danym roku.
    
    **Kolor: Dynamika (Czerwony = Spadek)**
    *Pokazuje kondycję wzrostową.*
    Czerwone punkty to branże kurczące się (recesja), Zielone to rosnące.
    
    **Wnioski:**
    Punkt w prawym-górnym rogu (Wysoki Dług + Wysoka Upadłość) to **STREFA ŚMIERCI**.
    Punkt w lewym-dolnym (Niski Dług + Niska Upadłość) to **Bezpieczna Przystań**.
    """)
    # RISK HEATMAP
    # X: Dynamics (Growth/Shrinkage)
    # Y: Bankruptcy Rate (Risk)
    # Color: Debt / Revenue Ratio (Leverage) or just Debt
    
    # Prepare metrics
    filtered_df['Leverage_Ratio'] = filtered_df.apply(
        lambda x: (x['Total_Debt'] / x['Revenue']) if x['Revenue'] > 0 else 0, axis=1
    )
    # Cap Leverage for visualization (e.g. at 200%) to avoid outliers blowing up scale
    filtered_df['Leverage_Vis'] = filtered_df['Leverage_Ratio'].clip(upper=5.0)
    
    fig_risk = charts.create_risk_radar_chart(filtered_df)
    st.plotly_chart(fig_risk, use_container_width=True)
    
    # RED ZONE TABLE
    st.markdown("### 🚨 Lista Ostrzeżeń (Red Zone)")
    st.caption("Branże kurczące się (Dynamika < 0%) z wysokim ryzykiem upadłości (> 1%).")
    
    red_zone_df = filtered_df[
        (filtered_df['Dynamics_YoY'] < 0) & 
        (filtered_df['Bankruptcy_Rate'] > 1.0)
    ].sort_values('Bankruptcy_Rate', ascending=False)
    
    if not red_zone_df.empty:
        # Format for display
        display_cols = ['PKD_Code', 'Industry_Name', 'Bankruptcy_Rate', 'Dynamics_YoY', 'Total_Debt', 'Revenue']
        
        # Stylized dataframe
        st.dataframe(
            red_zone_df[display_cols].style.format({
                'Bankruptcy_Rate': "{:.2f}%",
                'Dynamics_YoY': "{:+.2%}",
                'Total_Debt': "{:,.0f}",
                'Revenue': "{:,.0f}"
            }).background_gradient(subset=['Bankruptcy_Rate'], cmap='Reds'),
            use_container_width=True
        )
    else:
        st.success("Brak branż w strefie krytycznej dla wybranych filtrów! 🎉")
        

    st.stop() # Ensure Main View doesn't run

# --- RANKING & EXPORT VIEW LOGIC ---
# --- RANKING & EXPORT VIEW LOGIC ---
if view_mode == "🏆 Ranking & Eksport":
    st.markdown("### 🏆 Ranking Sektorów (Prognoza 2026)")
    st.caption("Ranking oparty o **prognozowaną kondycję branż na rok 2026**, uwzględniający trendy AI, zadłużenia i rentowności.")
    
    # 1. FORECASTING ENGINE
    # We iterate through each industry in the filtered view and project it to 2026.
    
    # progress_text = "Trwa generowanie zaawansowanych prognoz na rok 2026 dla wszystkich sektorów..."
    # my_bar = st.progress(0, text=progress_text)
    
    future_rows = []
    # total_items = len(filtered_df)
    
    # Metrics required for S&T Calculation + Interest
    metrics_to_forecast = [
        'Net_Profit_Margin', 'Debt_to_Revenue', 'Cash_Ratio', 'Bankruptcy_Rate',
        'Dynamics_YoY', 'Profitability', 'Capex_Intensity', 'Arxiv_Papers', 'Revenue'
    ]
    
    with st.spinner("Generowanie prognoz na rok 2026..."):
        for idx, row in filtered_df.iterrows():
            pkd = row['PKD_Code']
            
            # Get Full History for this entity
            hist_df = df_all[df_all['PKD_Code'] == pkd].sort_values('Year')
            
            # Base for Future Row
            # We explicitly store CURRENT scores to preserve them before recalculation
            future_row = {
                'PKD_Code': pkd, 
                'Industry_Name': row['Industry_Name'], 
                'Year': 2026,
                'Current_Revenue': row['Revenue'],
                'Stability_Current': row.get('Stability_Score', 0),
                'Transformation_Current': row.get('Transformation_Score', 0),
                'Is_Forecast': True # Trigger for utils.recalculate_future_st_scores
            }
            
            # Forecast each metric
            for metric in metrics_to_forecast:
                try:
                    # ArXiv Hype Fix: Train only on recent data
                    temp_hist = hist_df.copy()
                    if metric == 'Arxiv_Papers':
                        temp_hist = temp_hist[temp_hist['Year'] >= 2019]
                        
                    # Run Regressions
                    forecast_df = utils.calculate_forecast(temp_hist, metric, years_ahead=2) # 2024 -> 2026
                    
                    # Get 2026 value
                    val_2026 = forecast_df[forecast_df['Year'] == 2026][metric].iloc[0]
                    future_row[metric] = val_2026
                except:
                    # Fallback to current if forecast fails
                    future_row[metric] = row.get(metric, 0)

            future_rows.append(future_row)
            
    # 2. CREATE FUTURE DATAFRAME
    df_2026 = pd.DataFrame(future_rows)
    
    # 3. RECALCULATE SCORES (On 2026 Data)
    # The utils function overwrites 'Stability_Score' and 'Transformation_Score' based on the metrics in the row.
    # Since the row now contains 2026 metrics, these will be 2026 Scores.
    if not df_2026.empty:
        df_2026 = utils.recalculate_future_st_scores(
            df_2026, 
            w_growth=w_growth, 
            w_profit=w_profit, 
            w_safety=w_safety
        )
    else:
        # Handle empty case
        df_2026 = pd.DataFrame(columns=['PKD_Code', 'Industry_Name', 'Transformation_Score', 'Stability_Score'])

    # Rename for clarity
    df_2026.rename(columns={
        'Stability_Score': 'Stability_2026',
        'Transformation_Score': 'Transformation_2026'
    }, inplace=True)
    
    # 4. CALCULATE LENDING SCORE (Future Based)
    # Using Future Transformation Score (Potential) and Future Stability (Risk)
    # Ensure columns exist (fixes KeyError)
    if 'Transformation_2026' not in df_2026.columns:
         df_2026['Transformation_2026'] = 0
    if 'Stability_2026' not in df_2026.columns:
         df_2026['Stability_2026'] = 0

    # Helper wrapper to map new names to expected keys
    def calc_future_lending(r):
        # We construct a mock row that looks like what calculate_lending_opportunity expects
        # It expects 'Stability_Score' or we pass it explicit args?
        # Function sig: calculate_lending_opportunity(current_row, future_trans_score, current_liquidity=None)
        # Inside it uses row.get('Stability_Score')
        # So we need to cheat or modify the function.
        # Let's cheat by passing a mock dict
        mock_row = r.copy()
        mock_row['Stability_Score'] = r['Stability_2026'] # Use Future Stability? Or Current?
        # User wants "Future" Lending Score basically.
        # Original plan: 40% Future Trans, 40% **Current** Stability.
        # User Request: "Stability teraz, i stability prognozowane".
        # Let's stick to the "Lending Score 2026" being Fully Future.
        
        return utils.calculate_lending_opportunity(mock_row, r['Transformation_2026'])

    df_2026['Lending_Score_2026'] = df_2026.apply(calc_future_lending, axis=1)
    
    # 5. CLASSIFICATION (Updated for Future Context)
    def classify_future(row):
        # 1. Critical Risk
        if row['Bankruptcy_Rate'] > 2.5: 
            return "⚠️ Wysokie Ryzyko (2026)"
            
        # 2. AI Powerhouses
        if row['Transformation_2026'] > 60:
            if row['Stability_2026'] > 50:
                return "🌟 Liderzy Przyszłości"
            else:
                return "🚀 Wschodzące Gwiazdy"
                
        # 3. Cash Cows
        if row['Stability_2026'] > 65:
            return "🛡️ Bezpieczne Przystanie"
         
        # 4. Lending Targets
        if row['Lending_Score_2026'] > 70:
            return "💰 Cel Kredytowy"
            
        return "🔹 Neutralne"

    df_2026['Klasyfikacja'] = df_2026.apply(classify_future, axis=1)
    
    # 6. DISPLAY
    # Combine Columns
    
    cols = [
        'PKD_Code', 'Industry_Name', 'Klasyfikacja', 
        'Lending_Score_2026', 
        'Stability_Current', 'Stability_2026', 
        'Transformation_Current', 'Transformation_2026',
        'Revenue', 'Dynamics_YoY', 'Bankruptcy_Rate'
    ]
    
    rename_map = {
        'Lending_Score_2026': 'Lending Opp (2026)',
        'Stability_Current': 'Stability (Now)',
        'Stability_2026': 'Stability (2026)',
        'Transformation_Current': 'Transformation (Now)',
        'Transformation_2026': 'Transformation (2026)',
        'Revenue': 'Est. Revenue',
        'Dynamics_YoY': 'Est. Growth',
        'Bankruptcy_Rate': 'Est. Risk %'
    }
    
    display_df = df_2026[cols].rename(columns=rename_map)
    
    # Sort
    sort_col = st.selectbox("Sortuj Ranking:", list(rename_map.values()), index=0)
    display_df = display_df.sort_values(sort_col, ascending=False).reset_index(drop=True)

    st.dataframe(
        display_df.style.format({
            'Lending Opp (2026)': "{:.1f}",
            'Stability (Now)': "{:.1f}",
            'Stability (2026)': "{:.1f}",
            'Transformation (Now)': "{:.1f}",
            'Transformation (2026)': "{:.1f}",
            'Est. Revenue': "{:,.0f}",
            'Est. Growth': "{:+.1%}",
            'Est. Risk %': "{:.2f}%"
        }).background_gradient(subset=['Lending Opp (2026)'], cmap='Greens'),
        column_config={
            "Lending Opp (2026)": st.column_config.ProgressColumn("Lending Opp", min_value=0, max_value=100, format="%d"),
            "Stability (Now)": st.column_config.NumberColumn("Stab (Now)"),
            "Stability (2026)": st.column_config.NumberColumn("Stab (2026)"),
            "Transformation (Now)": st.column_config.NumberColumn("Trans (Now)"),
            "Transformation (2026)": st.column_config.NumberColumn("Trans (2026)"),
        },
        use_container_width=True,
        height=600
    )
    
    # Export
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Pobierz Raport Prognoz (CSV 2026)",
        data=csv,
        file_name=f'Raport_Prognoza_2026_Sektory.csv',
        mime='text/csv',
        type='primary'
    )
    
    st.stop()



# --- SELECTION LOGIC (PRE-CALC) ---
# We need this BEFORE the chart to pass the 'highlight' parameter
selection = st.session_state.get("bubble_chart", {}).get("selection", {}).get("points", [])
selected_pkd = None
selected_row = None

# 1. Chart Selection Priority
if selection:
    point = selection[0]
    x_val = point['x']
    y_val = point['y']
    
    # Find exact match
    possible_rows = filtered_df[
        (abs(filtered_df['Stability_Score'] - x_val) < 0.001) & 
        (abs(filtered_df['Transformation_Score'] - y_val) < 0.001)
    ]
    
    if not possible_rows.empty:
        selected_row = possible_rows.iloc[0]
        selected_pkd = str(selected_row['PKD_Code'])
        
# 2. Fallback: Auto-select Sector if no point clicked but Sector Filter is active
elif selected_sector != "Wszystkie":
    try:
        sec_letter = selected_sector.split(' - ')[0] # "F"
        target_pkd = f"SEK_{sec_letter}"
        
        # Check if in current filtered_df
        rows = filtered_df[filtered_df['PKD_Code'] == target_pkd]
        if not rows.empty:
            selected_row = rows.iloc[0]
            selected_pkd = str(selected_row['PKD_Code'])
    except:
        pass

# --- CHART (LEFT) ---
with col_main:
    # Calculate max revenue for global scaling
    max_rev_global = df_all['Revenue'].max()
    
    # Pass selected_pkd to the chart function
    fig = charts.create_main_bubble_chart(filtered_df, max_rev_global, highlight_pkd=selected_pkd)

    # Display Chart
    # Important: selection_mode="points" enables the click interaction
    st.plotly_chart(fig, use_container_width=True, key="bubble_chart", on_select="rerun", selection_mode="points")


# --- DETAILS (RIGHT + BOTTOM) ---
with col_details:
    st.subheader("AI Boardroom")
    
    # Logic moved up, just using result now
    if not selected_row is None:
        # Pass (logic continues below...)
        pass
            
    # DISPLAY SELECTION DETAILS
    if selected_row is not None:
        industry_name = selected_row['Industry_Name']
        selected_pkd = str(selected_row['PKD_Code'])
        
        st.markdown(f"#### {industry_name}")
        st.caption(f"PKD: {selected_pkd}")
        
        # Metrics Row
        m1, m2 = st.columns(2)
        m1.metric("Stability", f"{selected_row.get('Stability_Score', 0):.1f}", delta_color="normal")
        m2.metric("Transformation", f"{selected_row.get('Transformation_Score', 0):.1f}", delta_color="normal")
        
        # --- STABILITY RADAR CHART ---
        radar_fig = charts.create_stability_radar_chart(selected_row, filtered_df)
        st.plotly_chart(radar_fig, use_container_width=True, config={'displayModeBar': False})
        
        # Detailed Breakdown
        with st.expander("📊 Szczegóły Wyliczeń (Dynamiczne)"):
            # Helper for colors
            def color_val(val, inverse=False, is_percent=False):
                display_val = val * 100 if is_percent else val
                suffix = "%" if is_percent else ""
                
                if inverse:
                    color = "#ff4b4b" if val > 0 else "#2ecc71" # Red if > 0 (Risk/Debt), Green if <= 0
                else:
                    color = "#2ecc71" if val > 0 else "#ff4b4b" # Green if > 0, Red if <= 0
                    
                # Neutral for 0
                if abs(val) < 0.0001: color = "#888"
                    
                return f'<span style="color:{color}; font-weight:bold;">{display_val:+.2f}{suffix}</span>'

            st.markdown(f"""
            **Twoje Wagi Stability Score:**
            - Wzrost: {w_growth}
            - Zyskowność: {w_profit}
            - Bezpieczeństwo: {w_safety}
            
            **Składowe (Wartości Surowe):**
            - Dynamika przychodów: {color_val(selected_row.get('Dynamics_YoY', 0), is_percent=True)}
            - Marża Netto: {color_val(selected_row.get('Net_Profit_Margin', 0), is_percent=False)}%
            - Zyskowność (% firm): {color_val(selected_row.get('Profitability', 0), is_percent=True)}
            - Płynność (Cash Ratio): {color_val(selected_row.get('Cash_Ratio', 0), is_percent=False)}
            - Zadłużenie (Debt/Rev): {color_val(selected_row.get('Debt_to_Revenue', 0), inverse=True)}x
            - Ryzyko (Upadłości): {color_val(selected_row.get('Bankruptcy_Rate', 0), inverse=True, is_percent=False)}%
            
            **Transformacja (Inwestycje + Innowacje):**
            - Nakłady: **{selected_row.get('Investment', 0):,.1f} mln PLN**
            - Intensywność (Capex/Rev): {color_val(selected_row.get('Capex_Intensity', 0), is_percent=False)}%
            - Innovation Index (ArXiv): **{int(selected_row.get('Arxiv_Papers', 0))}**

            ---
            ### 🏦 Potencjał Kredytowy
            **Lending Opportunity Score: {selected_row.get('Lending_Score', 0):.1f}/100**
            *Miara atrakcyjności dla banku (Capex + Stability + Liquidity)*
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Debate Content
        debate = debates.get(selected_pkd)
        if debate:
            st.markdown("### 🏛️ AI Boardroom")
            
            specialist_op = debate.get('Specialist_Opinion', '')
            if specialist_op:
                with st.expander("👷 Opinia Specjalisty Branżowego", expanded=False):
                    st.markdown(f"""
                    <div class="specialist-bubble" style="margin-top: 0px;">
                        "{specialist_op}"
                    </div>
                    """, unsafe_allow_html=True)
            
            # CRO
            with st.expander("👩‍💼 Opinia CRO (Ryzyko)", expanded=False):
                st.markdown(f"""
                <div class="cro-bubble" style="margin-top: 0px;">
                    "{debate.get('CRO_Opinion','')}"
                </div>
                """, unsafe_allow_html=True)

            # CSO
            with st.expander("🚀 Opinia CSO (Strategia)", expanded=False):
                st.markdown(f"""
                <div class="cso-bubble" style="margin-top: 0px;">
                    "{debate.get('CSO_Opinion','')}"
                </div>
                """, unsafe_allow_html=True)
            
            # Recommendation
            # --- DYNAMIC LENDING SCORE (CALCULATED ON THE FLY) ---
            # 1. Get 2026 Forecast for Context
            forecast_trans_score = None
            try:
                # Need to run forecast specifically for this item if not already done?
                # For speed in UI, we might just estimate or look if we have it.
                # Since we haven't run global forecast yet in this block, let's run a quick one for this row.
                hist_data = df_all[df_all['PKD_Code'] == selected_pkd].sort_values('Year')
                if not hist_data.empty:
                    # Quick Forecast for Transformation Score components
                    # Note: We need recalculate_future_st_scores functionality
                    # Simpler approach: Calculate Forecast for 'Transformation_Score' directly if it was a column?
                    # No, it's calculated from components. 
                    # Let's perform the full forecast logic for this single entity.
                    
                    # Forecast Capex & Arxiv
                    df_capex = utils.calculate_forecast(hist_data, 'Capex_Intensity', 2)
                    df_arxiv = utils.calculate_forecast(hist_data, 'Arxiv_Papers', 2)
                    
                    # Get 2026 values
                    future_capex = df_capex[df_capex['Year'] == 2026]['Capex_Intensity'].iloc[0]
                    # Arxiv needs 2019+ filter inside forecast, but here we just take result if robust
                    # Let's assume utils handled it or we do basic linear
                    future_arxiv = df_arxiv[df_arxiv['Year'] == 2026]['Arxiv_Papers'].iloc[0]
                    
                    # Normalize & Score (Manual Re-impl or Helper?)
                    # Let's simple-norm using bounds from utils
                    b_capex = utils.norm(future_capex, *utils.bounds['Capex_Intensity'])
                    b_arxiv = utils.norm(future_arxiv, *utils.bounds['Arxiv_Papers'])
                    
                    forecast_trans_score = ((0.5 * b_capex) + (0.5 * b_arxiv)) * 100
            except:
                pass
            
            # 2. Compute Score
            lending_score = utils.calculate_lending_opportunity(selected_row, forecast_trans_score)
            
            st.markdown(f"""
            <div class="verdict-box">WERDYKT: {debate.get('Final_Verdict','')}</div>
            <div style="background-color: #f1c40f; padding: 5px; border-radius: 5px; margin-top: 5px; text-align: center; color: black; font-weight: bold;">
                BANK: {debate.get('Credit_Recommendation', 'DECISION_PENDING')}
            </div>
            <div style="margin-top: 10px; font-weight: bold; font-size: 1.1em;">
                 Opportunity Score: {lending_score:.1f}/100 
                 <span style="font-size:0.8em; color:gray;">(incl. 2026 Forecast)</span>
            </div>
            <div style="text-align: center; font-style: italic; font-size: 0.9em; margin-top: 5px;">
                "{debate.get('Recommendation_Rationale', '')}"
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Brak debaty (AI odpoczywa).")
            
    else:
        st.write("👈 Kliknij bąbelek lub wybierz Sektor!")

# --- RECURSIVE DRILL DOWN SECTION ---
current_selection_pkd = selected_pkd
level_depth = 0
max_depth = 3 # Safety break

while current_selection_pkd and level_depth < max_depth:
    st.divider()
    
    # Get details for current selection
    # Need to find row for current_selection_pkd in df_all (for correct Year)
    # We use df_all because child might not be in the initial 'filtered_df' if user filtered by something else, 
    # but logically drill down should show global context.
    
    current_row_df = df_all[(df_all['PKD_Code'] == current_selection_pkd) & (df_all['Year'] == selected_year)]
    if current_row_df.empty:
        break
        
    current_row = current_row_df.iloc[0]
    st.markdown(f"### 📉 Poziom {level_depth + 1}: `{current_row['Industry_Name']}`")
    
    # --- METRICS FOR CURRENT LEVEL ---
    # Use Metrics Calculated in Loader
    lev_rev = current_row['Revenue']
    lev_dyn = current_row['Dynamics_YoY']
    # Profit Margin
    lev_margin = current_row.get('Net_Profit_Margin', 0)
    # Debt Ratio
    lev_debt_ratio = current_row.get('Debt_to_Revenue', 0)
    # Cash Ratio
    lev_cash_ratio = current_row.get('Cash_Ratio', 0)
    # Risk
    lev_risk_percent = current_row.get('Bankruptcy_Rate', 0)
    lev_bankrupt_count = current_row.get('Bankruptcy_Count', 0)
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Wielkość", f"{lev_rev/1000:,.1f} mld PLN", f"{lev_dyn*100:+.1f}% r/r")
    m2.metric("Rentowność (Marża)", f"{lev_margin:.1f}%", help="Zysk Netto / Przychody")
    m3.metric("Zadłużenie", f"{lev_debt_ratio:.2f}x", help="Dług / Przychody")
    m4.metric("Płynność", f"{lev_cash_ratio:.2f}", help="Gotówka / Zobowiązania Krótkie")
    m5.metric("Ryzyko (Upadłości)", f"{lev_risk_percent:.2f}%", f"{lev_bankrupt_count:.0f} firm", delta_color="inverse")
    
    st.divider()
    
    col_hist, col_sub = st.columns(2)
    
    # 1. HISTORY CHART
    # 1. HISTORY & FORECAST CHARTS
    with col_hist:
        st.caption(f"📈 Trendy i Prognozy (2019-2026): {current_selection_pkd}")
        
        # Get full history
        hist_df = df_all[df_all['PKD_Code'] == current_selection_pkd].sort_values('Year')
        
        if not hist_df.empty:
            # Prepare Forecasts for Key Metrics
            # We predict 2 years ahead (2025-2026)
            
            # Prepare Forecasts for Key Metrics (2025-2026)
            # We need a Master Forecast DF with all metrics to recalculate S&T Scores
            
            # 1. Initialize Master with Anchor Metric
            # Ensure derived columns exist
            if 'Debt_to_Revenue' not in hist_df.columns:
                 hist_df['Debt_to_Revenue'] = hist_df['Total_Debt'] / hist_df['Revenue']
            
            # List of metrics to forecast
            metrics_to_forecast = [
                'Net_Profit_Margin', 'Debt_to_Revenue', 'Cash_Ratio', 'Bankruptcy_Rate',
                'Dynamics_YoY', 'Profitability', 'Capex_Intensity', 'Arxiv_Papers'
            ]
            
            # Initialize df_final with the first metric to set up the skeleton (rows)
            df_final = utils.calculate_forecast(hist_df, metrics_to_forecast[0], years_ahead=2)
            
            # Loop through the rest and fill in
            for metric in metrics_to_forecast[1:]:
                # We forecast based on the HISTORY PART only
                df_hist_only = df_final[df_final['Is_Forecast'] == False].copy()
                
                # Special handling for Arxiv: AI Hype is recent (2019+)
                # If we train on 2005-2024 (mostly zeros), the trendline will be flattened.
                # Train only on recent years to capture the "Hype".
                if metric == 'Arxiv_Papers':
                     df_hist_only = df_hist_only[df_hist_only['Year'] >= 2019]
                
                # Run forecast
                df_temp = utils.calculate_forecast(df_hist_only, metric, years_ahead=2)
                
                # Assign the forecast values to our master DF
                # Use careful assignment by Year to match rows
                for idx, row in df_temp[df_temp['Is_Forecast'] == True].iterrows():
                     yr = row['Year']
                     val = row[metric]
                     mask = (df_final['Year'] == yr) & (df_final['Is_Forecast'] == True)
                     df_final.loc[mask, metric] = val

            # 2. Recalculate S&T Scores based on forecasted metrics
            # NOW DYNAMIC: Passing weights from Sidebar Sliders
            df_final = utils.recalculate_future_st_scores(
                df_final, 
                w_growth=w_growth, 
                w_profit=w_profit, 
                w_safety=w_safety
            )
            
            # 3. Create Charts
            fig_profit = charts.create_historical_chart(df_final, 'Net_Profit_Margin', 'Rentowność (Marża)', 'Marża %', is_percent=False)
            fig_debt = charts.create_historical_chart(df_final, 'Debt_to_Revenue', 'Zadłużenie (Debt/Rev)', 'x', is_percent=False)
            fig_cash = charts.create_historical_chart(df_final, 'Cash_Ratio', 'Płynność (Gotówka)', 'Ratio', is_percent=False)
            fig_risk_chart = charts.create_historical_chart(df_final, 'Bankruptcy_Rate', 'Ryzyko Upadłości', '% Firm', is_percent=False)
            
            # New S&T Time Chart
            # Now showing Stability & Transformation over Time (Lines) instead of Matrix Trajectory
            fig_st_time = charts.create_st_time_chart(df_final)

            # 4. Display in Tabs
            t1, t2, t3 = st.tabs(["📊 Finanse", "🛡️ Ryzyko", "🧭 Strategia (S&T)"])
            
            with t1:
                st.plotly_chart(fig_profit, use_container_width=True, key=f"p_hist_{level_depth}_{current_selection_pkd}")
                st.plotly_chart(fig_debt, use_container_width=True, key=f"d_hist_{level_depth}_{current_selection_pkd}")
                
            with t2:
                st.plotly_chart(fig_risk_chart, use_container_width=True, key=f"r_hist_{level_depth}_{current_selection_pkd}")
                st.plotly_chart(fig_cash, use_container_width=True, key=f"c_hist_{level_depth}_{current_selection_pkd}")
                
            with t3:
                st.caption("Ewolucja wyników Stability & Transformation (2019-2026).")
                st.plotly_chart(fig_st_time, use_container_width=True, key=f"st_time_{level_depth}_{current_selection_pkd}")
    # 2. CHILDREN CHART
    next_selection = None
    with col_sub:
        st.caption(f"Składowe: {current_selection_pkd}")
        
        children_df = pd.DataFrame()
        
        # --- FIND CHILDREN LOGIC ---
        if current_selection_pkd.startswith('SEK_'):
             # Section Logic
            section_char = current_selection_pkd.split('_')[1]
            ranges = {
                'A': (1, 3), 'B': (5, 9), 'C': (10, 33), 'D': (35, 35), 'E': (36, 39),
                'F': (41, 43), 'G': (45, 47), 'H': (49, 53), 'I': (55, 56), 'J': (58, 63),
                'K': (64, 66), 'L': (68, 68), 'M': (69, 75), 'N': (77, 82), 'O': (84, 84),
                'P': (85, 85), 'Q': (86, 88), 'R': (90, 93), 'S': (94, 96)
            }
            if section_char in ranges:
                start, end = ranges[section_char]
                l2_candidates = df_all[
                    (df_all['Year'] == selected_year) & 
                    (df_all['PKD_Code'].str.len() == 3) & 
                    (~df_all['PKD_Code'].str.startswith('SEK'))
                ].copy()
                def get_prefix(code):
                    try: return int(str(code)[:2])
                    except: return -1
                l2_candidates['Prefix'] = l2_candidates['PKD_Code'].apply(get_prefix)
                children_df = l2_candidates[(l2_candidates['Prefix'] >= start) & (l2_candidates['Prefix'] <= end)]
        else:
            # Standard Logic
            # 01. (3) -> 01.x (4) | 01.1 (4) -> 01.xx (5)
            curr_len = len(current_selection_pkd)
            target_len = 0
            if curr_len == 3: target_len = 4
            elif curr_len == 4: target_len = 5
            
            if target_len:
                child_candidates = df_all[
                    (df_all['Year'] == selected_year) & 
                    (df_all['PKD_Code'].str.startswith(current_selection_pkd)) &
                    (df_all['PKD_Code'].str.len() == target_len)
                ].copy()
                children_df = child_candidates
        
        # --- RENDER SUB CHART ---
        if not children_df.empty:
            fig_sub = go.Figure()
            max_rev_sub = children_df['Revenue'].max()
            if max_rev_sub == 0: max_rev_sub = 1
            
            fig_sub.add_trace(go.Scatter(
                x=children_df['Stability_Score'],
                y=children_df['Transformation_Score'],
                mode='markers',
                text=children_df['Industry_Name'],
                marker=dict(
                    size=np.sqrt(children_df['Revenue'] / max_rev_sub) * 60 + 10,
                    color=children_df['Status'].map(color_map).fillna('#888'),
                    line=dict(width=1, color='white')
                ),
                customdata=children_df[['PKD_Code']], # Pass PKD for selection
                hovertemplate="<b>%{text}</b><extra></extra>"
            ))
            
            fig_sub.update_layout(
                xaxis_title="Stability Score",
                yaxis_title="Transformation Score",
                xaxis=dict(autorange=True, showgrid=False, zeroline=False),
                yaxis=dict(autorange=True, showgrid=False, zeroline=False),
                height=300,
                margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                font=dict(color='white')
            )
            
            # UNIQUE KEY for each level to capture selection
            chart_key = f"drill_chart_{level_depth}_{current_selection_pkd}"
            st.plotly_chart(fig_sub, use_container_width=True, key=chart_key, on_select="rerun", selection_mode="points")
            
            # CHECK SELECTION
            sub_sel = st.session_state.get(chart_key, {}).get("selection", {}).get("points", [])
            if sub_sel:
                # Find which point
                p = sub_sel[0]
                # Match by index or coordinate. 
                # Plotly selection returns pointIndex which corresponds to dataframe index IF reset.
                # Safer: Match x/y or use pointIndex if we ensure order.
                # "pointIndex" is reliable if we used 1 trace and didn't shuffle.
                # We used 1 trace here!
                
                try:
                    p = sub_sel[0]
                    next_pkd_code = children_df.iloc[p['point_index']]['PKD_Code']
                    child_row = children_df.iloc[p['point_index']]
                    next_selection = next_pkd_code
                    
                    # --- DETAILS INLINE ---
                    with st.expander(f"📊 Detale: {child_row['Industry_Name']}", expanded=True):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.markdown(f"**Dynamika:**<br>{utils.color_val(child_row.get('Dynamics_YoY',0)*100, is_percent=True)}", unsafe_allow_html=True)
                        c2.markdown(f"**Marża:**<br>{utils.color_val(child_row.get('Net_Profit_Margin',0), is_percent=False)}%", unsafe_allow_html=True)
                        c3.markdown(f"**Upadłość:**<br>{utils.color_val(child_row.get('Bankruptcy_Rate',0), inverse=True)}%", unsafe_allow_html=True)
                        c4.markdown(f"**Przychody:**<br>{child_row.get('Revenue',0):,.0f} mln", unsafe_allow_html=True)
                except Exception as e:
                    # st.error(f"Selection error: {e}")
                    pass
        else:
            st.write("Brak podkategorii.")
            
    # Advance loop
    if next_selection:
        current_selection_pkd = next_selection
        level_depth += 1
    else:
        break

