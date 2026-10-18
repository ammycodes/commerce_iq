import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.agents.tools import CommerceTools
from src.agents.state_machine import build_graph

load_dotenv()
tools = CommerceTools(os.getenv("COMMERCEIQ_DATA_DIR", "data/raw"))
graph = build_graph(tools)
app = FastAPI(title="CommerceIQ API", version="0.1.0")

class RecommendationInput(BaseModel):
    sku: str
    destination: str
    transfer_cost_per_unit: float = Field(default=5.0, ge=0)

class AskInput(BaseModel):
    question: str

class ApprovalInput(BaseModel):
    decision_id: str
    approved: bool
    manager: str = "demo-manager"
    comment: str = ""

@app.get("/health")
def health():
    return {"status": "ok", "service": "commerceiq"}

@app.get("/overview")
def overview():
    return tools.overview()

@app.get("/risks")
def risks():
    return tools.risks().to_dict("records")

@app.get("/products")
def products():
    return tools.data["products"].to_dict("records")

@app.get("/locations")
def locations():
    return sorted(tools.data["inventory"].location.astype(str).unique().tolist())

@app.post("/recommend")
def recommend(payload: RecommendationInput):
    try: return tools.recommend(payload.sku, payload.destination, payload.transfer_cost_per_unit)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc))

@app.post("/approval")
def approval(payload: ApprovalInput):
    try: return tools.approve(payload.decision_id, payload.approved, payload.manager, payload.comment)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc))

@app.get("/audit")
def audit():
    return {"audit": tools.audit_log, "ledger_events": tools.ledger_events}

@app.post("/ask")
def ask(payload: AskInput):
    result = graph.invoke({"question": payload.question})
    return result.get("result", tools.ask(payload.question))
