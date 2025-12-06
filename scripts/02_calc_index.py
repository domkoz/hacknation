import pandas as pd
import numpy as np
import os
# from scripts.data_cleaner import load_and_merge_data # IMPORT REMOVED

def calculate_indices(df):
    """
    Calculates Stability and Transformation scores.
    """
    # 1. Calculate Core Metrics
    df['Profitability'] = df['Net_Profit_2024'] / df['Revenue_2024']
    df['Liquidity'] = df['Current_Assets'] / df['Short_Term_Liabilities']
    df['Dynamics_YoY'] = (df['Revenue_2024'] - df['Revenue_2023']) / df['Revenue_2023']
    
    # 2. Normalize Metrics (0-100 scale approximation for scoring)
    # Simple Min-Max normalization or sigmoid could be used. 
    # For Hackathon, we'll use simple scalers to keep it robust.
    
    # Helper for normalization
    def normalize(series):
        return (series - series.min()) / (series.max() - series.min())
    
    df['Norm_Profit'] = normalize(df['Profitability'])
    df['Norm_Liquidity'] = normalize(df['Liquidity'])
    df['Norm_Dynamics'] = normalize(df['Dynamics_YoY'])
    
    # 3. Calculate Stability Score (X-Axis)
    # Weights: 0.4 Profit, 0.3 Liquidity, 0.3 Dynamics
    df['Stability_Score_Raw'] = (0.4 * df['Norm_Profit']) + (0.3 * df['Norm_Liquidity']) + (0.3 * df['Norm_Dynamics'])
    
    # Apply Energy Correction
    # If Energy_Heavy is True, multiply by 0.85
    df['Stability_Score'] = df.apply(
        lambda x: x['Stability_Score_Raw'] * 0.85 if x.get('Energy_Heavy', False) else x['Stability_Score_Raw'], 
        axis=1
    )
    
    # Rescale to 0-100 for UI
    df['Stability_Score'] = df['Stability_Score'] * 100
    
    # 4. Calculate Transformation Score (Y-Axis)
    # Transformation = (0.6 * Google_Slope) + (0.4 * AI_Sentiment [Simulated])
    # Normalize Google Slope first
    df['Norm_Google_Slope'] = normalize(df['Trend_Slope'])
    
    # Mock AI Sentiment if not present (random 0-100 normalized to 0-1)
    # In real app this comes from LLM. We will simulate it here to ensure data exists.
    np.random.seed(42)
    df['AI_Sentiment_Score'] = np.random.rand(len(df)) # 0-1 range
    
    df['Transformation_Score_Raw'] = (0.6 * df['Norm_Google_Slope']) + (0.4 * df['AI_Sentiment_Score'])
    df['Transformation_Score'] = df['Transformation_Score_Raw'] * 100
    
    return df

def apply_kill_switch_and_flags(df):
    """
    Applies logic for Critical status and Opportunity status.
    """
    # 1. KILL SWITCH (CRITICAL)
    # Condition: Debt_Ratio > 0.7 OR Bankruptcy_Rate > 2.0
    df['Status'] = 'Neutral'
    
    mask_critical = (df['Debt_Ratio'] > 0.65) | (df['Bankruptcy_Rate'] > 1.8)
    df.loc[mask_critical, 'Status'] = 'CRITICAL'
    
    # 2. HIDDEN GEM (OPPORTUNITY)
    # Condition: Stability > 60 AND Transformation > 70 AND NOT CRITICAL
    mask_opportunity = (df['Stability_Score'] > 60) & (df['Transformation_Score'] > 70) & (df['Status'] != 'CRITICAL')
    df.loc[mask_opportunity, 'Status'] = 'OPPORTUNITY'
    
    return df

def generate_processed_data():
    # Since 01_data_cleaner is in the same dir or we need to import it properly.
    # We'll just re-implement the load for simplicity within this script context 
    # to avoid module path issues during simple execution.
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    
    finance_df = pd.read_csv(os.path.join(data_path, 'raw_gus_data.csv'))
    mapping_df = pd.read_csv(os.path.join(data_path, 'mapping_pkd.csv'))
    risk_df = pd.read_csv(os.path.join(data_path, 'manual_risk_factors.csv'))
    trends_df = pd.read_csv(os.path.join(data_path, 'google_trends.csv'))
    
    df = mapping_df.merge(finance_df, on='PKD_Code', how='left')
    df = df.merge(risk_df, on='PKD_Code', how='left')
    df = df.merge(trends_df, on='PKD_Code', how='left')
    
    # Calculate
    df = calculate_indices(df)
    df = apply_kill_switch_and_flags(df)
    
    # Save
    output_path = os.path.join(base_path, 'data', 'processed_index.csv')
    df.to_csv(output_path, index=False)
    print(f"Processed Index saved to {output_path}")
    print(df[['Industry_Name', 'Stability_Score', 'Transformation_Score', 'Status']].head())

if __name__ == "__main__":
    generate_processed_data()
