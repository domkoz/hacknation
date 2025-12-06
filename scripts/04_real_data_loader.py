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
        'C Środki pieniężne i pap. wart. ': 'Cash'
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
    print("Merging Datasets with PKD Normalization...")
    # df_merged = pd.merge(df_pivot, df_krz, on=['PKD', 'Year'], how='left')
    
    # --- ROBUST MERGE LOGIC ---
    # 1. Clean KRZ PKD codes
    # Remove 'Z', spaces. e.g. "4120Z" -> "4120"
    df_krz['pkd_clean'] = df_krz['PKD'].astype(str).str.replace('Z', '').str.replace(' ', '').str.strip()
    
    # 2. Clean Financial PKD codes
    # Remove dots. e.g. "41." -> "41", "41.2" -> "412", "01.11" -> "0111"
    df_pivot['pkd_clean'] = df_pivot['PKD'].astype(str).str.replace('.', '', regex=False).str.strip()
    
    # 3. Create Aggregations for KRZ (Risk) at L2, L3, L4 levels
    # Aggregation dictionaries by Year and PKD prefix
    
    # We need a function to map a financial row to a bankruptcy count
    # Strategy:
    # - If Fin row is L2 (len 2, e.g. "41"), sum all KRZ starting with "41"
    # - If Fin row is L3 (len 3, e.g. "412"), sum all KRZ starting with "412"
    # - If Fin row is L4 (len 4), sum all KRZ starting with "4120"
    
    # Ideally, we pre-calculate these groups to avoid O(N*M).
    
    # Group KRZ by Year and Full 4-digit (or max available)
    # Actually, simpler: Explode KRZ to L2, L3, L4 keys? 
    # Or just iterate? No, dataframe merge is faster.
    
    # Let's create a "Risk Lookup" DataFrame that contains counts for ALL potential prefixes.
    risk_rows = []
    
    # Group by Year + pkd_clean first to dedup/sum if multiple entries
    base_risk = df_krz.groupby(['Year', 'pkd_clean'])['Bankruptcy_Count'].sum().reset_index()
    
    # Now generate L2, L3, L4 sums
    # Get all unique years
    years = base_risk['Year'].unique()
    
    # Optimize:
    # Expand base_risk to include truncated versions
    base_risk['L2'] = base_risk['pkd_clean'].str[:2]
    base_risk['L3'] = base_risk['pkd_clean'].str[:3]
    base_risk['L4'] = base_risk['pkd_clean'].str[:4]
    
    # Group by L2
    g2 = base_risk.groupby(['Year', 'L2'])['Bankruptcy_Count'].sum().reset_index().rename(columns={'L2': 'pkd_match'})
    # Group by L3
    g3 = base_risk.groupby(['Year', 'L3'])['Bankruptcy_Count'].sum().reset_index().rename(columns={'L3': 'pkd_match'})
    # Group by L4
    g4 = base_risk.groupby(['Year', 'L4'])['Bankruptcy_Count'].sum().reset_index().rename(columns={'L4': 'pkd_match'})
    
    # Concatenate all potential matches
    risk_lookup = pd.concat([g2, g3, g4]).drop_duplicates(subset=['Year', 'pkd_match'])
    
    # --- ADD SECTION AGGREGATION ---
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
    
    # Generate explicit SEK_ rows for risk lookup
    section_rows = []
    
    # We need to aggregate from base_risk (which has L2 computed as 'L2' col)
    # We must be careful not to double count if we just sum?
    # base_risk has 'pkd_clean' (full granular). We should sum from base_risk based on prefix.
    
    # Optimization: base_risk's 'L2' column is perfect for this.
    # Group base_risk by Year and L2 first to get Division totals.
    yearly_division_risk = base_risk.groupby(['Year', 'L2'])['Bankruptcy_Count'].sum().reset_index()
    
    for sek_code, divisions in section_map.items():
        # Clean divisions list (ensure 2 digits string)
        divs = [str(d).zfill(2) for d in divisions]
        
        # Filter rows where L2 is in divs
        mask = yearly_division_risk['L2'].isin(divs)
        sek_data = yearly_division_risk[mask].groupby('Year')['Bankruptcy_Count'].sum().reset_index()
        sek_data['pkd_match'] = sek_code # Key for join
        section_rows.append(sek_data)
        
    if section_rows:
        risk_sections = pd.concat(section_rows)
        # Add to lookup
        risk_lookup = pd.concat([risk_lookup, risk_sections])
    
    # 4. Merge
    df_merged = pd.merge(
        df_pivot, 
        risk_lookup, 
        left_on=['Year', 'pkd_clean'], 
        right_on=['Year', 'pkd_match'], 
        how='left'
    )
    
    # Fill NAs
    df_merged['Bankruptcy_Count'] = df_merged['Bankruptcy_Count'].fillna(0)
    
    # Drop temp cols
    df_merged.drop(columns=['pkd_clean', 'pkd_match'], inplace=True, errors='ignore')

    
    # 3. Calculate Derived Metrics
    
    # Fill Nans (Critical for sums)
    df_merged['Revenue'] = df_merged['Revenue'].fillna(0)
    df_merged['Net_Profit'] = df_merged['Net_Profit'].fillna(0)
    df_merged['Liabilities_Long'] = df_merged['Liabilities_Long'].fillna(0)
    df_merged['Liabilities_Short'] = df_merged['Liabilities_Short'].fillna(0)
    df_merged['Cash'] = df_merged['Cash'].fillna(0)
    
    # Calculate Total Debt
    df_merged['Total_Debt'] = df_merged['Liabilities_Long'] + df_merged['Liabilities_Short']

    # 1. Net Profit Margin (%)
    # Avoid division by zero
    df_merged['Net_Profit_Margin'] = df_merged.apply(lambda x: (x['Net_Profit'] / x['Revenue'] * 100) if x['Revenue'] != 0 else 0, axis=1)

    # 2. Debt Burden Ratio (Debt/Revenue)
    df_merged['Debt_to_Revenue'] = df_merged.apply(lambda x: (x['Total_Debt'] / x['Revenue']) if x['Revenue'] != 0 else 0, axis=1)

    # 3. Cash Ratio (Cash/ShortTermLiabilities)
    df_merged['Cash_Ratio'] = df_merged.apply(lambda x: (x['Cash'] / x['Liabilities_Short']) if x['Liabilities_Short'] != 0 else 0, axis=1)

    # 5. Relative Risk Ratio (Bankruptcies per 1000 entities)
    df_merged['Risk_Per_1000'] = df_merged.apply(lambda x: (x['Bankruptcy_Count'] / x['Entity_Count'] * 1000) if x['Entity_Count'] != 0 else 0, axis=1)

    # Profitability % (Share of profitable entities - existing metric, keeping it)
    df_merged['Profitability'] = df_merged['Profitable_Ent'] / df_merged['Entity_Count']
    
    # Bankruptcy Rate % (for backward compatibility)
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
    df_merged['Cash'] = df_merged['Cash'].fillna(0)
    df_merged['Net_Profit_Margin'] = df_merged['Net_Profit_Margin'].fillna(0)
    df_merged['Debt_to_Revenue'] = df_merged['Debt_to_Revenue'].fillna(0)
    df_merged['Cash_Ratio'] = df_merged['Cash_Ratio'].fillna(0)
    df_merged['Risk_Per_1000'] = df_merged['Risk_Per_1000'].fillna(0)
    
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
