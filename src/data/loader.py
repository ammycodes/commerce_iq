from pathlib import Path
import re
import pandas as pd
from src.data.generator import generate_demo_data

ALIASES = {
    "date": ["date", "day", "transaction_date"],
    "store_id": ["store_id", "store", "store_code", "location", "location_id"],
    "product_id": ["product_id", "product", "sku", "sku_id", "item_id", "product_code"],
    "category": ["category", "product_category"],
    "region": ["region", "area"],
    "inventory_level": ["inventory_level", "inventory", "on_hand", "stock", "stock_on_hand", "available_stock"],
    "units_sold": ["units_sold", "quantity_sold", "sales_units", "units", "quantity"],
    "units_ordered": ["units_ordered", "ordered_units", "replenishment_quantity"],
    "demand_forecast": ["demand_forecast", "forecast_demand", "vendor_forecast"],
    "price": ["price", "unit_price", "selling_price", "sale_price"],
    "discount": ["discount", "discount_percent", "discount_percentage"],
    "weather_condition": ["weather_condition", "weather"],
    "holiday_promotion": ["holiday_promotion", "holiday", "promotion", "promo_flag"],
    "competitor_pricing": ["competitor_pricing", "competitor_price"],
    "seasonality": ["seasonality", "season"],
}
EXPECTED_COLUMNS = ["date", "store_id", "product_id", "category", "region", "inventory_level",
                    "units_sold", "units_ordered", "demand_forecast", "price", "discount",
                    "weather_condition", "holiday_promotion", "competitor_pricing", "seasonality"]

def normalize_columns(df):
    df = df.copy()
    df.columns = [re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_") for c in df.columns]
    rename = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                rename[alias] = canonical
                break
    return df.rename(columns=rename)

def find_dataset_files(data_dir):
    data_dir = Path(data_dir)
    if not data_dir.exists():
        return []
    files = sorted(data_dir.glob("*.csv"))
    preferred = [p for p in files if "retail_store_inventory" in p.stem.lower()]
    return preferred + [p for p in files if p not in preferred]

def load_kaggle_inventory_csv(path):
    raw = normalize_columns(pd.read_csv(path))
    required = ("date", "store_id", "product_id", "inventory_level", "units_sold")
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise ValueError(f"{path.name} is not the expected Kaggle dataset; missing columns: {missing}")
    df = raw.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df["store_id"] = df["store_id"].astype("string").str.strip()
    df["product_id"] = df["product_id"].astype("string").str.strip()
    numeric_cols = ("inventory_level", "units_sold", "units_ordered", "price", "discount",
                    "demand_forecast", "competitor_pricing", "holiday_promotion")
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "store_id", "product_id"])
    df["units_sold"] = df["units_sold"].fillna(0).clip(lower=0)
    df["inventory_level"] = df["inventory_level"].fillna(0).clip(lower=0)
    df["units_ordered"] = df["units_ordered"].fillna(0).clip(lower=0)
    price_default = df["price"].median() if df["price"].notna().any() else 0
    df["price"] = df["price"].fillna(price_default).clip(lower=0)
    df["discount"] = df["discount"].fillna(0).clip(lower=0)
    df["holiday_promotion"] = df["holiday_promotion"].fillna(0).clip(lower=0)

    duplicate_count = int(df.duplicated(["date", "store_id", "product_id"]).sum())
    if duplicate_count:
        numeric = [c for c in numeric_cols if c in df.columns]
        aggs = {c: "mean" for c in numeric}
        for c in ("category", "region", "weather_condition", "seasonality"):
            if c in df.columns:
                aggs[c] = "last"
        df = df.groupby(["date", "store_id", "product_id"], as_index=False).agg(aggs)

    sales = df[["date", "product_id", "store_id", "units_sold"]].rename(
        columns={"product_id": "sku", "store_id": "location"})
    latest = df.sort_values("date").groupby(["product_id", "store_id"], as_index=False).tail(1)
    inventory = latest[["product_id", "store_id", "inventory_level", "date"]].rename(
        columns={"product_id": "sku", "store_id": "location",
                 "inventory_level": "on_hand", "date": "snapshot_date"})

    product_cols = ["product_id", "price"] + (["category"] if "category" in df.columns else [])
    product_aggs = {"price": "median"}
    if "category" in product_cols:
        product_aggs["category"] = "last"
    products = df[product_cols].groupby("product_id", as_index=False).agg(product_aggs).rename(
        columns={"product_id": "sku", "price": "unit_price"})
    products["margin"] = 0.30
    if "category" not in products.columns:
        products["category"] = "Unknown"

    signal_cols = ["product_id", "store_id"]
    for col in ("discount", "holiday_promotion", "weather_condition", "competitor_pricing", "seasonality"):
        if col in df.columns:
            signal_cols.append(col)
    signals = latest[signal_cols].rename(columns={"product_id": "sku", "store_id": "location"}).copy()
    signals["searches"] = 0
    signals["cart_additions"] = 0

    quality = {
        "file": str(path), "rows_loaded": int(len(df)), "duplicate_key_rows_resolved": duplicate_count,
        "date_min": str(df["date"].min().date()), "date_max": str(df["date"].max().date()),
        "store_count": int(df["store_id"].nunique()), "product_count": int(df["product_id"].nunique()),
        "store_product_pairs": int(df[["store_id", "product_id"]].drop_duplicates().shape[0]),
        "source_demand_forecast_used_as_feature": False,
        "margin_assumption": 0.30,
        "search_and_cart_signals_available": False,
    }
    return {"products": products, "sales": sales, "inventory": inventory, "signals": signals,
            "daily_records": df, "quality": quality}

class RetailDataLoader:
    def __init__(self, data_dir="data/raw"):
        self.data_dir = Path(data_dir)

    def load(self):
        files = find_dataset_files(self.data_dir)
        for path in files:
            try:
                data = load_kaggle_inventory_csv(path)
                data["source"] = pd.DataFrame([{
                    "mode": "Kaggle Retail Store Inventory Forecasting Dataset",
                    "csv_files_found": len(files), "data_dir": str(self.data_dir),
                    "file": path.name, "rows_loaded": data["quality"]["rows_loaded"]
                }])
                return data
            except Exception as exc:
                print(f"[CommerceIQ] Could not use {path.name}: {exc}")
        result = {k: v.copy() for k, v in generate_demo_data().items()}
        result["source"] = pd.DataFrame([{
            "mode": "synthetic demo fallback (no compatible Kaggle CSV found)",
            "csv_files_found": len(files), "data_dir": str(self.data_dir)
        }])
        result["quality"] = {"mode": "synthetic demo fallback"}
        result["daily_records"] = pd.DataFrame()
        return result
