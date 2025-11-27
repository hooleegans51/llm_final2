"""
Tool 노드 - 웹 검색 + LLM 결과 해석

[역할]
1. 도구 실행 (Google Search 등)
2. LLM으로 결과 해석 (n차 호출)
3. Observation 반환
4. 예산 초과 체크 → constraint_violations

[흐름]
도구 실행 → LLM 해석 (n차) → Observation → main_agent로 복귀
"""

from typing import List, Dict, Any
import re

from core.state import AgentState, ReActStep, record_llm_call
from core.prompts import format_constraints

# 기존 도구들 import
from web_search_tools.shopping_tool import search_shopping
from web_search_tools.recipe_tools import search_recipe
from web_search_tools.websearch_tool import web_search


def tool_node(state: AgentState) -> dict:
    """
    도구 실행 + LLM 해석 노드
    
    [단계]
    1. 도구 실행 (검색)
    2. LLM으로 결과 해석 (n차 호출)
    3. Observation 생성
    4. 제약조건 체크
    """
    
    action = state.get("current_action", "")
    action_input = state.get("current_action_input", "")
    queries = state.get("search_queries", [])
    constraints = state.get("user_constraints", {})
    budget = constraints.get("budget", float("inf"))
    
    # 쿼리 없으면 action_input 사용
    if not queries and action_input:
        queries = [action_input]
    
    all_results = []
    total_price = 0
    constraint_violations = []
    
    # =========================================
    # 1. 도구 실행
    # =========================================
    
    for query in queries:
        if action == "shopping_search" or "가격" in query or "장보기" in query:
            results = execute_shopping_search(query)
            for item in results:
                total_price += item.get("price", 0)
            all_results.extend(results)
        
        elif action == "recipe_search" or "레시피" in query:
            results = execute_recipe_search(query)
            all_results.extend(results)
        
        elif action == "rag_search":
            results = execute_rag_search(query)
            all_results.extend(results)
        
        else:
            results = execute_web_search(query)
            all_results.extend(results)
    
    # =========================================
    # 2. 예산 초과 체크
    # =========================================
    
    if total_price > budget:
        constraint_violations.append({
            "type": "budget_exceed",
            "budget": budget,
            "actual": total_price,
            "diff": total_price - budget
        })
    
    # =========================================
    # 3. LLM으로 결과 해석 (n차 호출)
    # =========================================
    
    observation, llm_record = interpret_results_with_llm(
        state=state,
        action=action,
        action_input=action_input,
        results=all_results,
        total_price=total_price,
        constraints=constraints
    )
    
    # =========================================
    # 4. ReAct 스텝 업데이트
    # =========================================
    
    updated_steps = update_observation_in_steps(state, observation)
    
    # =========================================
    # 5. State 업데이트
    # =========================================
    
    return {
        "search_results": state.get("search_results", []) + all_results,
        "constraint_violations": constraint_violations,
        "react_steps": updated_steps,
        "current_step": "tool_done",
        
        # LLM 호출 기록
        **llm_record
    }


# ============================================================
# 도구 실행 함수들
# ============================================================

def execute_shopping_search(query: str) -> List[Dict[str, Any]]:
    """쇼핑 검색 실행"""
    try:
        raw_results = search_shopping(query)
    except Exception as e:
        print(f"[tool_node] shopping_search 오류: {e}")
        raw_results = []
    
    results = []
    for item in raw_results:
        price = parse_price(item.get("price", "0"))
        results.append({
            "type": "shopping",
            "query": query,
            "title": item.get("title", ""),
            "price": price,
            "link": item.get("link", ""),
            "source": item.get("source", "")
        })
    
    # Mock 데이터 (실제 API 없을 때)
    if not results:
        results = [
            {"type": "shopping", "query": query, "title": "소고기 등심 300g", "price": 15000, "link": "", "source": "이마트"},
            {"type": "shopping", "query": query, "title": "버터 100g", "price": 5000, "link": "", "source": "쿠팡"},
            {"type": "shopping", "query": query, "title": "마늘 1팩", "price": 3000, "link": "", "source": "마켓컬리"},
        ]
    
    return results


def execute_recipe_search(query: str) -> List[Dict[str, Any]]:
    """레시피 검색 실행"""
    try:
        raw_results = search_recipe(query)
    except Exception as e:
        print(f"[tool_node] recipe_search 오류: {e}")
        raw_results = []
    
    results = []
    for item in raw_results:
        results.append({
            "type": "recipe",
            "query": query,
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "link": item.get("link", "")
        })
    
    # Mock 데이터
    if not results:
        results = [
            {
                "type": "recipe",
                "query": query,
                "title": "간단 스테이크 레시피",
                "content": "1. 소고기를 상온에 30분 둔다. 2. 소금, 후추로 간한다. 3. 버터를 녹여 굽는다.",
                "link": ""
            },
        ]
    
    return results


def execute_web_search(query: str) -> List[Dict[str, Any]]:
    """일반 웹 검색 실행"""
    try:
        raw_results = web_search(query)
    except Exception as e:
        print(f"[tool_node] web_search 오류: {e}")
        raw_results = []
    
    results = []
    for item in raw_results:
        results.append({
            "type": "general",
            "query": query,
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", "")
        })
    
    return results


def execute_rag_search(query: str) -> List[Dict[str, Any]]:
    """RAG 검색 실행"""
    try:
        from rag.retrieval import retrieve_documents
        from rag.embedder import get_embedding
        
        embedding = get_embedding(query)
        raw_results = retrieve_documents(query_embedding=embedding, top_k=3)
    except Exception as e:
        print(f"[tool_node] rag_search 오류: {e}")
        raw_results = []
    
    results = []
    for doc in raw_results:
        results.append({
            "type": "rag",
            "query": query,
            "content": doc.get("content", ""),
            "score": doc.get("score", 0)
        })
    
    return results


# ============================================================
# LLM 결과 해석 (n차 호출)
# ============================================================

def interpret_results_with_llm(
    state: AgentState,
    action: str,
    action_input: str,
    results: List[Dict[str, Any]],
    total_price: int,
    constraints: Dict[str, Any]
) -> tuple:
    """
    검색 결과를 LLM이 해석
    
    Returns:
        (observation: str, llm_record: dict)
    """
    
    if not results:
        observation = f"'{action_input}' 검색 결과가 없습니다."
        llm_record = record_llm_call(
            state,
            call_type="tool_interpret",
            node_name="tool_node",
            input_summary=f"No results for: {action_input[:30]}",
            output_summary="No results"
        )
        return observation, llm_record
    
    # 프롬프트 구성
    system_prompt = get_interpret_system_prompt(action)
    user_prompt = get_interpret_user_prompt(
        action=action,
        query=action_input,
        results=results,
        total_price=total_price,
        constraints=constraints
    )
    
    # TODO: 실제 LLM 호출
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(model="gpt-4")
    # response = llm.invoke([
    #     {"role": "system", "content": system_prompt},
    #     {"role": "user", "content": user_prompt}
    # ])
    # observation = response.content
    
    # ========== Mock 응답 ==========
    observation = mock_interpret_results(action, results, total_price, constraints)
    
    # LLM 호출 기록
    llm_record = record_llm_call(
        state,
        call_type="tool_interpret",
        node_name="tool_node",
        input_summary=f"{action}: {len(results)}개 결과",
        output_summary=observation[:50]
    )
    
    return observation, llm_record


def get_interpret_system_prompt(action: str) -> str:
    """도구별 해석 시스템 프롬프트"""
    prompts = {
        "shopping_search": """당신은 쇼핑 결과 분석 전문가입니다.
검색 결과를 분석하여:
1. 상품별 가격 정리
2. 총 비용 계산
3. 예산 대비 평가
를 간결하게 제공하세요.""",
        
        "recipe_search": """당신은 요리 전문가입니다.
레시피 검색 결과를 분석하여:
1. 핵심 재료 목록
2. 조리 단계 요약
3. 난이도와 예상 시간
을 제공하세요.""",
        
        "rag_search": """검색된 문서에서 핵심 정보를 추출하세요.""",
        
        "web_search": """웹 검색 결과에서 신뢰할 수 있는 정보를 선별하고 요약하세요."""
    }
    return prompts.get(action, "검색 결과를 분석하고 요약하세요.")


def get_interpret_user_prompt(
    action: str,
    query: str,
    results: List[Dict[str, Any]],
    total_price: int,
    constraints: Dict[str, Any]
) -> str:
    """도구 해석 유저 프롬프트"""
    
    # 결과 포맷팅
    results_text = format_results_for_interpret(results, action)
    budget = constraints.get("budget", "제한 없음")
    
    return f"""[검색 쿼리]
{query}

[검색 결과]
{results_text}

[총 가격]
{total_price:,}원

[예산]
{budget if isinstance(budget, str) else f"{budget:,}원"}

위 결과를 분석해주세요."""


def format_results_for_interpret(results: List[Dict], action: str) -> str:
    """LLM 해석용 결과 포맷"""
    lines = []
    
    for i, item in enumerate(results[:7], 1):
        if item.get("type") == "shopping":
            lines.append(f"{i}. {item.get('title', '')} - {item.get('price', 0):,}원 ({item.get('source', '')})")
        elif item.get("type") == "recipe":
            lines.append(f"{i}. {item.get('title', '')}")
            lines.append(f"   {item.get('content', '')[:80]}...")
        elif item.get("type") == "rag":
            lines.append(f"{i}. (관련도: {item.get('score', 0):.2f}) {item.get('content', '')[:100]}...")
        else:
            lines.append(f"{i}. {item.get('title', '')} - {item.get('snippet', '')[:60]}...")
    
    return "\n".join(lines)


def mock_interpret_results(
    action: str,
    results: List[Dict],
    total_price: int,
    constraints: Dict[str, Any]
) -> str:
    """Mock LLM 해석 결과"""
    budget = constraints.get("budget", float("inf"))
    
    if action == "shopping_search":
        status = "✅ 예산 내" if total_price <= budget else f"⚠️ 예산 초과 ({total_price - budget:,}원)"
        
        items_summary = "\n".join([
            f"- {r.get('title', '')}: {r.get('price', 0):,}원"
            for r in results[:5] if r.get("type") == "shopping"
        ])
        
        return f"""[쇼핑 검색 분석]
상품 {len(results)}개 발견

{items_summary}

💰 총 비용: {total_price:,}원 {status}"""
    
    elif action == "recipe_search":
        recipe = results[0] if results else {}
        return f"""[레시피 검색 분석]
레시피: {recipe.get('title', '레시피')}

{recipe.get('content', '조리법 정보 없음')[:150]}...

⏱️ 예상 조리시간: 약 30분"""
    
    elif action == "rag_search":
        contents = "\n".join([
            f"- {r.get('content', '')[:80]}..."
            for r in results[:3]
        ])
        return f"""[내부 지식 검색 분석]
관련 문서 {len(results)}개 발견

{contents}"""
    
    else:
        return f"[검색 분석] {len(results)}개 결과 발견"


# ============================================================
# 헬퍼 함수들
# ============================================================

def update_observation_in_steps(state: AgentState, observation: str) -> list:
    """마지막 ReAct 스텝에 Observation 추가"""
    steps = list(state.get("react_steps", []))
    
    if steps:
        # 마지막 스텝 업데이트
        last_step = dict(steps[-1])
        last_step["observation"] = observation
        steps[-1] = last_step
    
    return steps


def parse_price(price_str: str) -> int:
    """가격 문자열 → 정수"""
    if not price_str:
        return 0
    if isinstance(price_str, int):
        return price_str
    
    numbers = re.findall(r'\d+', str(price_str).replace(",", ""))
    return int("".join(numbers)) if numbers else 0


