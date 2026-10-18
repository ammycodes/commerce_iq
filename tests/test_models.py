import pandas as pd
from src.models.forecasting import forecast_demand
from src.models.inventory_risk import analyze_inventory
from src.models.optimizer import evaluate_transfer

def test_forecast_nonnegative():
    sales = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=7), "sku":["A"]*7,
                          "location":["X"]*7, "units_sold":[10,10,12,11,9,14,14]})
    assert forecast_demand(sales, "A", "X")["forecast_units"] > 0

def test_transfer_math():
    r = evaluate_transfer(sku="A", source_location="B", destination_location="A",
        source_on_hand=100, destination_on_hand=5, destination_deficit=20,
        unit_price=100, margin=.3, transfer_cost_per_unit=2, requested_quantity=15)
    assert r["transfer_quantity"] == 15
    assert r["gross_benefit"] == 450
    assert r["transfer_cost"] == 30
    assert r["net_benefit"] == 420
    assert r["recommendation"] == "EXECUTE_TRANSFER"

def test_quantity_bounded_by_surplus():
    r = evaluate_transfer(sku="A", source_location="B", destination_location="A",
        source_on_hand=8, destination_on_hand=0, destination_deficit=20,
        unit_price=100, margin=.3, transfer_cost_per_unit=2)
    assert r["transfer_quantity"] == 8

def test_inventory_risk_columns():
    sales = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=7), "sku":["A"]*7,
                          "location":["X"]*7, "units_sold":[10]*7})
    inv = pd.DataFrame({"sku":["A"], "location":["X"], "on_hand":[10]})
    out = analyze_inventory(sales, inv)
    assert {"forecast_units", "deficit", "risk_level", "cover_days"} <= set(out.columns)
    assert int(out.iloc[0].deficit) > 0
