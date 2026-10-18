# CommerceIQ data dictionary — Kaggle retail inventory dataset

Source: https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset

| Source column | Canonical field | Usage |
|---|---|---|
| Date | date | Time index for each store-product series |
| Store ID | location | Store identifier |
| Product ID | sku | Product identifier |
| Category | category | Descriptive category |
| Region | region | Descriptive region |
| Inventory Level | on_hand | Latest observed inventory snapshot |
| Units Sold | units_sold | Forecast target / observed demand |
| Units Ordered | units_ordered | Historical replenishment context |
| Demand Forecast | demand_forecast | Reference only; excluded from model features |
| Price | unit_price | Median historical price |
| Discount | discount | Contextual demand signal |
| Weather Condition | weather_condition | Contextual feature |
| Holiday/Promotion | holiday_promotion | Contextual feature |
| Competitor Pricing | competitor_pricing | Contextual feature |
| Seasonality | seasonality | Contextual feature |

The dataset does not provide search impressions, cart additions, supplier lead time, or gross margin.
Search/cart metrics are set to zero rather than fabricated. The optimizer uses an explicit 30% margin
assumption until a real margin field is supplied. Inventory is taken from the latest date for each
store-product pair. The source-provided forecast must not be used as an input feature when evaluating
our own forecast.
