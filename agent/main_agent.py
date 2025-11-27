"""
메인 에이전트 노드

[역할]
1. 1차 LLM 호출: 초안 + 도구 판단 (ReAct Thought/Action)
2. 2차 LLM 호출: 도구 결과 반영 → 최종 답변
3. System Interrupt 발생 (예산 초과 등)

[흐름]
1차 LLM → (도구 필요시) tool_node → 2차 LLM → 완료
"""

import os
import json
from typing import Dict, Any

from dotenv import load_dotenv
from langgraph.types import interrupt

from core.state import AgentState, ReActStep, record_llm_call
from core.prompts import (
    build_first_llm_prompt,
    build_second_llm_prompt,
    build_react_prompt,
    parse_react_response,
    format_search_results
)

load_dotenv()

# ============================================================
# OpenAI 클라이언트 설정
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

# OpenAI 클라이언트
_client = None

def get_openai_client():
    """OpenAI 클라이언트 싱글톤"""
    global _client
    if _client is None and OPENAI_API_KEY:
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            print(f"[main_agent] OpenAI 초기화 실패: {e}")
    return _client


def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """
    OpenAI LLM 호출
    
    Args:
        system_prompt: 시스템 프롬프트
        user_prompt: 사용자 프롬프트
        json_mode: JSON 응답 모드 여부
    
    Returns:
        LLM 응답 텍스트
    """
    client = get_openai_client()
    
    if client is None:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정하세요.")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    kwargs = {
        "model": CHAT_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


# ============================================================
# 메인 에이전트 노드
# ============================================================

def main_agent_node(state: AgentState) -> dict:
    """
    메인 에이전트 노드
    
    [단계]
    1. Interrupt 체크/처리
    2. 1차 LLM (초안 + 도구 판단)
    3. 2차 LLM (도구 결과 반영)
    """
    
    # =========================================
    # 1. System Interrupt 체크
    # =========================================
    if state["constraint_violations"] and not state["user_interrupt_response"]:
        violation = state["constraint_violations"][0]
        
        # interrupt() 호출 → 그래프 멈춤
        user_choice = interrupt({
            "type": violation["type"],
            "message": f"예산을 {violation.get('diff', 0):,}원 초과합니다. 어떻게 할까요?",
            "options": ["계속 진행", "저렴한 대안 찾기", "취소"]
        })
        
        return {
            "user_interrupt_response": user_choice,
            "current_step": "interrupt_resolved"
        }
    
    # =========================================
    # 2. Interrupt 응답 처리
    # =========================================
    if state["user_interrupt_response"]:
        return handle_interrupt_response(state)
    
    # =========================================
    # 3. 최대 반복 체크 (ReAct 무한루프 방지)
    # =========================================
    if state["iteration_count"] >= state["max_iterations"]:
        return {
            "final_response": generate_forced_answer(state),
            "current_step": "max_iteration_reached"
        }
    
    # =========================================
    # 4. 1차 LLM 호출 (아직 안 했으면)
    # =========================================
    if not state["llm_1st_response"]:
        return call_first_llm(state)
    
    # =========================================
    # 5. 2차 LLM 호출 (도구 결과 있으면)
    # =========================================
    if state["search_results"] and not state["llm_2nd_response"]:
        return call_second_llm(state)
    
    # =========================================
    # 6. 도구 불필요 → 1차 응답이 최종
    # =========================================
    if state["llm_1st_response"] and not state["need_web_search"]:
        return {
            "final_response": state["llm_1st_response"],
            "current_step": "complete"
        }
    
    # 도구 실행 대기 중
    return {"current_step": "waiting_tool"}


# ============================================================
# Interrupt 처리
# ============================================================

def handle_interrupt_response(state: AgentState) -> dict:
    """Interrupt 응답 처리"""
    response = state["user_interrupt_response"]
    
    if response == "취소":
        return {
            "final_response": "작업을 취소했습니다.",
            "current_step": "cancelled"
        }
    
    elif response == "저렴한 대안 찾기":
        # 상태 리셋하고 대안 찾기
        return {
            "llm_1st_response": "",
            "llm_2nd_response": "",
            "search_results": [],
            "constraint_violations": [],
            "user_interrupt_response": None,
            "need_web_search": True,
            "search_queries": [f"{state['user_query']} 저렴한 대안"],
            "current_thought": "사용자가 저렴한 대안을 원한다. 더 저렴한 옵션을 찾아보자.",
            "iteration_count": state["iteration_count"] + 1,
            "current_step": "finding_alternative"
        }
    
    else:  # "계속 진행"
        return {
            "user_interrupt_response": None,
            "constraint_violations": [],
            "current_step": "continue"
        }


# ============================================================
# 1차 LLM 호출
# ============================================================

def call_first_llm(state: AgentState) -> dict:
    """
    1차 LLM 호출
    - 초안 생성
    - 도구 필요 판단 (ReAct: Thought → Action)
    """
    
    # 프롬프트 생성
    system_prompt, user_prompt = build_first_llm_prompt(
        user_query=state["user_query"],
        constraints=state.get("user_constraints", {}),
        rag_results=state.get("retrieved_docs", [])
    )
    
    # JSON 응답을 위한 프롬프트 추가
    json_instruction = """

반드시 아래 JSON 형식으로만 응답하세요:
{
    "draft": "초안 답변 내용",
    "need_tools": true 또는 false,
    "thought": "현재 생각 과정",
    "action": "사용할 도구 이름 (shopping_search, recipe_search, calorie, weather 등) 또는 null",
    "action_input": "도구에 전달할 입력값",
    "tool_queries": ["검색할 쿼리 리스트"]
}

도구 목록:
- shopping_search: 재료 가격 검색
- recipe_search: 레시피 검색
- calorie: 칼로리 정보
- weather: 날씨 정보
- health_guidelines: 건강/질병 관련 정보
"""
    
    try:
        # 실제 LLM 호출
        response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt + json_instruction,
            json_mode=True
        )
        result = json.loads(response)
        
    except Exception as e:
        print(f"[main_agent] 1차 LLM 오류: {e}")
        # 오류 시 기본 응답
        result = {
            "draft": f"'{state['user_query']}'에 대해 답변드리겠습니다.",
            "need_tools": False,
            "thought": "LLM 호출 중 오류가 발생했습니다.",
            "action": None,
            "action_input": "",
            "tool_queries": []
        }
    
    # ReAct 스텝 생성
    new_step: ReActStep = {
        "thought": result.get("thought", "초안을 작성하고 도구 필요 여부를 판단한다."),
        "action": result.get("action"),
        "action_input": result.get("action_input", ""),
        "observation": None
    }
    
    # State 업데이트
    updates = {
        "llm_1st_response": result.get("draft", ""),
        "need_web_search": result.get("need_tools", False),
        "search_queries": result.get("tool_queries", []),
        "current_thought": new_step["thought"],
        "current_action": result.get("action"),
        "current_action_input": result.get("action_input", ""),
        "react_steps": [new_step],
        "iteration_count": state["iteration_count"] + 1,
        "current_step": "1st_llm_done",
        
        # LLM 호출 기록
        **record_llm_call(
            state,
            call_type="1st_llm",
            node_name="main_agent",
            input_summary=f"Query: {state['user_query'][:50]}",
            output_summary=f"Draft: {result.get('draft', '')[:50]}"
        )
    }
    
    return updates


# ============================================================
# 2차 LLM 호출
# ============================================================

def call_second_llm(state: AgentState) -> dict:
    """
    2차 LLM 호출
    - 도구 결과 반영
    - 최종 답변 생성
    """
    
    # 프롬프트 생성
    system_prompt, user_prompt = build_second_llm_prompt(
        draft=state["llm_1st_response"],
        search_results=state.get("search_results", []),
        constraints=state.get("user_constraints", {})
    )
    
    try:
        # 실제 LLM 호출
        final_answer = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False
        )
        
    except Exception as e:
        print(f"[main_agent] 2차 LLM 오류: {e}")
        # 오류 시 검색 결과 기반 기본 응답 생성
        final_answer = format_fallback_response(state)
    
    # ReAct 스텝 업데이트 (FINISH)
    finish_step: ReActStep = {
        "thought": "도구 결과를 받았다. 최종 답변을 생성하자.",
        "action": "FINISH",
        "action_input": final_answer[:100],
        "observation": None
    }
    
    # State 업데이트
    updates = {
        "llm_2nd_response": final_answer,
        "final_response": final_answer,
        "react_steps": [finish_step],
        "current_thought": finish_step["thought"],
        "current_step": "2nd_llm_done",
        
        # LLM 호출 기록
        **record_llm_call(
            state,
            call_type="2nd_llm",
            node_name="main_agent",
            input_summary=f"Search results: {len(state.get('search_results', []))}개",
            output_summary=f"Final: {final_answer[:50]}"
        )
    }
    
    return updates


def format_fallback_response(state: AgentState) -> str:
    """LLM 오류 시 폴백 응답 생성"""
    query = state["user_query"]
    search_results = state.get("search_results", [])
    constraints = state.get("user_constraints", {})
    budget = constraints.get("budget", 0)
    
    # 가격 합계 계산
    total_price = sum(
        item.get("price", 0) 
        for item in search_results 
        if item.get("type") == "shopping"
    )
    
    response = f"## {query} 결과\n\n"
    
    # 검색 결과 정리
    if search_results:
        shopping_items = [r for r in search_results if r.get("type") == "shopping"]
        recipe_items = [r for r in search_results if r.get("type") == "recipe"]
        
        if shopping_items:
            response += "### 🛒 재료 목록\n"
            for item in shopping_items[:5]:
                response += f"- {item.get('title', '상품')}: {item.get('price', 0):,}원\n"
            response += f"\n**총 예상 비용: {total_price:,}원**\n"
            
            if budget:
                if total_price <= budget:
                    response += f"✅ 예산 {budget:,}원 내입니다.\n"
                else:
                    response += f"⚠️ 예산 {budget:,}원을 {total_price - budget:,}원 초과합니다.\n"
        
        if recipe_items:
            response += "\n### 🍳 레시피\n"
            for item in recipe_items[:2]:
                response += f"- {item.get('title', '레시피')}\n"
                response += f"  {item.get('content', '')[:100]}...\n"
    
    return response


# ============================================================
# 강제 종료 응답
# ============================================================

def generate_forced_answer(state: AgentState) -> str:
    """최대 반복 도달 시 강제 응답"""
    
    collected = []
    
    if state.get("llm_1st_response"):
        collected.append(f"초안: {state['llm_1st_response'][:200]}")
    
    for step in state.get("react_steps", [])[-3:]:
        if step.get("observation"):
            collected.append(f"- {step['observation'][:100]}")
    
    return f"""최대 탐색 횟수({state['max_iterations']}회)에 도달했습니다.

수집된 정보:
{chr(10).join(collected) if collected else '정보를 수집하지 못했습니다.'}

더 자세한 정보가 필요하시면 다시 질문해주세요."""