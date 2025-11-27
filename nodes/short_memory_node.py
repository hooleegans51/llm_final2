"""
단기 메모리 노드 - 세션 컨텍스트 유지

[역할]
- 현재 턴 정보를 세션 버퍼에 추가
- 최근 N턴만 유지
- 엔티티 추출
"""

from typing import Dict, Any, List
from core.state import AgentState

# 인메모리 세션 저장소 (실제론 Redis 등 사용)
SESSION_STORE: Dict[str, List[Dict]] = {}


def short_memory_node(state: AgentState) -> dict:
    """
    단기 메모리 노드
    
    Input: user_query, final_response, session_id
    Output: short_memory, entities
    """
    
    session_id = state["session_id"]
    
    # 현재 턴 데이터
    current_turn = {
        "query": state["user_query"],
        "response": state.get("final_response", ""),
        "constraints": state.get("user_constraints", {}),
        "timestamp": get_timestamp()
    }
    
    # 세션 버퍼 가져오기 (없으면 생성)
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = []
    
    # 버퍼에 추가
    SESSION_STORE[session_id].append(current_turn)
    
    # 최근 10턴만 유지
    if len(SESSION_STORE[session_id]) > 10:
        SESSION_STORE[session_id] = SESSION_STORE[session_id][-10:]
    
    # 엔티티 추출
    entities = extract_entities(state)
    
    return {
        "short_memory": SESSION_STORE[session_id],
        "entities": entities,
        "current_step": "short_memory_done"
    }


def extract_entities(state: AgentState) -> Dict[str, Any]:
    """간단한 엔티티 추출"""
    entities = {}
    
    query = state["user_query"]
    constraints = state.get("user_constraints", {})
    
    # 예산
    if "budget" in constraints:
        entities["budget"] = constraints["budget"]
    
    # 인원수
    if "servings" in constraints:
        entities["servings"] = constraints["servings"]
    
    # TODO: NER 모델로 음식명, 재료명 등 추출
    
    return entities


def get_timestamp() -> str:
    """현재 시간 반환"""
    from datetime import datetime
    return datetime.now().isoformat()


def clear_session(session_id: str):
    """세션 종료 시 호출"""
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]