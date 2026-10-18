import pandas as pd
from src.models.forecasting import forecast_all

def analyze_inventory(sales, inventory, signals=None, horizon_days=7, safety_days=2):
    out = forecast_all(sales, horizon_days).merge(inventory[["sku", "location", "on_hand"]],
                                                  on=["sku", "location"], how="left")
    out["on_hand"] = pd.to_numeric(out["on_hand"], errors="coerce").fillna(0).clip(lower=0).astype(int)
    out["safety_stock"] = (out.daily_forecast * safety_days).round().astype(int)
    out["required_stock"] = out.forecast_units + out.safety_stock
    out["deficit"] = (out.required_stock - out.on_hand).clip(lower=0).astype(int)
    out["cover_days"] = out.apply(lambda r: round(r.on_hand / r.daily_forecast, 1) if r.daily_forecast else 999.0, axis=1)
    out["risk_level"] = out.apply(lambda r: "HIGH" if r.deficit > 0 and r.cover_days < 4
                                  else ("MEDIUM" if r.deficit > 0 or r.cover_days < 7 else "LOW"), axis=1)
    if signals is not None and not signals.empty:
        for c in ("searches", "cart_additions"):
            if c not in signals: signals[c] = 0
        out = out.merge(signals[["sku", "location", "searches", "cart_additions"]],
                        on=["sku", "location"], how="left")
        out[["searches", "cart_additions"]] = out[["searches", "cart_additions"]].fillna(0)
    else:
        out["searches"] = 0
        out["cart_additions"] = 0
    return out.sort_values("deficit", ascending=False).reset_index(drop=True)
