# 🛒 CommerceIQ
### *AI-powered inventory intelligence for modern retail*

> **Predict demand. Prevent stockouts. Protect revenue — before the shelf goes empty.**

---

## 💡 The Problem

Retail stockouts cost the global industry **$1.75 trillion per year**. Most retailers discover inventory gaps *after* customers walk away — too late to act. Demand signals are siloed, forecasts are manual, and transfer decisions take days of email chains.

**CommerceIQ** changes that.

---

## 🚀 What It Does

CommerceIQ is a **real-time retail decision-support system** that:

| Capability | What it means |
|---|---|
| 📈 **Demand Forecasting** | Predicts daily sell-through for every SKU × location pair using a transparent weighted recent-average model |
| ⚠️ **Inventory Risk Scoring** | Flags HIGH / MEDIUM / LOW risk positions — days of cover, deficit units, safety stock |
| 💰 **Transfer Economics** | Calculates exact net benefit of moving stock between stores: `net = (avoided lost sales × margin) − transfer cost` |
| ✅ **Manager Approval Workflow** | Every AI recommendation goes through a human-in-the-loop approval gate with a full audit trail |
| 🤖 **Gemini AI Analyst** | Natural language Q&A powered by Google Gemini 2.0 Flash (Vertex AI) — ask in plain English, get business-language answers |
| 🗺️ **REST API** | Full FastAPI backend — integrate CommerceIQ into any ERP, WMS, or dashboard |

---

## 🎯 Impact at a Glance

- Identifies deficit exposure across all SKU-location pairs **in seconds, not days**
- Converts raw inventory data into **actionable EXECUTE / ABSORB decisions** with dollar-value justification
- Every decision is **fully traceable** — audit log + simulated ledger event for compliance
- Works on **real Kaggle retail data** or instantly on synthetic fallback — zero setup friction for demos

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                         │
│   Executive Overview │ Decision Workbench │ AI Analyst  │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│             CommerceTools  (Orchestration Layer)        │
│         risks()  recommend()  approve()  ask()          │
└──────┬───────────────┬──────────────────┬───────────────┘
       │               │                  │
┌──────▼──────┐ ┌──────▼──────┐ ┌────────▼────────┐
│ Forecasting │ │  Inventory  │ │  LangGraph  +   │
│   Model     │ │ Risk Engine │ │  Gemini  (AI)   │
└──────┬──────┘ └──────┬──────┘ └────────┬────────┘
       └───────────────┴──────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│              Data Layer  (Kaggle CSV / Synthetic)        │
│   Sales history │ Inventory snapshots │ Product catalogue │
└───────────────────────────────────────────────────────────┘
                        │
           ┌────────────▼────────────┐
           │    FastAPI  REST  API   │
           │  /risks  /recommend     │
           │  /approval /audit /ask  │
           └─────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit + Plotly |
| API | FastAPI + Uvicorn |
| AI Agent | LangGraph state machine |
| LLM | Google Gemini 2.0 Flash (Vertex AI) |
| Data | Pandas + NumPy |
| Validation | Pydantic v2 |
| Dataset | [Kaggle Retail Store Inventory Forecasting](https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset) |

---

## 🖥️ Run Locally (2 minutes)

```bash
# 1. Clone & install
git clone <repo-url> && cd commerce_iq
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. (Optional) Add real data
#    Download retail_store_inventory.csv from Kaggle → place in data/raw/
#    Without it, a labeled synthetic dataset loads automatically

# 3. Launch UI
streamlit run src/ui/app.py

# 4. Launch API  (separate terminal)
uvicorn src.api.server:app --reload
# API docs → http://127.0.0.1:8000/docs

# 5. (Optional) Enable Gemini AI
#    Copy .env.example → .env  and set COMMERCEIQ_USE_GEMINI=true
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/overview` | SKU counts, risk summary |
| GET | `/risks` | Full inventory risk table |
| GET | `/products` | Product catalogue |
| GET | `/locations` | All store locations |
| POST | `/recommend` | Calculate transfer recommendation |
| POST | `/approval` | Approve or reject a decision |
| GET | `/audit` | Full audit log + ledger events |
| POST | `/ask` | Natural language Q&A via Gemini |

---

## 🔑 Key Design Choices

### Transparent, Not Black-Box
Forecasting uses a **weighted recent-average** (last 14 days of sales, linearly weighted). Every number is explainable — no model weights, no hidden features.

### Human-in-the-Loop First
AI recommends; **humans approve**. Every transfer recommendation starts as `PENDING_APPROVAL`. The audit trail records who approved what, when, and why.

### Honest About Limitations
- 30% margin assumption is **disclosed** — no fabricated data
- Search/cart signals are zero-valued, not invented
- Approvals update an **in-memory simulated ledger** — no real ERP write in this prototype
- Forecasting is a transparent baseline, not a trained ML model

### Transfer Economics Formula
```
Lost sales avoided  = min(recipient deficit, transfer quantity)
Gross benefit       = avoided × unit price × margin
Transfer cost       = quantity × transfer cost per unit
Net benefit         = gross benefit − transfer cost
```
`EXECUTE_TRANSFER` is recommended only when `qty > 0` AND `net_benefit > 0`.

---

## 📁 Project Structure

```
commerce_iq/
├── src/
│   ├── data/           # Loader, Kaggle adapter, synthetic generator
│   ├── models/         # Forecasting, inventory risk, transfer optimizer
│   ├── agents/         # LangGraph state machine + CommerceTools orchestrator
│   ├── api/            # FastAPI server
│   └── ui/             # Streamlit app
├── data/
│   ├── raw/            # Drop retail_store_inventory.csv here
│   └── DATA_DICTIONARY.md
├── tests/
├── requirements.txt
└── Dockerfile
```

---

## 🏆 AI Builder Cup — What Makes This Different

1. **Gemini is load-bearing, not decorative** — the `/ask` endpoint and AI Analyst tab route questions through a LangGraph agent; Gemini provides business-language explanations layered on deterministic results
2. **Grounded outputs** — the LLM is explicitly instructed *not to change numeric values*, preventing hallucination of financial figures
3. **Full workflow, not a demo toy** — data ingestion → forecasting → risk scoring → transfer optimization → AI explanation → human approval → audit trail is a complete, production-shaped loop
4. **Immediate reproducibility** — synthetic fallback means judges can run it with zero data setup in under 2 minutes

---

*Built for the AI Builder Cup Hackathon*
