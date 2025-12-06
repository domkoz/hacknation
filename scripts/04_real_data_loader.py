import pandas as pd
import os
import numpy as np

def clean_currency_string(x):
    """Cleans strings like '1 679 774,30' to float."""
    if pd.isna(x) or x == 'bd':
        return np.nan
    if isinstance(x, str):
        # Remove non-breaking spaces and regular spaces
        x = x.replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        return float(x)
    except ValueError:
        return np.nan

def load_and_process_real_data():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_path, 'data')
    organizer_dir = os.path.join(data_dir, 'data_from_organizer')
    
    # Paths
    wsk_fin_path = os.path.join(organizer_dir, 'wsk_fin.csv')
    krz_path = os.path.join(organizer_dir, 'krz_pkd.csv')
    
    print("Loading Financial Data...")
    # 1. Load Financial Data
    # CSV is semicolon separated, might have encoding issues, let's try reading header first
    df_fin = pd.read_csv(wsk_fin_path, sep=';', on_bad_lines='skip')
    
    # Filter for relevant indicators
    # Indicators: 
    # 'GS Przychody ogółem' -> Revenue
    # 'PEN Liczba rentownych jednostek gospodarczych' -> Profitable Count
    # 'EN Liczba jednostek gospodarczych' -> Entity Count
    
    indicators_map = {
        'GS Przychody ogółem ': 'Revenue',
        'PEN Liczba rentownych jednostek gospodarczych ': 'Profitable_Ent',
        'EN Liczba jednostek gospodarczych ': 'Entity_Count',
        'NP Wynik finansowy netto (zysk netto) ': 'Net_Profit',
        'LTL Zobowiązania długoterminowe ': 'Liabilities_Long',
        'STL Zobowiązania krótkoterminowe ': 'Liabilities_Short'
    }
    
    df_fin = df_fin[df_fin['WSKAZNIK'].isin(indicators_map.keys())].copy()
    
    # Melt years
    # Columns are PKD;NAZWA_PKD;NUMER_NAZWA_PKD;WSKAZNIK;2005;...;2024
    id_vars = ['PKD', 'NAZWA_PKD', 'NUMER_NAZWA_PKD', 'WSKAZNIK']
    value_vars = [str(y) for y in range(2005, 2025)]
    
    # Check if columns exist (sometimes header might have spaces)
    existing_years = [c for c in value_vars if c in df_fin.columns]
    
    df_melt = df_fin.melt(id_vars=id_vars, value_vars=existing_years, var_name='Year', value_name='Value')
    
    # Clean Values
    df_melt['Value'] = df_melt['Value'].apply(clean_currency_string)
    df_melt['Year'] = df_melt['Year'].astype(int)
    
    # Pivot to get indicators as columns
    df_pivot = df_melt.pivot_table(
        index=['PKD', 'NAZWA_PKD', 'Year'], 
        columns='WSKAZNIK', 
        values='Value', 
        aggfunc='first'
    ).reset_index()
    
    # Rename columns using map (handling potential whitespace in keys)
    df_pivot.columns = [indicators_map.get(c, c) for c in df_pivot.columns]
    
    # 2. Load Bankruptcy Data
    print("Loading Bankruptcy Data...")
    df_krz = pd.read_csv(krz_path, sep=';')
    # Header: rok;pkd;liczba_upadlosci
    df_krz.columns = ['Year', 'PKD', 'Bankruptcy_Count']
    
    # Clean Year and PKD
    df_krz['Year'] = pd.to_numeric(df_krz['Year'], errors='coerce')
    df_krz = df_krz.dropna(subset=['Year'])
    df_krz['Year'] = df_krz['Year'].astype(int)
    
    # Merge
    print("Merging Datasets...")
    df_merged = pd.merge(df_pivot, df_krz, on=['PKD', 'Year'], how='left')
    df_merged['Bankruptcy_Count'] = df_merged['Bankruptcy_Count'].fillna(0)
    
    # 3. Calculate Derived Metrics
    
    # Profitability %
    df_merged['Profitability'] = df_merged['Profitable_Ent'] / df_merged['Entity_Count']
    
    # Bankruptcy Rate %
    df_merged['Bankruptcy_Rate'] = (df_merged['Bankruptcy_Count'] / df_merged['Entity_Count']) * 100
    
    # Fill Nans (Critical for sums)
    df_merged['Revenue'] = df_merged['Revenue'].fillna(0)
    df_merged['Net_Profit'] = df_merged['Net_Profit'].fillna(0)
    df_merged['Liabilities_Long'] = df_merged['Liabilities_Long'].fillna(0)
    df_merged['Liabilities_Short'] = df_merged['Liabilities_Short'].fillna(0)
    
    # Calculate Total Debt
    df_merged['Total_Debt'] = df_merged['Liabilities_Long'] + df_merged['Liabilities_Short']

    # YoY Dynamics
    df_merged.sort_values(['PKD', 'Year'], inplace=True)
    df_merged['Revenue_Prev_Year'] = df_merged.groupby('PKD')['Revenue'].shift(1)
    df_merged['Dynamics_YoY'] = (df_merged['Revenue'] - df_merged['Revenue_Prev_Year']) / df_merged['Revenue_Prev_Year']
    
    # 4. Filter and Final Polish
    # Filter out empty sectors or years with bad data
    df_merged = df_merged.dropna(subset=['Revenue', 'Entity_Count'])
    
    # Map to project column names for compatibility
    # Project expects: 'PKD_Code', 'Industry_Name', 'Revenue_2024', 'Profitability', 'Dynamics_YoY' ...
    # Since we have time series, we'll keep 'Year' and just rename base cols.
    
    df_merged.rename(columns={
        'PKD': 'PKD_Code',
        'NAZWA_PKD': 'Industry_Name',
        'Revenue': 'Revenue'
    }, inplace=True)
    
    # Fill Nans
    df_merged['Dynamics_YoY'] = df_merged['Dynamics_YoY'].fillna(0)
    df_merged['Profitability'] = df_merged['Profitability'].fillna(0)
    df_merged['Total_Debt'] = df_merged['Total_Debt'].fillna(0)
    df_merged['Net_Profit'] = df_merged['Net_Profit'].fillna(0)
    
    # Add Sector (Optional - could try to map from first 1-2 digits of PKD if map file allows, or ignore)
    # For now, let's categorize purely by PKD Number if no mapping
    # A=01-03, C=10-33 etc. We can use a simple generic mapper or just leave it.
    df_merged['Sector'] = 'Ogólny' 
    
    # --- CALCULATE S&T SCORE (Backwards Compatible Logic) ---
    # Normalizing (Per Year to keep relative scale correct!)
    
    def calculate_scores(group):
        # Simple Min-Max scaler within the year
        def norm(s):
            if s.max() == s.min(): return 0
            return (s - s.min()) / (s.max() - s.min())
        
        group['Norm_Profit'] = norm(group['Profitability'])
        group['Norm_Dynamics'] = norm(group['Dynamics_YoY'])
        
        # Stability = (0.6 * Profit) + (0.4 * Dynamics) - simpler formula for real data
        group['Stability_Score'] = ((0.6 * group['Norm_Profit']) + (0.4 * group['Norm_Dynamics'])) * 100
        
        return group

    df_processed = df_merged.groupby('Year').apply(calculate_scores).reset_index(drop=True)
    
    # Transformation Score ?
    # We don't have real Google Trends for all these PKDs.
    # Strategy: Use Dynamics as a proxy for "Growth Potential" OR Mock it again for missing data.
    # Let's reuse Dynamics for Transformation heavily + Random factor to simulate "AI Hype"
    np.random.seed(42)
    df_processed['AI_Hype_Mock'] = np.random.rand(len(df_processed))
    
    # Transformation = (0.7 * Norm_Dynamics) + (0.3 * AI_Hype)
    df_processed['Transformation_Score'] = ((0.7 * df_processed['Norm_Dynamics']) + (0.3 * df_processed['AI_Hype_Mock'])) * 100
    
    # Status Logic
    def get_status(row):
        if row['Bankruptcy_Rate'] > 1.5: # Threshold 1.5% likely high
            return 'CRITICAL'
        if row['Płynność'] if 'Płynność' in row else 0: # We don't have liquidity, skip
            pass
        if row['Stability_Score'] > 60 and row['Transformation_Score'] > 60:
            return 'OPPORTUNITY'
        return 'Neutral'

    df_processed['Status'] = df_processed.apply(get_status, axis=1)

    # Save
    output_path = os.path.join(data_dir, 'processed_real_index.csv')
    df_processed.to_csv(output_path, index=False)
    print(f"Processed Real Index saved to {output_path}. Shape: {df_processed.shape}")
    print(df_processed[['Year', 'PKD_Code', 'Industry_Name', 'Revenue', 'Status']].tail())

if __name__ == "__main__":
    load_and_process_real_data()
