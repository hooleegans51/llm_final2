"""
장기 메모리 노드 - 영구 저장

[역할]
- 저장 가치 판단
- 벡터DB에 임베딩 저장
- 중복 체크
"""

from typing import Dict, Any, Optional
from core.state import AgentState


# 메모리 타입 정의
MEMORY_TYPES = {
    "preference": "사용자 선호도",      # 예: "매운 거 좋아함"
    "allergy": "알레르기/제한사항",     # 예: "견과류 알레르기"
    "history": "과거 요청 이력",        # 예: "지난주 스테이크 재료 구매"
    "feedback": "피드백"               # 예: "가격이 너무 비쌌음"
}


def long_memory_node(state: AgentState) -> dict:
    """
    장기 메모리 노드
    
    Input: user_query, final_response, user_id
    Output: long_memory (업데이트됨)
    """
    
    user_id = state["user_id"]
    query = state["user_query"]
    response = state.get("final_response", "")
    
    # 저장 가치 판단
    memory_content = judge_memory_value(state)
    
    if not memory_content:
        return {"current_step": "long_memory_skipped"}
    
    # 중복 체크
    if is_duplicate(user_id, memory_content["text"]):
        return {"current_step": "long_memory_duplicate"}
    
    # 임베딩 생성 및 저장
    try:
        from rag.embedder import get_embedding
        embedding = get_embedding(memory_content["text"])
    except Exception as e:
        print(f"[long_memory] 임베딩 생성 오류: {e}")
        embedding = [0.0] * 1536  # Mock 임베딩
    
    memory_id = save_memory(
        user_id=user_id,
        content=memory_content["text"],
        memory_type=memory_content["type"],
        embedding=embedding,
        metadata={
            "query": query,
            "response": response[:200],  # 일부만
            "timestamp": get_timestamp()
        }
    )
    
    # 저장된 메모리를 State에 추가
    new_memory = {
        "id": memory_id,
        "content": memory_content["text"],
        "type": memory_content["type"]
    }
    
    return {
        "long_memory": state.get("long_memory", []) + [new_memory],
        "current_step": "long_memory_done"
    }


def judge_memory_value(state: AgentState) -> Optional[Dict[str, str]]:
    """
    저장 가치 판단
    
    TODO: LLM으로 판단하거나 규칙 기반
    """
    query = state["user_query"].lower()
    
    # 규칙 기반 예시
    if "알레르기" in query or "못 먹" in query:
        return {
            "type": "allergy",
            "text": f"사용자 제한사항: {state['user_query']}"
        }
    
    if "좋아" in query or "선호" in query or "싫어" in query:
        return {
            "type": "preference",
            "text": f"사용자 선호: {state['user_query']}"
        }
    
    # 예산 정보
    if state.get("user_constraints", {}).get("budget"):
        budget = state["user_constraints"]["budget"]
        return {
            "type": "preference",
            "text": f"사용자 예산 선호: {budget:,}원"
        }
    
    return None


def is_duplicate(user_id: str, text: str, threshold: float = 0.95) -> bool:
    """중복 메모리 체크"""
    try:
        from rag.embedder import get_embedding
        from rag.vector_db import search_similar
        
        embedding = get_embedding(text)
        
        # 유사한 메모리 검색
        similar = search_similar(
            embedding=embedding,
            filter={"user_id": user_id},
            top_k=1
        )
        
        if similar and similar[0].get("score", 0) > threshold:
            return True
    except Exception as e:
        print(f"[long_memory] 중복 체크 오류: {e}")
    
    return False


def save_memory(
    user_id: str,
    content: str,
    memory_type: str,
    embedding: list,
    metadata: dict
) -> str:
    """벡터DB에 메모리 저장"""
    import uuid
    
    memory_id = str(uuid.uuid4())
    
    try:
        from rag.vector_db import upsert_vectors
        
        upsert_vectors(
            ids=[memory_id],
            embeddings=[embedding],
            metadatas=[{
                "user_id": user_id,
                "content": content,
                "type": memory_type,
                **metadata
            }]
        )
    except Exception as e:
        print(f"[long_memory] 메모리 저장 오류: {e}")
    
    return memory_id


def get_timestamp() -> str:
    from datetime import datetime
    return datetime.now().isoformat()