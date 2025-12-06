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
        'STL Zobowiązania krótkoterminowe ': 'Liabilities_Short',
        'C Środki pieniężne i pap. wart. ': 'Cash',
        'IO Wartość nakładów inwestycyjnych ': 'Investment'
    }
    
    df_fin = df_fin[df_fin['WSKAZNIK'].isin(indicators_map.keys())].copy()
    
    # Melt years
    id_vars = ['PKD', 'NAZWA_PKD', 'NUMER_NAZWA_PKD', 'WSKAZNIK']
    value_vars = [str(y) for y in range(2005, 2025)]
    existing_years = [c for c in value_vars if c in df_fin.columns]
    
    df_melt = df_fin.melt(id_vars=id_vars, value_vars=existing_years, var_name='Year', value_name='Value')
    
    # Clean Values
    def clean_currency_string(x):
        if isinstance(x, str):
            x = x.replace(' ', '').replace('\xa0', '').replace(',', '.')
        try:
            return float(x)
        except:
            return np.nan
            
    df_melt['Value'] = df_melt['Value'].apply(clean_currency_string)
    df_melt['Year'] = df_melt['Year'].astype(int)
    
    # Pivot
    df_pivot = df_melt.pivot_table(
        index=['PKD', 'NAZWA_PKD', 'Year'], 
        columns='WSKAZNIK', 
        values='Value', 
        aggfunc='first'
    ).reset_index()

    # Rename columns
    df_pivot.columns = [indicators_map.get(c, c) for c in df_pivot.columns]
    
    # 2. Load Bankruptcy Data
    print("Loading Bankruptcy Data...")
    df_krz = pd.read_csv(krz_path, sep=';')
    df_krz.columns = ['Year', 'PKD', 'Bankruptcy_Count']
    df_krz['Year'] = pd.to_numeric(df_krz['Year'], errors='coerce')
    df_krz = df_krz.dropna(subset=['Year'])
    df_krz['Year'] = df_krz['Year'].astype(int)
    
    # --- ROBUST MERGE LOGIC ---
    df_krz['pkd_clean'] = df_krz['PKD'].astype(str).str.replace('Z', '').str.replace(' ', '').str.strip()
    df_pivot['pkd_clean'] = df_pivot['PKD'].astype(str).str.replace('.', '', regex=False).str.strip()
    
    risk_rows = []
    base_risk = df_krz.groupby(['Year', 'pkd_clean'])['Bankruptcy_Count'].sum().reset_index()
    
    base_risk['L2'] = base_risk['pkd_clean'].str[:2]
    base_risk['L3'] = base_risk['pkd_clean'].str[:3]
    base_risk['L4'] = base_risk['pkd_clean'].str[:4]
    
    g2 = base_risk.groupby(['Year', 'L2'])['Bankruptcy_Count'].sum().reset_index().rename(columns={'L2': 'pkd_match'})
    g3 = base_risk.groupby(['Year', 'L3'])['Bankruptcy_Count'].sum().reset_index().rename(columns={'L3': 'pkd_match'})
    g4 = base_risk.groupby(['Year', 'L4'])['Bankruptcy_Count'].sum().reset_index().rename(columns={'L4': 'pkd_match'})
    
    risk_lookup = pd.concat([g2, g3, g4]).drop_duplicates(subset=['Year', 'pkd_match'])
    
    # SECTION AGGREGATION
    section_map = {
        'SEK_A': ['01', '02', '03'],
        'SEK_B': ['05', '06', '07', '08', '09'],
        'SEK_C': [str(x) for x in range(10, 34)],
        'SEK_D': ['35'],
        'SEK_E': ['36', '37', '38', '39'],
        'SEK_F': ['41', '42', '43'],
        'SEK_G': ['45', '46', '47'],
        'SEK_H': ['49', '50', '51', '52', '53'],
        'SEK_I': ['55', '56'],
        'SEK_J': ['58', '59', '60', '61', '62', '63'],
        'SEK_K': ['64', '65', '66'],
        'SEK_L': ['68'],
        'SEK_M': [str(x) for x in range(69, 76)],
        'SEK_N': [str(x) for x in range(77, 83)],
        'SEK_O': ['84'],
        'SEK_P': ['85'],
        'SEK_Q': ['86', '87', '88'],
        'SEK_R': ['90', '91', '92', '93'],
        'SEK_S': ['94', '95', '96']
    }
    
    section_rows = []
    yearly_division_risk = base_risk.groupby(['Year', 'L2'])['Bankruptcy_Count'].sum().reset_index()
    
    for sek_code, divisions in section_map.items():
        divs = [str(d).zfill(2) for d in divisions]
        mask = yearly_division_risk['L2'].isin(divs)
        sek_data = yearly_division_risk[mask].groupby('Year')['Bankruptcy_Count'].sum().reset_index()
        sek_data['pkd_match'] = sek_code
        section_rows.append(sek_data)
        
    if section_rows:
        risk_lookup = pd.concat([risk_lookup, pd.concat(section_rows)])
    
    print("Merging Datasets...")
    df_merged = pd.merge(
        df_pivot, 
        risk_lookup, 
        left_on=['Year', 'pkd_clean'], 
        right_on=['Year', 'pkd_match'], 
        how='left'
    )
    df_merged['Bankruptcy_Count'] = df_merged['Bankruptcy_Count'].fillna(0)
    df_merged.drop(columns=['pkd_clean', 'pkd_match'], inplace=True, errors='ignore')

    # 3. Calculate Derived Metrics (Update)
    
    # Fill Nans
    # Keep columns that exist
    for col in ['Revenue', 'Net_Profit', 'Liabilities_Long', 'Liabilities_Short', 'Cash', 'Investment']:
        if col in df_merged.columns:
             df_merged[col] = df_merged[col].fillna(0)
             
    # Fill Nans (Specific)
    df_merged['Revenue'] = df_merged.get('Revenue', pd.Series(0, index=df_merged.index)).fillna(0)
    df_merged['Investment'] = df_merged.get('Investment', pd.Series(0, index=df_merged.index)).fillna(0)
    
    # Calculate Total Debt
    df_merged['Total_Debt'] = df_merged['Liabilities_Long'] + df_merged['Liabilities_Short']

    # 1. Capex Intensity (Investment / Revenue)
    df_merged['Capex_Intensity'] = df_merged.apply(lambda x: (x['Investment'] / x['Revenue'] * 100) if x['Revenue'] != 0 else 0, axis=1)


    # 1. Net Profit Margin (%)
    df_merged['Net_Profit_Margin'] = df_merged.apply(lambda x: (x['Net_Profit'] / x['Revenue'] * 100) if x['Revenue'] != 0 else 0, axis=1)

    # 2. Debt Burden Ratio (Debt/Revenue)
    df_merged['Debt_to_Revenue'] = df_merged.apply(lambda x: (x['Total_Debt'] / x['Revenue']) if x['Revenue'] != 0 else 0, axis=1)

    # 3. Cash Ratio (Cash/ShortTermLiabilities)
    df_merged['Cash_Ratio'] = df_merged.apply(lambda x: (x['Cash'] / x['Liabilities_Short']) if x['Liabilities_Short'] != 0 else 0, axis=1)

    # 5. Relative Risk Ratio (Bankruptcies per 1000 entities)
    df_merged['Risk_Per_1000'] = df_merged.apply(lambda x: (x['Bankruptcy_Count'] / x['Entity_Count'] * 1000) if x['Entity_Count'] != 0 else 0, axis=1)

    # Profitability %
    df_merged['Profitability'] = df_merged['Profitable_Ent'] / df_merged['Entity_Count']
    
    # Bankruptcy Rate %
    df_merged['Bankruptcy_Rate'] = (df_merged['Bankruptcy_Count'] / df_merged['Entity_Count']) * 100
    
    # YoY Dynamics
    df_merged.sort_values(['PKD', 'Year'], inplace=True)
    df_merged['Revenue_Prev_Year'] = df_merged.groupby('PKD')['Revenue'].shift(1)
    df_merged['Dynamics_YoY'] = (df_merged['Revenue'] - df_merged['Revenue_Prev_Year']) / df_merged['Revenue_Prev_Year']
    
    # Filter out empty sectors or years with bad data
    df_merged = df_merged.dropna(subset=['Revenue', 'Entity_Count'])
    
    # Normalize Rename
    df_merged.rename(columns={
        'PKD': 'PKD_Code',
        'NAZWA_PKD': 'Industry_Name'
    }, inplace=True)
    
    # Fill Nans
    for col in ['Dynamics_YoY', 'Profitability', 'Total_Debt', 'Net_Profit', 'Cash', 'Net_Profit_Margin', 'Debt_to_Revenue', 'Cash_Ratio', 'Risk_Per_1000', 'Bankruptcy_Rate']:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(0)

    # --- MERGE ARXIV HYPE DATA ---
    import json
    arxiv_path = 'data/arxiv_hype.json'
    arxiv_map = {}
    if os.path.exists(arxiv_path):
        with open(arxiv_path, 'r') as f:
            arxiv_map = json.load(f)
            
    # Helper to map PKD to Section Code for ArXiv
    # We already define section_map in this script! Let's reuse the reverse mapping.
    # section_map: 'SEK_A': ['01', '02', '03']
    pkd_to_section = {}
    for sek, divs in section_map.items():
        for d in divs:
            pkd_to_section[d] = sek
            
    def get_arxiv_score(pkd_code):
        code_str = str(pkd_code).strip()
        # Direct match for Section codes (SEK_A etc.)
        if code_str in arxiv_map:
            return arxiv_map[code_str]
            
        # Extract first 2 digits for Sub-sectors
        prefix = code_str.replace('.', '').strip()[:2]
        if prefix in pkd_to_section:
            sek = pkd_to_section[prefix]
            return arxiv_map.get(sek, 0)
        return 0

    df_merged['Arxiv_Papers'] = df_merged['PKD_Code'].apply(get_arxiv_score)

    # --- CALCULATE S&T SCORE ---
    def calculate_scores(group):
        def norm(s):
            if s.max() == s.min(): return pd.Series(0.5, index=s.index)
            return (s - s.min()) / (s.max() - s.min())
        
        group['Norm_Profit'] = norm(group['Profitability'])
        group['Norm_Dynamics'] = norm(group['Dynamics_YoY'])
        
        # Stability (Static)
        group['Stability_Score'] = ((0.6 * group['Norm_Profit']) + (0.4 * group['Norm_Dynamics'])) * 100
        
        # TRANSFORMATION SCORE (HYBRID: CAPEX + ARXIV)
        group['Norm_Capex'] = norm(group['Capex_Intensity'])
        group['Norm_Arxiv'] = norm(group['Arxiv_Papers'])
        
        # 50% Money (Capex), 50% Science (ArXiv)
        group['Transformation_Score'] = ((0.5 * group['Norm_Capex']) + (0.5 * group['Norm_Arxiv'])) * 100
        
        return group

    df_processed = df_merged.groupby('Year').apply(calculate_scores).reset_index(drop=True)
    
    # Remove Mock Override logic

    
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
