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
