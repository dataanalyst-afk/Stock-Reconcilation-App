import pandas as pd

def verify_sheets():
    sheets = {
        "Stock Take": "1mKcRWrkCMHXOpofdjU1MrwRmhUGaaET8RUOG6eyHAqA",
        "Warehouse Issues": "1Cy0A4nQvbaW8GYlqyuiLvob-qed5Lu-GugPNGjSaGF4",
        "Sales Data": "1WOF03Jicq50xITuKeOvW2I8M-vApAlBSm5IQNLYOuFI"
    }

    for name, sheet_id in sheets.items():
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        print(f"Checking {name}...")
        try:
            # For Sales Data, we need to check the specific sheet name "MULLA HOUSE"
            if name == "Sales Data":
                df = pd.read_excel(url, sheet_name="MULLA HOUSE")
            else:
                df = pd.read_excel(url)
            
            print(f"  [SUCCESS] Loaded {len(df)} rows.")
            print(f"  Columns: {list(df.columns)[:5]}...")
        except Exception as e:
            print(f"  [FAILED] Error: {e}")

if __name__ == "__main__":
    verify_sheets()
