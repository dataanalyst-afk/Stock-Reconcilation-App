import json
import pandas as pd # Just for check? No need.
import os

file_path = r'c:\Yaraman(Data-Analyst)\Coffee Consumption - Copy\syrup.ipynb'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # We want to APPEND new logic for Reconciliation to the END.
    # The previous update added cells for "Inventory Logic".
    # Now we add cells for "Reconciliation".

    new_cells = [
      {
       "cell_type": "code",
       "execution_count": None,
       "id": "reconcile_logic",
       "metadata": {},
       "outputs": [],
       "source": [
        "# --- RECONCILIATION LOGIC ---\n",
        "\n",
        "def normalize_name(name):\n",
        "    if not isinstance(name, str): return \"\"\n",
        "    # Remove common noise words\n",
        "    noise = [\"monin\", \"syrup\", \"700ml\", \"1ltr\", \"bottle\", \" \", \"-\"]\n",
        "    clean = name.lower()\n",
        "    for n in noise:\n",
        "        clean = clean.replace(n, \"\")\n",
        "    return clean\n",
        "\n",
        "print(\"Performing Reconciliation...\")\n",
        "\n",
        "if 'syrup_deduction' in locals() and 'syrup_final' in locals():\n",
        "    # 1. Prepare Theoretical (From Sales)\n",
        "    # columns: syrup_name, syrup_liters_deducted\n",
        "    theo_df = syrup_deduction.copy()\n",
        "    theo_df[\"match_key\"] = theo_df[\"syrup_name\"].apply(normalize_name)\n",
        "    \n",
        "    # 2. Prepare Actual (From Inventory)\n",
        "    # columns: Item Name, Consumption (this is in Units/Bottles? No, Inventory is usually in Bottles)\n",
        "    # We need to check UOM. If UOM is Bottle, we might need to convert to ML if Recipe is in ML.\n",
        "    # Assumption: Inventory 'Consumption' is in BOTTLES (since it comes from stock take 0.5, 1.0 etc)\n",
        "    # Standard Syrup Bottle = 700ML usually, but let's assume 700ML for Monin.\n",
        "    \n",
        "    actual_df = syrup_final.copy()\n",
        "    actual_df[\"match_key\"] = actual_df[\"Item Name\"].apply(normalize_name)\n",
        "    \n",
        "    # Convert Actual Consumption (Bottles) to Liters for comparison\n",
        "    # Assumption: 1 Bottle = 0.7 Liters (700ml)\n",
        "    # If UOM says 'LTR', then maybe it's 1. \n",
        "    # Let's try to detect 700ml in name.\n",
        "    def get_conversion_factor(row):\n",
        "        name = str(row['Item Name']).lower()\n",
        "        if '1ltr' in name or '1000ml' in name:\n",
        "            return 1.0\n",
        "        if '250ml' in name:\n",
        "            return 0.25\n",
        "        # Default Monin\n",
        "        return 0.7\n",
        "        \n",
        "    actual_df[\"conv_factor\"] = actual_df.apply(get_conversion_factor, axis=1)\n",
        "    actual_df[\"Actual Liters\"] = actual_df[\"Consumption\"] * actual_df[\"conv_factor\"]\n",
        "    \n",
        "    # 3. Merge\n",
        "    merged = pd.merge(\n",
        "        actual_df, \n",
        "        theo_df, \n",
        "        on=\"match_key\", \n",
        "        how=\"outer\", \n",
        "        suffixes=(\"_inv\", \"_recipe\")\n",
        "    )\n",
        "    \n",
        "    # 4. Clean up Table\n",
        "    # If Item Name is NaN (meaning it was in Recipe but not in Stock??), use syrup_name\n",
        "    merged[\"Syrup Name\"] = merged[\"Item Name\"].fillna(merged[\"syrup_name\"])\n",
        "    \n",
        "    cols = [\n",
        "        \"Syrup Name\", \n",
        "        \"Opening Stock\", \n",
        "        \"Supplied Qty\", \n",
        "        \"Closing Stock\", \n",
        "        \"Actual Liters\", \n",
        "        \"syrup_liters_deducted\"\n",
        "    ]\n",
        "    \n",
        "    report = merged[cols].copy()\n",
        "    report.rename(columns={\n",
        "        \"syrup_liters_deducted\": \"Expected Liters (Sales)\",\n",
        "        \"Actual Liters\": \"Actual Liters (Stock)\"\n",
        "    }, inplace=True)\n",
        "    \n",
        "    report.fillna(0, inplace=True)\n",
        "    \n",
        "    # 5. Variance\n",
        "    # Variance = Actual - Expected. \n",
        "    # If Actual > Expected, we used MORE than we sold (loss/waste/theft/over-pour)\n",
        "    # If Actual < Expected, we used LESS (under-pour, or missing recipe entry)\n",
        "    report[\"Variance (Liters)\"] = report[\"Actual Liters (Stock)\"] - report[\"Expected Liters (Sales)\"]\n",
        "    \n",
        "    print(\"\\n⚖️ SYRUP VARIANCE REPORT (Liters)\")\n",
        "    # Highlight significant variance\n",
        "    report = report.sort_values(\"Variance (Liters)\", ascending=False)\n",
        "    \n",
        "    # Style for notebook\n",
        "    def highlight_variance(val):\n",
        "        color = 'red' if val > 0.5 else 'green' if val < -0.5 else 'black'\n",
        "        return f'color: {color}'\n",
        "        \n",
        "    display(report.style.format(\"{:.2f}\").applymap(highlight_variance, subset=[\"Variance (Liters)\"]))\n",
        "    \n",
        "else:\n",
        "    print(\"Include previous cells to run reconciliation.\")"
       ]
      }
    ]

    notebook['cells'].extend(new_cells)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)

    print("Notebook updated successfully with Reconcilation Logic.")
except Exception as e:
    print(f"Error: {e}")
