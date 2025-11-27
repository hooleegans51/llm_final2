"""
메인 에이전트 노드 (수정본 - 디버그 로그 포함)
"""

import os
import json
from typing import Dict, Any

from dotenv import load_dotenv

from core.state import AgentState, ReActStep, record_llm_call
from core.prompts import (
    build_first_llm_prompt,
    build_second_llm_prompt,
    format_search_results
)

load_dotenv()

# ============================================================
# OpenAI 클라이언트 설정
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

_client = None

def get_openai_client():
    """OpenAI 클라이언트 싱글톤"""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            print("[main_agent] 오류: OPENAI_API_KEY 없음!")
            return None
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=OPENAI_API_KEY)
            print("[main_agent] OpenAI 클라이언트 생성 완료")
        except Exception as e:
            print(f"[main_agent] OpenAI 초기화 실패: {e}")
    return _client


def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """OpenAI LLM 호출"""
    print("[call_llm] 함수 진입")
    
    client = get_openai_client()
    
    if client is None:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
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
    
    print(f"[call_llm] API 호출 시작 (model: {CHAT_MODEL})")
    response = client.chat.completions.create(**kwargs)
    print("[call_llm] API 호출 완료")
    
    return response.choices[0].message.content


# ============================================================
# 메인 에이전트 노드
# ============================================================

def main_agent_node(state: AgentState) -> dict:
    """메인 에이전트 노드"""
    
    print(f"[main_agent] 진입 - 1st: {bool(state.get('llm_1st_response'))}, 2nd: {bool(state.get('llm_2nd_response'))}, search: {len(state.get('search_results', []))}")
    
    # 1. 이미 최종 응답 있으면 종료
    if state.get("final_response"):
        print("[main_agent] 이미 완료됨")
        return {"current_step": "complete"}
    
    # 2. 검색 결과 있고 2차 LLM 안 했으면 → 2차 호출
    if state.get("search_results") and not state.get("llm_2nd_response"):
        print("[main_agent] 2차 LLM 호출")
        return call_second_llm(state)
    
    # 3. 1차 LLM 안 했으면 → 1차 호출
    if not state.get("llm_1st_response"):
        print("[main_agent] 1차 LLM 호출")
        return call_first_llm(state)
    
    # 4. 1차 완료, 도구 불필요 → 1차 응답으로 종료
    if state.get("llm_1st_response") and not state.get("need_web_search"):
        print("[main_agent] 도구 불필요, 완료")
        return {
            "final_response": state["llm_1st_response"],
            "current_step": "complete"
        }
    
    # 5. 도구 필요 → tool 노드로
    if state.get("need_web_search"):
        print("[main_agent] 도구 필요, tool로")
        return {"current_step": "need_tool"}
    
    # 6. 예외 - 강제 종료
    print("[main_agent] 예외 상황, 강제 종료")
    return {
        "final_response": state.get("llm_1st_response", "죄송합니다. 응답을 생성하지 못했습니다."),
        "current_step": "complete"
    }


# ============================================================
# 1차 LLM 호출
# ============================================================

def call_first_llm(state: AgentState) -> dict:
    """1차 LLM - 초안 + 도구 판단"""
    
    print("[call_first_llm] 함수 진입")
    
    system_prompt, user_prompt = build_first_llm_prompt(
        user_query=state["user_query"],
        constraints=state.get("user_constraints", {}),
        rag_results=state.get("retrieved_docs", [])
    )
    
    print(f"[call_first_llm] 프롬프트 생성 완료, user_query: {state['user_query'][:30]}")
    
    json_instruction = """

반드시 아래 JSON 형식으로만 응답하세요:
{
    "draft": "초안 답변 내용 (상세하게)",
    "need_tools": true 또는 false,
    "thought": "생각 과정",
    "tool_queries": ["검색 쿼리"] 
}

도구가 필요한 경우:
- 가격/구매 정보가 필요할 때
- 최신 레시피를 찾아야 할 때
- 칼로리/영양 정보가 필요할 때

일반적인 레시피 질문은 도구 없이 바로 답변 가능합니다.
"""
    
    try:
        print("[call_first_llm] LLM 호출 시작...")
        response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt + json_instruction,
            json_mode=True
        )
        print(f"[call_first_llm] LLM 호출 완료! 응답 길이: {len(response)}")
        print(f"[call_first_llm] 응답 미리보기: {response[:200]}")
        
        result = json.loads(response)
        print(f"[call_first_llm] JSON 파싱 완료 - need_tools: {result.get('need_tools')}")
        
    except Exception as e:
        print(f"[call_first_llm] 오류 발생: {e}")
        # 오류 시 직접 답변 생성
        return {
            "llm_1st_response": f"'{state['user_query']}'에 대한 답변입니다.",
            "need_web_search": False,
            "final_response": f"'{state['user_query']}'에 대한 답변입니다.",
            "current_step": "complete"
        }
    
    draft = result.get("draft", "")
    need_tools = result.get("need_tools", False)
    
    print(f"[call_first_llm] draft 길이: {len(draft)}, need_tools: {need_tools}")
    
    updates = {
        "llm_1st_response": draft,
        "need_web_search": need_tools,
        "search_queries": result.get("tool_queries", []),
        "current_step": "1st_llm_done",
        "iteration_count": state.get("iteration_count", 0) + 1
    }
    
    # 도구 불필요하면 바로 최종 응답 설정
    if not need_tools:
        updates["final_response"] = draft
        updates["current_step"] = "complete"
        print("[call_first_llm] 도구 불필요 - 완료 처리")
    
    return updates


# ============================================================
# 2차 LLM 호출
# ============================================================

def call_second_llm(state: AgentState) -> dict:
    """2차 LLM - 도구 결과 반영"""
    
    print("[call_second_llm] 함수 진입")
    
    system_prompt, user_prompt = build_second_llm_prompt(
        draft=state["llm_1st_response"],
        search_results=state.get("search_results", []),
        constraints=state.get("user_constraints", {})
    )
    
    try:
        print("[call_second_llm] LLM 호출 시작...")
        final_answer = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False
        )
        print(f"[call_second_llm] LLM 호출 완료! 응답 길이: {len(final_answer)}")
        
    except Exception as e:
        print(f"[call_second_llm] 오류 발생: {e}")
        final_answer = state.get("llm_1st_response", "응답 생성 실패")
    
    return {
        "llm_2nd_response": final_answer,
        "final_response": final_answer,
        "current_step": "complete"
    }


# ============================================================
# 헬퍼 함수
# ============================================================

def handle_interrupt_response(state: AgentState) -> dict:
    """Interrupt 응답 처리"""
    response = state.get("user_interrupt_response")
    
    if response == "취소":
        return {
            "final_response": "작업을 취소했습니다.",
            "current_step": "cancelled"
        }
    
    return {"current_step": "continue"}


def generate_forced_answer(state: AgentState) -> str:
    """강제 종료 응답"""
    return state.get("llm_1st_response", "응답을 생성하지 못했습니다.")