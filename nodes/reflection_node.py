"""
Reflection 노드 - 메모리 반영 + 확신도 계산

[역할]
- 장기 메모리에서 관련 정보 검색
- 단기 메모리 컨텍스트 확인
- 초안에 메모리 반영
- 확신도 계산 (rerank 필요 여부 판단)
"""

from typing import List, Dict, Any
from core.state import AgentState


def reflection_node(state: AgentState) -> dict:
    """
    Reflection 노드
    
    Input: final_response, short_memory, long_memory, retrieved_docs
    Output: refined_response, confidence_score, need_rerank
    """
    
    query = state["user_query"]
    response = state.get("final_response", "")
    user_id = state["user_id"]
    
    # 1. 장기 메모리에서 관련 정보 검색
    relevant_memories = search_long_memory(query, user_id)
    
    # 2. 단기 메모리에서 컨텍스트 확인
    short_context = get_short_context(state.get("short_memory", []))
    
    # 3. 메모리 반영하여 응답 개선
    refined_response = refine_response(
        original=response,
        memories=relevant_memories,
        context=short_context
    )
    
    # 4. 확신도 계산
    confidence = calculate_confidence(state)
    
    # 5. rerank 필요 여부
    need_rerank = confidence < 0.7
    
    return {
        "final_response": refined_response,
        "confidence_score": confidence,
        "need_rerank": need_rerank,
        "current_step": "reflection_done"
    }


def search_long_memory(query: str, user_id: str, top_k: int = 3) -> List[Dict]:
    """장기 메모리에서 관련 정보 검색"""
    try:
        from rag.embedder import get_embedding
        from rag.vector_db import search_similar
        
        embedding = get_embedding(query)
        
        results = search_similar(
            embedding=embedding,
            filter={"user_id": user_id},
            top_k=top_k
        )
        
        return results or []
    except Exception as e:
        print(f"[reflection] 장기 메모리 검색 오류: {e}")
        return []


def get_short_context(short_memory: List[Dict]) -> str:
    """단기 메모리에서 컨텍스트 추출"""
    if not short_memory:
        return ""
    
    # 최근 3턴만
    recent = short_memory[-3:]
    
    context_parts = []
    for turn in recent:
        context_parts.append(f"Q: {turn.get('query', '')}")
        context_parts.append(f"A: {turn.get('response', '')[:100]}")
    
    return "\n".join(context_parts)


def refine_response(
    original: str,
    memories: List[Dict],
    context: str
) -> str:
    """메모리 기반 응답 개선"""
    
    if not memories and not context:
        return original
    
    # TODO: LLM으로 개선
    # 지금은 간단히 메모리 정보 추가
    
    additions = []
    
    for mem in memories:
        mem_type = mem.get("metadata", {}).get("type", "")
        content = mem.get("metadata", {}).get("content", "")
        
        if mem_type == "allergy":
            additions.append(f"⚠️ 참고: {content}")
        elif mem_type == "preference":
            additions.append(f"💡 선호도 반영: {content}")
    
    if additions:
        return original + "\n\n" + "\n".join(additions)
    
    return original


def calculate_confidence(state: AgentState) -> float:
    """
    확신도 계산
    
    [고려 요소]
    - RAG 검색 결과 품질
    - 검색 결과 개수
    - 출처 다양성
    """
    
    score = 0.5  # 기본값
    
    # RAG 결과
    docs = state.get("retrieved_docs", [])
    if docs:
        avg_score = sum(d.get("score", 0) for d in docs) / len(docs)
        score += avg_score * 0.3
    
    # 검색 결과
    search_results = state.get("search_results", [])
    if search_results:
        score += min(len(search_results) / 10, 0.2)
    
    # 제약조건 위반 없음
    if not state.get("constraint_violations"):
        score += 0.1
    
    return min(score, 1.0)