"""
수정 에이전트 - User Interrupt 처리

[역할]
- 사용자 수정 요청 처리 ("2인분으로 바꿔줘", "매운 걸로" 등)
- 수정 유형 분류
- 재검색 필요 여부 판단
- 수정된 응답 생성

[트리거] supervisor에서 is_modification_request = True일 때 라우팅됨
"""

from typing import Dict, Any, List
from core.state import AgentState


def modify_agent_node(state: AgentState) -> dict:
    """
    수정 에이전트 노드
    
    [Input] original_response, modification_request, modification_type
    [Output] final_response (수정된 응답)
    """
    
    original = state.get("original_response", "")
    request = state.get("modification_request", state.get("user_query", ""))
    mod_type = state.get("modification_type") or classify_modification(request)
    
    # 원본 응답이 없으면 에러
    if not original:
        return {
            "final_response": "수정할 이전 응답이 없습니다. 먼저 요청을 해주세요.",
            "current_step": "modify_error"
        }
    
    # 재검색 필요 여부 판단
    need_search = judge_need_research(mod_type, request)
    
    # 재검색 실행 (필요시)
    search_results = []
    if need_search:
        search_results = execute_modification_search(request, mod_type)
    
    # 수정 LLM 호출
    modified, changes = call_modify_llm(
        original=original,
        request=request,
        mod_type=mod_type,
        search_results=search_results,
        short_memory=state.get("short_memory", [])
    )
    
    return {
        "final_response": modified,
        "original_response": original,
        "modification_type": mod_type,
        "current_step": "modify_complete"
    }


def classify_modification(request: str) -> str:
    """수정 유형 분류"""
    request_lower = request.lower()
    
    if any(kw in request_lower for kw in ["인분", "명", "사람"]):
        return "servings"
    elif any(kw in request_lower for kw in ["재료", "대신", "바꿔", "빼"]):
        return "ingredient"
    elif any(kw in request_lower for kw in ["예산", "가격", "저렴", "비싼"]):
        return "budget"
    elif any(kw in request_lower for kw in ["매운", "싱거운", "달게", "짜게"]):
        return "preference"
    else:
        return "general"


def judge_need_research(mod_type: str, request: str) -> bool:
    """재검색 필요 여부 판단"""
    
    if mod_type == "budget":
        return True
    if mod_type == "ingredient":
        if any(kw in request for kw in ["대신", "대체"]):
            return True
    
    return False


def execute_modification_search(request: str, mod_type: str) -> List[Dict]:
    """수정용 재검색 실행"""
    # TODO: 실제 검색 실행
    return []


def call_modify_llm(
    original: str,
    request: str,
    mod_type: str,
    search_results: List[Dict],
    short_memory: List[Dict]
) -> tuple:
    """수정 LLM 호출"""
    
    # TODO: 실제 LLM 호출
    modified, changes = mock_modify_response(original, request, mod_type)
    
    return modified, changes


def mock_modify_response(original: str, request: str, mod_type: str) -> tuple:
    """Mock 수정 응답"""
    
    changes = []
    modified = original
    
    if mod_type == "servings":
        import re
        match = re.search(r'(\d+)\s*인분', request)
        if match:
            new_servings = match.group(1)
            modified = f"[{new_servings}인분으로 조정됨]\n\n" + original
            changes.append(f"인원수를 {new_servings}인분으로 변경")
    
    elif mod_type == "ingredient":
        modified = f"[재료 변경 적용됨]\n\n" + original
        changes.append("재료 변경 적용")
    
    elif mod_type == "budget":
        modified = f"[예산 조정됨]\n\n" + original
        changes.append("예산에 맞게 조정")
    
    elif mod_type == "preference":
        modified = f"[선호도 반영됨]\n\n" + original
        changes.append("선호도 반영")
    
    else:
        modified = f"[수정됨]\n\n" + original
        changes.append("일반 수정 적용")
    
    return modified, changes