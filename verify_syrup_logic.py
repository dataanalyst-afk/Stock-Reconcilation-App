import pandas as pd

# --- LOGIC PORTED FROM APP.PY ---

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

def preprocess_data(stock):
    if stock is None: return pd.DataFrame()
    # Standardize columns
    stock.columns = stock.columns.str.lower().str.strip()
    
    # Date conversion
    if "inventory date :" in stock.columns:
        stock["inventory date :"] = pd.to_datetime(stock["inventory date :"])
        stock["month"] = stock["inventory date :"].dt.to_period("M")
    
    return stock

def get_stock_summary(stock):
    if stock.empty: return pd.DataFrame()
    # We need unique closing stock per item per month.
    # Key columns for grouping - Group by Item Code and Month ONLY for uniqueness
    group_cols = ["item code :", "month"]
    
    # Aggregation rules: Sum quantity, take first available description/category
    agg_dict = {
        "physical quantity :": "sum",
        "item name :": "first",
        "category :": "first",
        "uom :": "first"
    }
    
    # Filter agg_dict to only include columns present in df
    agg_dict = {k: v for k, v in agg_dict.items() if k in stock.columns}
    
    # Aggregate
    monthly_stock = stock.groupby(group_cols).agg(agg_dict).reset_index()
    monthly_stock.rename(columns={"physical quantity :": "closing_stock"}, inplace=True)
    
    return monthly_stock

def load_warehouse_data():
    try:
        # Warehouse Issues Sheet
        sheet_id = "1Cy0A4nQvbaW8GYlqyuiLvob-qed5Lu-GugPNGjSaGF4"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        warehouse = pd.read_excel(url)
        return warehouse
    except Exception as e:
        print(f"Error loading Warehouse Data: {e}")
        return None

def preprocess_warehouse(warehouse):
    if warehouse is None: return pd.DataFrame()
    warehouse.columns = warehouse.columns.str.lower().str.strip()
    if "issue date :" in warehouse.columns:
        warehouse["issue date :"] = pd.to_datetime(warehouse["issue date :"])
        warehouse["month"] = warehouse["issue date :"].dt.to_period("M")
    return warehouse

def get_warehouse_summary(warehouse):
    if warehouse.empty: return pd.DataFrame()
    # Group by Item Code and Month to get total issued quantity
    group_cols = ["item code", "month"]
    
    # Aggregation: Sum issue quantity
    agg_dict = {
        "issue quantity :": "sum"
    }
    
    # Filter agg_dict
    agg_dict = {k: v for k, v in agg_dict.items() if k in warehouse.columns}
    
    warehouse_summary = warehouse.groupby(group_cols).agg(agg_dict).reset_index()
    warehouse_summary.rename(columns={"issue quantity :": "supplied_qty", "item code": "item code :"}, inplace=True)
    
    return warehouse_summary

# --- EXECUTION ---

print("Loading Data... (This may take a moment)")
raw_stock = load_data()
df_stock = preprocess_data(raw_stock)
stock_summary = get_stock_summary(df_stock)

raw_warehouse = load_warehouse_data()
warehouse_df_raw = preprocess_warehouse(raw_warehouse)
warehouse_summary = get_warehouse_summary(warehouse_df_raw)

# Determine Month (Using Latest)
if not df_stock.empty and "month" in df_stock.columns:
    available_months = df_stock["month"].unique().astype(str)
    available_months = sorted(available_months, reverse=True)
    selected_month_str = available_months[0] # Selecting Last Month
    selected_month = pd.Period(selected_month_str, freq="M")
    print(f"Analyzed Month: {selected_month_str}")
else:
    print("No data found.")
    selected_month = None

if selected_month:
    # Calculate Opening Stock (Previous Month Closing)
    previous_month = selected_month - 1
    prev_month_data = stock_summary[stock_summary["month"] == previous_month].copy()
    prev_month_data = prev_month_data.set_index("item code :")
    
    # Current Month Closing
    current_month_data = stock_summary[stock_summary["month"] == selected_month].copy()
    current_month_data = current_month_data.set_index("item code :")

    # Current Month Supply
    current_month_supply = warehouse_summary[warehouse_summary["month"] == selected_month].copy()
    current_month_supply = current_month_supply.set_index("item code :")

    # Master Data Construction (Opening + Closing + Supply)
    # Union of all relevant items
    all_items = prev_month_data.index.union(current_month_supply.index).union(current_month_data.index)
    
    master_df = pd.DataFrame(index=all_items)
    
    # Metadata Map
    # Map item names from stock data first (most reliable)
    master_item_map = df_stock[["item code :", "item name :", "category :", "uom :"]].drop_duplicates("item code :")
    master_item_map = master_item_map.set_index("item code :")
    
    master_df = master_df.join(master_item_map, how="left")
    master_df.rename(columns={"item name :": "Item Name", "category :": "Category", "uom :": "UOM"}, inplace=True)
    
    # Fill Data
    master_df["Opening Stock"] = prev_month_data["closing_stock"]
    master_df["Supplied Qty"] = current_month_supply["supplied_qty"]
    master_df["Closing Stock"] = current_month_data["closing_stock"]
    
    master_df.fillna(0, inplace=True)
    
    # Consumption Logic
    master_df["Total Available"] = master_df["Opening Stock"] + master_df["Supplied Qty"]
    master_df["Consumption"] = master_df["Total Available"] - master_df["Closing Stock"]

    master_df.index.name = "Item Code"
    master_df = master_df.reset_index()

    # --- SYRUP FILTER ---
    syrup_df = master_df[master_df["Category"].astype(str).str.contains("SYRUP", case=False, na=False)].copy()

    print("\n🍯 SYRUP INVENTORY & ACTUAL CONSUMPTION")
    cols = ["Item Name", "Opening Stock", "Supplied Qty", "Total Available", "Closing Stock", "Consumption", "UOM"]
    syrup_final = syrup_df[cols].sort_values("Consumption", ascending=False)
    print(syrup_final.to_string())
