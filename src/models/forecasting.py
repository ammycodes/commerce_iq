import pandas as pd

def forecast_demand(sales, sku, location, horizon_days=7):
    subset = sales[(sales.sku.astype(str) == str(sku)) &
                   (sales.location.astype(str) == str(location))].copy()
    if subset.empty:
        return {"sku": str(sku), "location": str(location), "horizon_days": horizon_days,
                "daily_forecast": 0.0, "forecast_units": 0, "method": "weighted_recent_average"}
    subset["date"] = pd.to_datetime(subset["date"], errors="coerce")
    subset["units_sold"] = pd.to_numeric(subset["units_sold"], errors="coerce").fillna(0)
    values = subset.dropna(subset=["date"]).sort_values("date").tail(14)["units_sold"].astype(float).tolist()
    weights = list(range(1, len(values) + 1))
    daily = sum(v*w for v, w in zip(values, weights)) / sum(weights) if values else 0.0
    return {"sku": str(sku), "location": str(location), "horizon_days": int(horizon_days),
            "daily_forecast": round(max(0, daily), 2),
            "forecast_units": int(round(max(0, daily) * horizon_days)),
            "method": "weighted_recent_daily_average"}

def forecast_all(sales, horizon_days=7):
    pairs = sales[["sku", "location"]].drop_duplicates()
    return pd.DataFrame([forecast_demand(sales, r.sku, r.location, horizon_days)
                         for r in pairs.itertuples(index=False)])
