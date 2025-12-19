import pandas as pd

try:
    warehouse = pd.read_excel("Dataset/Issue Details ( AUG - DEC ).xlsx") if False else pd.read_excel("Issue Details ( AUG - DEC ).xlsx")
    stock = pd.read_excel("Stock Take.xlsx")
    
    print("Stock Categories:")
    print(stock["Category :"].unique())
    
    print("\nWarehouse Categories:")
    print(warehouse["Category :"].unique())
    
    # Check for specific keywords
    print("\nPotential Coffee Items:")
    print(stock[stock["Item Name :"].str.contains("Coffee|Bean|Espresso", case=False, na=False)]["Item Name :"].unique())
    
    print("\nPotential Cup Items:")
    print(stock[stock["Item Name :"].str.contains("Cup|Lid", case=False, na=False)]["Item Name :"].unique())

except Exception as e:
    print(f"Error: {e}")

