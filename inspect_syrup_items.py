import pandas as pd

def load_data():
    try:
        # Stock Take Sheet
        sheet_id = "1mKcRWrkCMHXOpofdjU1MrwRmhUGaaET8RUOG6eyHAqA"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        stock = pd.read_excel(url)
        return stock
    except Exception as e:
        print(f"Error loading Stock Data: {e}")
        return None

df = load_data()
if df is not None:
    df.columns = df.columns.str.lower().str.strip()
    if "item name :" in df.columns:
        syrups = df[df["item name :"].astype(str).str.contains("syrup", case=False, na=False)]
        if not syrups.empty:
            print("Found Syrups:")
            print(syrups[["item name :", "category :"]].drop_duplicates().to_string())
        else:
            print("No items with 'Syrup' found.")
    else:
        print("Column 'item name :' not found.")
