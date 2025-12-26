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
    if "category :" in df.columns:
        cats = df["category :"].dropna().unique()
        print("Categories found:")
        for c in cats:
            print(f"- {c}")
    else:
        print("Column 'category :' not found.")
