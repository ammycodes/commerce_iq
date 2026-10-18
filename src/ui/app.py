import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from src.agents.tools import CommerceTools
from src.agents.state_machine import build_graph, gemini_explanation

load_dotenv()
st.set_page_config(page_title="CommerceIQ", page_icon="📦", layout="wide")
@st.cache_resource
def get_tools():
    return CommerceTools(os.getenv("COMMERCEIQ_DATA_DIR", "data/raw"))
tools = get_tools()
if "decision" not in st.session_state: st.session_state.decision = None
if "history" not in st.session_state: st.session_state.history = []
risks = tools.risks()
overview = tools.overview()
st.title("CommerceIQ | Commerce Command Center")
st.caption("Predict demand. Optimize inventory. Make smarter commerce decisions.")
st.info("Prototype: approvals affect an in-memory simulated ledger only. No real ERP or warehouse is connected.")
t1, t2, t3 = st.tabs(["Executive Overview", "Decision Workbench", "AI Analyst"])

with t1:
    a,b,c,d = st.columns(4)
    a.metric("SKUs", overview["sku_count"])
    b.metric("Locations", overview["location_count"])
    c.metric("High-risk pairs", overview["high_risk_count"])
    d.metric("Modeled deficit units", f"{overview['total_deficit_units']:,}")
    st.subheader("Largest inventory deficits")
    chart_data = risks.sort_values("deficit", ascending=False).head(30)
    st.plotly_chart(px.bar(chart_data, x="sku", y="deficit", color="risk_level", facet_col="location",
                           facet_col_wrap=2), use_container_width=True)
    st.dataframe(risks[["sku","location","on_hand","daily_forecast","forecast_units","safety_stock",
                        "deficit","cover_days","risk_level","searches","cart_additions"]],
                 use_container_width=True, hide_index=True)
    st.caption(f"Data: {overview['data_source']['mode']} | CSV files found: {overview['data_source']['csv_files_found']}")

with t2:
    st.subheader("Evaluate a transfer")
    skus = sorted(tools.data["products"].sku.astype(str).unique())
    sku = st.selectbox("SKU", skus, index=skus.index("SKU_001") if "SKU_001" in skus else 0)
    subset = risks[risks.sku.astype(str) == sku]
    destinations = sorted(subset.location.astype(str).unique())
    dest = st.selectbox("Destination location", destinations, index=destinations.index("HYD-01") if "HYD-01" in destinations else 0)
    cost = st.number_input("Transfer cost per unit", min_value=0.0, value=5.0, step=1.0)
    if st.button("Calculate recommendation", type="primary"):
        st.session_state.decision = tools.recommend(sku, dest, cost)
    decision = st.session_state.decision
    if decision:
        x1,x2,x3,x4 = st.columns(4)
        x1.metric("Transfer quantity", f"{decision['transfer_quantity']:,}")
        x2.metric("Gross benefit", f"${decision['gross_benefit']:,.2f}")
        x3.metric("Transfer cost", f"${decision['transfer_cost']:,.2f}")
        x4.metric("Net benefit", f"${decision['net_benefit']:,.2f}")
        st.write(f"**Recommendation:** `{decision['recommendation']}`")
        st.write(f"**Route:** {decision['source_location']} → {decision['destination_location']}")
        st.write(decision["explanation"])
        manager = st.text_input("Manager name", "demo-manager")
        comment = st.text_input("Approval comment", "")
        ca, cr = st.columns(2)
        with ca:
            if st.button("Approve transfer", disabled=decision["status"] != "PENDING_APPROVAL"):
                st.success(tools.approve(decision["decision_id"], True, manager, comment)["event"])
                st.rerun()
        with cr:
            if st.button("Reject recommendation", disabled=decision["status"] != "PENDING_APPROVAL"):
                st.warning(tools.approve(decision["decision_id"], False, manager, comment)["event"])
                st.rerun()
    if tools.audit_log:
        st.subheader("Audit trail")
        st.dataframe(pd.DataFrame(tools.audit_log), use_container_width=True, hide_index=True)
    if tools.ledger_events:
        st.subheader("Simulated inventory ledger")
        st.dataframe(pd.DataFrame(tools.ledger_events), use_container_width=True, hide_index=True)

with t3:
    st.subheader("Ask the CommerceIQ analyst")
    with st.form("ask_form", clear_on_submit=True):
        question = st.text_input("Question", placeholder="Which locations have the highest stockout risk?")
        submitted = st.form_submit_button("Ask")
    if submitted and question.strip():
        result = build_graph(tools).invoke({"question": question}).get("result", tools.ask(question))
        explanation = gemini_explanation(f"Question: {question}\nResult: {result}")
        if explanation: result["gemini_explanation"] = explanation
        st.session_state.history.append({"question": question, "result": result})
    for item in reversed(st.session_state.history):
        st.markdown("**You:** " + item["question"])
        st.write(item["result"].get("answer", "No answer"))
        if item["result"].get("gemini_explanation"): st.caption(item["result"]["gemini_explanation"])
        if item["result"].get("evidence"): st.dataframe(pd.DataFrame(item["result"]["evidence"]), hide_index=True)
        st.divider()
