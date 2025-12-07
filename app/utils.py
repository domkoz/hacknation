import streamlit as st
import pandas as pd
import os
import json

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Adjust path to find data relative to this file
    # this file is in app/utils.py, so data is in ../data
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    processed_path = os.path.join(data_path, 'processed_real_index.csv')
    df = pd.read_csv(processed_path)
    
    # Filter out "Dead Entities" / Outliers
    # Rows where both Revenue and Total_Debt are 0 (likely dormant or data errors)
    # This prevents crowding at (0,0) on charts.
    df = df[~((df['Revenue'] == 0) & (df['Total_Debt'] == 0))]
    
    return df

def load_debates():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(base_path, 'app', 'assets')
    json_path = os.path.join(assets_path, 'ai_debates.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def normalize(series):
    if series.max() == series.min():
        return pd.Series(0.5, index=series.index)
    return (series - series.min()) / (series.max() - series.min())

def color_val(val, inverse=False, is_percent=False):
    if pd.isna(val): return "-"
    
    # Define thresholds
    # Standard: High is Green. Inverse: Low is Green.
    color = "black"
    
    # Simple logic for now
    if inverse:
        if val < 0: color = "green"
        elif val > 0: color = "red"
    else:
        if val > 0: color = "green"
        elif val < 0: color = "red"
        
    fmt_val = f"{val:+.1f}%" if is_percent else f"{val:.2f}"
    return f'<span style="color:{color}">{fmt_val}</span>'

import numpy as np

def calculate_forecast(df_history, target_col, years_ahead=2):
    """
    Calculates linear forecast for the next 'years_ahead' years.
    Returns a DataFrame with historical + forecast rows.
    """
    # 1. Prepare Data
    df = df_history.copy().sort_values('Year')
    
    # Ensure Is_Forecast exists (default to False if missing)
    if 'Is_Forecast' not in df.columns:
        df['Is_Forecast'] = False
    
    # Check if 'Is_Forecast' is string "True"/"False" and convert to bool if needed
    if df['Is_Forecast'].dtype == 'object':
        df['Is_Forecast'] = df['Is_Forecast'].replace({'True': True, 'False': False})

    # 2. Identify Real Data vs Existing Forecast
    # We train ONLY on Real Data
    real_df = df[df['Is_Forecast'] == False].copy()
    
    # If no real data, return as is
    if len(real_df) < 2:
        return df

    # Prepare X (Years) and Y (Values)
    x = real_df['Year'].values
    y = real_df[target_col].values
    
    # Handle NaNs
    mask = ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return df
        
    # 3. Train Regression (Linear)
    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    
    # 4. Generate NEW Forecast
    # We base the start year on the LAST REAL YEAR, not the last row (which might be an old forecast)
    last_real_year = int(real_df['Year'].max())
    future_years = [last_real_year + i for i in range(1, years_ahead + 1)]
    
    forecast_rows = []
    for yr in future_years:
        val = slope * yr + intercept
        row = {
            'Year': yr,
            target_col: val,
            'Is_Forecast': True,
            'PKD_Code': real_df['PKD_Code'].iloc[0],
            'Industry_Name': real_df['Industry_Name'].iloc[0]
        }
        forecast_rows.append(row)
    
    new_forecast_df = pd.DataFrame(forecast_rows)
    
    # 5. Return Real Data + New Forecast
    # We discard old forecasts from the input to avoid duplication/confusion
    return pd.concat([real_df, new_forecast_df], ignore_index=True)

def recalculate_future_st_scores(df_full, w_growth=4.0, w_profit=6.0, w_safety=3.0):
    """
    Recalculates Stability and Transformation scores for Forecast years.
    Uses normalization bounds from the LAST REAL YEAR (2024) to ensure comparability.
    Assumes df_full contains both history and forecast rows.
    """
    df = df_full.copy()
    
    # Identify Real vs Forecast
    if 'Is_Forecast' not in df.columns: return df
    
    # We need reference bounds (min/max) from REAL DATA (e.g. 2024 context)
    # Ideally, we should normalize against the whole market in that year, but for a single-industry forecast,
    # we can use the industry's own historical range OR assuming standard 0-1 scaling if variables are ratios.
    # BETTER APPROACH: Use pre-calculated columns if available? No, forecast rows miss them.
    # WE WILL USE ABSOLUTE SCORING RULES for Forecasts to be safe.
    
    # Define Weights (Passed as arguments)
    # Default values match default slider values

    
    # Transformation
    w_capex = 50
    w_innov = 50
    
    # Helper to clamp/normalize single value against a fixed range (approximate market bounds)
    def norm(val, min_v, max_v):
        if pd.isna(val): return 0.5
        if max_v == min_v: return 0.5
        return np.clip((val - min_v) / (max_v - min_v), 0, 1)

    # Market Bounds Assumptions (Based on typical data ranges seen in dashboard)
    # These effectively act as "Standard" benchmarks
    bounds = {
        'Dynamics_YoY': (-0.10, 0.20),    # -10% to +20% (More sensitive to moderate growth)
        'Net_Profit_Margin': (-5.0, 20.0), # -5% to 20% margin
        'Profitability': (0.4, 1.0),       # 40% to 100% profitable entities (Relaxed floor)
        'Cash_Ratio': (0.0, 1.2),          # 0 to 1.2 coverage (Relaxed max)
        'Debt_to_Revenue': (0.0, 4.0),     # 0 to 4x leverage
        'Bankruptcy_Rate': (0.0, 4.0),     # 0% to 4% failure rate
        'Capex_Intensity': (0.0, 0.15),    # 0% to 15% revenue reinvested
        'Arxiv_Papers': (0, 5000)          # 0 to 5000 papers (Increased for 2025+ context)
    }
    
    # Apply calculation row by row
    def calculate_row_score(row):
        # STABILITY COMPONENTS
        # 1. Growth
        n_growth = norm(row.get('Dynamics_YoY', 0), *bounds['Dynamics_YoY'])
        
        # 2. Profitability
        n_margin = norm(row.get('Net_Profit_Margin', 0), *bounds['Net_Profit_Margin'])
        # If Profitability % is missing (often hard to forecast), assume high if margin is high
        n_prof_share = norm(row.get('Profitability', 0), *bounds['Profitability']) 
        n_profitability = (n_margin + n_prof_share) / 2
        
        # 3. Safety
        n_cash = norm(row.get('Cash_Ratio', 0), *bounds['Cash_Ratio'])
        
        # Debt (Low is good)
        val_debt = row.get('Debt_to_Revenue', 0)
        n_debt = 1 - norm(val_debt, *bounds['Debt_to_Revenue'])
        
        # Risk (Low is good)
        val_risk = row.get('Bankruptcy_Rate', 0)
        n_risk = 1 - norm(val_risk, *bounds['Bankruptcy_Rate'])
        
        n_safety = (n_cash + n_debt + n_risk) / 3
        
        n_safety = (n_cash + n_debt + n_risk) / 3
        
        total_w = w_growth + w_profit + w_safety
        if total_w == 0: total_w = 1
        
        stab_score = (w_growth * n_growth + w_profit * n_profitability + w_safety * n_safety) / total_w * 100
        
        # TRANSFORMATION COMPONENTS
        n_capex = norm(row.get('Capex_Intensity', 0), *bounds['Capex_Intensity'])
        n_arxiv = norm(row.get('Arxiv_Papers', 0), *bounds['Arxiv_Papers'])
        
        # Weights are hardcoded 50/50 currently
        w_capex = 50
        w_innov = 50
        trans_score = (w_capex * n_capex + w_innov * n_arxiv) / (w_capex + w_innov) * 100
        
        return pd.Series([stab_score, trans_score])

    # Apply only to forecast rows to verify feasibility, but practically we want trend line
    # so we might recalculate ALL rows to keep trend consistent?
    # NO, main.py uses dynamic relative scoring for history.
    # Mixing relative (history) and absolute (forecast) might cause a "jump".
    # FIX: Recalculate ALL rows in this specific DF using these Absolute Bounds
    # This ensures the trend line is smooth and comparable self-consistently.
    
    scores = df.apply(calculate_row_score, axis=1)
    df['Stability_Score'] = scores[0]
    df['Transformation_Score'] = scores[1]
    
    return df
