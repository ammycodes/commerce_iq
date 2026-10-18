from typing import TypedDict, Any
from src.agents.tools import CommerceTools

class AgentState(TypedDict, total=False):
    question: str
    result: dict[str, Any]
    route: str

def build_graph(tools: CommerceTools):
    try:
        from langgraph.graph import StateGraph, END
        def route(state):
            q = state.get("question", "").lower()
            return {"route": "risk" if any(w in q for w in ("risk", "stockout", "shortage", "deficit")) else "general"}
        def answer(state):
            return {"result": tools.ask(state.get("question", ""))}
        graph = StateGraph(AgentState)
        graph.add_node("route", route)
        graph.add_node("answer", answer)
        graph.set_entry_point("route")
        graph.add_edge("route", "answer")
        graph.add_edge("answer", END)
        return graph.compile()
    except Exception:
        class Fallback:
            def invoke(self, state):
                return {"result": tools.ask(state.get("question", "")), "route": "fallback"}
        return Fallback()

def gemini_explanation(prompt):
    import os
    if os.getenv("COMMERCEIQ_USE_GEMINI", "false").lower() != "true": return None
    try:
        from langchain_google_vertexai import ChatVertexAI
        llm = ChatVertexAI(model_name="gemini-2.0-flash", temperature=0)
        result = llm.invoke("Explain this result in business language. Do not change numeric values.\n" + prompt)
        return str(result.content)
    except Exception as exc:
        return f"Gemini unavailable ({type(exc).__name__}); deterministic result is unchanged."
