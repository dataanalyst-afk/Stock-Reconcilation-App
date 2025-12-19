import pandas as pd

try:
    file_path = "Mulla House ( AUG - DEC 18 ) PetPooja.xlsx"
    df = pd.read_excel(file_path)
    
    # Clean columns
    df.columns = df.columns.str.lower().str.strip()
    
    print("Columns found:")
    for c in df.columns:
        print(c)


except Exception as e:
    print(f"Error: {e}")
