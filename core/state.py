"""
LangGraph Agent State 정의

[구조]
1. 1차/2차 LLM 호출 (고정) - 교수님 강조
   - 1차: 초안 + 도구 판단
   - 2차: 도구 결과 반영 → 최종 답변

2. ReAct 패턴 (동적) - 전체 사고 흐름
   - Thought → Action → Observation 반복

3. n차 LLM 호출 추적 - tool_node에서 결과 해석
   - llm_call_count, llm_call_history

[흐름]
main_agent: 1차 LLM → llm_1st_response
    ↓
tool_node: n차 LLM (결과 해석) → llm_call_history
    ↓
main_agent: 2차 LLM → llm_2nd_response → final_response
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages


# ============================================================
# 커스텀 Reducer
# ============================================================

def keep_last_n(n: int):
    """최근 N개만 유지하는 reducer"""
    def reducer(existing: list, new: list) -> list:
        merged = existing + new
        return merged[-n:]
    return reducer


# ============================================================
# ReAct Step 정의
# ============================================================

class ReActStep(TypedDict):
    """ReAct 한 스텝"""
    thought: str                 # 생각
    action: Optional[str]        # 도구 이름 (None이면 최종 답변)
    action_input: Optional[str]  # 도구 입력
    observation: Optional[str]   # 도구 결과 (LLM 해석 포함)


# ============================================================
# LLM 호출 기록 (n차 호출 추적)
# ============================================================

class LLMCallRecord(TypedDict):
    """LLM 호출 기록"""
    call_number: int      # 몇 차 호출인지 (1, 2, 3...)
    call_type: str        # "1st_llm", "2nd_llm", "tool_interpret", "react" 등
    node_name: str        # 어느 노드에서 호출했는지
    input_summary: str    # 입력 요약
    output_summary: str   # 출력 요약


# ============================================================
# Main Agent State
# ============================================================

class AgentState(TypedDict):
    """메인 에이전트 상태"""
    
    # ========================================
    # 1. 대화 히스토리 (누적)
    # ========================================
    messages: Annotated[List[Dict[str, Any]], add_messages]
    
    # ========================================
    # 2. 현재 요청 정보
    # ========================================
    user_query: str
    user_id: str
    session_id: str
    
    # ========================================
    # 3. 사용자 제약조건
    # ========================================
    user_constraints: Dict[str, Any]  # {"budget": 20000, "servings": 2, ...}
    
    # ========================================
    # 4. RAG 검색 결과
    # ========================================
    retrieved_docs: List[Dict[str, Any]]
    
    # ========================================
    # 5. 웹 검색
    # ========================================
    search_queries: List[str]
    search_results: List[Dict[str, Any]]
    
    # ========================================
    # 6. LLM 응답 (1차/2차 고정)
    # ========================================
    llm_1st_response: str   # 1차 LLM: 초안 + 도구 판단
    llm_2nd_response: str   # 2차 LLM: 도구 결과 반영 최종 답변
    final_response: str     # 최종 응답 (llm_2nd 또는 llm_1st)
    
    # ========================================
    # 7. 메모리
    # ========================================
    short_memory: Annotated[List[Dict[str, Any]], keep_last_n(10)]
    long_memory: List[Dict[str, Any]]
    entities: Dict[str, Any]
    
    # ========================================
    # 8. 제어 플래그
    # ========================================
    current_step: str
    need_web_search: bool
    need_rerank: bool
    confidence_score: float
    
    # ========================================
    # 9. System Interrupt (예산 초과 등)
    # ========================================
    constraint_violations: List[Dict[str, Any]]
    awaiting_user_response: bool
    user_interrupt_response: Optional[str]
    
    # ========================================
    # 10. User Interrupt (수정 요청)
    # ========================================
    is_modification_request: bool
    modification_type: Optional[str]
    original_response: str
    modification_request: str

    # ========================================
    # 11. ReAct 관련 (사고 흐름)
    # ========================================
    react_steps: Annotated[List[ReActStep], keep_last_n(10)]
    current_thought: str
    current_action: Optional[str]
    current_action_input: str
    iteration_count: int
    max_iterations: int
    
    # ========================================
    # 12. LLM 호출 추적 (n차 호출)
    # ========================================
    llm_call_count: int
    llm_call_history: Annotated[List[LLMCallRecord], keep_last_n(20)]


# ============================================================
# Modify Agent State
# ============================================================

class ModifyState(TypedDict):
    """수정 에이전트 전용 State"""
    original_response: str
    modification_request: str
    modification_type: str
    short_memory: List[Dict[str, Any]]
    need_re_search: bool
    re_search_results: List[Dict[str, Any]]
    modified_response: str
    changes_made: List[str]


# ============================================================
# 초기 State 생성
# ============================================================

def create_initial_state(
    user_query: str,
    user_id: str = "default_user",
    session_id: str = "default_session",
    user_constraints: Optional[Dict[str, Any]] = None,
    max_iterations: int = 5
) -> AgentState:
    """초기 State 생성"""
    return {
        # 대화
        "messages": [{"role": "user", "content": user_query}],
        "user_query": user_query,
        "user_id": user_id,
        "session_id": session_id,
        
        # 제약조건
        "user_constraints": user_constraints or {},
        
        # RAG/검색
        "retrieved_docs": [],
        "search_queries": [],
        "search_results": [],
        
        # LLM (1차/2차)
        "llm_1st_response": "",
        "llm_2nd_response": "",
        "final_response": "",
        
        # 메모리
        "short_memory": [],
        "long_memory": [],
        "entities": {},
        
        # 제어
        "current_step": "start",
        "need_web_search": False,
        "need_rerank": False,
        "confidence_score": 0.0,
        
        # Interrupt
        "constraint_violations": [],
        "awaiting_user_response": False,
        "user_interrupt_response": None,
        
        # 수정
        "is_modification_request": False,
        "modification_type": None,
        "original_response": "",
        "modification_request": "",

        # ReAct
        "react_steps": [],
        "current_thought": "",
        "current_action": None,
        "current_action_input": "",
        "iteration_count": 0,
        "max_iterations": max_iterations,
        
        # LLM 호출 추적
        "llm_call_count": 0,
        "llm_call_history": [],
    }


# ============================================================
# LLM 호출 기록 헬퍼
# ============================================================

def record_llm_call(
    state: AgentState,
    call_type: str,
    node_name: str,
    input_summary: str,
    output_summary: str
) -> dict:
    """
    LLM 호출 기록 생성
    
    Args:
        state: 현재 State
        call_type: "1st_llm", "2nd_llm", "tool_interpret", "react"
        node_name: "main_agent", "tool_node" 등
        input_summary: 입력 요약
        output_summary: 출력 요약
    
    Returns:
        State 업데이트용 dict (spread해서 사용)
    
    사용 예:
        return {
            "llm_1st_response": response,
            **record_llm_call(state, "1st_llm", "main_agent", query, response[:50])
        }
    """
    new_count = state.get("llm_call_count", 0) + 1
    
    new_record: LLMCallRecord = {
        "call_number": new_count,
        "call_type": call_type,
        "node_name": node_name,
        "input_summary": input_summary[:100],
        "output_summary": output_summary[:100],
    }
    
    return {
        "llm_call_count": new_count,
        "llm_call_history": [new_record],  # Annotated라서 자동 병합
    }




## 📋 전체 흐름

# [사용자 질문]
#       ↓
# [rag_node] ─────────────────────────────────────────┐
#       ↓                                              │
# [main_agent] ◀───────────────────────────────────────┤
#       │                                              │
#       ├─ 🧠 ReAct Thought: "레시피 찾았고, 가격 필요" │
#       ├─ 📝 1차 LLM 호출 → llm_1st_response          │
#       ├─ 🎯 Action: shopping_search                 │
#       ↓                                              │
# [tool_node] ─────────────────────────────────────────┤
#       │                                              │
#       ├─ 🔍 도구 실행 (검색)                         │
#       ├─ 📝 n차 LLM 호출 → llm_call_history          │
#       ├─ 👀 Observation 생성                        │
#       ↓                                              │
# [main_agent] ◀───────────────────────────────────────┘
#       │
#       ├─ 🧠 ReAct Thought: "정보 충분!"
#       ├─ 📝 2차 LLM 호출 → llm_2nd_response
#       ├─ ✅ final_response 설정
#       ↓
# [memory_writer] → [reflection] → END
# ```

# ---

## 📊 LLM 호출 추적 예시

# llm_call_count: 4
# llm_call_history: [
#     {call_number: 1, call_type: "1st_llm", node_name: "main_agent", ...},
#     {call_number: 2, call_type: "tool_interpret", node_name: "tool_node", ...},
#     {call_number: 3, call_type: "tool_interpret", node_name: "tool_node", ...},
#     {call_number: 4, call_type: "2nd_llm", node_name: "main_agent", ...},
# ]

# llm_1st_response: "스테이크 재료: 소고기, 버터... (도구 필요: 가격 검색)"
# llm_2nd_response: "스테이크 재료 목록입니다. 총 비용: 35,000원..."
# final_response: (llm_2nd_response와 동일)