"""
Supervisor - 요청 분류 및 에이전트 라우팅

[역할]
1. 사용자 입력 분석
2. 수정 요청인지, 새 요청인지 판단
3. 적절한 에이전트로 라우팅 (main_agent / modify_agent)

[판단 기준]
- 수정 요청: "바꿔줘", "변경해줘", "대신", "2인분으로" 등
- 새 요청: 그 외 모든 요청
"""

from typing import Dict, Any
from core.state import AgentState


# ============================================================
# 수정 요청 키워드
# ============================================================

MODIFICATION_KEYWORDS = [
    # 인원수 변경
    "인분으로", "명으로", "사람으로",
    # 재료 변경
    "대신", "바꿔", "빼줘", "넣어줘", "추가해", "제외",
    # 양 조절
    "늘려", "줄여", "더", "덜",
    # 예산 변경
    "저렴하게", "비싸게", "예산",
    # 선호도
    "맵게", "안맵게", "달게", "짜게", "싱겁게",
    # 일반 수정
    "수정", "변경", "고쳐", "다시"
]


# ============================================================
# Supervisor 노드
# ============================================================

def supervisor_node(state: AgentState) -> dict:
    """
    Supervisor 노드 - 요청 분류
    
    [Input] user_query, original_response (있으면)
    [Output] is_modification_request, modification_type
    """
    
    query = state.get("user_query", "")
    has_previous_response = bool(state.get("original_response") or state.get("final_response"))
    
    # 수정 요청 판단
    is_modification = is_modification_request(query, has_previous_response)
    
    if is_modification:
        mod_type = classify_modification_type(query)
        return {
            "is_modification_request": True,
            "modification_type": mod_type,
            "modification_request": query,
            "original_response": state.get("final_response", ""),
            "current_step": "supervisor_to_modify"
        }
    else:
        return {
            "is_modification_request": False,
            "modification_type": None,
            "current_step": "supervisor_to_main"
        }


def is_modification_request(query: str, has_previous: bool) -> bool:
    """
    수정 요청인지 판단
    
    조건:
    1. 이전 응답이 있어야 함 (수정할 대상 필요)
    2. 수정 키워드가 있어야 함
    """
    
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
    
    # 인원수 변경
    if any(kw in query_lower for kw in ["인분", "명", "사람"]):
        return "servings"
    
    # 재료 변경
    if any(kw in query_lower for kw in ["재료", "대신", "바꿔", "빼", "넣어", "추가", "제외"]):
        return "ingredient"
    
    # 예산 변경
    if any(kw in query_lower for kw in ["예산", "가격", "저렴", "비싼", "싸게"]):
        return "budget"
    
    # 선호도 변경
    if any(kw in query_lower for kw in ["맵", "달", "짜", "싱거", "매운", "단", "짠"]):
        return "preference"
    
    # 양 조절
    if any(kw in query_lower for kw in ["늘려", "줄여", "더", "덜"]):
        return "quantity"
    
    return "general"


# ============================================================
# 라우팅 함수 (graph.py에서 사용)
# ============================================================

def route_after_supervisor(state: AgentState) -> str:
    """
    supervisor 후 라우팅
    
    - is_modification_request = True → modify_agent
    - is_modification_request = False → main_agent
    """
    
    if state.get("is_modification_request"):
        return "modify_agent"
    return "main_agent"