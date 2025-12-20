import streamlit as pd_st
import streamlit as st
import pandas as pd
from datetime import timedelta

# Set page config
st.set_page_config(page_title="Stock Checking App", layout="wide")

@st.cache_data
def load_data():
    try:
        # Stock Take Sheet
        sheet_id = "1mKcRWrkCMHXOpofdjU1MrwRmhUGaaET8RUOG6eyHAqA"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        stock = pd.read_excel(url)
        return stock
    except Exception as e:
        # Fallback or error logging
        st.error(f"Error loading Stock Data: {e}")
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

@st.cache_data
def load_warehouse_data():
    try:
        # Warehouse Issues Sheet
        sheet_id = "1Cy0A4nQvbaW8GYlqyuiLvob-qed5Lu-GugPNGjSaGF4"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        warehouse = pd.read_excel(url)
        return warehouse
    except Exception as e:
        st.error(f"Error loading Warehouse Data: {e}")
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

@st.cache_data
def load_sales_data():
    try:
        # Sales Data Sheet (Petpooja)
        sheet_id = "1WOF03Jicq50xITuKeOvW2I8M-vApAlBSm5IQNLYOuFI"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        # Assuming Data is in 'MULLA HOUSE' sheet, or we try reading the first sheet if that fails?
        # Keeping sheet_name="MULLA HOUSE" as per original code logic
        sales = pd.read_excel(url, sheet_name="MULLA HOUSE")
        return sales
    except Exception as e:
        st.error(f"Error loading Sales Data: {e}")
        return None

def preprocess_sales(sales):
    if sales is None: return pd.DataFrame()
    sales.columns = sales.columns.str.lower().str.strip()
    # Check for date column variations
    date_col = next((c for c in sales.columns if "date" in c), None)
    if date_col:
        sales["date"] = pd.to_datetime(sales[date_col])
        sales["month"] = sales["date"].dt.to_period("M")
    return sales

def main():
    st.title("Stock Opening & Closing Checker")
    
    # Sidebar Navigation
    page = st.sidebar.radio("Navigate", ["Stock Overview", "Warehouse Supply", "Coffee Consumption", "Cup Consumption"])
    
    # Load Data
    raw_df = load_data()
    warehouse_df_raw = load_warehouse_data()
    sales_df_raw = load_sales_data()
    
    if raw_df is None:
        st.error("File `Stock Take.xlsx` not found.")
        st.stop()
        
    df = preprocess_data(raw_df)
    
    stock_summary = get_stock_summary(df)
    
    # Common Sidebar Filters
    st.sidebar.header("Filters")
    
    # Month Filter
    available_months = df["month"].unique().astype(str)
    available_months = sorted(available_months, reverse=True)
    selected_month_str = st.sidebar.selectbox("Select Month", available_months, key="month_select")
    selected_month = pd.Period(selected_month_str, freq="M")
    
    # Category Filter (Only show for pages that are generic)
    if page in ["Stock Overview", "Warehouse Supply", "Coffee Consumption"]:
        available_categories = df["category :"].dropna().unique()
        selected_categories = st.sidebar.multiselect("Select Category", available_categories, default=available_categories, key="category_select")
        
        # Item Filter logic (shared)
        if selected_categories:
            available_items = df[df["category :"].isin(selected_categories)]["item name :"].dropna().unique()
        else:
            available_items = df["item name :"].dropna().unique()
        selected_items = st.sidebar.multiselect("Select Item", sorted(available_items), key="item_select")

    # Calculate Opening Stock (Previous Month Closing)
    previous_month = selected_month - 1
    prev_month_data = stock_summary[stock_summary["month"] == previous_month].copy()
    prev_month_data = prev_month_data.set_index("item code :")
    
    # Current Month Closing
    current_month_data = stock_summary[stock_summary["month"] == selected_month].copy()
    current_month_data = current_month_data.set_index("item code :")

    # Helper to build Supply DF
    def build_supply_df(w_raw, selected_m):
        if w_raw is None: return pd.DataFrame()
        w_df = preprocess_warehouse(w_raw)
        w_summary = get_warehouse_summary(w_df)
        curr_supply = w_summary[w_summary["month"] == selected_m].copy()
        return curr_supply.set_index("item code :")

    current_month_supply = build_supply_df(warehouse_df_raw, selected_month)

    # Master Data Construction (Opening + Closing + Supply)
    # Union of all relevant items
    all_items = prev_month_data.index.union(current_month_supply.index).union(current_month_data.index)
    
    master_df = pd.DataFrame(index=all_items)
    
    # Metadata Map
    # Map item names from stock data first (most reliable)
    master_item_map = df[["item code :", "item name :", "category :", "uom :"]].drop_duplicates("item code :").set_index("item code :")
    
    master_df["Item Name"] = master_item_map["item name :"]
    master_df["Category"] = master_item_map["category :"]
    master_df["UOM"] = master_item_map["uom :"]
    
    # Fill Data
    master_df["Opening Stock"] = prev_month_data["closing_stock"].fillna(0)
    master_df["Supplied Qty"] = current_month_supply["supplied_qty"].fillna(0) if not current_month_supply.empty else 0
    master_df["Closing Stock"] = current_month_data["closing_stock"].fillna(0)
    
    # Consumption Logic
    master_df["Total Available"] = master_df["Opening Stock"] + master_df["Supplied Qty"]
    master_df["Consumption"] = master_df["Total Available"] - master_df["Closing Stock"]
    # Handle negative consumption (data error or adjustment) ? For now leave as is or clip at 0
    # master_df["Consumption"] = master_df["Consumption"].clip(lower=0) 

    master_df.index.name = "Item Code"
    master_df = master_df.reset_index()

    if page == "Stock Overview":
        st.subheader(f"Stock Data for {selected_month_str}")
        st.write(f"**Opening Stock Source**: Closing of {previous_month}")
        
        # Filtering
        if selected_categories:
            master_df = master_df[master_df["Category"].isin(selected_categories)]
        if selected_items:
            master_df = master_df[master_df["Item Name"].isin(selected_items)]
            
        cols = ["Item Code", "Item Name", "Category", "Opening Stock", "Closing Stock", "UOM"]
        st.dataframe(master_df[cols], use_container_width=True)

    elif page == "Warehouse Supply":
        st.subheader(f"Warehouse Supply & Availability for {selected_month_str}")
        
        if warehouse_df_raw is None:
            st.warning("Warehouse data file missing.")
        
        # Filtering
        if selected_categories:
            master_df = master_df[master_df["Category"].isin(selected_categories)]
        if selected_items:
            master_df = master_df[master_df["Item Name"].isin(selected_items)]
            
        cols = ["Item Code", "Item Name", "Category", "Opening Stock", "Supplied Qty", "Total Available", "UOM"]
        st.dataframe(master_df[cols], use_container_width=True)
        
    elif page == "Cup Consumption":
        st.subheader(f"🥤 Cup Consumption Reconciliation for {selected_month_str}")
        
        if sales_df_raw is None:
            st.error("Sales data file `Mulla House ( AUG - DEC 18 ) PetPooja.xlsx` not found.")
        else:
            sales_df = preprocess_sales(sales_df_raw)
            
            # ---------------------------------------------------------
            # 1. SALES SIDE (Expected Consumption)
            # ---------------------------------------------------------
            # Categories defined by user
            cup_categories = [
                "coffee", "cold coffee", "iced coffee", "chocolate", "hot brews [o]",
                "tea", "manual brews", "tasteful infusions (non coffee) [o]",
                "juices", "iced coffees [o]", "manual brews [o]",
                "monsoon special beverages [o]", "beverages [o]", "little ones [o]", "smoothies(o)"
            ]
            
            # Normalize sales categories
            sales_df["category_clean"] = sales_df["category"].astype(str).str.lower().str.strip()
            
            # Filter: Month
            s_df = sales_df[sales_df["month"] == selected_month].copy()
            
            # Filter: Category Match
            s_df = s_df[s_df["category_clean"].isin(cup_categories)]
            
            # Filter: Order Type != Dine In
            if "order type" in s_df.columns:
                s_df["order type norm"] = s_df["order type"].astype(str).str.lower().str.strip()
                # Exclude Dine In (Keep Delivery, Pick Up, Parcel, Takeaway etc.)
                s_df = s_df[~s_df["order type norm"].str.contains("dine in", case=False, na=False)]
            
            # Calculate Total Sales Cups
            # Finding quantity column
            qty_col = next((c for c in s_df.columns if c in ["qty.", "qty", "quantity"]), None)
            # Fallback
            if not qty_col:
                 qty_col = next((c for c in s_df.columns if "qty" in c or "quantity" in c), None)

            if qty_col:
                total_sales_cups = s_df[qty_col].sum()
            else:
                total_sales_cups = 0
                st.error("Quantity column not found in sales data.")
                
            # ---------------------------------------------------------
            # 2. INVENTORY SIDE (Actual Stock)
            # ---------------------------------------------------------
            # 2. INVENTORY SIDE (Actual Stock)
            # ---------------------------------------------------------
            # Filter master_df for items that represent Cups (Current Month)
            current_month_cups = master_df[master_df["Item Name"].str.contains("CUP|LID", case=False, na=False)].copy()

            # Global Cup List (from full history) to prevent filter reset when changing months
            # We use 'df' which contains all months data
            all_possible_cups = df[df["item name :"].str.contains("CUP|LID", case=False, na=False)]["item name :"].dropna().unique()
            cup_item_names = sorted(all_possible_cups)
            
            # User Request: Select specific cup items to include
            selected_cup_items = st.multiselect("Select Cup Inventory Items", cup_item_names, default=cup_item_names, key="cup_inventory_select")
            
            if selected_cup_items:
                inventory_cups_df = current_month_cups[current_month_cups["Item Name"].isin(selected_cup_items)].copy()
            else:
                inventory_cups_df = current_month_cups.copy()
            
            total_opening = inventory_cups_df["Opening Stock"].sum()
            total_supplied = inventory_cups_df["Supplied Qty"].sum()
            total_closing = inventory_cups_df["Closing Stock"].sum()
            
            # ---------------------------------------------------------
            # 3. RECONCILIATION
            # ---------------------------------------------------------
            total_available = total_opening + total_supplied
            # Logic: Opening + Supplied - Consumed(Sales) should be Closing
            # So Variance = (Opening + Supplied - Consumed) - Actual Closing
            # Or Missing = Expected Closing - Actual Closing
            
            expected_closing = total_available - total_sales_cups
            missing_cups = expected_closing - total_closing
            
            # Display Table
            st.write("### 📊 Reconciliation Summary")
            
            rec_data = {
                "Metric": [
                    "Opening Stock (Inventory)", 
                    "Supplied (Warehouse)", 
                    "Total Available", 
                    "Consumed (Sales Calculation)", 
                    "Expected Closing Stock", 
                    "Actual Closing Stock (Inventory)", 
                    "Missing / Variance"
                ],
                "Quantity": [
                    total_opening, 
                    total_supplied, 
                    total_available, 
                    total_sales_cups, 
                    expected_closing, 
                    total_closing, 
                    missing_cups
                ]
            }
            rec_df = pd.DataFrame(rec_data)
            
            # Formatting
            st.dataframe(
                rec_df.style.format({"Quantity": "{:,.0f}"})
                .background_gradient(subset=["Quantity"], cmap="coolwarm", axis=0), 
                use_container_width=True
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Missing Cups**: {missing_cups:,.0f}")
            with col2:
                if total_sales_cups > 0:
                    pct_sales_cups = (missing_cups / total_sales_cups) * 100
                    st.metric("Missing / Sales Cups", f"{pct_sales_cups:.1f}%")
                else:
                    st.metric("Missing / Sales Cups", "N/A")
            with col3:
                if total_available > 0:
                    pct_available = (missing_cups / total_available) * 100
                    st.metric("Missing / Total Available", f"{pct_available:.1f}%")
                else:
                    st.metric("Missing / Total Available", "N/A")

            # ---------------------------------------------------------
            # DETAILED VIEWS
            # ---------------------------------------------------------
            st.divider()
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("#### 🧾 Sales Breakdown (Beverages)")
                if qty_col:
                    item_col = next((c for c in s_df.columns if "item" in c and "name" in c), "item name")
                    sales_breakdown = s_df.groupby(item_col)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False)
                    sales_breakdown.columns = ["Beverage", "Qty Sold"]
                    st.dataframe(sales_breakdown, use_container_width=True, height=300)
            
            with col_b:
                st.write("#### 📦 Inventory Breakdown (Cups & Lids)")
                inv_cols = ["Item Name", "Opening Stock", "Supplied Qty", "Closing Stock"]
                st.dataframe(inventory_cups_df[inv_cols].sort_values("Closing Stock", ascending=False), use_container_width=True, height=300)
        
    elif page == "Coffee Consumption":
        st.subheader(f"☕ Coffee Consumption for {selected_month_str}")
        
        # Filter for Coffee
        coffee_df = master_df[master_df["Category"].str.contains("TEAS & COFFEES", case=False, na=False)].copy()
        
        if coffee_df.empty:
            st.info("No Coffee items found for this month.")
        else:
            # Metrics
            total_consumption = coffee_df["Consumption"].sum()
            avg_consumption = coffee_df["Consumption"].mean()
            
            col1, col2 = st.columns(2)
            col1.metric("Total Consumption (Units/Kg)", f"{total_consumption:,.2f}")
            col2.metric("Avg Consumption per Item", f"{avg_consumption:,.2f}")
            
            # Chart
            st.write("### Consumption by Item")
            chart_data = coffee_df.set_index("Item Name")[["Consumption"]].sort_values("Consumption", ascending=False)
            st.bar_chart(chart_data)
            
            # Detailed Table
            st.write("### Detailed Breakdown")
            cols = ["Item Name", "Opening Stock", "Supplied Qty", "Total Available", "Closing Stock", "Consumption", "UOM"]
            st.dataframe(coffee_df[cols].style.background_gradient(subset=["Consumption"], cmap="Reds"), use_container_width=True)

if __name__ == "__main__":
    main()