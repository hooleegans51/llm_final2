"""
RAG 노드 - 단순화
"""

from core.state import AgentState


def rag_node(state: AgentState) -> dict:
    print(f"[rag_node] 진입 - query: {state['user_query'][:30]}")
    print("[rag_node] 완료")
    
    return {
        "retrieved_docs": [],
        "current_step": "rag_done"
    }