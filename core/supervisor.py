"""
Supervisor - 요청 분류 및 에이전트 라우팅 (수정본)
"""

from typing import Dict, Any
from core.state import AgentState


MODIFICATION_KEYWORDS = [
    "인분으로", "명으로", "사람으로",
    "대신", "바꿔", "빼줘", "넣어줘", "추가해", "제외",
    "늘려", "줄여", "더", "덜",
    "저렴하게", "비싸게", "예산",
    "맵게", "안맵게", "달게", "짜게", "싱겁게",
    "수정", "변경", "고쳐", "다시"
]


def supervisor_node(state: AgentState) -> dict:
    """Supervisor 노드"""
    print(f"[supervisor] 진입 - query: {state.get('user_query', '')[:30]}")
    
    query = state.get("user_query", "")
    has_previous_response = bool(state.get("original_response") or state.get("final_response"))
    
    is_modification = is_modification_request(query, has_previous_response)
    
    if is_modification:
        mod_type = classify_modification_type(query)
        print(f"[supervisor] 수정 요청 → modify_agent")
        return {
            "is_modification_request": True,
            "modification_type": mod_type,
            "modification_request": query,
            "original_response": state.get("final_response", ""),
            "current_step": "supervisor_to_modify"
        }
    else:
        print(f"[supervisor] 새 요청 → main_agent")
        return {
            "is_modification_request": False,
            "modification_type": None,
            "current_step": "supervisor_to_main"
        }


def is_modification_request(query: str, has_previous: bool) -> bool:
    """수정 요청인지 판단"""
    if not has_previous:
        return False
    
    query_lower = query.lower()
    for keyword in MODIFICATION_KEYWORDS:
        if keyword in query_lower:
            return True
    
    return False


def classify_modification_type(query: str) -> str:
    """수정 유형 분류"""
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in ["인분", "명", "사람"]):
        return "servings"
    if any(kw in query_lower for kw in ["재료", "대신", "바꿔", "빼", "넣어", "추가", "제외"]):
        return "ingredient"
    if any(kw in query_lower for kw in ["예산", "가격", "저렴", "비싼", "싸게"]):
        return "budget"
    if any(kw in query_lower for kw in ["맵", "달", "짜", "싱거", "매운", "단", "짠"]):
        return "preference"
    
    return "general"


def route_after_supervisor(state: AgentState) -> str:
    """supervisor 후 라우팅"""
    if state.get("is_modification_request"):
        print("[route] supervisor → modify_agent")
        return "modify_agent"
    print("[route] supervisor → main_agent")
    return "main_agent"