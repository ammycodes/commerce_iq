from src.data.loader import RetailDataLoader
from src.models.inventory_risk import analyze_inventory
from src.models.optimizer import evaluate_transfer, find_best_donor

class CommerceTools:
    def __init__(self, data_dir="data/raw"):
        self.data = RetailDataLoader(data_dir).load()
        self.decisions = {}
        self.audit_log = []
        self.ledger_events = []

    def risks(self):
        return analyze_inventory(self.data["sales"], self.data["inventory"], self.data.get("signals"))

    def overview(self):
        r = self.risks()
        return {"sku_count": int(self.data["products"].sku.nunique()),
                "location_count": int(self.data["inventory"].location.nunique()),
                "high_risk_count": int((r.risk_level == "HIGH").sum()),
                "medium_risk_count": int((r.risk_level == "MEDIUM").sum()),
                "total_deficit_units": int(r.deficit.sum()),
                "data_source": self.data["source"].iloc[0].to_dict()}

    def recommend(self, sku, destination, transfer_cost_per_unit=5.0):
        risks = self.risks()
        recipient = risks[(risks.sku.astype(str) == str(sku)) & (risks.location.astype(str) == str(destination))]
        if recipient.empty: raise ValueError(f"No risk record for {sku} at {destination}")
        rec = recipient.iloc[0]
        donor = find_best_donor(risks, sku, destination)
        prod = self.data["products"][self.data["products"].sku.astype(str) == str(sku)]
        price = float(prod.iloc[0].unit_price) if not prod.empty else 100.0
        margin = float(prod.iloc[0].margin) if not prod.empty else .3
        source = donor["source"] if donor else "NO_DONOR"
        donor_row = risks[(risks.sku.astype(str) == str(sku)) & (risks.location.astype(str) == source)]
        source_stock = int(donor_row.iloc[0].on_hand) if not donor_row.empty else 0
        source_surplus = int(donor["surplus"]) if donor else 0
        decision = evaluate_transfer(sku=sku, source_location=source, destination_location=destination,
            source_on_hand=source_surplus, destination_on_hand=int(rec.on_hand),
            destination_deficit=int(rec.deficit), unit_price=price, margin=margin,
            transfer_cost_per_unit=transfer_cost_per_unit)
        decision["explanation"] = "Python rules calculated the forecast-based deficit, feasible quantity, gross benefit, transfer cost, and net benefit. Manager approval is required."
        self.decisions[decision["decision_id"]] = decision
        return decision

    def approve(self, decision_id, approved, manager="demo-manager", comment=""):
        decision = self.decisions.get(decision_id)
        if not decision: raise ValueError("Decision not found; calculate a recommendation first.")
        if decision["status"] != "PENDING_APPROVAL": raise ValueError("This decision has already been reviewed.")
        decision["status"] = "APPROVED" if approved else "REJECTED"
        event = {"decision_id": decision_id, "approved": bool(approved), "manager": manager,
                 "comment": comment, "event": decision["status"]}
        self.audit_log.append(event)
        if approved and decision["transfer_quantity"] > 0:
            self.ledger_events.append({"event": "SIMULATED_INVENTORY_TRANSFER", "decision_id": decision_id,
                "sku": decision["sku"], "source_location": decision["source_location"],
                "destination_location": decision["destination_location"],
                "quantity": decision["transfer_quantity"]})
        return event

    def ask(self, question):
        q = question.lower()
        overview = self.overview()
        if any(x in q for x in ["risk", "stockout", "shortage", "deficit"]):
            rows = self.risks().sort_values("deficit", ascending=False).head(8)
            return {"answer": f"There are {overview['high_risk_count']} high-risk SKU-location pairs and {overview['total_deficit_units']} modeled deficit units.",
                    "evidence": rows[["sku", "location", "on_hand", "forecast_units", "deficit", "risk_level"]].to_dict("records")}
        return {"answer": f"CommerceIQ tracks {overview['sku_count']} SKUs across {overview['location_count']} locations. Ask about inventory risk or use the Decision Workbench for a transfer calculation.",
                "evidence": []}
