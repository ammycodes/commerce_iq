from uuid import uuid4

def evaluate_transfer(*, sku, source_location, destination_location, source_on_hand,
                      destination_on_hand, destination_deficit, unit_price, margin,
                      transfer_cost_per_unit=5.0, requested_quantity=None):
    donor_surplus = max(0, int(source_on_hand))
    need = max(0, int(destination_deficit))
    feasible = min(donor_surplus, need)
    qty = feasible if requested_quantity is None else min(max(0, int(requested_quantity)), feasible)
    avoided = min(need, qty)
    gross = avoided * max(0.0, float(unit_price)) * max(0.0, float(margin))
    cost = qty * max(0.0, float(transfer_cost_per_unit))
    net = gross - cost
    return {"decision_id": str(uuid4())[:8], "sku": str(sku), "source_location": str(source_location),
        "destination_location": str(destination_location), "source_on_hand": int(source_on_hand),
        "destination_on_hand": int(destination_on_hand), "destination_deficit": need,
        "transfer_quantity": qty, "lost_sales_avoided": avoided, "unit_price": float(unit_price),
        "margin": float(margin), "transfer_cost_per_unit": float(transfer_cost_per_unit),
        "gross_benefit": round(gross, 2), "transfer_cost": round(cost, 2), "net_benefit": round(net, 2),
        "recommendation": "EXECUTE_TRANSFER" if qty > 0 and net > 0 else "ABSORB_LOSS",
        "feasible": qty > 0, "status": "PENDING_APPROVAL"}

def find_best_donor(risks, sku, destination):
    recipient = risks[(risks.sku.astype(str) == str(sku)) & (risks.location.astype(str) == str(destination))]
    if recipient.empty: return None
    need = int(recipient.iloc[0].deficit)
    donors = risks[(risks.sku.astype(str) == str(sku)) & (risks.location.astype(str) != str(destination))].copy()
    donors["surplus"] = (donors.on_hand - donors.required_stock).clip(lower=0)
    donors = donors[donors.surplus > 0].sort_values("surplus", ascending=False)
    if donors.empty or need <= 0: return None
    return {"source": str(donors.iloc[0].location), "surplus": int(donors.iloc[0].surplus), "need": need}
