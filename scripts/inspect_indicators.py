import pandas as pd
import os

base_path = 'data/data_from_organizer/wsk_fin.csv'
try:
    df = pd.read_csv(base_path, sep=';', on_bad_lines='skip', encoding='utf-8')
    print("Columns:", df.columns)
    if 'WSKAZNIK' in df.columns:
        print("\nUnique Indicators:")
        for i in sorted(df['WSKAZNIK'].unique()):
            print(f"- {i}")
except Exception as e:
    print(e)
