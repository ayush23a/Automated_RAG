from langgraph.graph import StateGraph, START, END
from server.state import RAGState
from server.nodes import (
    intent_classifier_node,
    strategy_router,
    doc_rag_node,
    web_search_node,
    final_synthesizer_node
)

def build_agent_graph():
    workflow = StateGraph(RAGState)
    
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("doc_rag", doc_rag_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("final_synthesizer", final_synthesizer_node)
    
    workflow.add_edge(START, "intent_classifier")
    
    workflow.add_conditional_edges(
        "intent_classifier",
        strategy_router,
        {
            "doc_rag_node": "doc_rag",
            "web_search_node": "web_search",
            "final_synthesizer_node": "final_synthesizer"
        }
    )
    
    def post_doc_rag_router(state: RAGState):
        intent = state.get("intent", "casual")
        if intent in ["mixed", "deep_research"]:
            return "web_search"
        return "final_synthesizer"
        
    workflow.add_conditional_edges(
        "doc_rag",
        post_doc_rag_router,
        {
            "web_search": "web_search",
            "final_synthesizer": "final_synthesizer"
        }
    )
    
    workflow.add_edge("web_search", "final_synthesizer")
    workflow.add_edge("final_synthesizer", END)
    
    return workflow.compile()

agent_graph = build_agent_graph()

def rag_agent(query: str, session_id: str = "default"):
    initial_state = {
        "query": query,
        "session_id": session_id,
        "intent": "casual",
        "documents": [],
        "web_results": [],
        "final_answer": "",
        "sources": []
    }
    
    result = agent_graph.invoke(initial_state)
    
    return {
        "answer": result.get("final_answer", "No answer generated."),
        "sources": result.get("sources", []),
        "intent": result.get("intent", "unknown")
    }
