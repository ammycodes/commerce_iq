# CommerceIQ
**Predict demand. Optimize inventory. Make smarter commerce decisions.**

A local-first retail decision-support prototype with demand forecasting, inventory-risk analysis,
deterministic transfer economics, manager approval, audit events, FastAPI, Streamlit, and optional
Gemini explanations through Vertex AI.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
streamlit run src/ui/app.py
```
In a second terminal run `uvicorn src.api.server:app --reload`; API docs are at
http://127.0.0.1:8000/docs.

## Data
Put `retail_store_inventory.csv` from the Kaggle Retail Store Inventory Forecasting Dataset in
`data/raw/`. The adapter maps Date, Store ID, Product ID, Inventory Level, Units Sold, Units Ordered,
Demand Forecast, Price, Discount, Weather Condition, Holiday/Promotion, Competitor Pricing, and
Seasonality into CommerceIQ's internal schema. It parses dates with day-first support and uses the
latest record per store-product pair as the current inventory snapshot. Source `Demand Forecast` is
kept for reference only and excluded from forecasting features to prevent leakage.

The dataset has no search impressions, cart additions, supplier lead time, or gross margin. Missing
search/cart metrics are represented as zero (not invented); the optimizer uses a disclosed 30% margin
assumption until a real margin field is supplied. See `data/DATA_DICTIONARY.md`.
If no compatible CSV is found, a labeled synthetic fallback keeps the prototype runnable.

## Important limitations
Forecasting is a transparent weighted recent-average baseline, not a trained ML model.
Approvals update an in-memory simulated ledger only; no real warehouse, ERP, or BigQuery write
occurs. Restarting the process resets approvals. Validate data mappings against the actual dataset
before presenting results as real business findings.

## Economics
Lost sales avoided = min(recipient deficit, transfer quantity).
Gross benefit = lost sales avoided * unit price * margin.
Transfer cost = transfer quantity * transfer cost per unit.
Net benefit = gross benefit - transfer cost.
Positive net benefit is recommended only when transfer quantity is feasible and greater than zero.
