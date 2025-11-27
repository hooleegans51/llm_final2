"""
LLM 프롬프트 템플릿 모음

[프롬프트 종류]
1. 1차 LLM: 초안 생성 + 도구 필요 판단
2. 2차 LLM: 도구 결과 반영하여 최종 답변
3. Reflection: 메모리 반영
4. Summary: 메모리 압축
5. Modify: 수정 요청 처리
"""

# ============================================================
# 1차 LLM 프롬프트 (초안 + 도구 판단)
# ============================================================

FIRST_LLM_SYSTEM = """당신은 요리와 장보기를 도와주는 AI 어시스턴트입니다.

[역할]
1. 사용자의 요청을 분석합니다.
2. RAG 검색 결과를 참고하여 초안을 작성합니다.
3. 추가 정보(가격, 레시피 등)가 필요한지 판단합니다.

[출력 형식]
다음 JSON 형식으로 응답하세요:
{
    "draft": "초안 내용",
    "need_tools": true/false,
    "tool_queries": ["검색할 쿼리1", "검색할 쿼리2"],
    "reasoning": "도구가 필요한/불필요한 이유"
}

[도구 필요 상황]
- 가격 정보 필요: 장보기, 구매, 비용 관련
- 레시피 정보 필요: 만드는 법, 조리법 관련
- 최신 정보 필요: 할인, 행사, 시세 관련
"""

FIRST_LLM_USER = """[사용자 요청]
{user_query}

[제약조건]
{constraints}

[RAG 검색 결과]
{rag_results}

위 정보를 바탕으로 초안을 작성하고, 추가 도구 사용이 필요한지 판단해주세요."""


# ============================================================
# 2차 LLM 프롬프트 (도구 결과 반영)
# ============================================================

SECOND_LLM_SYSTEM = """당신은 요리와 장보기를 도와주는 AI 어시스턴트입니다.

[역할]
1. 초안과 웹 검색 결과를 종합합니다.
2. 사용자 제약조건(예산, 인원 등)을 확인합니다.
3. 최종 답변을 작성합니다.

[주의사항]
- 가격 정보는 검색 결과 기준으로 정확히 기재
- 예산 초과 시 명확히 안내
- 대안이 있다면 함께 제시
"""

SECOND_LLM_USER = """[초안]
{draft}

[웹 검색 결과]
{search_results}

[사용자 제약조건]
- 예산: {budget}원
- 인원: {servings}인분

검색 결과를 반영하여 최종 답변을 작성해주세요.
총 예상 비용도 계산해주세요."""


# ============================================================
# 🆕 ReAct 프롬프트
# ============================================================

REACT_SYSTEM = """당신은 요리와 장보기를 도와주는 AI 어시스턴트입니다.
ReAct (Reasoning + Acting) 패턴으로 사고하세요.

[사용 가능한 도구]
1. rag_search: 내부 레시피/요리 지식 검색
   - 입력: 검색 쿼리
   - 용도: 레시피, 조리법, 요리 팁

2. shopping_search: 상품 가격 검색
   - 입력: 상품명
   - 용도: 재료 가격, 구매처

3. recipe_search: 웹 레시피 검색
   - 입력: 요리명
   - 용도: 최신 레시피, 다양한 변형

4. web_search: 일반 웹 검색
   - 입력: 검색어
   - 용도: 기타 정보

5. calculator: 가격 계산
   - 입력: 계산식 (예: "15000 + 5000 + 3000")
   - 용도: 총 비용 계산

6. FINISH: 최종 답변 준비 완료
   - 입력: 최종 답변
   - 용도: 모든 정보 수집 완료 시

[사고 방식]
매 단계마다 다음 형식으로 응답하세요:

Thought: 현재 상황 분석, 다음에 뭘 해야 할지 생각
Action: 사용할 도구 이름 (위 목록 중 하나)
Action Input: 도구에 전달할 입력값

[규칙]
1. 한 번에 하나의 도구만 선택
2. 충분한 정보가 모이면 FINISH 사용
3. 예산 초과 시 반드시 언급
4. 최대 {max_iterations}번 반복 가능

[예시]
Thought: 사용자가 스테이크 재료를 요청했다. 먼저 스테이크 레시피를 찾아서 필요한 재료를 파악해야겠다.
Action: rag_search
Action Input: 스테이크 레시피 재료"""


REACT_USER = """[사용자 요청]
{user_query}

[제약조건]
{constraints}

[이전 단계들]
{previous_steps}

[현재까지 수집한 정보]
- RAG 결과: {rag_summary}
- 검색 결과: {search_summary}

이제 다음 단계를 진행하세요.
Thought:"""


REACT_OBSERVATION = """[Observation]
{observation}

위 결과를 바탕으로 다음 단계를 진행하세요.
Thought:"""

# ============================================================
# Reflection 프롬프트 (메모리 반영)
# ============================================================

REFLECTION_SYSTEM = """당신은 사용자 맞춤형 응답을 만드는 AI입니다.

[역할]
1. 기존 응답을 검토합니다.
2. 사용자의 과거 선호도/제한사항을 반영합니다.
3. 개인화된 최종 응답을 생성합니다.

[반영 우선순위]
1. 알레르기/제한사항 (필수)
2. 선호도 (권장)
3. 과거 이력 (참고)
"""

REFLECTION_USER = """[현재 응답]
{current_response}

[장기 메모리 - 사용자 정보]
{long_memory}

[단기 메모리 - 최근 대화]
{short_memory}

위 메모리 정보를 반영하여 응답을 개선해주세요.
특히 알레르기나 제한사항이 있다면 반드시 반영하세요."""


# ============================================================
# Summary 프롬프트 (메모리 압축)
# ============================================================

SUMMARY_SYSTEM = """당신은 대화 내용을 요약하는 AI입니다.

[역할]
여러 턴의 대화를 간결하게 요약합니다.

[요약 포함 내용]
1. 주요 요청 사항
2. 사용자 선호도/제한사항
3. 중요한 결정 사항

[요약 제외 내용]
- 인사말, 감사 표현
- 중복되는 내용
- 사소한 확인 질문
"""

SUMMARY_USER = """[대화 내용]
{conversations}

위 대화를 3-5문장으로 요약해주세요.
사용자의 선호도나 제한사항은 반드시 포함하세요."""


# ============================================================
# Modify 프롬프트 (수정 요청 처리)
# ============================================================

MODIFY_SYSTEM = """당신은 기존 응답을 수정하는 AI입니다.

[수정 유형]
1. servings: 인원수 변경 → 재료 양 조절
2. ingredient: 재료 변경 → 대체 재료 적용
3. budget: 예산 변경 → 가격대 조절
4. preference: 선호도 반영 → 조리법/재료 조정

[주의사항]
- 원본의 핵심 내용은 유지
- 변경된 부분만 명확히 표시
- 변경 이유 간단히 설명
"""

MODIFY_USER = """[원본 응답]
{original_response}

[수정 요청]
{modification_request}

[수정 유형]
{modification_type}

[참고 - 최근 대화]
{short_memory}

수정 요청을 반영하여 응답을 수정해주세요."""


# ============================================================
# 도구 판단 프롬프트 -> dkdkdkdkdkdkkd
# ============================================================

TOOL_DECISION_SYSTEM = """사용자 요청을 분석하여 필요한 도구를 판단하세요.

[사용 가능한 도구]
1. shopping_search: 상품 가격 검색
2. recipe_search: 레시피 검색
3. web_search: 일반 웹 검색
4. calculator: 가격 계산
5. calorie: 칼로리 계산

[출력 형식]
{
    "tools_needed": ["tool1", "tool2"],
    "queries": {
        "tool1": "검색 쿼리",
        "tool2": "검색 쿼리"
    }
}
"""


# ============================================================
# 헬퍼 함수
# ============================================================

def format_rag_results(docs: list) -> str:
    """RAG 결과 포맷팅"""
    if not docs:
        return "검색 결과 없음"
    
    formatted = []
    for i, doc in enumerate(docs, 1):
        content = doc.get("content", "")[:300]
        score = doc.get("score", 0)
        formatted.append(f"[{i}] (관련도: {score:.2f})\n{content}")
    
    return "\n\n".join(formatted)


def format_search_results(results: list) -> str:
    """웹 검색 결과 포맷팅"""
    if not results:
        return "검색 결과 없음"
    
    formatted = []
    for item in results:
        item_type = item.get("type", "general")
        
        if item_type == "shopping":
            formatted.append(
                f"🛒 {item.get('title', '')}\n"
                f"   가격: {item.get('price', 0):,}원\n"
                f"   출처: {item.get('source', '')}"
            )
        elif item_type == "recipe":
            formatted.append(
                f"🍳 {item.get('title', '')}\n"
                f"   {item.get('content', '')[:100]}"
            )
        else:
            formatted.append(
                f"🔍 {item.get('title', '')}\n"
                f"   {item.get('snippet', '')[:100]}"
            )
    
    return "\n\n".join(formatted)


def format_constraints(constraints: dict) -> str:
    """제약조건 포맷팅"""
    if not constraints:
        return "없음"
    
    parts = []
    if "budget" in constraints:
        parts.append(f"예산: {constraints['budget']:,}원")
    if "servings" in constraints:
        parts.append(f"인원: {constraints['servings']}인분")
    if "allergies" in constraints:
        parts.append(f"알레르기: {', '.join(constraints['allergies'])}")
    if "preferences" in constraints:
        parts.append(f"선호: {', '.join(constraints['preferences'])}")
    
    return ", ".join(parts) if parts else "없음"


def format_memory(memories: list) -> str:
    """메모리 포맷팅"""
    if not memories:
        return "없음"
    
    formatted = []
    for mem in memories:
        if isinstance(mem, dict):
            mem_type = mem.get("type", "")
            content = mem.get("content", "")
            formatted.append(f"- [{mem_type}] {content}")
        else:
            formatted.append(f"- {mem}")
    
    return "\n".join(formatted)


def build_first_llm_prompt(
    user_query: str,
    constraints: dict,
    rag_results: list
) -> tuple:
    """1차 LLM 프롬프트 생성"""
    system = FIRST_LLM_SYSTEM
    user = FIRST_LLM_USER.format(
        user_query=user_query,
        constraints=format_constraints(constraints),
        rag_results=format_rag_results(rag_results)
    )
    return system, user


def build_second_llm_prompt(
    draft: str,
    search_results: list,
    constraints: dict
) -> tuple:
    """2차 LLM 프롬프트 생성"""
    system = SECOND_LLM_SYSTEM
    user = SECOND_LLM_USER.format(
        draft=draft,
        search_results=format_search_results(search_results),
        budget=constraints.get("budget", "제한 없음"),
        servings=constraints.get("servings", 1)
    )
    return system, user


def build_reflection_prompt(
    current_response: str,
    long_memory: list,
    short_memory: list
) -> tuple:
    """Reflection 프롬프트 생성"""
    system = REFLECTION_SYSTEM
    user = REFLECTION_USER.format(
        current_response=current_response,
        long_memory=format_memory(long_memory),
        short_memory=format_memory(short_memory)
    )
    return system, user


def build_modify_prompt(
    original_response: str,
    modification_request: str,
    modification_type: str,
    short_memory: list
) -> tuple:
    """수정 프롬프트 생성"""
    system = MODIFY_SYSTEM
    user = MODIFY_USER.format(
        original_response=original_response,
        modification_request=modification_request,
        modification_type=modification_type,
        short_memory=format_memory(short_memory)
    )
    return system, user


# ============================================================
# ReAct 헬퍼 함수
# ============================================================

def format_react_steps(steps: list) -> str:
    """이전 ReAct 스텝들 포맷팅"""
    if not steps:
        return "없음 (첫 번째 단계)"
    
    formatted = []
    for i, step in enumerate(steps, 1):
        formatted.append(f"--- Step {i} ---")
        formatted.append(f"Thought: {step.get('thought', '')}")
        if step.get('action'):
            formatted.append(f"Action: {step.get('action', '')}")
            formatted.append(f"Action Input: {step.get('action_input', '')}")
        if step.get('observation'):
            formatted.append(f"Observation: {step.get('observation', '')[:200]}...")
    
    return "\n".join(formatted)


def format_info_summary(items: list, max_items: int = 3) -> str:
    """정보 요약"""
    if not items:
        return "없음"
    
    summaries = []
    for item in items[:max_items]:
        if isinstance(item, dict):
            title = item.get("title", item.get("content", ""))[:50]
            summaries.append(f"- {title}")
        else:
            summaries.append(f"- {str(item)[:50]}")
    
    if len(items) > max_items:
        summaries.append(f"... 외 {len(items) - max_items}개")
    
    return "\n".join(summaries)


def build_react_prompt(state: dict) -> tuple:
    """ReAct 프롬프트 생성"""
    system = REACT_SYSTEM.format(
        max_iterations=state.get("max_iterations", 5)
    )
    
    user = REACT_USER.format(
        user_query=state.get("user_query", ""),
        constraints=format_constraints(state.get("user_constraints", {})),
        previous_steps=format_react_steps(state.get("react_steps", [])),
        rag_summary=format_info_summary(state.get("retrieved_docs", [])),
        search_summary=format_info_summary(state.get("search_results", []))
    )
    
    return system, user


def build_react_observation_prompt(observation: str) -> str:
    """Observation 후 프롬프트"""
    return REACT_OBSERVATION.format(observation=observation)


def parse_react_response(response: str) -> dict:
    """LLM 응답에서 ReAct 파싱"""
    result = {
        "thought": "",
        "action": None,
        "action_input": ""
    }
    
    lines = response.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("Thought:"):
            result["thought"] = line[8:].strip()
        elif line.startswith("Action:"):
            result["action"] = line[7:].strip()
        elif line.startswith("Action Input:"):
            result["action_input"] = line[13:].strip()
    
    return result