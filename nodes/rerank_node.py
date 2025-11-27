"""
Rerank 노드 - 검색 결과 재정렬

[역할]
- 확신도 낮을 때만 실행
- Cross-encoder로 재정렬
- 상위 결과만 유지
"""

from typing import List, Dict
from core.state import AgentState


def rerank_node(state: AgentState) -> dict:
    """
    Rerank 노드
    
    Input: retrieved_docs, search_results, confidence_score
    Output: retrieved_docs (재정렬됨), need_rerank=False
    """
    
    query = state["user_query"]
    docs = state.get("retrieved_docs", [])
    
    if not docs:
        return {
            "need_rerank": False,
            "current_step": "rerank_skipped"
        }
    
    # Cross-encoder로 재정렬
    reranked = cross_encoder_rerank(query, docs)
    
    # 상위 3개만 유지
    top_docs = reranked[:3]
    
    return {
        "retrieved_docs": top_docs,
        "need_rerank": False,  # 재시도 방지
        "confidence_score": 0.8,  # 재정렬 후 신뢰도 상승
        "current_step": "rerank_done"
    }


def cross_encoder_rerank(query: str, docs: List[Dict]) -> List[Dict]:
    """
    Cross-encoder로 재정렬
    
    TODO: 실제 Cross-encoder 모델 사용
    - sentence-transformers/cross-encoder
    - Cohere Rerank API
    """
    
    # 임시: 기존 score 기반 정렬
    # 실제로는 Cross-encoder 점수 계산
    
    scored_docs = []
    for doc in docs:
        # TODO: cross_encoder.predict([(query, doc["content"])])
        score = doc.get("score", 0)
        
        # 쿼리 키워드 매칭 보너스 (임시)
        content = doc.get("content", "").lower()
        query_words = query.lower().split()
        matches = sum(1 for w in query_words if w in content)
        bonus = matches * 0.1
        
        scored_docs.append({
            **doc,
            "rerank_score": score + bonus
        })
    
    # 재정렬
    scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    return scored_docs