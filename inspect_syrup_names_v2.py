import pandas as pd
import re

def load_data():
    try:
        sheet_id = "1mKcRWrkCMHXOpofdjU1MrwRmhUGaaET8RUOG6eyHAqA"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        stock = pd.read_excel(url)
        return stock
    except Exception as e:
        print(f"Error: {e}")
        return None

df = load_data()
if df is not None:
    df.columns = df.columns.str.lower().str.strip()
    
    # Filter for Syrup
    if "category :" in df.columns:
        syrups = df[df["category :"].astype(str).str.contains("SYRUP", case=False, na=False)]
        
        print("\nFound Syrups in Inventory:")
        # Check unique Item Names
        unique_syrups = syrups["item name :"].unique()
        for s in unique_syrups:
            print(f"- {s}")
            
    else:
        print("Category column not found")
