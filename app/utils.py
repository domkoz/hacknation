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
