import pandas as pd
import os

def load_and_merge_data():
    """
    Loads raw CSV data and merges them into a single DataFrame.
    """
    # Define paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    
    # Load files
    finance_df = pd.read_csv(os.path.join(data_path, 'raw_gus_data.csv'))
    mapping_df = pd.read_csv(os.path.join(data_path, 'mapping_pkd.csv'))
    risk_df = pd.read_csv(os.path.join(data_path, 'manual_risk_factors.csv'))
    trends_df = pd.read_csv(os.path.join(data_path, 'google_trends.csv'))
    
    # Merge DataFrames
    # Start with Mapping to ensure we have names
    merged_df = mapping_df.merge(finance_df, on='PKD_Code', how='left')
    merged_df = merged_df.merge(risk_df, on='PKD_Code', how='left')
    merged_df = merged_df.merge(trends_df, on='PKD_Code', how='left')
    
    return merged_df

if __name__ == "__main__":
    df = load_and_merge_data()
    print("Data merged successfully. Preview:")
    print(df.head())
    
    # Save intermediate file for inspection if needed
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'merged_raw_data.csv')
    df.to_csv(output_path, index=False)
    print(f"Merged data saved to {output_path}")
