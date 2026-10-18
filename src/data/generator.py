import numpy as np
import pandas as pd

def generate_demo_data(seed=42, days=90):
    rng = np.random.default_rng(seed)
    skus = [f"SKU_{i:03d}" for i in range(1, 51)]
    locations = ["HYD-01", "BLR-01", "MUM-01", "DEL-01", "CHE-01"]
    names = ["Wireless Noise-Cancelling Headphones", "Smart Watch", "USB-C Hub",
             "Bluetooth Speaker", "Portable SSD", "Wireless Mouse", "Mechanical Keyboard",
             "Webcam", "Power Bank", "Fitness Band"]
    products = pd.DataFrame([{"sku": s, "name": names[i % len(names)],
        "unit_price": float(rng.integers(30, 250) * 10),
        "margin": round(float(rng.uniform(.18, .48)), 2)} for i, s in enumerate(skus)])
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    sales = []
    for i, sku in enumerate(skus):
        base = int(rng.integers(5, 25))
        for loc in locations:
            factor = {"HYD-01": 1, "BLR-01": .9, "MUM-01": 1.15, "DEL-01": 1.05, "CHE-01": .8}[loc]
            for j, day in enumerate(dates):
                surge = 2.8 if sku == "SKU_001" and loc == "HYD-01" and j >= days - 7 else 1
                weekly = 1.18 if day.dayofweek in (4, 5) else 1
                sales.append({"date": day.date().isoformat(), "sku": sku, "location": loc,
                              "units_sold": int(rng.poisson(base * factor * surge * weekly))})
    sales = pd.DataFrame(sales)
    avg = sales.groupby(["sku", "location"])["units_sold"].mean().reset_index(name="avg")
    inventory = avg.assign(on_hand=(avg["avg"] * 10).round().astype(int),
                           snapshot_date=dates[-1].date().isoformat())[["sku", "location", "on_hand", "snapshot_date"]]
    inventory.loc[(inventory.sku == "SKU_001") & (inventory.location == "HYD-01"), "on_hand"] = 350
    inventory.loc[(inventory.sku == "SKU_001") & (inventory.location == "BLR-01"), "on_hand"] = 900
    signals = pd.DataFrame([{"sku": s, "location": loc,
        "searches": int(rng.integers(50, 200) * (2.4 if s == "SKU_001" and loc == "HYD-01" else 1)),
        "cart_additions": int(rng.integers(10, 60) * (2.4 if s == "SKU_001" and loc == "HYD-01" else 1))}
        for s in skus for loc in locations])
    return {"products": products, "sales": sales, "inventory": inventory, "signals": signals}
