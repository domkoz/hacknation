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
    max_year = int(df_all['Year'].max())
    
    selected_year = st.slider("Wybierz Rok:", min_value=min_year, max_value=max_year, value=2024)
    
    st.divider()
    
    # Filter by Year first
    df = df_all[df_all['Year'] == selected_year].copy()
    
    # --- VIEW SELECTOR ---
    view_mode = st.radio("Tryb Widoku:", ["Macierz S&T (Główna)", "Analiza Ryzyka (Upadłości)"], index=0)
    
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
        *   **40%** Popyt na kapitał (Capex)
        *   **40%** Bezpieczeństwo (Stability)
        *   **20%** Płynność (Liquidity)
        
        **4. Prognoza (Forecast):**
        *   Model liniowy (Linear Regression) na danych 2019-2024.
        *   Predykcja dla lat 2025-2026.
        """)
    
    # --- DYNAMIC STABILITY SCORE CALCULATION ---
    # We recalculate Stability Score based on:
    # 1. Growth: Dynamics_YoY (Higher is better)
    # 2. Profitability: Combine Profitability (%) and Net_Profit_Margin (Higher is better)
    # 3. Safety: Combine Cash_Ratio (High is better) - Debt_to_Revenue (Low is better) - Bankruptcy_Rate (Low is better)
    
    if not filtered_df.empty:
        # 1. Growth
        norm_growth = utils.normalize(filtered_df['Dynamics_YoY'])
        
        # 2. Profitability (Mix of Share of Profitable Entities and Net Margin)
        # Net Margin can be negative. Normalize carefully.
        norm_margin = utils.normalize(filtered_df['Net_Profit_Margin'])
        norm_prof_share = utils.normalize(filtered_df['Profitability'])
        norm_profitability = (norm_margin + norm_prof_share) / 2
        
        # 3. Safety
        # Cash Ratio -> Maximize
        norm_cash = utils.normalize(filtered_df['Cash_Ratio'])
        
        # Debt Ratio -> Minimize (1 - Norm)
        norm_debt = 1 - utils.normalize(filtered_df['Debt_to_Revenue'])
        
        # Risk -> Minimize (1 - Norm)
        norm_risk = 1 - utils.normalize(filtered_df['Bankruptcy_Rate']) # or Risk_Per_1000
        
        norm_safety = (norm_cash + norm_debt + norm_risk) / 3
        
        # Weighted Sum
        total_weight = w_growth + w_profit + w_safety
        if total_weight == 0: total_weight = 1 # Avoid div/0
        
        filtered_df['Stability_Score'] = (
            (w_growth * norm_growth) + 
            (w_profit * norm_profitability) + 
            (w_safety * norm_safety)
        ) / total_weight * 100
        
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
    st.markdown("### 🛡️ Radar Ryzyka: Upadłość vs Dynamika")
    st.markdown("""
    **Oś X: Stability Score (Kondycja Finansowa 2.0)**
    *Mierzy bezpieczeństwo bankowe branży.*
    Składowe: Zyskowność (40%) + Dynamika Wzrostu (30%) + Bezpieczeństwo Długu (15%) + Płynność (15%).
    
    **Oś Y: Transformation Index (Inwestycje + Innowacje)**
    *Mierzy potencjał przyszłościowy branży.*
    Hybrydowa ocena: 50% Intensywność Inwestycyjna (Capex) + 50% Innovation Index (ArXiv).
    Pokazuje, kto wydaje pieniądze (Inwestycje) i kto ma zaplecze badawcze.

    **Wielkość Bąbelka:** Przychody ogółem branży.
    **Kolor:** Status (CRITICAL = Wysokie Ryzyko Upadłości).
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


# --- CHART (LEFT) ---
with col_main:
    # Calculate max revenue for global scaling
    max_rev_global = df_all['Revenue'].max()
    
    fig = charts.create_main_bubble_chart(filtered_df, max_rev_global)

    # Display Chart
    st.plotly_chart(fig, use_container_width=True, key="bubble_chart", on_select="rerun", selection_mode="points")


# --- DETAILS (RIGHT + BOTTOM) ---
with col_details:
    st.subheader("AI Boardroom")
    
    # Check if a point is selected
    # Check if a point is selected
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
        # Extract Section Letter from "F - BUDOWNICTWO"
        try:
            sec_letter = selected_sector.split(' - ')[0] # "F"
            target_pkd = f"SEK_{sec_letter}"
            
            # Find row for this Section (global lookup or filtered)
            # We want the attributes of the Section itself.
            # Usually 'filtered_df' might only contain children if level is drilled, 
            # BUT if level is L1 (Sekcje), it's there. 
            # If level is L2, the Section row is filtered out.
            # So we look at 'df_all' for the Section row details.
            
            sec_row_df = df_all[(df_all['PKD_Code'] == target_pkd) & (df_all['Year'] == selected_year)]
            if not sec_row_df.empty:
                selected_row = sec_row_df.iloc[0]
                selected_pkd = target_pkd
        except:
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
            st.markdown(f"""
            <div class="verdict-box">WERDYKT: {debate.get('Final_Verdict','')}</div>
            <div style="background-color: #f1c40f; padding: 5px; border-radius: 5px; margin-top: 5px; text-align: center; color: black; font-weight: bold;">
                BANK: {debate.get('Credit_Recommendation', 'DECISION_PENDING')}
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
    with col_hist:
        st.caption(f"Historia i Prognoza (2019-2026): {current_selection_pkd}")
        
        # Get full history including forecast
        hist_df = df_all[df_all['PKD_Code'] == current_selection_pkd].sort_values('Year')
        
        if not hist_df.empty:
            fig_h = go.Figure()
            
            # Split Data
            is_forecast_col = 'Is_Forecast' in hist_df.columns
            
            if is_forecast_col:
                real_df = hist_df[hist_df['Is_Forecast'] == False]
                forecast_df = hist_df[hist_df['Is_Forecast'] == True]
                
                # Add last real point to forecast to bridge the gap
                if not real_df.empty and not forecast_df.empty:
                    last_real = real_df.iloc[[-1]]
                    forecast_plot = pd.concat([last_real, forecast_df])
                else:
                    forecast_plot = forecast_df
            else:
                real_df = hist_df
                forecast_plot = pd.DataFrame()
                
            # Plot Real
            fig_h.add_trace(go.Scatter(
                x=real_df['Year'], 
                y=real_df['Revenue'], 
                name='Przychody (Historia)', 
                line=dict(color='#3498db', width=3)
            ))
            
            # Plot Forecast
            if not forecast_plot.empty:
                fig_h.add_trace(go.Scatter(
                    x=forecast_plot['Year'], 
                    y=forecast_plot['Revenue'], 
                    name='Prognoza (2025-26)', 
                    line=dict(color='#f1c40f', width=3, dash='dot')
                ))

            fig_h.update_layout(
                height=300, 
                margin=dict(l=0,r=0,t=20,b=0), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font=dict(color='white'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_h, use_container_width=True, key=f"hist_{level_depth}_{current_selection_pkd}")
            
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

